# -*- coding: utf-8 -*-

__doc__ = """\
Module for minification functions.
"""

# Import built-in modules
import re, tokenize, keyword
try:
    import cStringIO as io
except ImportError: # We're using Python 3
    import io

# Import our own modules
from . import analyze, token_utils

# Compile our regular expressions for speed
multiline_quoted_string = re.compile(r'(\'\'\'|\"\"\")')
not_quoted_string = re.compile(r'(\".*\'\'\'.*\"|\'.*\"\"\".*\')')
trailing_newlines = re.compile(r'\n\n')
multiline_indicator = re.compile('\\\\(\s*#.*)?\n')
left_of_equals = re.compile('^.*?=')
# The above also removes trailing comments: "test = 'blah \ # comment here"

# These aren't used but they're a pretty good reference:
double_quoted_string = re.compile(r'((?<!\\)".*?(?<!\\)")')
single_quoted_string = re.compile(r"((?<!\\)'.*?(?<!\\)')")
single_line_single_quoted_string = re.compile(r"((?<!\\)'''.*?(?<!\\)''')")
single_line_double_quoted_string = re.compile(r'((?<!\\)""".*?(?<!\\)""")')

def remove_comments(tokens):
    """
    Removes comments from *tokens* which is expected to be a list equivalent of
    tokenize.generate_tokens() (so we can update in-place).

    .. note::

        * If the comment makes up the whole line, the newline will also be removed (so you don't end up with lots of blank lines).
        * Preserves shebangs and encoding strings.
    """
    preserved_shebang = ""
    preserved_encoding = ""
    # This (short) loop preserves shebangs and encoding strings:
    for tok in tokens[0:4]: # Will always be in the first four tokens
        line = tok[4]
        # Save the first comment line if it starts with a shebang
        # (e.g. '#!/usr/bin/env python')
        if analyze.shebang.match(line): # Must be first line
            preserved_shebang = line
        # Save the encoding string (must be first or second line in file)
        # (e.g. '# -*- coding: utf-8 -*-')
        elif analyze.encoding.match(line):
            preserved_encoding = line
    # Now remove comments:
    prev_tok_type = 0
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        if token_type == tokenize.COMMENT:
            tokens[index][1] = '' # Making it an empty string removes it
        # TODO: Figure out a way to make this work
        #elif prev_tok_type == tokenize.COMMENT:
            #if token_type == tokenize.NL:
                #tokens[index][1] = '' # Remove trailing newline
        prev_tok_type = token_type
    # Prepend our preserved items back into the token list:
    if preserved_shebang: # Have to re-tokenize them
        io_obj = io.StringIO(preserved_shebang + preserved_encoding)
        preserved = [list(a) for a in tokenize.generate_tokens(io_obj.readline)]
        preserved.pop() # Get rid of ENDMARKER
        preserved.reverse() # Round and round we go!
        for item in preserved:
            tokens.insert(0, item)

def remove_docstrings(tokens):
    """
    Removes docstrings from *tokens* which is expected to be a list equivalent
    of `tokenize.generate_tokens()` (so we can update in-place).
    """
    prev_tok_type = None
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        if token_type == tokenize.STRING:
            if prev_tok_type == tokenize.INDENT:
                # Definitely a docstring
                tokens[index][1] = '' # Remove it
                # Remove the leftover indentation and newline:
                tokens[index-1][1] = ''
                tokens[index-2][1] = ''
            elif prev_tok_type == tokenize.NL:
                # This captures whole-module docstrings:
                if tokens[index+1][0] == tokenize.NEWLINE:
                    tokens[index][1] = ''
                    # Remove the trailing newline:
                    tokens[index+1][1] = ''
        prev_tok_type = token_type

def remove_comments_and_docstrings(source):
    """
    Returns *source* minus comments and docstrings.

    .. note:: Uses Python's built-in tokenize module to great effect.

    Example::

        def noop(): # This is a comment
            '''
            Does nothing.
            '''
            pass # Don't do anything

    Will become::

        def noop():
            pass
    """
    io_obj = io.StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += (" " * (start_col - last_col))
        # Remove comments:
        if token_type == tokenize.COMMENT:
            pass
        # This series of conditionals removes docstrings:
        elif token_type == tokenize.STRING:
            if prev_toktype != tokenize.INDENT:
        # This is likely a docstring; double-check we're not inside an operator:
                if prev_toktype != tokenize.NEWLINE:
                    # Note regarding NEWLINE vs NL: The tokenize module
                    # differentiates between newlines that start a new statement
                    # and newlines inside of operators such as parens, brackes,
                    # and curly braces.  Newlines inside of operators are
                    # NEWLINE and newlines that start new code are NL.
                    # Catch whole-module docstrings:
                    if start_col > 0:
                        # Unlabelled indentation means we're inside an operator
                        out += token_string
                    # Note regarding the INDENT token: The tokenize module does
                    # not label indentation inside of an operator (parens,
                    # brackets, and curly braces) as actual indentation.
                    # For example:
                    # def foo():
                    #     "The spaces before this docstring are tokenize.INDENT"
                    #     test = [
                    #         "The spaces before this string do not get a token"
                    #     ]
        else:
            out += token_string
        prev_toktype = token_type
        last_col = end_col
        last_lineno = end_line
    return out

def reduce_operators(source):
    """
    Remove spaces between operators in *source* and returns the result.
    Example::

        def foo(foo, bar, blah):
            test = "This is a %s" % foo

    Will become::

        def foo(foo,bar,blah):
            test="This is a %s"%foo

    ..  note::

        Also removes trailing commas and joins disjointed strings like
        ``("foo" "bar")``.
    """
    io_obj = io.StringIO(source)
    prev_tok = None
    out_tokens = []
    out = ""
    last_lineno = -1
    last_col = 0
    nl_types = (tokenize.NL, tokenize.NEWLINE)
    joining_strings = False
    new_string = ""
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        if start_line > last_lineno:
            last_col = 0
        if token_type != tokenize.OP:
            if start_col > last_col and token_type not in nl_types:
                if prev_tok[0] != tokenize.OP:
                    out += (" " * (start_col - last_col))
            if token_type == tokenize.STRING:
                if prev_tok[0] == tokenize.STRING:
                    # Join the strings into one
                    string_type = token_string[0] # '' or ""
                    prev_string_type = prev_tok[1][0]
                    out = out.rstrip(" ") # Remove any spaces we inserted prev
                    if not joining_strings:
                        # Remove prev token and start the new combined string
                        out = out[:(len(out)-len(prev_tok[1]))]
                        prev_string = prev_tok[1].strip(prev_string_type)
                        new_string = (
                            prev_string + token_string.strip(string_type))
                        joining_strings = True
                    else:
                        new_string += token_string.strip(string_type)
        else:
            if token_string in ('}', ')', ']'):
                if prev_tok[1] == ',':
                    out = out.rstrip(',')
            if joining_strings:
                # NOTE: Using triple quotes so that this logic works with
                # mixed strings using both single quotes and double quotes.
                out += "'''" + new_string + "'''"
                joining_strings = False
            if token_string == '@': # Decorators need special handling
                if prev_tok[0] == tokenize.NEWLINE:
                    # Ensure it gets indented properly
                    out += (" " * (start_col - last_col))
        if not joining_strings:
            out += token_string
        last_col = end_col
        last_lineno = end_line
        prev_tok = tok
    return out

def join_multiline_pairs(source, pair="()"):
    """
    Finds and removes newlines in multiline matching pairs of characters in
    *source*.

    By default it joins parens () but it will join any two characters given via
    the *pair* variable.

    .. note::

        Doesn't remove extraneous whitespace that ends up between the pair.
        Use `reduce_operators()` for that.

    Example::

        test = (
            "This is inside a multi-line pair of parentheses"
        )

    Will become::

        test = (            "This is inside a multi-line pair of parentheses"        )

    """
    opener = pair[0]
    closer = pair[1]
    io_obj = io.StringIO(source)
    out_tokens = []
    open_count = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.OP and token_string in pair:
            if token_string == opener:
                open_count += 1
            elif token_string == closer:
                open_count -= 1
            out_tokens.append(tok)
        elif token_type in (tokenize.NL, tokenize.NEWLINE):
            if open_count == 0:
                out_tokens.append(tok)
        else:
            out_tokens.append(tok)
    return token_utils.untokenize(out_tokens)

def dedent(source, use_tabs=False):
    """
    Minimizes indentation to save precious bytes.  Optionally, *use_tabs*
    may be specified if you want to use tabulators (\t) instead of spaces.

    Example::

        def foo(bar):
            test = "This is a test"

    Will become::

        def foo(bar):
         test = "This is a test"
    """
    if use_tabs:
        indent_char = '\t'
    else:
        indent_char = ' '
    io_obj = io.StringIO(source)
    out = ""
    last_lineno = -1
    last_col = 0
    prev_start_line = 0
    indentation = ""
    indentation_level = 0
    for i, tok in enumerate(tokenize.generate_tokens(io_obj.readline)):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        if start_line > last_lineno:
            last_col = 0
        if token_type == tokenize.INDENT:
            indentation_level += 1
            continue
        if token_type == tokenize.DEDENT:
            indentation_level -= 1
            continue
        indentation = indent_char * indentation_level
        if start_line > prev_start_line:
            if token_string in (',', '.'):
                out += str(token_string)
            else:
                out += indentation + str(token_string)
        elif start_col > last_col:
            out += indent_char + str(token_string)
        else:
            out += token_string
        prev_start_line = start_line
        last_col = end_col
        last_lineno = end_line
    return out

# TODO:  Rewrite this to use tokens
def fix_empty_methods(source):
    """
    Appends 'pass' to empty methods/functions (i.e. where there was nothing but
    a docstring before we removed it =).

    Example::

        # Note: This triple-single-quote inside a triple-double-quote is also a
        # pyminifier self-test
        def myfunc():
            '''This is just a placeholder function.'''

    Will become::

        def myfunc(): pass
    """
    def_indentation_level = 0
    output = ""
    just_matched = False
    previous_line = None
    method = re.compile(r'^\s*def\s*.*\(.*\):.*$')
    for line in source.split('\n'):
        if len(line.strip()) > 0: # Don't look at blank lines
            if just_matched == True:
                this_indentation_level = len(line.rstrip()) - len(line.strip())
                if def_indentation_level == this_indentation_level:
                    # This method is empty, insert a 'pass' statement
                    indent = " " * (def_indentation_level + 1)
                    output += "%s\n%spass\n%s\n" % (previous_line, indent, line)
                else:
                    output += "%s\n%s\n" % (previous_line, line)
                just_matched = False
            elif method.match(line):
                def_indentation_level = len(line) - len(line.strip())
                just_matched = True
                previous_line = line
            else:
                output += "%s\n" % line # Another self-test
        else:
            output += "\n"
    return output

def remove_blank_lines(source):
    """
    Removes blank lines from *source* and returns the result.

    Example:

    .. code-block:: python

        test = "foo"

        test2 = "bar"

    Will become:

    .. code-block:: python

        test = "foo"
        test2 = "bar"
    """
    io_obj = io.StringIO(source)
    source = [a for a in io_obj.readlines() if a.strip()]
    return "".join(source)

def minify(tokens, options):
    """
    Performs minification on *tokens* according to the values in *options*
    """
    # Remove comments
    remove_comments(tokens)
    # Remove docstrings
    remove_docstrings(tokens)
    result = token_utils.untokenize(tokens)
    # Minify our input script
    result = multiline_indicator.sub('', result)
    result = fix_empty_methods(result)
    result = join_multiline_pairs(result)
    result = join_multiline_pairs(result, '[]')
    result = join_multiline_pairs(result, '{}')
    result = remove_blank_lines(result)
    result = reduce_operators(result)
    result = dedent(result, use_tabs=options.tabs)
    return result

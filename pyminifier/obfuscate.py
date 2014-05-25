#!/usr/bin/env python
# -*- coding: utf-8 -*-

__doc__ = """\
A collection of functions for obfuscating code.
"""

import os, tokenize, keyword, sys
from itertools import permutations

# Import our own modules
from . import analyze
from . import token_utils

# Reserved words can be overridden by the script that imports this module
reserved_words = keyword.kwlist + analyze.builtins

def obfuscation_machine(use_unicode=False, count=1):
    """
    A generator that returns short sequential combinations of lower and
    upper-case letters that will never repeat.

    If use_unicode is True, use nonlatin cryllic, arabic, and syriac letters
    instead of the usual ABCs.
    """
    from random import shuffle
    # This generates a list of the letters a-z:
    lowercase = list(map(chr, range(97, 123)))
    # Same thing but ALL CAPS:
    uppercase = list(map(chr, range(65, 90)))
    if use_unicode:
        # Python 3 lets us have some *real* fun:
        arabic = list(map(chr, range(1580, 1594)))
        arabic2 = list(map(chr, range(1656, 1663)))
        syriac = list(map(chr, range(1811, 1838)))
        #dingbats = list(map(chr, range(9985, 10174))) #Python 3 doesn't like :(
        funfun = list(map(chr, range(11704, 11710))) # Loopy!
        combined = funfun + arabic + arabic2 + syriac
    else:
        combined = lowercase + uppercase
    shuffle(combined) # Randomize it all to keep things interesting
    while True:
        for perm in permutations(combined, count):
            perm = "".join(perm)
            if perm not in reserved_words: # Can't replace reserved words
                yield perm
        count += 1

def apply_obfuscation(source):
    """
    Returns 'source' all obfuscated.
    """
    global keyword_args
    global imported_modules
    tokens = token_utils.listified_tokenizer(source)
    keyword_args = analyze.enumerate_keyword_args(tokens)
    imported_modules = analyze.enumerate_imports(tokens)
    variables = find_obfuscatables(tokens, obfuscatable_variable)
    classes = find_obfuscatables(tokens, obfuscatable_class)
    functions = find_obfuscatables(tokens, obfuscatable_function)
    for variable in variables:
        replace_obfuscatables(
            tokens, obfuscate_variable, variable, name_generator)
    for function in functions:
        replace_obfuscatables(
            tokens, obfuscate_function, function, name_generator)
    for _class in classes:
        replace_obfuscatables(tokens, obfuscate_class, _class, name_generator)
    return token_utils.untokenize(tokens)

def find_obfuscatables(tokens, obfunc):
    """
    Iterates over *tokens*, which must be an equivalent output to what
    tokenize.generate_tokens() produces, calling *obfunc* on each with the
    following parameters:

        - **tok:**        The current token
        - **prev_tok:**   The previous token

    *obfunc* is expected to return the token string if that token can be safely
    obfuscated **or** one of the following optional values which will instruct
    find_obfuscatables() how to proceed:

        - **'__skipline__'**   Keep skipping tokens until a newline is reached.
        - **'__skipnext__'**   Skip the next token in the sequence.
    """
    global keyword_args
    keyword_args = analyze.enumerate_keyword_args(tokens)
    global imported_modules
    imported_modules = analyze.enumerate_imports(tokens)
    # Pretend the first line is '#\n':
    prev_tok = (54, '\n', (1, 1), (1, 2), '#\n')
    skip_line = False
    skip_next = False
    obfuscatables = []
    for count, tok in enumerate(tokens):
        token_type = tok[0]
        line = tok[4]
        try:
            next_tok = tokens[count+1]
        except IndexError: # Last token, no biggie
            # Pretend it is an empty comment ending in a newline
            next_tok = (54, '\n', (1, 1), (1, 2), '#\n')
        if token_type == tokenize.NEWLINE:
            skip_line = False
        if skip_line:
            prev_tok = tok
            continue
        result = obfunc(tok, next_tok, prev_tok)
        if result:
            if skip_next:
                skip_next = False
            elif result == '__skipline__':
                skip_line = True
            elif result == '__skipnext__':
                skip_next = True
            elif result in obfuscatables:
                pass
            else:
                obfuscatables.append(result)
        else: # If result is empty we need to reset skip_next so we don't
            skip_next = False # accidentally skip the next identifier
        prev_tok = tok
    return obfuscatables

# Note: I'm using 'tok' instead of 'token' since 'token' is a built-in module
def obfuscatable_variable(tok, next_tok, prev_tok):
    """
    Given a token, returns the token string if it is a variable name that can
    be safely obfuscated.

    Returns '__skipline__' if the rest of the tokens on this line should be skipped.
    Returns '__skipnext__' if the next token should be skipped.
    """
    token_type = tok[0]
    token_string = tok[1]
    line = tok[4]
    prev_tok_type = prev_tok[0]
    prev_tok_string = prev_tok[1]
    next_tok_string = next_tok[1]
    if token_string == "=":
        return '__skipline__'
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string.startswith('__'):
        return None
    if next_tok_string == ".":
        if token_string in imported_modules:
            return None
    if prev_tok_string == ".":
        return '__skipnext__'
    if prev_tok_string == "for":
        if len(token_string) > 2:
            return token_string
    if token_string == "for":
        return None
    if token_string in keyword_args.keys():
        return None
    if token_string in ["def", "class", 'if', 'elif', 'import']:
        return '__skipline__'
    if prev_tok_type != tokenize.INDENT and '=' not in line:
        return '__skipline__'
    if len(token_string) < 3:
        return None
    if token_string in reserved_words:
        return None
    return token_string

def obfuscatable_class(tok, next_tok, prev_tok):
    """
    Given a token, returns the token string if it is a class name that can be
    safely obfuscated.
    """
    token_type = tok[0]
    token_string = tok[1]
    prev_tok_string = prev_tok[1]
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string.startswith('__'): # Don't mess with specials
        return None
    if prev_tok_string == "class":
        return token_string

def obfuscatable_function(tok, next_tok, prev_tok):
    """
    Given a token, returns the token string if it is a function or method name
    that can be safely obfuscated.
    """
    token_type = tok[0]
    token_string = tok[1]
    prev_tok_string = prev_tok[1]
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string.startswith('__'): # Don't mess with specials
        return None
    if prev_tok_string == "def":
        return token_string

def replace_obfuscatables(module, tokens, obfunc, replace, name_generator, table=None):
    """
    Iterates over *tokens*, which must be an equivalent output to what
    tokenize.generate_tokens() produces, replacing the given identifier name
    (*replace*) by calling *obfunc* on each token with the following parameters:

        - **module:**       The name of the script we're currently obfuscating.
        - **tok:**          The current token.
        - **prev_tok:**     The previous token in the sequence.
        - **next_tok:**     The next token in the sequence.
        - **replace:**      The token string that we're replacing.
        - **replacement:**  A randomly generated, unique value that will be used to replace, *replace*.
        - **right_of_equal:**   A True or False value representing whether or not the token is to the right of an equal sign.  **Note:** This gets reset to False if a comma or open paren are encountered.
        - **inside_parens:**    An integer that is incremented whenever an open paren is encountered and decremented when a close paren is encountered.
        - **inside_function:**  If not False, the name of the function definition we're inside of (used in conjunction with *keyword_args* to determine if a safe replacement can be made).

    *obfunc* is expected to return the token string if that token can be safely
    obfuscated **or** one of the following optional values which will instruct
    find_obfuscatables() how to proceed:

        - **'__open_paren__'**        Increment the inside_parens value
        - **'__close_paren__'**       Decrement the inside_parens value
        - **'__comma__'**             Reset the right_of_equal value to False
        - **'__right_of_equal__'**    Sets the right_of_equal value to True

    **Note:** The right_of_equal and the inside_parens values are reset whenever a NEWLINE is encountered.

    When obfuscating a list of files, *table* is used to keep track of which
    obfuscatable identifiers are which inside each resulting file.  It must be
    an empty dictionary that will be populated like so::

        {orig_name: obfuscated_name}

    This *table* of "what is what" will be used to ensure that references from
    one script/module that call another are kept in sync when they are replaced
    with obfuscated values.
    """
    # Pretend the first line is '#\n':
    prev_tok = (54, '\n', (1, 1), (1, 2), '#\n')
    skip_line = False
    skip_next = False
    right_of_equal = False
    inside_parens = 0
    inside_function = False
    indent = 0
    function_indent = 0
    replacement = next(name_generator)
    for count, tok in enumerate(tokens):
        try:
            next_tok = tokens[count+1]
        except IndexError: # Last token, no biggie
            # Pretend it is a newline
            next_tok = (54, '\n', (1, 1), (1, 2), '#\n')
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.NEWLINE:
            skip_line = False
            right_of_equal = False
            inside_parens = 0
        elif token_type == tokenize.INDENT:
            indent += 1
        elif token_type == tokenize.DEDENT:
            indent -= 1
            if inside_function and function_indent == indent:
                function_indent = 0
                inside_function = False
        if token_string == "def":
            function_indent = indent
            function_name = tokens[count+1][1]
            inside_function = function_name
        result = obfunc(
            tok,
            next_tok,
            prev_tok,
            replace,
            replacement,
            right_of_equal,
            inside_parens,
            inside_function
        )
        prev_tok = tok
        if result:
            if skip_next:
                skip_next = False
            elif skip_line:
                pass
            elif result == '__skipline__':
                skip_line = True
            elif result == '__skipnext__':
                skip_next = True
            elif result == '__open_paren__':
                right_of_equal = False
                inside_parens += 1
            elif result == '__close_paren__':
                inside_parens -= 1
            elif result == '__comma__':
                right_of_equal = False
            elif result == '__right_of_equal__':
                right_of_equal = True
            else:
                if table: # Save it for later use in other files
                    combined_name = "%s.%s" % (module, token_string)
                    try: # Attempt to use an existing value
                        tokens[count][1] = table[0][combined_name]
                    except KeyError: # Doesn't exist, add it to table
                        table[0].update({combined_name: result})
                        tokens[count][1] = result
                else:
                    tokens[count][1] = result

def obfuscate_variable(
        tok,
        next_tok,
        prev_tok,
        replace,
        replacement,
        right_of_equal,
        inside_parens,
        inside_function):
    """
    If the token string inside *tok* matches *replace*, return *replacement*.
    *next_tok*, *prev_tok*, *right_of_equal*, and *inside_parens* are used to
    determine whether or not this token is safe to obfuscate.
    """
    token_type = tok[0]
    token_string = tok[1]
    prev_tok_string = prev_tok[1]
    if token_string == "import":
        return '__skipline__'
    if next_tok[1] == '.':
        if token_string in imported_modules:
            return None
    if token_string == "=":
        return '__right_of_equal__'
    if token_string == "(":
        return '__open_paren__'
    if token_string == ")":
        return '__close_paren__'
    if token_string == ",":
        return '__comma__'
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string.startswith('__'):
        return None
    if prev_tok_string == 'def':
        return '__skipnext__' # Don't want to touch functions
    if token_string == replace and prev_tok_string != '.':
        if inside_function:
            if token_string not in keyword_args[inside_function]:
                if not right_of_equal:
                    if not inside_parens:
                        return replacement
                    else:
                        if next_tok[1] != '=':
                            return replacement
                elif not inside_parens:
                    return replacement
                else:
                    if next_tok[1] != '=':
                        return replacement
        elif not right_of_equal:
            if not inside_parens:
                return replacement
            else:
                if next_tok[1] != '=':
                    return replacement
        elif right_of_equal and not inside_parens:
            return replacement

def obfuscate_function(tok, next_tok, prev_tok, replace, replacement, *args):
    """
    If the token string inside *tok* matches *replace*, return *replacement*.
    """
    token_type = tok[0]
    token_string = tok[1]
    prev_tok_string = prev_tok[1]
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string.startswith('__'):
        return None
    if prev_tok_string != '.':
        if token_string == replace:
            return replacement

def obfuscate_class(tok, next_tok, prev_tok, replace, replacement, *args):
    """
    If the token string inside *tok* matches *replace*, return *replacement*.
    """
    token_type = tok[0]
    token_string = tok[1]
    prev_tok_string = prev_tok[1]
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string.startswith('__'):
        return None
    if prev_tok_string != '.':
        if token_string == replace:
            return replacement

def obfuscate_unique(tok, next_tok, prev_tok, replace, replacement, *args):
    """
    If the token string inside *tok* matches *replace*, return *replacement*.

    .. note::

        This function is only for replacing absolutely unique ocurrences of
        *replace* (where we don't have to worry about their position).
    """
    token_type = tok[0]
    token_string = tok[1]
    if token_type != tokenize.NAME:
        return None # Skip this token
    if token_string == replace:
        return replacement

def remap_name(name_generator, names, table=None):
    """
    Produces a series of variable assignments in the form of::

        <obfuscated name> = <some identifier>

    for each item in *names* using *name_generator* to come up with the
    replacement names.

    If *table* is provided, replacements will be looked up there before
    generating a new unique name.
    """
    out = ""
    for name in names:
        if table and name in table[0].keys():
            replacement = table[0][name]
        else:
            replacement = next(name_generator)
        out += "%s=%s\n" % (replacement, name)
    return out

def insert_in_next_line(tokens, index, string):
    """
    Inserts the given string after the next newline inside tokens starting at
    *tokens[index]*.  Indents must be a list of indentation tokens that will
    preceeed the insert (can be an empty list).
    """
    tokenized_string = token_utils.listified_tokenizer(string)
    for i, tok in list(enumerate(tokens[index:])):
        token_type = tok[0]
        if token_type in [tokenize.NL, tokenize.NEWLINE]:
            for count, item in enumerate(tokenized_string):
                tokens.insert(index+count+i+1, item)
            break

def obfuscate_builtins(module, tokens, name_generator, table=None):
    """
    Inserts an assignment, '<obfuscated identifier> = <builtin function>'  at
    the beginning of *tokens* (after the shebang and encoding if present) for
    every Python built-in function that is used inside *tokens*.  Also, replaces
    all of said builti-in functions in *tokens* with each respective obfuscated
    identifer.

    Obfuscated identifier names are pulled out of name_generator via next().

    If *table* is provided, replacements will be looked up there before
    generating a new unique name.
    """
    used_builtins = analyze.enumerate_builtins(tokens)
    obfuscated_assignments = remap_name(name_generator, used_builtins, table)
    replacements = []
    for assignment in obfuscated_assignments.split('\n'):
        replacements.append(assignment.split('=')[0])
    replacement_dict = dict(zip(used_builtins, replacements))
    if table:
        table[0].update(replacement_dict)
    iter_replacements = iter(replacements)
    for builtin in used_builtins:
        replace_obfuscatables(
            module, tokens, obfuscate_unique, builtin, iter_replacements)
    # Check for shebangs and encodings before we do anything else
    skip_tokens = 0
    matched_shebang = False
    matched_encoding = False
    for tok in tokens[0:4]: # Will always be in the first four tokens
        line = tok[4]
        if analyze.shebang.match(line): # (e.g. '#!/usr/bin/env python')
            if not matched_shebang:
                matched_shebang = True
                skip_tokens += 1
        elif analyze.encoding.match(line): # (e.g. '# -*- coding: utf-8 -*-')
            if not matched_encoding:
                matched_encoding = True
                skip_tokens += 1
    insert_in_next_line(tokens, skip_tokens, obfuscated_assignments)

def obfuscate_global_import_methods(module, tokens, name_generator, table=None):
    """
    Replaces the used methods of globally-imported modules with obfuscated
    equivalents.  Updates *tokens* in-place.

    *module* must be the name of the module we're currently obfuscating

    If *table* is provided, replacements for import methods will be attempted
    to be looked up there before generating a new unique name.
    """
    global_imports = analyze.enumerate_global_imports(tokens)
    local_imports = analyze.enumerate_local_modules(tokens, os.getcwd())
    module_methods = analyze.enumerate_import_methods(tokens)
    # Make a 1-to-1 mapping dict of module_method<->replacement:
    if table:
        replacement_dict = {}
        for module_method in module_methods:
            if module_method in table[0].keys():
                replacement_dict.update({module_method: table[0][module_method]})
            else:
                replacement_dict.update({module_method: next(name_generator)})
        # Update the global lookup table with the new entries:
        table[0].update(replacement_dict)
    else:
        method_map = [next(name_generator) for i in module_methods]
        replacement_dict = dict(zip(module_methods, method_map))
    import_line = False
    # Replace module methods with our obfuscated names in *tokens*
    for module_method in module_methods:
        for index, tok in enumerate(tokens):
            token_type = tok[0]
            token_string = tok[1]
            if token_type != tokenize.NAME:
                continue # Speedup
            tokens[index+1][1]
            if token_string == module_method.split('.')[0]:
                if tokens[index+1][1] == '.':
                    if tokens[index+2][1] == module_method.split('.')[1]:
                        if table: # Attempt to use an existing value
                            tokens[index][1] = table[0][module_method]
                            tokens[index+1][1] = ""
                            tokens[index+2][1] = ""
                        else:
                            tokens[index][1] = replacement_dict[module_method]
                            tokens[index+1][1] = ""
                            tokens[index+2][1] = ""
    # Insert our map of replacement=what after each respective module import
    for module_method, replacement in replacement_dict.items():
        indents = []
        index = 0
        for tok in tokens[:]:
            token_type = tok[0]
            token_string = tok[1]
            if token_type == tokenize.NEWLINE:
                import_line = False
            elif token_type == tokenize.INDENT:
                indents.append(tok)
            elif token_type == tokenize.DEDENT:
                indents.pop()
            elif token_string == "import":
                import_line = True
            elif import_line:
                if token_string == module_method.split('.')[0]:
                    # Insert the obfuscation assignment after the import
                    imported_module = ".".join(module_method.split('.')[:-1])
                    if table and imported_module in local_imports:
                        line = "%s=%s.%s\n" % ( # This ends up being 6 tokens
                            replacement_dict[module_method],
                            imported_module,
                            replacement_dict[module_method]
                        )
                    else:
                        line = "%s=%s\n" % ( # This ends up being 6 tokens
                            replacement_dict[module_method], module_method)
                    for indent in indents: # Fix indentation
                        line = "%s%s" % (indent[1], line)
                        index += 1
                    insert_in_next_line(tokens, index, line)
                    index += 6 # To make up for the six tokens we inserted
            index += 1

def obfuscate(module, tokens, options, name_generator=None, table=None):
    """
    Obfuscates *tokens* in-place.  *options* is expected to be the options
    variable passed through from pyminifier.py.

    *module* must be the name of the module we're currently obfuscating

    If *name_generator* is provided it will be used to obtain replacement values
    for identifiers.  If not, a new instance of

    If *table* is given (should be a list containing a single dictionary), it
    will be used to perform lookups of replacements and any new replacements
    will be added to it.
    """
    # Need a universal instance of our generator to avoid duplicates
    identifier_length = int(options.replacement_length)
    if not name_generator:
        if options.use_nonlatin:
            if sys.version_info[0] == 3:
                name_generator = obfuscation_machine(
                    use_unicode=True, count=identifier_length
                )
            else:
                print(
                    "ERROR: You can't use nonlatin characters without Python 3")
        else:
            name_generator = obfuscation_machine(count=identifier_length)
    if options.obfuscate:
        variables = find_obfuscatables(
            tokens, obfuscatable_variable)
        classes = find_obfuscatables(
            tokens, obfuscatable_class)
        functions = find_obfuscatables(
            tokens, obfuscatable_function)
        for variable in variables:
            replace_obfuscatables(
                module,
                tokens,
                obfuscate_variable,
                variable,
                name_generator,
                table
            )
        for function in functions:
            replace_obfuscatables(
                module,
                tokens,
                obfuscate_function,
                function,
                name_generator,
                table
            )
        for _class in classes:
            replace_obfuscatables(
                module, tokens, obfuscate_class, _class, name_generator, table)
        obfuscate_global_import_methods(module, tokens, name_generator, table)
        #print("# table: \n%s" % table)
        obfuscate_builtins(module, tokens, name_generator, table)
    else:
        if options.obf_classes:
            classes = find_obfuscatables(
                tokens, obfuscatable_class)
            for _class in classes:
                replace_obfuscatables(
                    module,
                    tokens,
                    obfuscate_class,
                    _class,
                    name_generator,
                    table
                )
        if options.obf_functions:
            functions = find_obfuscatables(
                tokens, obfuscatable_function)
            for function in functions:
                replace_obfuscatables(
                    module,
                    tokens,
                    obfuscate_function,
                    function,
                    name_generator,
                    table
                )
        if options.obf_variables:
            variables = find_obfuscatables(
                tokens, obfuscatable_variable)
            for variable in variables:
                replace_obfuscatables(
                    module,
                    tokens,
                    obfuscate_variable,
                    variable,
                    name_generator,
                    table
                )
        if options.obf_import_methods:
            obfuscate_global_import_methods(
                module, tokens, name_generator, table)
        if options.obf_builtins:
            obfuscate_builtins(module, tokens, name_generator, table)

if __name__ == "__main__":
    global name_generator
    try:
        source = open(sys.argv[1]).read()
    except:
        print("Usage: %s <filename.py>" % sys.argv[0])
        sys.exit(1)
    if sys.version_info[0] == 3:
        name_generator = obfuscation_machine(use_unicode=True)
    else:
        name_generator = obfuscation_machine(count=1)
    source = apply_obfuscation(source)
    print(source)

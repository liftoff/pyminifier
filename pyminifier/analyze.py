# -*- coding: utf-8 -*-

__doc__ = """\
A module of useful functions for analyzing Python code.
"""

# Import builtins
import os, sys, re, tokenize, keyword
try:
    import cStringIO as io
except ImportError: # Ahh, Python 3
    import io

# Globals
py3 = False

if not isinstance(sys.version_info, tuple):
    if sys.version_info.major == 3:
        py3 = True

shebang = re.compile('^#\!.*$')
encoding = re.compile(".*coding[:=]\s*([-\w.]+)")
# __builtins__ is different for every module so we need a hard-coded list:
builtins = [
    'ArithmeticError',
    'AssertionError',
    'AttributeError',
    'BaseException',
    'BufferError',
    'BytesWarning',
    'DeprecationWarning',
    'EOFError',
    'Ellipsis',
    'EnvironmentError',
    'Exception',
    'False',
    'FloatingPointError',
    'FutureWarning',
    'GeneratorExit',
    'IOError',
    'ImportError',
    'ImportWarning',
    'IndentationError',
    'IndexError',
    'KeyError',
    'KeyboardInterrupt',
    'LookupError',
    'MemoryError',
    'NameError',
    'None',
    'NotImplemented',
    'NotImplementedError',
    'OSError',
    'OverflowError',
    'PendingDeprecationWarning',
    'ReferenceError',
    'RuntimeError',
    'RuntimeWarning',
    'StandardError',
    'StopIteration',
    'SyntaxError',
    'SyntaxWarning',
    'SystemError',
    'SystemExit',
    'TabError',
    'True',
    'TypeError',
    'UnboundLocalError',
    'UnicodeDecodeError',
    'UnicodeEncodeError',
    'UnicodeError',
    'UnicodeTranslateError',
    'UnicodeWarning',
    'UserWarning',
    'ValueError',
    'Warning',
    'ZeroDivisionError',
    '__IPYTHON__',
    '__IPYTHON__active',
    '__debug__',
    '__doc__',
    '__import__',
    '__name__',
    '__package__',
    'abs',
    'all',
    'any',
    'apply',
    'basestring',
    'bin',
    'bool',
    'buffer',
    'bytearray',
    'bytes',
    'callable',
    'chr',
    'classmethod',
    'cmp',
    'coerce',
    'compile',
    'complex',
    'copyright',
    'credits',
    'delattr',
    'dict',
    'dir',
    'divmod',
    'dreload',
    'enumerate',
    'eval',
    'execfile',
    'exit',
    'file',
    'filter',
    'float',
    'format',
    'frozenset',
    'getattr',
    'globals',
    'hasattr',
    'hash',
    'help',
    'hex',
    'id',
    'input',
    'int',
    'intern',
    'ip_set_hook',
    'ipalias',
    'ipmagic',
    'ipsystem',
    'isinstance',
    'issubclass',
    'iter',
    'jobs',
    'len',
    'license',
    'list',
    'locals',
    'long',
    'map',
    'max',
    'min',
    'next',
    'object',
    'oct',
    'open',
    'ord',
    'pow',
    'print',
    'property',
    'quit',
    'range',
    'raw_input',
    'reduce',
    'reload',
    'repr',
    'reversed',
    'round',
    'set',
    'setattr',
    'slice',
    'sorted',
    'staticmethod',
    'str',
    'sum',
    'super',
    'tuple',
    'type',
    'unichr',
    'unicode',
    'vars',
    'xrange',
    'zip'
]

reserved_words = keyword.kwlist + builtins

def enumerate_keyword_args(tokens):
    """
    Iterates over *tokens* and returns a dictionary with function names as the
    keys and lists of keyword arguments as the values.
    """
    keyword_args = {}
    inside_function = False
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.NEWLINE:
            inside_function = False
        if token_type == tokenize.NAME:
            if token_string == "def":
                function_name = tokens[index+1][1]
                inside_function = function_name
                keyword_args.update({function_name: []})
            elif inside_function:
                if tokens[index+1][1] == '=': # keyword argument
                    keyword_args[function_name].append(token_string)
    return keyword_args

def enumerate_imports(tokens):
    """
    Iterates over *tokens* and returns a list of all imported modules.

    .. note:: This ignores imports using the 'as' and 'from' keywords.
    """
    imported_modules = []
    import_line = False
    from_import = False
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.NEWLINE:
            import_line = False
            from_import = False
        elif token_string == "import":
            import_line = True
        elif token_string == "from":
            from_import = True
        elif import_line:
            if token_type == tokenize.NAME and tokens[index+1][1] != 'as':
                if not from_import:
                    if token_string not in reserved_words:
                        if token_string not in imported_modules:
                            imported_modules.append(token_string)
    return imported_modules

def enumerate_global_imports(tokens):
    """
    Returns a list of all globally imported modules (skips modules imported
    inside of classes, methods, or functions).  Example::

        >>> enumerate_global_modules(tokens)
        ['sys', 'os', 'tokenize', 're']

    .. note::

        Does not enumerate imports using the 'from' or 'as' keywords.
    """
    imported_modules = []
    import_line = False
    from_import = False
    parent_module = ""
    function_count = 0
    indentation = 0
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.INDENT:
            indentation += 1
        elif token_type == tokenize.DEDENT:
            indentation -= 1
        elif token_type == tokenize.NEWLINE:
            import_line = False
            from_import = False
        elif token_type == tokenize.NAME:
            if token_string in ["def", "class"]:
                function_count += 1
            if indentation == function_count - 1:
                function_count -= 1
            elif function_count >= indentation:
                if token_string == "import":
                    import_line = True
                elif token_string == "from":
                    from_import = True
                elif import_line:
                    if token_type == tokenize.NAME \
                        and tokens[index+1][1] != 'as':
                        if not from_import \
                            and token_string not in reserved_words:
                            if token_string not in imported_modules:
                                if tokens[index+1][1] == '.': # module.module
                                    parent_module = token_string + '.'
                                else:
                                    if parent_module:
                                        module_string = (
                                            parent_module + token_string)
                                        imported_modules.append(module_string)
                                        parent_module = ''
                                    else:
                                        imported_modules.append(token_string)

    return imported_modules

# TODO: Finish this (even though it isn't used):
def enumerate_dynamic_imports(tokens):
    """
    Returns a dictionary of all dynamically imported modules (those inside of
    classes or functions) in the form of {<func or class name>: [<modules>]}

    Example:
        >>> enumerate_dynamic_modules(tokens)
        {'myfunc': ['zlib', 'base64']}
    """
    imported_modules = []
    import_line = False
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.NEWLINE:
            import_line = False
        elif token_string == "import":
            try:
                if tokens[index-1][0] == tokenize.NEWLINE:
                    import_line = True
            except IndexError:
                import_line = True # Just means this is the first line
        elif import_line:
            if token_type == tokenize.NAME and tokens[index+1][1] != 'as':
                if token_string not in reserved_words:
                    if token_string not in imported_modules:
                        imported_modules.append(token_string)
    return imported_modules

def enumerate_method_calls(tokens, modules):
    """
    Returns a list of all object (not module) method calls in the given tokens.

    *modules* is expected to be a list of all global modules imported into the
    source code we're working on.

    For example:
        >>> enumerate_method_calls(tokens)
        ['re.compile', 'sys.argv', 'f.write']
    """
    out = []
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        token_string = tok[1]
        if token_type == tokenize.NAME:
            next_tok_string = tokens[index+1][1]
            if next_tok_string == '(': # Method call
                prev_tok_string = tokens[index-1][1]
                # Check if we're attached to an object or module
                if prev_tok_string == '.': # We're attached
                    prev_prev_tok_string = tokens[index-2][1]
                    if prev_prev_tok_string not in ['""',"''", ']', ')', '}']:
                        if prev_prev_tok_string not in modules:
                            to_replace = "%s.%s" % (
                                prev_prev_tok_string, token_string)
                            if to_replace not in out:
                                out.append(to_replace)
    return out

def enumerate_builtins(tokens):
    """
    Returns a list of all the builtins being used in *tokens*.
    """
    out = []
    for index, tok in enumerate(tokens):
        token_type = tok[0]
        token_string = tok[1]
        if token_string in builtins:
            # Note: I need to test if print can be replaced in Python 3
            special_special = ['print'] # Print is special in Python 2
            if py3:
                special_special = []
            if token_string not in special_special:
                if not token_string.startswith('__'): # Don't count magic funcs
                    if tokens[index-1][1] != '.' and tokens[index+1][1] != '=':
                        if token_string not in out:
                            out.append(token_string)
    return out

def enumerate_import_methods(tokens):
    """
    Returns a list of imported module methods (such as re.compile) inside
    *tokens*.
    """
    global_imports = enumerate_global_imports(tokens)
    out = []
    for item in global_imports:
        for index, tok in enumerate(tokens):
            try:
                next_tok = tokens[index+1]
                try:
                    next_next_tok = tokens[index+2]
                except IndexError:
                    # Pretend it is a newline
                    next_next_tok = (54, '\n', (1, 1), (1, 2), '#\n')
            except IndexError: # Last token, no biggie
                # Pretend it is a newline here too
                next_tok = (54, '\n', (1, 1), (1, 2), '#\n')
            token_type = tok[0]
            token_string = tok[1]
            if token_string == item:
                if next_tok[1] == '.': # We're calling a method
                    module_method = "%s.%s" % (token_string, next_next_tok[1])
                    if module_method not in out:
                        out.append(module_method)
    return out

def enumerate_local_modules(tokens, path):
    """
    Returns a list of modules inside *tokens* that are local to *path*.

    **Note:**  Will recursively look inside *path* for said modules.
    """
    # Have to get a list of all modules before we can do anything else
    modules = enumerate_imports(tokens)
    local_modules = []
    parent = ""
    # Now check the local dir for matching modules
    for root, dirs, files in os.walk(path):
        if not parent:
            parent = os.path.split(root)[1]
        for f in files:
            if f.endswith('.py'):
                f = f[:-3] # Strip .py
                module_tree = root.split(parent)[1].replace('/', '.')
                module_tree = module_tree.lstrip('.')
                if module_tree:
                    module = "%s.%s" % (module_tree, f)
                else:
                    module = f
                if not module in modules:
                    local_modules.append(module)
    return local_modules

def get_shebang(tokens):
    """
    Returns the shebang string in *tokens* if it exists.  None if not.
    """
    # This (short) loop preserves shebangs and encoding strings:
    for tok in tokens[0:4]: # Will always be in the first four tokens
        line = tok[4]
        # Save the first comment line if it starts with a shebang
        # (e.g. '#!/usr/bin/env python')
        if shebang.match(line): # Must be first line
            return line

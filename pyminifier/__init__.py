# -*- coding: utf-8 -*-
#
#       Copyright 2013 Liftoff Software Corporation
#
# For license information see LICENSE.txt

# Meta
__version__ = '2.2'
__version_info__ = (2, 2)
__license__ = "GPLv3" # See LICENSE.txt
__author__ = 'Dan McDougall <daniel.mcdougall@liftoffsoftware.com>'

# TODO: Add the ability to mark variables, functions, classes, and methods for non-obfuscation.
# TODO: Add the ability to selectively obfuscate identifiers inside strings (for metaprogramming stuff).
# TODO: Add the ability to use a config file instead of just command line args.
# TODO: Add the ability to save a file that allows for de-obfuscation later (or at least the ability to debug).
# TODO: Separate out the individual functions of minification so that they can be chosen selectively like the obfuscation functions.

__doc__ = """\
**Python Minifier:**  Reduces the size of (minifies) Python code for use on
embedded platforms.

Performs the following:

    * Removes docstrings.
    * Removes comments.
    * Minimizes code indentation.
    * Removes trailing commas.
    * Joins multiline pairs of parentheses, braces, and brackets (and removes extraneous whitespace within).
    * Joins disjointed strings like, ``("some" "disjointed" "string")`` into single strings: ``('''some disjointed string''')
    * Preserves shebangs and encoding info (e.g. "# -- coding: utf-8 --").
    * Optionally, produces a bzip2 or gzip-compressed self-extracting python script containing the minified source for ultimate minification. *Added in version 1.4*
    * Optionally, obfuscates the code using the shortest possible combination of letters and numbers for one or all of class names, function/method names, and variables. The options are ``--obfuscate`` or ``-O`` to obfuscate everything, ``--obfuscate-variables``, ``--obfuscate-functions``, and ``--obfuscate-classes`` to obfuscate things individually (say, if you wanted to keep your module usable by external programs).  *Added in version 2.0*
    * Optionally, a value may be specified via --replacement-length to set the minimum length of random strings that are used to replace identifier names when obfuscating.
    * Optionally, if using Python 3, you may specify ``--nonlatin`` to use funky unicode characters when obfuscating. WARNING: This will result in some seriously hard-to-read code! **Tip:** Combine this setting with higher ``--replacement-length`` values to make the output even wackier.  *Added in version 2.0*
    * Pyminifier can now minify/obfuscate an arbitrary number of Python scripts in one go.  For example, ``pyminifier -O *.py`` will minify and obfuscate all files in the current directory ending in .py.  To prevent issues with using differentiated obfuscated identifiers across multiple files, pyminifier will keep track of what replaces what via a lookup table to ensure foo_module.whatever is gets the same replacement across all source files.  *Added in version 2.0*
    * Optionally, creates an executable zip archive (pyz) containing the minified/obfuscated source script and all implicit (local path) imported modules.  This mechanism automatically figures out which source files to include in the .pyz archive by analyzing the script passed to pyminifier on the command line (listing all the modules your script uses is unnecessary).  This is also the **ultimate** in minification/compression besting both the gzip and bzip2 compression mechanisms with the disadvantage that .pyz files cannot be imported into other Python scripts.  *Added in version 2.0*

Just how much space can be saved by pyminifier?  Here's a comparison:

    * The pyminifier source (all six files) takes up about 164k.
    * Performing basic minification on all pyminifier source files reduces that to ~104k.
    * Minification plus obfuscation provides a further reduction to 92k.
    * Minification plus the base64-encoded gzip trick (--gzip) reduces it to 76k.
    * Minification plus gzip compression plus obfuscation is also 76k (demonstrating that obfuscation makes no difference when compression algorthms are used).
    * Using the --pyz option on pyminifier.py creates a ~14k .pyz file that includes all the aforementioned files.

Various examples and edge cases are sprinkled throughout the pyminifier code so
that it can be tested by minifying itself.  The way to test is thus:

.. code-block:: bash

    $ python __main__.py __main__.py > minified_pyminifier.py
    $ python minified_pyminifier.py __main__.py > this_should_be_identical.py
    $ diff minified_pyminifier.py this_should_be_identical.py
    $

If you get an error executing minified_pyminifier.py or
``this_should_be_identical.py`` isn't identical to minified_pyminifier.py then
something is broken.

.. note::

    The test functions below are meaningless.  They only serve as test/edge
    cases for testing pyminifier.
"""

# Import built-in modules
import os, sys, re, io
from optparse import OptionParser
from collections import Iterable

# Import our own modules
from . import minification
from . import token_utils
from . import obfuscate
from . import compression

py3 = False
lzma = False
if not isinstance(sys.version_info, tuple):
    if sys.version_info.major == 3:
        py3 = True
        try:
            import lzma
        except ImportError:
            pass

# Regexes
multiline_indicator = re.compile('\\\\(\s*#.*)?\n')

# The test.+() functions below are for testing pyminifier...
def test_decorator(f):
    """Decorator that does nothing"""
    return f

def test_reduce_operators():
    """Test the case where an operator such as an open paren starts a line"""
    (a, b) = 1, 2 # The indentation level should be preserved
    pass

def test_empty_functions():
    """
    This is a test function.
    This should be replaced with 'def test_empty_functions(): pass'
    """

class test_class(object):
    "Testing indented decorators"

    @test_decorator
    def test_function(self):
        pass

def test_function():
    """
    This function encapsulates the edge cases to prevent them from invading the
    global namespace.
    """
    # This tests method obfuscation:
    method_obfuscate = test_class()
    method_obfuscate.test_function()
    foo = ("The # character in this string should " # This comment
           "not result in a syntax error") # ...and this one should go away
    test_multi_line_list = [
        'item1',
        'item2',
        'item3'
    ]
    test_multi_line_dict = {
        'item1': 1,
        'item2': 2,
        'item3': 3
    }
    # It may seem strange but the code below tests our docstring removal code.
    test_string_inside_operators = imaginary_function(
        "This string was indented but the tokenizer won't see it that way."
    ) # To understand how this could mess up docstring removal code see the
    # minification.minification.remove_comments_and_docstrings() function
    # starting at this line:
    #     "elif token_type == tokenize.STRING:"
    # This tests remove_extraneous_spaces():
    this_line_has_leading_indentation    = '''<--That extraneous space should be
                                              removed''' # But not these spaces

def is_iterable(obj):
    """
    Returns `True` if *obj* is iterable but *not* if *obj* is a string, bytes,
    or a bytearray.
    """
    if isinstance(obj, (str, bytes, bytearray)):
        return False
    return isinstance(obj, Iterable)

def pyminify(options, files):
    """
    Given an *options* object (from `optparse.OptionParser` or similar),
    performs minification and/or obfuscation on the given *files* (any iterable
    containing file paths) based on said *options*.

    All accepted options can　be listed by running ``python __main__.py -h`` or
    examining the :py:func:`__init__.main` function.
    """
    global name_generator
    if not is_iterable(files):
        print(
            "Error: The 'files' argument must be a list, tuple, etc of files.  "
            "Strings and bytes won't work.")
        sys.exit(1)
    if options.pyz:
        # Check to make sure we were only passed one script (only one at a time)
        if len(files) > 1:
            print("ERROR: The --pyz option only works with one python file at "
                  "a time.")
            print("(Dependencies will be automagically included in the "
                  "resulting .pyz)")
            sys.exit(1)
        # Make our .pyz:
        compression.zip_pack(files, options)
        return None # Make sure we don't do anything else
    # Read in our prepend text (if any)
    prepend = None
    if options.prepend:
        try:
            prepend = open(options.prepend).read()
        except Exception as err:
            print("Error reading %s:" % options.prepend)
            print(err)

    obfuscations = (options.obfuscate, options.obf_classes,
                    options.obf_functions, options.obf_variables,
                    options.obf_builtins, options.obf_import_methods)

    # Automatically enable obfuscation if --nonlatin (implied if no explicit
    # obfuscation is stated)
    if options.use_nonlatin and not any(obfuscations):
        options.obfuscate = True
    if len(files) > 1: # We're dealing with more than one file
        name_generator = None # So we can tell if we need to obfuscate
        if any(obfuscations):
            # Put together that will be used for all obfuscation functions:
            identifier_length = int(options.replacement_length)
            if options.use_nonlatin:
                if sys.version_info[0] == 3:
                    name_generator = obfuscate.obfuscation_machine(
                        use_unicode=True, identifier_length=identifier_length
                    )
                else:
                    print(
                        "ERROR: You can't use nonlatin characters without Python 3")
                    sys.exit(2)
            else:
                name_generator = obfuscate.obfuscation_machine(
                    identifier_length=identifier_length)
            table =[{}]
        cumulative_size = 0 # For size reduction stats
        cumulative_new = 0 # Ditto
        for sourcefile in files:
            # Record how big the file is so we can compare afterwards
            filesize = os.path.getsize(sourcefile)
            cumulative_size += filesize
            # Get the module name from the path
            module = os.path.split(sourcefile)[1]
            module = ".".join(module.split('.')[:-1])
            source = open(sourcefile).read()
            tokens = token_utils.listified_tokenizer(source)
            if not options.nominify: # Perform minification
                source = minification.minify(tokens, options)
            # Have to re-tokenize for obfucation (it is quick):
            tokens = token_utils.listified_tokenizer(source)
            # Perform obfuscation if any of the related options were set
            if name_generator:
                obfuscate.obfuscate(
                    module,
                    tokens,
                    options,
                    name_generator=name_generator,
                    table=table
                )
            # Convert back to text
            result = ''
            if prepend:
                result += prepend
            result += token_utils.untokenize(tokens)
            # Compress it if we were asked to do so
            if options.bzip2:
                result = compression.bz2_pack(result)
            elif options.gzip:
                result = compression.gz_pack(result)
            elif lzma and options.lzma:
                result = compression.lzma_pack(result)
            result += (
                "# Created by pyminifier "
                "(https://github.com/liftoff/pyminifier)\n")
            # Either save the result to the output file or print it to stdout
            if not os.path.exists(options.destdir):
                os.mkdir(options.destdir)
            # Need the path where the script lives for the next steps:
            filepath = os.path.split(sourcefile)[1]
            path = options.destdir + '/' + filepath # Put everything in destdir
            f = open(path, 'w')
            f.write(result)
            f.close()
            new_filesize = os.path.getsize(path)
            cumulative_new += new_filesize
            percent_saved = round((float(new_filesize) / float(filesize)) * 100, 2) if float(filesize)!=0 else 0
            print((
                "{sourcefile} ({filesize}) reduced to {new_filesize} bytes "
                "({percent_saved}% of original size)").format(**locals()))
        p_saved = round(
            (float(cumulative_new) / float(cumulative_size) * 100), 2)
        print("Overall size reduction: {0}% of original size".format(p_saved))
    else:
        # Get the module name from the path
        _file = files[0]
        module = os.path.split(_file)[1]
        module = ".".join(module.split('.')[:-1])
        filesize = os.path.getsize(_file)
        source = open(_file).read()
        # Convert the tokens from a tuple of tuples to a list of lists so we can
        # update in-place.
        tokens = token_utils.listified_tokenizer(source)
        if not options.nominify: # Perform minification
            source = minification.minify(tokens, options)
            # Convert back to tokens in case we're obfuscating
            tokens = token_utils.listified_tokenizer(source)
        # Perform obfuscation if any of the related options were set
        if options.obfuscate or options.obf_classes or options.obf_functions \
                or options.obf_variables or options.obf_builtins \
                or options.obf_import_methods:
            identifier_length = int(options.replacement_length)
            name_generator = obfuscate.obfuscation_machine(
                identifier_length=identifier_length)
            obfuscate.obfuscate(module, tokens, options)
        # Convert back to text
        result = ''
        if prepend:
            result += prepend
        result += token_utils.untokenize(tokens)
        # Compress it if we were asked to do so
        if options.bzip2:
            result = compression.bz2_pack(result)
        elif options.gzip:
            result = compression.gz_pack(result)
        elif lzma and options.lzma:
            result = compression.lzma_pack(result)
        result += (
            "# Created by pyminifier "
            "(https://github.com/liftoff/pyminifier)\n")
        # Either save the result to the output file or print it to stdout
        if options.outfile:
            f = io.open(options.outfile, 'w', encoding='utf-8')
            f.write(result)
            f.close()
            new_filesize = os.path.getsize(options.outfile)
            percent_saved = round(float(new_filesize)/float(filesize) * 100, 2)
            print((
                "{_file} ({filesize}) reduced to {new_filesize} bytes "
                "({percent_saved}% of original size)".format(**locals())))
        else:
            print(result)

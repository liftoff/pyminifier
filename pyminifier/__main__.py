from optparse import OptionParser
import sys

from . import pyminify
from . import __version__

py3 = False
lzma = False
if not isinstance(sys.version_info, tuple):
    if sys.version_info.major == 3:
        py3 = True
        try:
            import lzma
        except ImportError:
            pass

def main():
    """
    Sets up our command line options, prints the usage/help (if warranted), and
    runs :py:func:`pyminifier.pyminify` with the given command line options.
    """
    usage = '%prog [options] "<input file>"'
    if '__main__.py' in sys.argv[0]: # python -m pyminifier
        usage = 'pyminifier [options] "<input file>"'
    parser = OptionParser(usage=usage, version=__version__)
    parser.disable_interspersed_args()
    parser.add_option(
        "-o", "--outfile",
        dest="outfile",
        default=None,
        help="Save output to the given file.",
        metavar="<file path>"
    )
    parser.add_option(
        "-d", "--destdir",
        dest="destdir",
        default="./minified",
        help=("Save output to the given directory. "
              "This option is required when handling multiple files. "
              "Defaults to './minified' and will be created if not present. "),
        metavar="<file path>"
    )
    parser.add_option(
        "--nominify",
        action="store_true",
        dest="nominify",
        default=False,
        help="Don't bother minifying (only used with --pyz).",
    )
    parser.add_option(
        "--use-tabs",
        action="store_true",
        dest="tabs",
        default=False,
        help="Use tabs for indentation instead of spaces.",
    )
    parser.add_option(
        "--bzip2",
        action="store_true",
        dest="bzip2",
        default=False,
        help=("bzip2-compress the result into a self-executing python script.  "
              "Only works on stand-alone scripts without implicit imports.")
    )
    parser.add_option(
        "--gzip",
        action="store_true",
        dest="gzip",
        default=False,
        help=("gzip-compress the result into a self-executing python script.  "
              "Only works on stand-alone scripts without implicit imports.")
    )
    if lzma:
        parser.add_option(
            "--lzma",
            action="store_true",
            dest="lzma",
            default=False,
            help=("lzma-compress the result into a self-executing python script.  "
                  "Only works on stand-alone scripts without implicit imports.")
        )
    parser.add_option(
        "--pyz",
        dest="pyz",
        default=None,
        help=("zip-compress the result into a self-executing python script. "
              "This will create a new file that includes any necessary implicit"
              " (local to the script) modules.  Will include/process all files "
              "given as arguments to pyminifier.py on the command line."),
        metavar="<name of archive>.pyz"
    )
    parser.add_option(
        "-O", "--obfuscate",
        action="store_true",
        dest="obfuscate",
        default=False,
        help=(
            "Obfuscate all function/method names, variables, and classes.  "
            "Default is to NOT obfuscate."
        )
    )
    parser.add_option(
        "--obfuscate-classes",
        action="store_true",
        dest="obf_classes",
        default=False,
        help="Obfuscate class names."
    )
    parser.add_option(
        "--obfuscate-functions",
        action="store_true",
        dest="obf_functions",
        default=False,
        help="Obfuscate function and method names."
    )
    parser.add_option(
        "--obfuscate-variables",
        action="store_true",
        dest="obf_variables",
        default=False,
        help="Obfuscate variable names."
    )
    parser.add_option(
        "--obfuscate-import-methods",
        action="store_true",
        dest="obf_import_methods",
        default=False,
        help="Obfuscate globally-imported mouled methods (e.g. 'Ag=re.compile')."
    )
    parser.add_option(
        "--obfuscate-builtins",
        action="store_true",
        dest="obf_builtins",
        default=False,
        help="Obfuscate built-ins (i.e. True, False, object, Exception, etc)."
    )
    parser.add_option(
        "--replacement-length",
        dest="replacement_length",
        default=1,
        help=(
            "The length of the random names that will be used when obfuscating "
            "identifiers."
        ),
        metavar="1"
    )
    parser.add_option(
        "--nonlatin",
        action="store_true",
        dest="use_nonlatin",
        default=False,
        help=(
            "Use non-latin (unicode) characters in obfuscation (Python 3 only)."
            "  WARNING: This results in some SERIOUSLY hard-to-read code."
        )
    )
    parser.add_option(
        "--prepend",
        dest="prepend",
        default=None,
        help=(
            "Prepend the text in this file to the top of our output.  "
            "e.g. A copyright notice."
        ),
        metavar="<file path>"
    )
    options, files = parser.parse_args()
    if not files:
        parser.print_help()
        sys.exit(2)
    pyminify(options, files)


if __name__ == "__main__":
    main()

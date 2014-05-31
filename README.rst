pyminifier
==========

Pyminifier is a Python code minifier, obfuscator, and compressor.

.. note::

    * For the latest, complete documentation: http://liftoff.github.io/pyminifier/
    * For the latest code: https://github.com/liftoff/pyminifier

Overview
--------
When you install pyminifier it should automatically add a 'pyminifier'
executable to your ``$PATH``.  This executable has a number of command line
arguments:

.. code-block:: sh

    $ pyminifier --help
    Usage: pyminifier [options] "<input file>"

    Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    -o <file path>, --outfile=<file path>
                          Save output to the given file.
    -d <file path>, --destdir=<file path>
                          Save output to the given directory. This option is
                            required when handling multiple files. Defaults to
                            './minified' and will be created if not present.
    --nominify            Don't bother minifying (only used with --pyz).
    --use-tabs            Use tabs for indentation instead of spaces.
    --bzip2               bzip2-compress the result into a self-executing python
                            script.  Only works on stand-alone scripts without
                            implicit imports.
    --gzip                gzip-compress the result into a self-executing python
                            script.  Only works on stand-alone scripts without
                            implicit imports.
    --lzma                lzma-compress the result into a self-executing python
                            script.  Only works on stand-alone scripts without
                            implicit imports.
    --pyz=<name of archive>.pyz
                          zip-compress the result into a self-executing python
                            script. This will create a new file that includes any
                            necessary implicit (local to the script) modules.
                            Will include/process all files given as arguments to
                            pyminifier.py on the command line.
    -O, --obfuscate       Obfuscate all function/method names, variables, and
                            classes.  Default is to NOT obfuscate.
    --obfuscate-classes   Obfuscate class names.
    --obfuscate-functions
                          Obfuscate function and method names.
    --obfuscate-variables
                          Obfuscate variable names.
    --obfuscate-import-methods
                          Obfuscate globally-imported mouled methods (e.g.
                            'Ag=re.compile').
    --obfuscate-builtins  Obfuscate built-ins (i.e. True, False, object,
                            Exception, etc).
    --replacement-length=1
                          The length of the random names that will be used when
                            obfuscating identifiers.
    --nonlatin            Use non-latin (unicode) characters in obfuscation
                            (Python 3 only).  WARNING: This results in some
                            SERIOUSLY hard-to-read code.
    --prepend=<file path>
                          Prepend the text in this file to the top of our
                            output.  e.g. A copyright notice.

For the examples below we'll be minifying, obfuscating, and compressing the
following totally made-up Python script (saved to ``/tmp/tumult.py``)::

    #!/usr/bin/env python
    """
    tumult.py - Because everyone needs a little chaos every now and again.
    """

    try:
        import demiurgic
    except ImportError:
        print("Warning: You're not demiurgic. Actually, I think that's normal.")
    try:
        import mystificate
    except ImportError:
        print("Warning: Dark voodoo may be unreliable.")

    # Globals
    ATLAS = False # Nothing holds up the world by default

    class Foo(object):
        """
        The Foo class is an abstract flabbergaster that when instantiated
        represents a discrete dextrogyratory inversion of a cattywompus
        octothorp.
        """
        def __init__(self, *args, **kwargs):
            """
            The initialization vector whereby the ineffably obstreperous
            becomes paramount.
            """
            # TODO.  BTW: What happens if we remove that docstring? :)

        def demiurgic_mystificator(self, dactyl):
            """
            A vainglorious implementation of bedizenment.
            """
            inception = demiurgic.palpitation(dactyl) # Note the imported call
            demarcation = mystificate.dark_voodoo(inception)
            return demarcation

        def test(self, whatever):
            """
            This test method tests the test by testing your patience.
            """
            print(whatever)

    if __name__ == "__main__":
        print("Forming...")
        f = Foo("epicaricacy", "perseverate")
        f.test("Codswallop")

By default pyminifier will perform basic minification and print the resulting
code to stdout:

.. note:: The tumult.py script is 1358 bytes.  Remember that.

.. code-block:: sh

    $ pyminifier /tmp/tumult.py
    #!/usr/bin/env python
    try:
     import demiurgic
    except ImportError:
     print("Warning: You're not demiurgic. Actually, I think that's normal.")
    try:
     import mystificate
    except ImportError:
     print("Warning: Dark voodoo may be unreliable.")
    ATLAS=False
    class Foo(object):
     def __init__(self,*args,**kwargs):
      pass
     def demiurgic_mystificator(self,dactyl):
      inception=demiurgic.palpitation(dactyl)
      demarcation=mystificate.dark_voodoo(inception)
      return demarcation
     def test(self,whatever):
      print(whatever)
    if __name__=="__main__":
     print("Forming...")
     f=Foo("epicaricacy","perseverate")
     f.test("Codswallop")
    # Created by pyminifier.py

This reduced the size of tumult.py from 1358 bytes to 640 bytes.  Not bad!

Minifying by itself can reduce code size considerably but pyminifier can go
further by obfuscating the code.  What that means is that it will replace the
names of things like variables and functions to the smallest possible size.

To see more examples of pyminifier in action (e.g. compression features) see the
`full documentation <http://liftoff.github.io/pyminifier/>`_

Special Sauce
-------------
So let's pretend for a moment that your intentions are not pure; that you
totally want to mess with the people that look at your minified code.  What you
need is Python 3 and the ``--nonlatin`` option...

.. code-block:: sh

    #!/usr/bin/env python
    ﵛ=ImportError
    ࡅ=print
    㮀=False
    搓=object
    try:
     import demiurgic
    except ﵛ:
    ࡅ("Warning: You're not demiurgic. Actually, I think that's normal.")
    try:
     import mystificate
    except ﵛ:
    ࡅ("Warning: Dark voodoo may be unreliable.")
    ﵩ=㮀
    class רּ(搓):
     def __init__(self,*args,**kwargs):
      pass
     def 𐨱(self,dactyl):
      ﱲ=demiurgic.palpitation(dactyl)
      ꁁ=mystificate.dark_voodoo(ﱲ)
      return ꁁ
     def 𨠅(self,whatever):
      ࡅ(whatever)
    if __name__=="__main__":
     ࡅ("Forming...")
     녂=רּ("epicaricacy","perseverate")
     녂.𨠅("Codswallop")
    # Created by pyminifier.py (https://github.com/liftoff/pyminifier)

Yes, that code actually works *but only using Python 3*.  This is because Python
3 supports coding in languages that use non-latin character sets.

.. note::

    Most text editors/IDEs will have a hard time with code generated using the
    ``--nonlatin`` option because it will be a random mix of left-to-right
    and right-to-left characters.  Often the result is some code appearing on
    the left of the screen and some code appearing on the right.  This makes it
    *really* hard to figure out things like indentation levels and whatnot!

There's even more ways to mess with people in the
`full documentation <http://liftoff.github.io/pyminifier/>`_

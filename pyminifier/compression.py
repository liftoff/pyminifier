# -*- coding: utf-8 -*-

__doc__ = """\
compression.py - A module providing functions to turn a python script into a
self-executing archive in a few different formats...

**gz_pack format:**

    - Typically provides better compression than bzip2 (for Python scripts).
    - Scripts compressed via this method can still be imported as modules.
    - The resulting binary data is base64-encoded which isn't optimal compression.

**bz2_pack format:**

    - In some cases may provide better compression than gzip.
    - Scripts compressed via this method can still be imported as modules.
    - The resulting binary data is base64-encoded which isn't optimal compression.

**lzma_pack format:**

    - In some cases may provide better compression than bzip2.
    - Scripts compressed via this method can still be imported as modules.
    - The resulting binary data is base64-encoded which isn't optimal compression.

The gz_pack, bz2_pack, and lzma_pack formats only work on individual .py
files.  To pack a number of files at once using this method use the
``--destdir`` command line option:

.. code-block: shell

    $ pyminifier --gzip --destdir=/tmp/minified *.py

**zip_pack format:**

    - Provides the best compression of Python scripts.
    - Resulting script cannot be imported as a module.
    - Any required modules that are local (implied path) will be automatically included in the archive.
"""

# Import standard library modules
import os, sys, tempfile, shutil

# Import our own supporting modules
from . import analyze, token_utils, minification, obfuscate

py3 = False
if not isinstance(sys.version_info, tuple):
    if sys.version_info.major == 3:
        py3 = True

def bz2_pack(source):
    """
    Returns 'source' as a bzip2-compressed, self-extracting python script.

    .. note::

        This method uses up more space than the zip_pack method but it has the
        advantage in that the resulting .py file can still be imported into a
        python program.
    """
    import bz2, base64
    out = ""
    # Preserve shebangs (don't care about encodings for this)
    first_line = source.split('\n')[0]
    if analyze.shebang.match(first_line):
        if py3:
            if first_line.rstrip().endswith('python'): # Make it python3
                first_line = first_line.rstrip()
                first_line += '3' #!/usr/bin/env python3
        out = first_line + '\n'
    compressed_source = bz2.compress(source.encode('utf-8'))
    out += 'import bz2, base64\n'
    out += "exec(bz2.decompress(base64.b64decode('"
    out += base64.b64encode(compressed_source).decode('utf-8')
    out += "')))\n"
    return out

def gz_pack(source):
    """
    Returns 'source' as a gzip-compressed, self-extracting python script.

    .. note::

        This method uses up more space than the zip_pack method but it has the
        advantage in that the resulting .py file can still be imported into a
        python program.
    """
    import zlib, base64
    out = ""
    # Preserve shebangs (don't care about encodings for this)
    first_line = source.split('\n')[0]
    if analyze.shebang.match(first_line):
        if py3:
            if first_line.rstrip().endswith('python'): # Make it python3
                first_line = first_line.rstrip()
                first_line += '3' #!/usr/bin/env python3
        out = first_line + '\n'
    compressed_source = zlib.compress(source.encode('utf-8'))
    out += 'import zlib, base64\n'
    out += "exec(zlib.decompress(base64.b64decode('"
    out += base64.b64encode(compressed_source).decode('utf-8')
    out += "')))\n"
    return out

def lzma_pack(source):
    """
    Returns 'source' as a lzma-compressed, self-extracting python script.

    .. note::

        This method uses up more space than the zip_pack method but it has the
        advantage in that the resulting .py file can still be imported into a
        python program.
    """
    import lzma, base64
    out = ""
    # Preserve shebangs (don't care about encodings for this)
    first_line = source.split('\n')[0]
    if analyze.shebang.match(first_line):
        if py3:
            if first_line.rstrip().endswith('python'): # Make it python3
                first_line = first_line.rstrip()
                first_line += '3' #!/usr/bin/env python3
        out = first_line + '\n'
    compressed_source = lzma.compress(source.encode('utf-8'))
    out += 'import lzma, base64\n'
    out += "exec(lzma.decompress(base64.b64decode('"
    out += base64.b64encode(compressed_source).decode('utf-8')
    out += "')))\n"
    return out

def prepend(line, path):
    """
    Appends *line* to the _beginning_ of the file at the given *path*.

    If *line* doesn't end in a newline one will be appended to the end of it.
    """
    if isinstance(line, str):
        line = line.encode('utf-8')
    if not line.endswith(b'\n'):
        line += b'\n'
    temp = tempfile.NamedTemporaryFile('wb')
    temp_name = temp.name # We really only need a random path-safe name
    temp.close()
    with open(temp_name, 'wb') as temp:
        temp.write(line)
        with open(path, 'rb') as r:
            temp.write(r.read())
    # Now replace the original with the modified version
    shutil.move(temp_name, path)

def zip_pack(filepath, options):
    """
    Creates a zip archive containing the script at *filepath* along with all
    imported modules that are local to *filepath* as a self-extracting python
    script.  A shebang will be appended to the beginning of the resulting
    zip archive which will allow it to

    If being run inside Python 3 and the `lzma` module is available the
    resulting 'pyz' file will use ZIP_LZMA compression to maximize compression.

    *options* is expected to be the the same options parsed from pyminifier.py
    on the command line.

    .. note::

        * The file resulting from this method cannot be imported as a module into another python program (command line execution only).
        * Any required local (implied path) modules will be automatically included (well, it does its best).
        * The result will be saved as a .pyz file (which is an extension I invented for this format).
    """
    import zipfile
    # Hopefully some day we'll be able to use ZIP_LZMA too as the compression
    # format to save even more space...
    compression_format = zipfile.ZIP_DEFLATED
    cumulative_size = 0 # For tracking size reduction stats
    # Record the filesize for later comparison
    cumulative_size += os.path.getsize(filepath)
    dest = options.pyz
    z = zipfile.ZipFile(dest, "w", compression_format)
    # Take care of minifying our primary script first:
    source = open(filepath).read()
    primary_tokens = token_utils.listified_tokenizer(source)
    # Preserve shebangs (don't care about encodings for this)
    shebang = analyze.get_shebang(primary_tokens)
    if not shebang:
    # We *must* have a shebang for this to work so make a conservative default:
        shebang = "#!/usr/bin/env python"
    if py3:
        if shebang.rstrip().endswith('python'): # Make it python3 (to be safe)
            shebang = shebang.rstrip()
            shebang += '3\n' #!/usr/bin/env python3
    if not options.nominify: # Minify as long as we don't have this option set
        source = minification.minify(primary_tokens, options)
    # Write out to a temporary file to add to our zip
    temp = tempfile.NamedTemporaryFile(mode='w')
    temp.write(source)
    temp.flush()
    # Need the path where the script lives for the next steps:
    path = os.path.split(filepath)[0]
    if not path:
        path = os.getcwd()
    main_py = path + '/__main__.py'
    if os.path.exists(main_py):
        # There's an existing __main__.py, use it
        z.write(main_py, '__main__.py')
        z.write(temp.name, os.path.split(filepath)[1])
    else:
        # No __main__.py so we rename our main script to be the __main__.py
        # This is so it will still execute as a zip
        z.write(filepath, '__main__.py')
    temp.close()
    # Now write any required modules into the zip as well
    local_modules = analyze.enumerate_local_modules(primary_tokens, path)
    name_generator = None # So we can tell if we need to obfuscate
    if options.obfuscate or options.obf_classes \
        or options.obf_functions or options.obf_variables \
        or options.obf_builtins or options.obf_import_methods:
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
    included_modules = []
    for module in local_modules:
        module = module.replace('.', '/')
        module = "%s.py" % module
        # Add the filesize to our total
        cumulative_size += os.path.getsize(module)
        # Also record that we've added it to the archive
        included_modules.append(module)
        # Minify these files too
        source = open(os.path.join(path, module)).read()
        tokens = token_utils.listified_tokenizer(source)
        maybe_more_modules = analyze.enumerate_local_modules(tokens, path)
        for mod in maybe_more_modules:
            if mod not in local_modules:
                local_modules.append(mod) # Extend the current loop, love it =)
        if not options.nominify:
            # Perform minification (this also handles obfuscation)
            source = minification.minify(tokens, options)
        # Have to re-tokenize for obfucation (it's quick):
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
        result = token_utils.untokenize(tokens)
        # Write out to a temporary file to add to our zip
        temp = tempfile.NamedTemporaryFile(mode='w')
        temp.write(source)
        temp.flush()
        z.write(temp.name, module)
        temp.close()
    z.close()
    # Finish up by writing the shebang to the beginning of the zip
    prepend(shebang, dest)
    os.chmod(dest, 0o755) # Make it executable (since we added the shebang)
    pyz_filesize = os.path.getsize(dest)
    percent_saved = round(float(pyz_filesize) / float(cumulative_size) * 100, 2)
    print('%s saved as compressed executable zip: %s' % (filepath, dest))
    print('The following modules were automatically included (as automagic '
          'dependencies):\n')
    for module in included_modules:
        print('\t%s' % module)
    print('\nOverall size reduction: %s%% of original size' % percent_saved)

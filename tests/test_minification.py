import unittest
import subprocess
import tempfile
import os

testdir = os.path.dirname(__file__)
maindir = os.path.dirname(testdir)


class TestPyMinify(unittest.TestCase):
    def minimy_file(self, inpath, cwd):
        proc = subprocess.Popen(['python', '-m', 'pyminifier', inpath], cwd=cwd, stdout=subprocess.PIPE)
        data, err = proc.communicate()
        assert err is None
        return data

    def test_minify_self(self):
        """
        Test if a minified version of 'pyminifier' returns the same results as
        the original one
        """
        _testdir = tempfile.mkdtemp()
        testdir = os.path.join(_testdir, 'pyminifier')
        os.mkdir(testdir)

        sourcedir = os.path.join(maindir, 'pyminifier')

        sourcefiles = [filename for filename in os.listdir(sourcedir) if filename.endswith('.py')]
        results = {}

        for filename in sourcefiles:
            source = os.path.join(sourcedir, filename)
            dest = os.path.join(testdir, filename)
            data = self.minimy_file(source, maindir)
            results[filename] = data

            with open(dest, 'wb') as destfile:
                destfile.write(data)

        for filename in sourcefiles:
            source = os.path.join(sourcedir, filename)
            res = self.minimy_file(source, cwd=_testdir)
            self.assertEqual(res, results[filename])

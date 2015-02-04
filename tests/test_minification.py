#!/usr/bin/env python

import unittest
import subprocess
import tempfile
import os
import shutil

testdir = os.path.abspath(os.path.split(__file__)[0])
maindir = os.path.dirname(testdir)


class TestPyMinify(unittest.TestCase):
    def setUp(self):
        self._testdir = tempfile.mkdtemp()
        self.testdir = os.path.join(self._testdir, 'pyminifier')
        os.mkdir(self.testdir)
        self.sourcedir = os.path.join(maindir, 'pyminifier')

    def minimy_file(self, inpath, cwd):
        proc = subprocess.Popen(
            ['pyminifier', inpath], cwd=cwd, stdout=subprocess.PIPE)
        data, err = proc.communicate()
        assert err is None
        return data

    def test_minify_self(self):
        """
        Test if a minified version of 'pyminifier' returns the same results as
        the original one
        """
        sourcefiles = [
            filename for filename
                in os.listdir(self.sourcedir) if filename.endswith('.py')]
        results = {}

        for filename in sourcefiles:
            source = os.path.join(self.sourcedir, filename)
            dest = os.path.join(self.testdir, filename)
            data = self.minimy_file(source, maindir)
            results[filename] = data

            with open(dest, 'wb') as destfile:
                destfile.write(data)

        for filename in sourcefiles:
            source = os.path.join(self.sourcedir, filename)
            res = self.minimy_file(source, cwd=self._testdir)
            self.assertEqual(res, results[filename])

    def tearDown(self):
        """
        Clean up after ourselves
        """
        shutil.rmtree(self.testdir)

if __name__ == '__main__':
    unittest.main()

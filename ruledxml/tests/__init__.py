#!/usr/bin/env python3

import unittest
from . import test_destination
from . import test_source
from . import test_foreach

TEST_MODULES = [test_destination, test_source, test_foreach]


def runall():
    suite = unittest.TestSuite()
    for mod in TEST_MODULES:
        for member in dir(mod):
            if member.lower().startswith('test'):
                suite.addTest(unittest.makeSuite(getattr(mod, member)))

    return unittest.TextTestRunner(verbosity=2).run(suite)

def main():
    print(runall())


if __name__ == '__main__':
    main()

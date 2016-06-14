#!/usr/bin/env python3

import io
import unittest

import ruledxml

from . import utils


class TestRuledXmlNamespaces(unittest.TestCase):
    def run_test(self, nr):
        result = io.BytesIO()
        with open(utils.data(nr + '_source.xml')) as src:
            ruledxml.run(src, utils.data(nr + '_rules.py'), result)
        with open(utils.data(nr + '_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_040(self):
        self.run_test('040')

    def test_041(self):
        self.run_test('041')


def run():
    unittest.main()

if __name__ == '__main__':
    run()

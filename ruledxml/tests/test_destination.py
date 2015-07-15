#!/usr/bin/env python3

import io
import unittest
import lxml.etree

import ruledxml

from . import utils


class TestRuledXmlDestination(unittest.TestCase):
    def test_001(self):
        with open(utils.data('001_source.xml')) as src:
            with self.assertRaises(ruledxml.exceptions.RuledXmlException):
                ruledxml.run(src, utils.data('001_rules.py'), io.BytesIO())

    def test_002(self):
        result = io.BytesIO()
        with open(utils.data('002_source.xml')) as src:
            ruledxml.run(src, utils.data('002_rules.py'), result)
        with open(utils.data('002_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_003(self):
        result = io.BytesIO()
        with open(utils.data('003_source.xml')) as src:
            ruledxml.run(src, utils.data('003_rules.py'), result)
        with open(utils.data('003_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())


def run():
    unittest.main()

if __name__ == '__main__':
    run()

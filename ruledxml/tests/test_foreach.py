#!/usr/bin/env python3

import io
import unittest

import ruledxml

from . import utils


class TestRuledXmlForeach(unittest.TestCase):
    def test_020(self):
        result = io.BytesIO()
        with open(utils.data('020_source.xml')) as src:
            with self.assertRaises(ruledxml.exceptions.RuleForeachException):
                ruledxml.run(src, utils.data('020_rules.py'), result)

    def test_021(self):
        result = io.BytesIO()
        with open(utils.data('021_source.xml')) as src:
            ruledxml.run(src, utils.data('021_rules.py'), result)
        with open(utils.data('021_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_022(self):
        result = io.BytesIO()
        with open(utils.data('022_source.xml')) as src:
            ruledxml.run(src, utils.data('022_rules.py'), result)
        with open(utils.data('022_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_023(self):
        result = io.BytesIO()
        with open(utils.data('023_source.xml')) as src:
            ruledxml.run(src, utils.data('023_rules.py'), result)
        with open(utils.data('023_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_024(self):
        result = io.BytesIO()
        with open(utils.data('024_source.xml')) as src:
            ruledxml.run(src, utils.data('024_rules.py'), result)
        with open(utils.data('024_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_025(self):
        result = io.BytesIO()
        with open(utils.data('025_source.xml')) as src:
            ruledxml.run(src, utils.data('025_rules.py'), result)
        with open(utils.data('025_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_026(self):
        result = io.BytesIO()
        with open(utils.data('026_source.xml')) as src:
            ruledxml.run(src, utils.data('026_rules.py'), result)
        with open(utils.data('026_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())


def run():
    unittest.main()

if __name__ == '__main__':
    run()

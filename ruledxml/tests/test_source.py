#!/usr/bin/env python3

import io
import os
import lxml.etree
import unittest

import ruledxml

from . import utils


class TestRuledXmlSource(unittest.TestCase):
    def test_010(self):
        result = io.BytesIO()
        with open(utils.data('010_source.xml')) as src:
            with self.assertRaises(ruledxml.exceptions.RuledXmlException):
                ruledxml.run(src, utils.data('010_rules.py'), result)

    def test_011(self):
        result = io.BytesIO()
        with open(utils.data('011_source.xml')) as src:
            ruledxml.run(src, utils.data('011_rules.py'), result)
        with open(utils.data('011_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_012(self):
        result = io.BytesIO()
        with open(utils.data('012_source.xml')) as src:
            ruledxml.run(src, utils.data('012_rules.py'), result)
        with open(utils.data('012_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())


def run():
    unittest.main()

if __name__ == '__main__':
    run()

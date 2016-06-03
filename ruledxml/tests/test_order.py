#!/usr/bin/env python3

import io
import unittest

import ruledxml

from . import utils


class TestRuledXmlForeach(unittest.TestCase):
    def test_030(self):
        result = io.BytesIO()
        with open(utils.data('030_source.xml')) as src:
            ruledxml.run(src, utils.data('030_rules.py'), result)
        with open(utils.data('030_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())

    def test_031(self):
        result = io.BytesIO()
        with open(utils.data('031_source.xml')) as src:
            ruledxml.run(src, utils.data('031_rules.py'), result)
        with open(utils.data('031_target.xml'), 'rb') as target:
            utils.xmlEquals(self, result.getvalue(), target.read())


def run():
    unittest.main()

if __name__ == '__main__':
    run()

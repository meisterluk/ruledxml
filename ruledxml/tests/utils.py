#!/usr/bin/env python3

import os.path
import lxml.etree


def data(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


def xmlEquals(tc, xml1, xml2):
    """Are `xml1` and `xml2` in whitespace-canonicalized form equivalent?"""
    given = lxml.etree.tostring(lxml.etree.fromstring(xml1), method='c14n')
    expect = lxml.etree.tostring(lxml.etree.fromstring(xml2), method='c14n')
    print('Given: ', given)
    print('Expected: ', expect)
    tc.assertEquals(given, expect)

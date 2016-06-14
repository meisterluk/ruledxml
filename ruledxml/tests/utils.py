#!/usr/bin/env python3

import os.path
import lxml.etree


def data(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


def reorder_alphabetically(node):
    children = []
    for child in node.iterchildren():
        children.append(child)
        node.remove(child)

    children.sort(key=lambda c: c.tag)
    for child in children:
        node.append(child)

    return node


def reorder_recursively(root):
    reorder_alphabetically(root)
    for child in root.iterchildren():
        reorder_recursively(child)
    return root


def remove_whitespace(root):
    if root.tail:
        root.tail = root.tail.strip()
    if root.text:
        root.text = root.text.strip()
    for child in root.iterchildren():
        remove_whitespace(child)


def xmlEquals(tc, xml1, xml2):
    """Are `xml1` and `xml2` in whitespace-canonicalized form equivalent?"""
    tree1 = lxml.etree.fromstring(xml1)
    tree2 = lxml.etree.fromstring(xml2)

    remove_whitespace(tree1)
    reorder_recursively(tree1)
    remove_whitespace(tree2)
    reorder_recursively(tree2)

    given = lxml.etree.tostring(tree1, method='c14n')
    expect = lxml.etree.tostring(tree2, method='c14n')

    if given != expect:
        print("== Given XML tree ==")
        print(given)
        print("== Expected XML tree ==")
        print(expect)

    tc.assertEquals(given, expect)

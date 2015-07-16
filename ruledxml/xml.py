#!/usr/bin/env python3

"""
    XML creator
    -----------

    This library provides custom XML tools
    for ruledxml using the lxml library.

    (C) 2015, meisterluk, BSD 3-clause license
"""

import lxml.etree

from . import exceptions


def read(xmlinfile: str):
    """Given a filepath or file descriptor to an XML file, read the XML.

    :param xmlinfile:   file descriptor to XML file
    :type xmlinfile:    str
    :return:            an object representing the document object model
    :rtype:             lxml.etree.Element
    """
    return lxml.etree.parse(xmlinfile).getroot()


def write(dom: lxml.etree.Element, fd, encoding='utf-8', **lxml_options):
    """Write a given DOM into open file descriptor `fd`.

    :param dom:             a DOM (ie. root element) to store in an XML file
    :type dom:              lxml.etree.Element
    :param fd:              the file descriptor to write to
    :type fd:               _io.TextIOWrapper
    :param encoding:        which encoding shall be used for the XML file?
    :type encoding:         str
    :param lxml_options:    options for the lxml.etree.tostring
    :type lxml_options:     dict
    """
    opts = {
        'xml_declaration': True,
        'pretty_print': True,
        'encoding': encoding
    }
    opts.update(lxml_options)
    fd.write(lxml.etree.tostring(dom, **opts))


def strip_last_element(path):
    """Strip the last element off an XPath `path`.
    Raises InvalidPathException, if path refers to an attribute.

    For example ``/root/child`` returns ``/root`` and ``child``.

    :param path:    the XPath
    :type path:     str
    """
    index = path.rfind('/')
    if index == -1:
        base, last = '', path
    else:
        base, last = path[0:index], path[index + 1:]

    if '@' in last:
        msg = 'Expected path {} to refer to an element; refers to attribute'
        raise exceptions.InvalidPathException(msg.format(path))
    else:
        return base, last


def traverse(dom, path, *,
    initial_element=lambda elem: lxml.etree.Element(elem),
    multiple_options=lambda opts: opts[0],
    no_options=lambda elem, current: None,
    finish=lambda elem, attribute='', attr_xmlns='': None) -> tuple:
    """Traverse an XPath `path` in `dom`.

    *initial_element(name)*
      Called to create the root element representing the tree
    *multiple_options(alternatives)*
      Called whenever `path` is ambiguous.
      Return value is one of `alternatives` to pick to continue traversal.
    *no_options(name, current)*
      Called whenever at element `current` in DOM,
      element `name` does not exist. Return value
      contains a new element to consider as new current
      element. If None is returned instead, traversal is aborted.
    *finish(element, attribute, attr_xmlns)*
      Called when traversal is about to finish at `element`.
      If `attribute` is non-empty, it is the attribute name requested
      in the original `path` and `attr_xmlns` attribute's namespace.
      Return value is second return value of `traverse` function.

    :param dom:                 a root node representing a DOM
    :type dom:                  lxml.etree.Element
    :param path:                an XPath to traverse
    :type path:                 str
    :param multiple_options:    see above
    :type multiple_options:     function
    :param no_options:      see above
    :type no_options:       function
    :param finish:      see above
    :type finish:       function
    :return:        A root node for the new XML DOM and the finish return value
    :rtype:         tuple([lxml.etree.Element, *])
    """
    path, *attrs = str(path).split('@')
    elements = path.lstrip('/').split('/')
    if elements[-1] == '':
        elements = elements[:-1]

    current = dom
    for i, pelement in enumerate(elements):
        if i == 0 and dom is None:
            current = dom = initial_element(pelement)
            continue
        elif i == 0 and (dom.tag == pelement or dom.tag.endswith("}" + pelement)):
            # <tag>.xpath("tag") returns []   => current = dom
            continue

        options = current.xpath(pelement)

        if len(options) == 0 or options is None:
            current = no_options(name=pelement, current=current)
            if current is None:
                return dom, None
        elif len(options) == 1:
            current = options[0]
        else:
            current = multiple_options(options)

    if attrs:
        if ':' in attrs[0]:
            xmlns, attr = attrs[0].split(':')
        else:
            xmlns, attr = None, attrs[0]

        return dom, finish(element=current, attribute=attr, attr_xmlns=xmlns)
    else:
        return dom, finish(element=current)


def xmlns_to_lxml(element, xmlmap={}):
    """Given an `element` and an optional `xmlmap`. Return lxml-element name.

    >>> xmlns_to_lxml('name')
    'name'
    >>> xmlns_to_lxml('text', xmlmap={None: "http://www.w3.org/2000/svg",
    ... "xhtml":"http://www.w3.org/1999/xhtml"})
    ...
    '{http://www.w3.org/2000/svg}text'
    >>> xmlns_to_lxml('xhtml:text', xmlmap={None: "http://www.w3.org/2000/svg",
    ... "xhtml":"http://www.w3.org/1999/xhtml"})
    ...
    '{http://www.w3.org/1999/xhtml}text'

    :param element:     An element/element name
    :type element:      str
    :param xmlmap:      associates namespace identifiers to its URIs
    :type xmlmap:       dict
    :return:            lxml-element name (eg. useful for lxml.etree.Element)
    :rtype:             str
    """
    if not xmlmap:
        return element

    try:
        if ':' in element:
            ns, tag = element.split(":")
        else:
            ns, tag = None, element
    except ValueError:
        msg = "Invalid element name: '{}'".format(element)
        raise exceptions.InvalidPathException(msg)

    try:
        uri = xmlmap[ns]
    except KeyError:
        if ns is None:
            ns = 'default namespace'
        msg = "Unknown XML namespace: {}".format(ns)
        raise exceptions.InvalidPathException(msg)

    return '{' + uri + '}' + tag


def write_base_destination(dom: lxml.etree.Element, path: str, value,
    bases: list, xmlmap=None) -> lxml.etree.Element:
    """Behaves very much like `write_destination`, but also accepts `bases`,
    which defines a set of elements which is considered if the path is ambiguous.

    `value` will be converted to a string.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath to apply
    :type path:     str
    :param value:   the value to be written as text content or attribute value
    :param bases:   a set of elements considered if path is ambiguous
    :type bases:    iterable
    :param xmlmap:  Create new elements with given xmlmap and
                    traverse `path` with given `xmlmap`
    :type xmlmap:   dict
    :return:        text content, attribute or ''
    :rtype:         str
    """
    def root(name):
        return lxml.etree.Element(xmlns_to_lxml(name, xmlmap))

    def base_or_first(alternatives):
        for alt in alternatives:
            if alt in bases:
                return alt
        return alternatives[0]

    def write(element, *, attribute='', attr_xmlns=None):
        if attribute and not attr_xmlns:
            element.attrib[attribute] = str(value)
        elif attribute and attr_xmlns:
            attrname = '{%s}%s' % (attr_xmlns, attribute)
            element.attrib[attrname] = str(value)
        else:
            element.text = str(value)

    def create_element(name, current):
        new_element = lxml.etree.Element(name, nsmap=xmlmap)
        current.append(new_element)
        return new_element

    return traverse(dom, path, initial_element=root,
        multiple_options=base_or_first, no_options=create_element,
        finish=write)[0]


def read_base_source(dom: lxml.etree.Element, path: str, bases: list) -> str:
    """Behaves very much like `read_source`, but also accepts `bases`, which
    defines a set of elements which is considered if the path is ambiguous.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath to apply
    :type path:     str
    :param bases:   a set of elements considered if path is ambiguous
    :type bases:    iterable
    :return:        text content, attribute or ''
    :rtype:         str
    """
    def base_or_first(alternatives):
        for alt in alternatives:
            if alt in bases:
                return alt
        return alternatives[0]

    def read(element, attribute='', attr_xmlns=None):
        # TODO: namespace support
        if attribute:
            return str(element.attrib[attribute])
        else:
            return str(element.text or '')

    def abort(name, current):
        return None

    return traverse(dom, path, multiple_options=base_or_first,
        no_options=abort, finish=read)[1] or ''


def write_new_ambiguous_element(dom: lxml.etree.Element, path: str,
    bases=None, xmlmap=None) -> lxml.etree.Element:
    """Given a `path`, traverse it in `path`, use `bases` on ambiguous elements
    and create a new element for the top-level element of `path`.

    If a base for decision is missing, the first match is taken.

    :param dom:     root element of a DOM tree
    :type dom:      lxml.etree.Element
    :param path:    XPath to apply
    :type path:     str
    :param bases:   bases (ie. elements) to use if ambiguous
    :type bases:    list
    :param xmlmap:  Create new elements with given xmlmap and
                    traverse `path` with given `xmlmap`
    :type xmlmap:   dict
    :return:        the new created element at `path`
    :rtype:         lxml.etree.Element
    """
    path, last = strip_last_element(path)

    if bases is None:
        bases = []
    if not last:
        msg = "Path '{}' does not specify an element to create"
        raise exceptions.InvalidPathException(msg.format(path))

    def base_or_first(alternatives):
        for alt in alternatives:
            if alt in bases:
                return alt
        return alternatives[0]

    def return_element(element, attribute='', attr_xmlns=None):
        if attribute:
            msg = "Expected reference to element, but attribute {} reference given"
            raise exceptions.InvalidPathException(msg.format(attribute))
        return element

    def create_element(name, current):
        new_element = lxml.etree.Element(name, nsmap=xmlmap)
        current.append(new_element)
        return new_element

    last_element = traverse(dom, path, multiple_options=base_or_first,
        no_options=create_element, finish=return_element)[1]
    new_element = create_element(last, last_element)

    return new_element


def read_ambiguous_element(dom: lxml.etree.Element, path: str, bases=None) -> list:
    """Given a `path`, traverse it in `path`, use `bases` on ambiguous elements
    and return all elements which exist at the most-nested level of `path`.

    If a base for decision is missing, the first match is taken.

    :param dom:     root element of a DOM tree
    :type dom:      lxml.etree.Element
    :param path:    XPath to apply
    :type path:     str
    :param bases:   bases (ie. elements) to use if ambiguous
    :type bases:    list
    :return:        a list of elements at `path`
    :rtype:         list([lxml.etree.Element])
    """
    path, last = strip_last_element(path)

    if bases is None:
        bases = []
    if not last:
        return dom.xpath(last)

    def base_or_first(alternatives):
        for alt in alternatives:
            if alt in bases:
                return alt
        return alternatives[0]

    def return_element(element, attribute='', attr_xmlns=None):
        if attribute:
            msg = "Expected reference to element, but attribute {} reference given"
            raise exceptions.InvalidPathException(msg.format(attribute))
        return element

    def cont(name, current):
        return None

    last_element = traverse(dom, path, multiple_options=base_or_first,
        no_options=cont, finish=return_element)[1]
    if last_element is None:
        return []

    return last_element.xpath(last) or []


def write_destination(dom: lxml.etree.Element, path: str, value,
    xmlmap=None) -> lxml.etree.Element:
    """Write a `value` to an XPath `path` in `dom`.
    If `path` points to element, set text node to `value`.
    If `path` points to attribute, set attribute content to `value`.
    `value` will be converted to a string before written.

    This corresponds to the behavior of @destination.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath to apply
    :type path:     str
    :param value:   a value to write, string representation is taken
    :param xmlmap:  Create new elements with given xmlmap and
                    traverse `path` with given `xmlmap`
    :type xmlmap:   dict
    :return:        the (potentially modified) `dom` element
    :rtype:         lxml.etree.Element
    """
    def root(name):
        element_id = xmlns_to_lxml(name, xmlmap=xmlmap)
        return lxml.etree.Element(element_id, nsmap=xmlmap)

    def first(alternatives):
        return alternatives[0]

    def write(element, *, attribute='', attr_xmlns=None):
        if attribute and not attr_xmlns:
            element.attrib[attribute] = str(value)
        elif attribute and attr_xmlns:
            try:
                attrname = '{%s}%s' % (xmlmap[attr_xmlns], attribute)
                element.attrib[attrname] = str(value)
            except KeyError:
                raise KeyError("Unknown namespace: {}".format(attr_xmlns))
        else:
            element.text = str(value)

    def cont(name, current):
        new_element = lxml.etree.Element(name, nsmap=xmlmap)
        current.append(new_element)
        return new_element

    return traverse(dom, path, initial_element=root,
        multiple_options=first, no_options=cont, finish=write)[0]


def read_source(dom: lxml.etree.Element, path: str) -> str:
    """Apply a XPath `path` to `dom`. If path is ambiguous, take first option.
    If `path` points to element, return text node of it.
    If `path` points to attribute, return attribute content as string.
    If any error occurs, return an empty string.

    This corresponds to the behavior of @source.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath to apply
    :type path:     str
    :return:        text content, attribute or ''
    :rtype:         str
    """
    # TODO: namespace support
    if path == '':
        return ''
    elif '@' in path:
        val = dom.xpath(path)
        if val:
            return val[0] or ''
        else:
            return ''
    else:
        elements = dom.xpath(path)
        if elements:
            return elements[0].text or ''
        else:
            return ''

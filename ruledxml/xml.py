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


def make_xpath(element, query, nsmap):
    """Perform an XPath query on `element`. Maps `nsmap` back into the query.
    Instead of::

    >>> element.xpath('/{http://example.org}root',
    ...               namespaces={'ns': 'http://example.org'})

    you need to call

    >>> element.xpath('/ns:root', namespaces={'ns': 'http://example.org'})

    This helper function resolves this namespacing.

    :param element:     element of an XML DOM
    :type element:      lxml.etree.Element
    :param query:       an XPath expression
    :type query:        str
    :param nsmap:       a map of XML namespaces
    :type nsmap:        dict
    :return:            the xpath call return value
    """
    wo_default = dict((k, v) for k,v in nsmap.items() if k is not None)
    if '{' not in query:
        return element.xpath(query, namespaces=wo_default)

    for name, uri in nsmap.items():
        if name is None:
            query = query.replace('{' + uri + '}', '')
        else:
            query = query.replace('{' + uri + '}', name + ':')

    return element.xpath(query, namespaces=wo_default)


def split_xmlpath(xmlpath: str) -> list:
    """Given an XML-like path. Return its split components.

    >>> split_xmlpath('/a/b')
    ['a', 'b']
    >>> split_xmlpath('/a/@b')
    ['a']
    >>> split_xmlpath('/{http://example.org}a/b')
    ['{http://example.org}a', 'b']

    :param xmlpath:     An XML path like string to parse
    :type xmlpath:      str
    :return:            components of the given path
    :rtype:             list
    """
    in_brackets = False
    indices = []
    for i, char in enumerate(xmlpath):
        if not in_brackets and char == '{':
            in_brackets = True
        elif in_brackets and char == '}':
            in_brackets = False
        elif not in_brackets and char == '/':
            indices.append(i)

    a = [0] + indices[:]
    b = indices[:] + [len(xmlpath)]
    return [xmlpath[src + 1:dst] for src, dst in zip(a, b)
            if src < dst and xmlpath[src + 1:dst]]


def strip_last_element(path):
    """Strip the last element off an XPath-like `path`.
    Raises InvalidPathException, if path refers to an attribute.

    For example ``/root/child`` returns ``/root`` and ``child``.

    :param path:    the XPath-like path
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
    initial_element=lambda elem, xmlmap: lxml.etree.Element(elem),
    multiple_options=lambda opts: opts[0],
    no_options=lambda elem, current, xmlmap: None,
    finish=lambda elem, attr, xmlmap: None,
    xmlmap={}) -> tuple:
    """Traverse an XPath-like `path` in `dom`.

    *initial_element(name, xmlmap)*
      Called to create the root element representing the tree.
    *multiple_options(alternatives)*
      Called whenever `path` is ambiguous.
      Return value is one of `alternatives` to pick to continue traversal.
    *no_options(name, current, xmlmap)*
      Called whenever at element `current` in DOM,
      element `name` does not exist. Return value
      contains a new element to consider as new current
      element. If None is returned instead, traversal is aborted.
    *finish(element, attr=None, xmlmap=[])*
      Called when traversal is about to finish at `element`.
      If `attr` is non-empty, it is the (optionally namespaced)
      attribute's name requested in the original `path` and
      `xmlmap` attribute's namespace.
      Return value is second return value of `traverse` function.

    :param dom:              a root node representing a DOM
    :type dom:               lxml.etree.Element
    :param path:             an XPath-like path to traverse
    :type path:              str
    :param initial_element:  called to create the root element, see above
    :type initial_element:   function
    :param multiple_options: choose one option, see above
    :type multiple_options:  function
    :param no_options:       if no element for traversal exists, see above
    :type no_options:        function
    :param finish:           access element or attribute, see above
    :type finish:            function
    :param xmlmap:           XML namespaces as dictionary ``{name: uri}``
    :type xmlmap:            dict
    :return:                 A root node for the new XML DOM and
                             the finish return value
    :rtype:                  tuple([lxml.etree.Element, *])
    """
    base, *attrs = str(path).split('@')
    elements = split_xmlpath(base)

    if xmlmap is None:
        xmlmap = {}

    current = dom
    for i, pelement in enumerate(elements):
        # if root
        if i == 0 and dom is None:
            current = dom = initial_element(pelement, xmlmap)
            continue
        elif i == 0 and (dom.tag == pelement or dom.tag.endswith("}" + pelement)):
            # REMARK <tag>.xpath("tag") returns []   => current = dom
            continue

        # check options
        options = make_xpath(current, pelement, xmlmap)

        # case distinction for number of options
        if len(options) == 0 or options is None:
            current = no_options(pelement, current, xmlmap)
            if current is None:
                return dom, None
        elif len(options) == 1:
            current = options[0]
        else:
            current = multiple_options(options)

    if not attrs:
        attrs = [None]

    return dom, finish(current, attrs[0], xmlmap)


def element_to_path(element):
    """Given an ``lxml.etree.Element``, return a qualified path.

    :param element:     element of an XML DOM
    :type element:      lxml.etree.Element
    :return:            a qualified path like ``/b/{http://example.org}a``
    :rtype:             str
    """
    path = []
    for parent in element.iterancestors()[-1]:
        path.append(parent.tag)
    path.append(element.tag)
    return path


def write_base_destination(dom: lxml.etree.Element, path: str, value,
    bases: list, xmlmap=None) -> lxml.etree.Element:
    """Behaves very much like `write_destination`, but also accepts `bases`,
    which defines a set of elements which is considered if the path is ambiguous.

    `value` will be converted to a string.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param value:   the value to be written as text content or attribute value
    :param bases:   a set of elements considered if path is ambiguous
    :type bases:    iterable
    :param xmlmap:  an association of XML namespaces to URIs
    :type xmlmap:   dict
    :return:        text content, attribute or ''
    :rtype:         str
    """
    def root(name, xmlmap):
        return lxml.etree.Element(name, nsmap=xmlmap)

    def base_or_first(alternatives):
        for alt in alternatives:
            if alt in bases:
                return alt
        return alternatives[0]

    def create_element(name, current, xmlmap):
        new_element = lxml.etree.Element(name, nsmap=xmlmap)
        current.append(new_element)
        return new_element

    def write(element, attribute='', attr_xmlns={}):
        if attribute:
            if attr_xmlns:
                element.nsmap.update(attr_xmlns)
            element.attrib[attribute] = str(value)
        else:
            element.text = str(value)

    return traverse(dom, path, initial_element=root,
        multiple_options=base_or_first, no_options=create_element,
        finish=write, xmlmap=xmlmap)[0]


def read_base_source(dom: lxml.etree.Element, path: str,
    bases: list, xmlmap={}) -> str:
    """Behaves very much like `read_source`, but also accepts `bases`, which
    defines a set of elements which is considered if the path is ambiguous.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param bases:   a set of elements considered if path is ambiguous
    :type bases:    iterable
    :param xmlmap:  an association of XML namespaces to URIs
    :type xmlmap:   dict
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
    bases=None, xmlmap={}) -> lxml.etree.Element:
    """Given a `path`, traverse it in `path`, use `bases` on ambiguous elements
    and create a new element for the top-level element of `path`.

    If a base for decision is missing, the first match is taken.

    :param dom:     root element of a DOM tree
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param bases:   bases (ie. elements) to use if ambiguous
    :type bases:    list
    :param xmlmap:  an association of XML namespaces to URIs
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

    def return_element(element, attribute='', xmlmap=None):
        if attribute:
            msg = "Expected reference to element, but attribute {} reference given"
            raise exceptions.InvalidPathException(msg.format(attribute))
        return element

    def create_element(name, current, xmlmap):
        new_element = lxml.etree.Element(name, nsmap=xmlmap)
        current.append(new_element)
        return new_element

    last_element = traverse(dom, path, multiple_options=base_or_first,
        no_options=create_element, finish=return_element)[1]
    new_element = create_element(last, last_element, xmlmap)

    return new_element


def read_ambiguous_element(dom: lxml.etree.Element,
    path: str, bases=None, xmlmap={}) -> list:
    """Given a `path`, traverse it in `path`, use `bases` on ambiguous elements
    and return all elements which exist at the most-nested level of `path`.

    If a base for decision is missing, the first match is taken.

    :param dom:     root element of a DOM tree
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param bases:   bases (ie. elements) to use if ambiguous
    :type bases:    list
    :param xmlmap:  an association of XML namespaces to URIs
    :type xmlmap:   dict
    :return:        a list of elements at `path`
    :rtype:         list([lxml.etree.Element])
    """
    path, last = strip_last_element(path)

    if bases is None:
        bases = []
    if not last:
        return make_xpath(dom, last, xmlmap)

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

    return make_xpath(last_element, last, xmlmap) or []


def write_destination(dom: lxml.etree.Element, path: str, value,
    xmlmap=None) -> lxml.etree.Element:
    """Write a `value` to an XPath-like `path` in `dom`.
    If `path` points to element, set text node to `value`.
    If `path` points to attribute, set attribute content to `value`.
    `value` will be converted to a string before written.

    This corresponds to the behavior of @destination.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param value:   a value to write, string representation is taken
    :param xmlmap:  an association of XML namespaces to URIs
    :type xmlmap:   dict
    :return:        the (potentially modified) `dom` element
    :rtype:         lxml.etree.Element
    """
    def root(name, xmlmap):
        return lxml.etree.Element(name, nsmap=xmlmap)

    def first(alternatives):
        return alternatives[0]

    def write(element, attribute='', attr_xmlns={}):
        if attribute:
            if attr_xmlns:
                element.nsmap.update(attr_xmlns)
            element.attrib[attribute] = str(value)
        else:
            element.text = str(value)

    def cont(name, current, xmlmap):
        new_element = lxml.etree.Element(name, nsmap=xmlmap)
        current.append(new_element)
        return new_element

    return traverse(dom, path, initial_element=root,
        multiple_options=first, no_options=cont,
        finish=write, xmlmap=xmlmap)[0]


def read_source(dom: lxml.etree.Element, path: str, xmlmap={}) -> str:
    """Apply a XPath-like `path` to `dom`. If path is ambiguous, take first option.
    If `path` points to element, return text node of it.
    If `path` points to attribute, return attribute content as string.
    If any error occurs, return an empty string.

    This corresponds to the behavior of @source.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param xmlmap:  map of XML namespaces
    :type xmlmap:   dict
    :return:        text content, attribute or ''
    :rtype:         str
    """
    if path == '':
        return ''
    elif '@' in path:
        val = make_xpath(dom, path, xmlmap)
        if val:
            return val[0] or ''
        else:
            return ''
    else:
        elements = make_xpath(dom, path, xmlmap)
        if elements:
            return elements[0].text or ''
        else:
            return ''

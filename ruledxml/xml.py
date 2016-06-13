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
    initial_element=lambda elem, xmlns: lxml.etree.Element(elem),
    multiple_options=lambda opts: opts[0],
    no_options=lambda elem, current, xmlns: None,
    finish=lambda elem,
    xmlns=None: list) -> tuple:
    """Traverse an XPath-like `path` in `dom`.

    *initial_element(name, xmlns)*
      Called to create the root element representing the tree.
      Namespaced names are received as ``name``=``ns:tagname``.
    *multiple_options(alternatives)*
      Called whenever `path` is ambiguous.
      Return value is one of `alternatives` to pick to continue traversal.
    *no_options(name, current, xmlns)*
      Called whenever at element `current` in DOM,
      element `name` does not exist. Return value
      contains a new element to consider as new current
      element. If None is returned instead, traversal is aborted.
      Namespaced names are provided as ``name``=``ns:tagname``.
    *finish(element, attr=None, xmlns=[])*
      Called when traversal is about to finish at `element`.
      If `attr` is non-empty, it is the attribute's name requested
      in the original `path` and `xmlns` attribute's namespace.
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
    :param xmlns:            list of XML namespaces to apply
    :type xmlns:             list
    :return:                 A root node for the new XML DOM and
                             the finish return value
    :rtype:                  tuple([lxml.etree.Element, *])
    """
    base, *attrs = str(path).split('@')
    elements = base.strip('/').split('/')

    if xmlns is None:
        xmlns = []

    current = dom
    for i, pelement in enumerate(elements):
        # if root
        if i == 0 and dom is None:
            current = dom = initial_element(pelement, xmlns)
            continue
        elif i == 0 and (dom.tag == pelement or dom.tag.endswith("}" + pelement)):
            # REMARK <tag>.xpath("tag") returns []   => current = dom
            continue

        # check options
        options = current.xpath(pelement)

        # case distinction for number of options
        if len(options) == 0 or options is None:
            current = no_options(pelement, current, xmlns)
            if current is None:
                return dom, None
        elif len(options) == 1:
            current = options[0]
        else:
            current = multiple_options(options)

    if not attrs:
        attrs = [None]

    return dom, finish(current, attrs[0], xmlns)


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
    if element is None:
        raise TypeError("<None> cannot be an XML element")

    element = str(element).strip()
    try:
        if ':' in element and element[0] != ':':
            ns, tag = element.split(":")
        else:
            ns, tag = None, element
    except (ValueError, TypeError):
        msg = "Invalid element name: '{}'".format(element)
        raise exceptions.InvalidPathException(msg)

    if ns == 'xml':
        return '{http://www.w3.org/XML/1998/namespace}' + tag
    if ns is None:
        if xmlmap.get(ns):
            return '{' + xmlmap[ns] + '}' + tag
        else:
            return tag

    try:
        uri = xmlmap[ns]
    except KeyError:
        if ns is None:
            ns = 'default namespace'
        msg = "Unknown XML namespace: {}, given {!r}".format(ns, xmlmap)
        raise exceptions.InvalidPathException(msg)

    return '{' + uri + '}' + tag


def selected_xmlmap(xmlpath, xmlns):
    """Given an XML map (list of triples), return an XML map (``dict {name: URI}``)
    selecting XML namespaces which apply ``path``.

    >>> selected_xmlmap("/a/b", [('/a', 'ns0', 'http://example.org'),
    ...                          ('/a/b', 'ns1', 'http://example.com'),
    ...                          ('/other', 'ns2', 'http://xample.org')])
    {'ns0': 'http://example.org', 'ns1': 'http://example.com'}
    >>> selected_xmlmap("/a/b", [('/', 'ns0', 'http://example.org/')])
    {None: 'http://example.org/'}

    :param xmlpath: XPath-like to apply
    :type xmlpath:  str
    :param xmlns:   list of xml namespaces
    :type xmlns:    list
    :rtype:         dict
    :return:        a map of XML namespaces
    """
    def norm(p):
        base = p.split('@')[0].strip('/')
        if not base:
            return []
        rep = []
        for field in base.split('/'):
            if ':' in field and field[0] != ':':
                rep.append(field.split(':'))
            else:
                rep.append((None, field))
        return rep

    ref = norm(xmlpath)

    xmlmap = {}
    for path, name, uri in xmlns:
        base = norm(path)
        if path == '/' or not path:
            xmlmap[name] = uri
        elif ref[0:len(base)] == base:
            xmlmap[name] = uri

    return xmlmap


def namespaced_name(xmlpath, xmlns):
    """Given an XML map (list of triples), return a namespaced tag name or attribute.

    >>> namespaced_name("/b", [])
    'b'
    >>> namespaced_name("/a/b", [('/x', 'ns0', 'http://example.org')])
    'b'
    >>> namespaced_name("/a@b")
    'b'
    >>> namespaced_name("/ns0:a/ns0:b", [('/a', 'ns0', 'http://example.org')])
    '{http://example.org}b'
    >>> namespaced_name("/ns0:a@ns0:b", [('/a', 'ns0', 'http://example.org')])
    '{http://example.org}b'

    :param xmlpath: XPath-like to apply
    :type xmlpath:  str
    :param xmlns:   list of xml namespaces
    :type xmlns:    list
    :rtype:         string
    :return:        a namespaced tagname
    """
    def norm(p):
        base = p.split('@')[0].strip('/')
        if not base:
            return []
        rep = []
        for field in base.split('/'):
            if ':' in field and field[0] != ':':
                rep.append(field.split(':'))
            else:
                rep.append((None, field))
        return rep

    assert xmlpath, 'xmlpath must be non-empty'
    base, *attrs = xmlpath.split('@')
    ref = norm(base)

    xmlmap = {}
    for path, name, uri in xmlns:
        base = norm(path)
        if ref[0:len(base)] == base:
            xmlmap[name] = uri

    ns, name = None, ''
    if attrs:
        *n, attr = attrs[0].split(':')
        ns, name = n[0] if n else None, attr
    else:
        ns, name = ref[-1]

    if ns:
        try:
            return '{' + xmlmap[ns] + '}' + name
        except KeyError:
            errmsg = 'Unknown XML namespace: {} in {}'.format(ns, xmlpath)
            raise exceptions.InvalidPathException(errmsg)
    else:
        return name

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
    bases: list, xmlns=None) -> lxml.etree.Element:
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
    :param xmlns:   list of xml namespaces
    :type xmlns:    list
    :return:        text content, attribute or ''
    :rtype:         str
    """
    def root(name, xmlns):
        xml_map = selected_xmlmap('/' + name, xmlns)
        elementname = xmlns_to_lxml(name, xml_map)
        return lxml.etree.Element(elementname, nsmap=xml_map)

    def base_or_first(alternatives):
        for alt in alternatives:
            if alt in bases:
                return alt
        return alternatives[0]

    def create_element(name, current, xmlns):
        xml_map = selected_xmlmap(name, xmlns) # TODO ''
        new_element = lxml.etree.Element(name, nsmap=xml_map)
        current.append(new_element)
        return new_element

    def write(element, *, attribute='', attr_xmlns=None):
        if attribute and not attr_xmlns:
            element.attrib[attribute] = str(value)
        elif attribute and attr_xmlns:
            attrname = '{%s}%s' % (attr_xmlns, attribute)
            element.attrib[attrname] = str(value)
        else:
            element.text = str(value)

    return traverse(dom, path, initial_element=root,
        multiple_options=base_or_first, no_options=create_element,
        finish=write)[0]


def read_base_source(dom: lxml.etree.Element, path: str, bases: list) -> str:
    """Behaves very much like `read_source`, but also accepts `bases`, which
    defines a set of elements which is considered if the path is ambiguous.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param bases:   a set of elements considered if path is ambiguous
    :type bases:    iterable
    :return:        text content, attribute or ''
    :rtype:         str
    """
    print('read_base_source path={}  bases={}'.format(path, bases))
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
    bases=None, xmlns=None) -> lxml.etree.Element:
    """Given a `path`, traverse it in `path`, use `bases` on ambiguous elements
    and create a new element for the top-level element of `path`.

    If a base for decision is missing, the first match is taken.

    :param dom:     root element of a DOM tree
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :param bases:   bases (ie. elements) to use if ambiguous
    :type bases:    list
    :param xmlns:   list of xml namespaces
    :type xmlns:    list
    :return:        the new created element at `path`
    :rtype:         lxml.etree.Element
    """
    print('write_new_ambiguous_element path={}  bases={}  xmlns={}'.format(path, bases, xmlns))
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
        xml_map = selected_xmlmap('', xmlns)  # TODO ''
        new_element = lxml.etree.Element(name, nsmap=xml_map)
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
    :param path:    XPath-like path to apply
    :type path:     str
    :param bases:   bases (ie. elements) to use if ambiguous
    :type bases:    list
    :return:        a list of elements at `path`
    :rtype:         list([lxml.etree.Element])
    """
    print('read_ambiguous_element {} bases={}'.format(path, bases))
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
    xmlns=None) -> lxml.etree.Element:
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
    :param xmlns:   Create new elements with given namespaces and
                    traverse `path` with given `xmlns`
    :type xmlns:    list
    :return:        the (potentially modified) `dom` element
    :rtype:         lxml.etree.Element
    """
    def root(name):
        xml_map = selected_xmlmap(name, xmlns)
        element_id = xmlns_to_lxml(name, xml_map)
        #print(name, xmlns, element_id, xml_map)
        return lxml.etree.Element(element_id, nsmap=xml_map)

    def first(alternatives):
        return alternatives[0]

    def write(element, *, attribute='', attr_xmlns=None):
        if attribute and not attr_xmlns:
            element.attrib[attribute] = str(value)
        elif attribute and attr_xmlns:
            try:
                attrname = '{%s}%s' % (xmlns[attr_xmlns], attribute)
                element.attrib[attrname] = str(value)
            except KeyError:
                raise KeyError("Unknown namespace: {}".format(attr_xmlns))
        else:
            element.text = str(value)

    def cont(name, current):
        xml_map = selected_xmlmap(name, xmlns)
        new_element = lxml.etree.Element(name, nsmap=xml_map)
        current.append(new_element)
        return new_element

    return traverse(dom, path, initial_element=root,
        multiple_options=first, no_options=cont, finish=write)[0]


def read_source(dom: lxml.etree.Element, path: str) -> str:
    """Apply a XPath-like `path` to `dom`. If path is ambiguous, take first option.
    If `path` points to element, return text node of it.
    If `path` points to attribute, return attribute content as string.
    If any error occurs, return an empty string.

    This corresponds to the behavior of @source.

    :param dom:     root element of an XML DOM
    :type dom:      lxml.etree.Element
    :param path:    XPath-like path to apply
    :type path:     str
    :return:        text content, attribute or ''
    :rtype:         str
    """
    print('read_source {}'.format(path))
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

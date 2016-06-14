#!/usr/bin/env python3

"""
    ruledxml.core
    -------------

    Core implementation for application of rules to XML files.
    It covers the following steps:

    1. Read rules file
    2. Retrieve source XML file
    3. Do required elements exist?
    4. Apply rules
    5. Write resulting XML to file

    (C) 2015, meisterluk, BSD 3-clause license
"""

import re
import sys
import os.path
import logging
import pathlib
import argparse
import importlib.machinery
import collections

import lxml.etree

from . import fs
from . import xml
from . import exceptions


def unique_function(filepath: str):
    """Quick&dirty check that every python rule function has a unique name.

    :param filepath:            Filepath to a python file
    :type filepath:             str
    :raises RuledXmlException:  if a function name is defined twice
    """
    pattern = re.compile("def\s+(rule\w+)")
    functions = {}
    errmsg = ("Function name {} is defined multiple times "
              "in file {} (lines {} and {})")

    with open(filepath) as fp:
        for lineno, line in enumerate(fp):
            m = pattern.match(line)
            if not m:
                continue

            name = m.group(1)
            if name in functions:
                first = functions[name]
                msg = errmsg.format(name, filepath, first, lineno)
                raise exceptions.RuledXmlException(msg)

            functions[name] = lineno
            logging.info("Found {} at line {}".format(name, lineno))


def required_exists(dom: lxml.etree.Element, nonempty=None, required=None, *, filepath=''):
    """Validate `required` and `nonempty` fields.
    ie. raise InvalidPathException if path does not exist in `dom`.

    :param dom:                   the root element of a DOM to validate
    :type dom:                    lxml.etree.Element
    :param nonempty:              set of paths with nonempty values
    :type nonempty:               set
    :param required:              set of required paths
    :type required:               set
    :param filepath:              filepath (additional info for error message)
    :type filepath:               str
    :raises InvalidPathException: some required path does not exist / is empty
    """
    if not required:
        required = set()
    if not nonempty:
        nonempty = set()

    suffix = ""
    if filepath:
        suffix = " in XML file '{}'".format(filepath)

    for req in required:
        if not dom.xpath(req):
            errmsg = 'Path {} does not exist{}'.format(req, suffix)
            raise exceptions.InvalidPathException(errmsg.format(req))

    for req in nonempty:
        requested, xmlmap = normalize_path(req, xmlns)  # TODO: xmlns undefined
        if xml.read_source(dom, requested, xmlmap) == '':
            errmsg = 'Path {} is empty{}; must contain value'.format(req, suffix)
            raise exceptions.InvalidPathException(errmsg.format(req))


def read_rulesfile(filepath: str) -> tuple([dict, set]):
    """Given a `filepath`, return its contained rules and required attributes.
    Raises a exceptions.RuledXmlException if file does not contain any rule.

    :param filepath:        A filepath in the filesystem
    :type filepath:         str
    :return:                rules (associates name to implementation) and metadata
                            such as required attributes, xml namespaces and encoding
    :rtype:                 tuple(dict, dict)
    """
    def modulename(path: str) -> str:
        """Return module name for a rule file in given path"""
        return os.path.splitext(os.path.basename(path))[0]

    logging.info('Reading rules from %s', filepath)

    loader = importlib.machinery.SourceFileLoader(modulename(filepath), filepath)
    rulesfile = loader.load_module()

    rules = {}
    metadata = {
        'input_required': set(),
        'input_nonempty': set(),
        'input_xml_namespaces': [],
        'output_encoding': 'utf-8',
        'output_xml_namespaces': []
    }
    tmpl = "Found %s attribute with %d elements"

    for member in dir(rulesfile):
        if member.startswith("rule"):
            rules[member] = getattr(rulesfile, member)
            logging.info("Found %s", member)
        elif member in {"input_required", "input_nonempty",
                        "output_required", "output_nonempty"}:
            metadata[member] = set(getattr(rulesfile, member))
            logging.info(tmpl, member, len(metadata[member]))
        elif member == "input_xml_namespaces":
            metadata['input_xml_namespaces'] = getattr(rulesfile, member)
            logging.info(tmpl, "input_xml_namespaces", len(metadata['input_xml_namespaces']))
        elif member == "output_xml_namespaces":
            metadata['output_xml_namespaces'] = getattr(rulesfile, member)
            logging.info(tmpl, 'output_xml_namespaces', len(metadata['output_xml_namespaces']))
        elif member == "output_encoding":
            metadata['output_encoding'] = getattr(rulesfile, member)
            logging.info('Attribute %s found. Is set to %s', 'output_encoding',
                metadata['output_encoding'])

    # compatibility of input_xml_namespaces:
    #  dict in version 1 {name: uri}
    #  list in version 2 [(path, name, uri)]
    try:
        # lists don't have .get methods
        metadata['input_xml_namespaces'].get('fail')

    except AttributeError:
        # is a list: version 2 definition, fine
        pass

    else:
        # is a dict: version 1 definition, convert now
        input_xmlns = metadata['input_xml_namespaces']
        metadata['input_xml_namespaces'] = []
        for nsname, uri in input_xmlns:
            metadata['input_xml_namespaces'].append(('/', nsname, uri))

    # compatibility of output_xml_namespaces
    try:
        metadata['output_xml_namespaces'].get('fail')
    except AttributeError:
        pass
    else:
        output_xmlns = metadata['output_xml_namespaces']
        metadata['output_xml_namespaces'] = []
        for nsname, uri in output_xmlns:
            metadata['output_xml_namespaces'].append(('/', nsname, uri))

    # the following namespaces are predefined
    # https://www.w3.org/TR/REC-xml-names/#ns-decl
    XML_NS = 'http://www.w3.org/XML/1998/namespace'

    for key in ['input_xml_namespaces', 'output_xml_namespaces']:
        xml_found = False

        for path, name, uri in metadata[key]:
            if name == 'xml':
                logging.warn("xml namespace is defined per default")
                if uri != XML_NS:
                    logging.warn("xml namespace is non-standard, will be replaced")
            if name == 'xmlns':
                logging.error("xml namespace 'xmlns' is illegal, will be removed")

        metadata[key] = map(lambda e: (e[0], e[1], XML_NS if e[1] == 'xml' else e[2]), metadata[key])
        metadata[key] = list(filter(lambda e: e[1] != 'xmlns', metadata[key]))

        if not xml_found:
            metadata[key].append(('/', 'xml', XML_NS))

    if not rules:
        msg = "Expected at least one rule definition, none given in {}"
        raise exceptions.RuledXmlException(msg.format(filepath))

    logging.debug('metadata found: %s', str(metadata))

    return rules, metadata


def validate_rules(rules: dict):
    """Validate rules. Test whether decorator setup is fine for all of them.

    :param rules:               rule names associated to their implementation
    :type rules:                dict(str: function)
    :raises RuledXmlException:  a decorator is set up wrongfully
    """
    for rulename, rule in rules.items():
        # a rule must have @source, @destination or @foreach applied
        if not hasattr(rule, 'metadata'):
            msg = ("Function {} is considered to be a rule, but it "
                   "requires at least a @destination declaration")
            raise exceptions.InvalidRuleDestination(msg.format(rulename))

        # a rule must have at least one @destination
        dst = rule.metadata.get('dst', {})
        dst_len = len(dst.get('dests', []))
        if dst_len != 1:
            msg = "A rule must have exactly 1 @destination. {} has {}"
            raise exceptions.TooManyRuleDestinations(msg.format(rulename, dst_len))

        # distinguish: foreach, no-foreach
        if 'each' in rule.metadata:
            each_len = len(rule.metadata['each'])
            if each_len == 0:
                msg = "A @foreach rule requires at least 2 arguments. {} has 0"
                raise exceptions.InvalidRuleForeach(msg.format(rulename))

            each_arg_len = len(rule.metadata['each'][0])
            if each_arg_len != 2:
                msg = "@foreach must have exactly two arguments. {} has {}"
                raise exceptions.InvalidRuleForeach(msg.format(rulename, each_arg_len))

            each_dst_len = len(rule.metadata.get('dst', {}).get('dsts', []))
            if each_dst_len > 1:
                msg = ("@foreach rules must have at most "
                       "1 @destination. {} has {}")
                raise exceptions.InvalidRuleForeach(msg.format(rulename, each_dst_len))

            # outer @foreach[0] must be prefix of innner @foreach[0]
            destination = rule.metadata['dst']['dests'][0]
            for source in rule.metadata.get('src', []):
                prev_base_src = None
                for base_src, base_dst in rule.metadata['each']:
                    if prev_base_src is not None and not base_src.startswith(prev_base_src):
                        msg = ("Outer first @foreach argument '{}' must be prefix of "
                               "inner first @foreach argument '{}'")
                        raise exceptions.InvalidRuleForeach(msg.format(prev_base_src, base_src))

                    prev_base_src = base_src

        else:
            pass  # no further checks


def build_recursive_structure(rules: list) -> list:
    """Build a recursive structure based on foreach-sources of the given rules.

    >>> rule1 = {
    ...   'foreach': [('a', 'x'), ('ab', 'xy')],
    ...   'source': ['1', 'a2', 'ab3', 'ab4'],
    ...   'destination': ['xy5']
    ... }
    >>> rule2 = {
    ...   'foreach': [('a', 'x'), ('ac', 'xz')],
    ...   'source': ['6'],
    ...   'destination': ['xz7']
    ... }
    >>> build_recursive_structure([rule1, rule2])
    [{
        'class': 'iteration',
        'dstbase': 'x',
        'srcbase': 'a',
        'children': [
            {   'class': 'iteration',
                'dstbase': 'xy',
                'srcbase': 'ab',
                'children': []
            }, {'class': 'iteration',
                'dstbase': 'xz',
                'srcbase': 'ac',
                'children': []
        }]
    }]

    :param rules:       a set of rules to read @foreach attributes from
    :type rules:        list
    :return:            a list of (potentially nested) dictionaries
    :rtype:             list
    """
    all_each_bases = set()
    for rule in rules:
        for each in rule['foreach']:
            all_each_bases.add(each)

    all_each_bases = list(all_each_bases)
    all_each_bases.sort(key=lambda e: e[0])

    structure = []

    for base in all_each_bases:
        current = structure

        added = False
        while not added:
            for element in current:
                if base[0].startswith(element['srcbase']):
                    current = element['children']
                    break
            else:
                childs = []
                current.append({
                    'class': 'iteration',
                    'srcbase': base[0],
                    'dstbase': base[1],
                    'children': childs
                })
                current = childs
                added = True

    return structure


def classify_rules(rules: dict):
    """Classify rules. Represent rules as dictionary with associated metadata.
    Returns a data structure with is nicely structured to perform the @source
    and @destination algorithms with respect to @foreach semantics.

    :param rules:       rule names associated to their implementation
    :type rules:        dict(str: function)
    :return:            a list of dictionaries containing rules with metadata;
                        might be recursive (dicts contain lists of dicts)
    :rtype:             [dict(), dict(), ...]
    """
    classified = []
    max_user_dorder = None

    # add basic rules
    each_found = False
    for rulename, rule in rules.items():
        if 'each' in rule.metadata:
            each_found = True
            continue

        user_dorder = rule.metadata.get('dst', {}).get('order')
        if user_dorder is not None:
            user_dorder = int(user_dorder)
        if max_user_dorder is None or (user_dorder is not None and user_dorder > max_user_dorder):
            max_user_dorder = user_dorder

        classified.append({
            'name': rulename,
            'class': 'basicrule',
            'rule': rule,
            'each': [],
            'src': rule.metadata.get('src', []),
            'dst': rule.metadata.get('dst', {}).get('dests', []),
            'dorder': user_dorder
        })

    if max_user_dorder is None:
        max_user_dorder = 0

    # assign destination orders not defined by user
    for ruledata in classified:
        if ruledata['dorder'] is None:
            max_user_dorder += 1
            ruledata['dorder'] = max_user_dorder

    if not each_found:
        return classified

    # collect the set of all @foreach base sources
    foreach_rules = []
    for rulename, rule in rules.items():
        if 'each' not in rule.metadata:
            continue

        dorder = rule.metadata.get('dst', {}).get('dorder')
        if dorder is None:
            max_user_dorder += 1
            dorder = max_user_dorder

        foreach_rules.append({
            'foreach': rule.metadata.get('each', []),
            'source': rule.metadata.get('src', []),
            'destination': rule.metadata.get('dst', {}).get('dests', []),
            'dorder': dorder
        })

    # build recursive structure for @foreach entries
    # node tell when an ambiguous element has to be iterated
    recursive_structure = build_recursive_structure(foreach_rules)

    # annotate rules to it
    def traverse(tree, xpath):
        # Assumption. xpath exists as base in tree.
        assert xpath
        current = tree
        found = False
        while not found:
            for element in current:
                if xpath == element['srcbase']:
                    return element['children']
                if xpath.startswith(element['srcbase']):
                    current = element['children']

    # add the rules to the recursive structure
    for rulename, rule in rules.items():
        if 'each' not in rule.metadata:
            continue

        dorder = rule.metadata.get('dst', {}).get('dorder')
        if dorder is None:
            max_user_dorder += 1
            dorder = max_user_dorder

        most_nested = rule.metadata['each'][-1]
        lst = traverse(recursive_structure, most_nested[0])
        lst.append({
            'class': 'foreach-rule',
            'name': rulename,
            'src': rule.metadata.get('src', []),
            'dst': rule.metadata.get('dst', {}).get('dests', []),
            'dorder': dorder,
            'rule': rule
        })

    for struct in recursive_structure:
        classified.append(struct)

    return classified


def reorder_rules(rules: dict):
    """Take `rules` and reorder rules such that rule
    with low orders are executed first.

    :param rules:       a recursive structure representing rules to be executed
    :type rules:        dict(str: function)
    :return:            a list of dictionaries containing rules with metadata;
                        might be recursive (dicts contain lists of dicts)
    :rtype:             [dict(), dict(), ...]
    """
    def sorting_traverse(node):
        node.sort(key=lambda v: v.get('dorder', float('inf')))
        for d in node:
            if 'children' in d:
                sorting_traverse(d['children'])

    sorting_traverse(rules)
    return rules



def normalize_path(xmlpath: str, xmlns=[]) -> str:
    """Normalize a given `xmlpath`. Hence replace namespaces with actual URIs
    and normalize spaces/slashes.

    :param xmlpath: an XPath-like expression
    :type xmlpath:  str
    :param xmlns:   XML namespace list as triples ``(path, name, uri)``
    :type xmlns:    list
    :return:        normalized path and XML map that applies
    :rtype:         (str, dict)
    """
    def norm(p):
        base, *attrs = p.split('@')
        elements = list(filter(bool, base.strip('/').split('/')))

        # prepare attribute
        if attrs:
            attre = attrs[0].split(':')
            assert len(attre) <= 2, "Only one namespace allowed in attributes"
            if len(attre) == 1:
                attr = (None, attre[0])
            else:
                attr = (attre[0], attre[1])
        else:
            attr = None

        # if empty path
        if not elements:
            return [], attr

        # prepare children
        rep = []
        for elem in elements:
            if ':' in elem and elem[0] != ':':
                rep.append(tuple(elem.split(':')))
            else:
                rep.append((None, elem))

        return rep, attr

    assert 0 <= xmlpath.count('@') <= 1, "only one @ symbol allowed in paths"
    base, base_attr = norm(xmlpath)
    xmlmap = {}
    for path, name, uri in xmlns:
        ref, attr = norm(path)
        if base[0:len(ref)] == ref:
            xmlmap[name] = uri

    normalized_path = ''
    for ns, element in base:
        normalized_path += '/'
        if ns:
            try:
                normalized_path += '{' + xmlmap[ns] + '}'
            except KeyError:
                errmsg = "Unknown namespace {} in path {}".format(ns, xmlpath)
                raise exceptions.InvalidPathException(errmsg)
        normalized_path += element

    if base_attr:
        if base_attr[0] is not None:
            try:
                attr = '{' + xmlmap[base_attr[0]] + '}' + base_attr[1]
            except KeyError:
                errmsg = "Unknown attribute namespace {} in path {}".format(base_attr[0], xmlpath)
                raise exceptions.InvalidPathException(errmsg)
        else:
            attr = base_attr[1]
        normalized_path += '/@' + attr

    return normalized_path, xmlmap


def run_rules(src_dom: lxml.etree.Element, target_dom: lxml.etree.Element,
    classified: list, input_xmlns=None, output_xmlns=None):
    """Actually apply the classified rules to a target DOM.

    :param src_dom:      the root element of a DOM to retrieve source data from
    :type src_dom:       lxml.etree.Element
    :param target_dom:   the root element of a DOM to write destination data to
    :type target_dom:    lxml.etree.Element
    :param classified:   a list of dictionaries containing rules with metadata;
                         might be recursive (dicts contain lists of dicts)
    :type classified:    [dict(), dict(), ...]
    :param input_xmlns:  XML namespaces occuring when reading the source file
    :type input_xmlns:   list
    :param output_xmlns: XML namespaces to be declared in a target file
    :type output_xmlns:  list
    :param bases:        Base elements (created for source @foreach elements)
    :type bases:         list
    :return:             the root element of a new DOM
    :rtype:              lxml.etree.Element
    """
    def finish_a_tree(src_dom, target_dom, node, src_bases, dst_bases):
        if node['class'] == 'iteration':
            srcbase, xmlmap = normalize_path(node['srcbase'], input_xmlns)
            for src_base in xml.read_ambiguous_element(src_dom, srcbase, src_bases, xmlmap):
                dstbase, xmlmap2 = normalize_path(node['dstbase'], output_xmlns)
                dst_base = xml.write_new_ambiguous_element(target_dom,
                    dstbase, dst_bases, xmlmap2)
                for child in node['children']:
                    target_dom = finish_a_tree(src_dom, target_dom, child,
                        src_bases.copy() + [src_base], dst_bases.copy() + [dst_base])
            return target_dom
        elif node['class'] == 'foreach-rule':
            args = []
            for src in node['src']:
                source, xmlmap = normalize_path(src, input_xmlns)
                args.append(xml.read_base_source(src_dom, source,
                    bases=src_bases, xmlmap=xmlmap))
            output = node['rule'](*args)
            if output is None:
                return target_dom
            dst, xmlmap = normalize_path(node['dst'][0], output_xmlns)
            return xml.write_base_destination(target_dom, dst,
                output, bases=dst_bases, xmlmap=xmlmap)

    for obj in classified:
        if obj['class'] == 'basicrule':
            logging.info("Applying %s", obj['name'])

            args = []
            for src in obj['src']:
                source, xmlmap = normalize_path(src, input_xmlns)
                args.append(xml.read_source(src_dom, source, xmlmap))

            logging.debug("Applying %s with arguments %s", obj['name'], str(args))

            output = obj['rule'](*args)
            if output is None:
                continue
            dst, xmlmap = normalize_path(obj['dst'][0], output_xmlns)
            target_dom = xml.write_destination(target_dom, dst, output, xmlmap=xmlmap)

        elif obj['class'] in ('iteration', 'foreach-rule'):
            target_dom = finish_a_tree(src_dom, target_dom, obj, [], [])

    return target_dom


def apply_rules(dom: lxml.etree.Element, rules: dict, *, input_xmlns=None, output_xmlns=None):
    """Apply given rules to the given DOM.

    :param dom:                 the root element of a DOM
    :type dom:                  lxml.etree.Element
    :param rules:               rule names associated to their implementation
    :type rules:                dict(str : function)
    :param input_xmlns:         XML namespaces of source file to be considered
    :type input_xmlns:          list
    :param input_xmlns:         XML namespaces to target file be considered
    :type input_xmlns:          list
    :return:                    root element of a new DOM
    :rtype:                     lxml.etree.Element
    :raises RuledXmlException:  some rule is invalid
    """
    validate_rules(rules)
    classified = classify_rules(rules)
    ordered = reorder_rules(classified)
    return run_rules(dom, None, ordered, input_xmlns, output_xmlns)


def run(in_fd, rules_filepath: str, out_fd, *, infile='', outfile='') -> int:
    """Process one file.

    :param in_fd:           File descriptor to one input XML file
    :type in_fd:            _io.TextIOWrapper
    :param rules_filepath:  Filepath to a rulesfile
    :type rules_filepath:   str
    :param out_fd:          File descriptor to an output XML file
    :type out_fd:           _io.TextIOWrapper
    :param infile:          original XML input file path for debugging purposes
    :type infile:           str
    :param outfile:         output XML file path for debugging purposes
    :type outfile:          str
    :return:                exit code 0
    :rtype:                 int
    """
    # read rules file
    unique_function(rules_filepath)
    rules, meta = read_rulesfile(rules_filepath)

    # retrieve source xmlfile
    src_dom = xml.read(in_fd)

    # test: required elements exist?
    required_exists(src_dom, meta['input_nonempty'], meta['input_required'], filepath=infile)

    # apply rules
    target_dom = apply_rules(src_dom, rules,
        input_xmlns=meta['input_xml_namespaces'],
        output_xmlns=meta['output_xml_namespaces'])

    # write target XML to file
    xml.write(target_dom, out_fd, encoding=meta['output_encoding'])

    return 0


def batch_run(in_fd, rules_filepath: str, out_filepaths: list([str]),
    base: str, *, infile='') -> int:
    """Process one file. Apply rules for some base path.
    Create several target DOMs.

    :param in_fd:           File descriptor to one input XML file
    :type in_fd:            _io.TextIOWrapper
    :param rules_filepath:  Filepath to a rulesfile
    :type rules_filepath:   str
    :param out_filepaths:   File descriptor to an output XML file
    :type out_filepaths:    _io.TextIOWrapper
    :param base:            A base XPath, all rules are applied relative to this path
    :type base:             str
    :param infile:          original XML input file path for debugging purposes
    :type infile:           str
    :return:                exit code 0
    :rtype:                 int
    """
    # read rules file
    unique_function(rules_filepath)
    rules, meta = read_rulesfile(rules_filepath)

    # retrieve source xmlfile
    src_dom = xml.read(in_fd)

    count = 0
    for element in src_dom.xpath(base):
        # test: required elements exist?
        required_exists(element, meta['input_nonempty'],
            meta['input_required'], filepath=infile)

        # apply rules
        target_dom = apply_rules(element, rules,
            input_xmlns=meta['input_xml_namespaces'],
            output_xmlns=meta['output_xml_namespaces'])

        # test: required elements exist?
        required_exists(target_dom, meta['output_nonempty'], meta['output_required'])

        # write target XML to file
        fs.create_base_directories(out_filepaths[count])
        with open(out_filepaths[count], 'wb') as out_fd:
            xml.write(target_dom, out_fd, encoding=meta['output_encoding'])

        count += 1

    if count < len(out_filepaths):
        msg = "Number of output filepaths was {}; expected {}"
        logging.warn(msg.format(count, len(out_filepaths)))

    return 0

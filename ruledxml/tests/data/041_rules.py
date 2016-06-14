#!/usr/bin/env python3

from ruledxml import source, destination

input_xml_namespaces = [
    ("/doc:doc", "doc", "http://example.org/")
]

output_xml_namespaces = [
    ("/xhtml:html", "xhtml", "http://www.w3.org/1999/xhtml")
]


@destination("/xhtml:html/@xml:lang")
def ruleLanguage():
    return "de"


@source("/doc:doc/doc:head")
@destination("/xhtml:html/xhtml:head/xhtml:title")
def ruleTitle(head):
    return head


@source("/doc:doc/doc:body")
@destination("/xhtml:html/xhtml:body")
def ruleBody(body):
    return body

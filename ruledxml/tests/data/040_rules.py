#!/usr/bin/env python3

from ruledxml import source, destination

output_xml_namespaces = [
    ("/html", None, "http://www.w3.org/1999/xhtml")
]


@destination("/html@xml:lang")
def ruleLanguage():
    return "de"


@source("/doc/head")
@destination("/html/head/title")
def ruleTitle(head):
    return head


@source("/doc/body")
@destination("/html/body")
def ruleBody(body):
    return body

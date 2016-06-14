from ruledxml import destination, source, foreach


@foreach("/html/body/article", "/doc/section")
@source("/html/head/meta/@charset")
@destination("/doc/section/@charset")
def ruleMultipleNestedBasesCharset(charset):
    return charset

@foreach("/html/body/article", "/doc/section")
@source("/html/body/article/lang")
@destination("/doc/section/@language")
def ruleMultipleNestedBasesLanguage(lang):
    return lang

@foreach("/html/body/article", "/doc/section")
@source("/html/body/article/p")
@source("/html/body/article/h1")
@destination("/doc/section/text/paragraph")
def ruleMultipleNestedBasesParagraph(h1, p):
    return h1 + ": " + p

@foreach("/html/body/article", "/doc/section")
@destination("/doc/section/text/paragraph/@style")
def ruleMultipleNestedBasesParagraphStyle():
    return "text-indent:5px"


@foreach("/html/body/article/ul/li", "/doc/section/text/list/item")
@foreach("/html/body/article", "/doc/section")
@source("/html/body/article/ul/li")
@destination("/doc/section/text/list/item")
def ruleMultipleNestedBasesItems(li):
    return li

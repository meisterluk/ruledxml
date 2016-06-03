from ruledxml import destination, source, foreach

@source("/html/head")
@destination("/doc/header", order=1)
def ruleHead(head):
    return head

@source("/html/body")
@destination("/doc/article", order=2)
def ruleBody(text):
    return text


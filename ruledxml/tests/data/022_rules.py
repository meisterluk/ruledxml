from ruledxml import destination, source, foreach


@foreach("/xml/element", "/doc/message")
@source("/xml/element/child")
@destination("/doc/message/text")
def ruleMultipleBases(child_text):
    return child_text

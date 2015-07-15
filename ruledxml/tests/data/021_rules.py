from ruledxml import destination, source, foreach


@foreach("/xml/element", "/doc/message")
@source("/xml/element/child")
@destination("/doc/message/text")
def rule34(child_text):
    return child_text + "2"

from ruledxml import destination, source, foreach


@foreach("/xml/element")
@source("/xml/element/child")
@destination("/doc/text")
def ruleInvalidNumberOfForeachArguments(child_text):
    return child_text + "2"

from ruledxml import destination, source, foreach


@foreach("/xml/element", "/doc/number")
@source("/xml/element/child")
@destination("/doc/number")
def ruleMultipleBases(num):
    return num

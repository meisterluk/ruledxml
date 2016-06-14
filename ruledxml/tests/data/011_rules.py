from ruledxml import destination, source


@source("/xml/number")
@destination("/doc/preamble/meta/@num")
def ruleMetaNumber(num):
    return float(num) * 0.1

@source("/xml/type")
@destination("/doc/preamble/meta/@type")
def ruleMetaType(typed):
    return typed

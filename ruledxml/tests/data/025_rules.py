from ruledxml import destination, source, foreach


@foreach("/xml/base", "/doc/dst")
@source("/xml/base/a/very/nested/source/element@attr")
@destination("/doc/dst/that/yrev/detsen/ecruos/tnemele@rtta")
def ruleStronglyNestedBases(attr):
    return " " + attr + " "

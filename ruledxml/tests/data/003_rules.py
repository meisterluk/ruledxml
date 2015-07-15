from ruledxml import destination


@destination("/root/nested/child@attr")
def ruleNestedElement():
    return 3.5

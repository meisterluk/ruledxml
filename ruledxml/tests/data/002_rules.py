from ruledxml import destination


@destination("/root")
def ruleNewElement():
    return "test002"

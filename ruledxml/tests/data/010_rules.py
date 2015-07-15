# Expect: ValueError

# a rules file must not contain two rules with the same name.
# If so, python would overwrite those rules and only use the
# second rule.

from ruledxml import destination, source


@source("/from")
@destination("/to")
def ruleNestedElement(s):
    return s

@source("/from")
@destination("/to")
def ruleNestedElement(s):
    return s

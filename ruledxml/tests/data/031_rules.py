from ruledxml import destination, source, foreach

@source("/input/first")
@destination("/output/four", order=4)
def ruleFirst(head):
    return head

@source("/input/second")
@destination("/output/three", order=3)
def ruleSecond(text):
    return text

@source("/input/third")
@destination("/output/two", order=2)
def ruleThree(text):
    return text

@source("/input/fourth")
@destination("/output/one", order=1)
def ruleFour(text):
    return text

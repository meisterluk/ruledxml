from ruledxml import destination, source


@source("/xml/number")
@source("/xml/type")
@source("/xml/op")
@source("/xml/factor")
@destination("/doc/preamble/meta")
def ruleMeta(factor, op, typed, num):
    value1 = __builtins__[typed](num)
    value2 = __builtins__[typed](factor)
    return getattr(value1, op)(value2)

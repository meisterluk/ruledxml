from ruledxml import destination, source, foreach


@foreach("/xml/operation", "/doc/computed")
@source("/xml/operation/opcode")
@source("/xml/operation/param2")
@source("/xml/operation/param1")
@destination("/doc/computed")
def ruleMultipleSourceBases(param1, param2, opcode):
    if opcode == "ADD":
        return str(int(param1) + int(param2))
    elif opcode == "CONCAT":
        return param1 + param2
    else:
        return "ERROR"

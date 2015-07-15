#!/usr/bin/env python3

"""
    ruledxml.exceptions
    -------------------

    Custom exceptions occuring at ruledxml runtime.

    ┌ RuledXmlException
    ├─── InvalidPathException [ValueError]
    ├──┬ RuleSourceException [TypeError]
    │  ├─── MissingRuleSource
    │  └─── InvalidRuleSource
    ├──┬ RuleDestinationException [TypeError]
    │  ├─── MissingRuleDestination
    │  ├─── InvalidRuleDestination
    │  └─── TooManyRuleDestinations
    └──┬ RuleForeachException [TypeError]
       ├─── MissingRuleForeach
       └─── InvalidRuleForeach

    (C) 2015, meisterluk, BSD 3-clause license
"""


class RuledXmlException(Exception):
    """The common exception base class of all custom exceptions"""


class InvalidPathException(RuledXmlException, ValueError):
    """The specified path is invalid, ie. an element has an invalid name,
    an element reference instead of an attribute reference is excepted
    or an XML namespace is unknown.
    """


class RuleSourceException(RuledXmlException, TypeError):
    """The rule has an invalid @source, missing some @source
    or too many @source calls.
    """


class RuleDestinationException(RuledXmlException, TypeError):
    """The rule has an invalid @destination, missing some @destination
    or too many @destination calls.
    """


class RuleForeachException(RuledXmlException, TypeError):
    """The rule has an invalid @foreach, missing some @foreach
    or too many @foreach calls.
    """


class MissingRuleSource(RuleSourceException):
    """The rule is lacking a @source decorator"""


class MissingRuleDestination(RuleDestinationException):
    """The rule is lacking a @destination decorator"""


class MissingRuleForeach(RuleForeachException):
    """The rule is lacking a @foreach decorator"""


class InvalidRuleSource(RuleSourceException):
    """The rule's @source decorator has invalid arguments"""


class InvalidRuleDestination(RuleDestinationException):
    """The rule's @destination decorator has invalid arguments"""


class InvalidRuleForeach(RuleForeachException):
    """The rule's @foreach decorator has invalid arguments"""


class TooManyRuleDestinations(RuleDestinationException):
    """The rule has too many @destination decorators applied"""
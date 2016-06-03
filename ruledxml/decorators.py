#!/usr/bin/env python3

"""
    ruledxml.decorators
    -------------------

    Decorators implemented for ruledxml to be applied to rules.

    (C) 2015, meisterluk, BSD 3-clause license
"""


def annotate_function(key, init, clbk):
    """Magic function introducing a ``metadata`` dictionary attribute.
    If this attribute does not exist yet, index `key` will be set to `init`.
    Otherwise `clbk` will be executed with the old metadata attribute as argument.
    The attribute's new value is the return value of `clbk`.

    :param key:         metadata attribute name
    :type key:          str | int
    :param init:        initial value
    :param clbk:        A callback taking one argument and returning new value for key
    :rtype:             function
    """
    def outer(func):
        if hasattr(func, 'metadata'):
            if key in func.metadata:
                func.metadata[key] = clbk(func.metadata.get(key))
            else:
                func.metadata[key] = init
        else:
            setattr(func, 'metadata', { key : init })

        def inner(*args, **kwargs):
            return func(*args, **kwargs)

        inner.metadata = func.metadata
        return inner
    return outer


def source(*vals):
    """Decorator: Declare the source values that data will be taken from"""
    return annotate_function("src", list(vals), lambda v: v.extend(vals) or v)


def destination(*vals, order=None):
    """Decorator: Declare the destination values that data will be written to"""
    data = {'dests': vals, 'order': order}
    return annotate_function("dst", data, lambda v: v['dests'].extend(vals) or v)


def foreach(*vals):
    """Decorator: Define a 1:1 mapping between @source and @destination.
    Let e be an element with @foreach(V, X), @source(W) and @destination(Y).
    W must be a nested element of V or V=W unless W is an attribute.
    Y must be a nested element of X or X=Y.
    @foreach only changes the behavior of @source and @destination
    iff there are multiple elements at V.

    For every element V_i, a destination element Y_i is created.
    For every element V_i,
      * the corresponding source element W is looked up and
      * provided as argument to the rule function and
      * the return value of the rule function is taken and
      * written to the corresponding destination Y
    """
    return annotate_function("each", [tuple(vals)], lambda v: v.extend([vals]) or v)

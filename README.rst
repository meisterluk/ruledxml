ruledxml
========

Given an XML file. Transform it into another XML file using a rules file.
A rules file reads some element, process them and returns a new value
which is written to an XML path. Rules are inspired by Business Rule Engines
such as `Intellect <https://pypi.python.org/pypi/Intellect>`_.

Installation
------------

Installation with source package:

1. ``python3 setup.py install``
2. ``pip3 install -r requirements.txt``

Installation from PyPI:

1. ``pip3 install ruledxml``

Run the testsuite:

1. Start ``python3``
2. Run ``import ruledxml.tests``
3. Run ``ruledxml.tests.runall()``

Rules
-----

Rules are designed to be written with little technical knowledge.
However, not all transformations (comparable to XSLT) are possible.
If elements occur multiple times in the source XML,
the capabilities are limited.

Rules are written in the python programming language::

    @source("/root/body/header")
    @destination("/html/body/article/h1")
    def ruleFirstHeader(header):
        return header + "!"

The first element at XPath ``/root/body/header`` is read, its
text content is looked up and passed as argument ``header``
to the function ``ruleFirstHeader``.

If the source element does not exist, an empty string is supplied.
Be aware that source parameters are always strings.

The rule returns the original header appended with an exclamation mark.
The return value is written to the destination XPath
``/html/body/article/h1``. All non-existing elements will be created.
If an element already exists, the first match is taken.

Required elements
-----------------

A source of errors in that design is when elements do not exist
and an empty string is supplied as argument. This is a silent error.

You can specify required elements in a variable ``input_required`` which
is interpreted before the actual processing starts::

    input_required = [
        "/root/body/header"
    ]

If the element ``/root/body/header`` does not exist in the source XML file,
a ValueError is thrown.

Non-empty elements
------------------

Similarly to required elements, we have non-empty elements. Paths mentioned
in the ``input_nonempty`` variable are required to yield nonempty values.
Otherwise an error is thrown and processing aborted.

Implementation
--------------

A little bit of lxml and lots of decorator magic ;)

License
-------

3-claused BSD license. Hence you can use the software
for whatever you like, if you want to mention my name
in your software product, you need to ask me.

cheers,
meisterluk <admin@lukas-prokop.at>

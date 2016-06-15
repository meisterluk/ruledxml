#!/usr/bin/env python

"""
    ruledxml
    ~~~~~~~~~
    
    Rule-based XML transformations.
    Implementation module.

    **Remarks:**
    * Function documentation is rather verbose. Use help().
    * Tested with python 3.4
    * Rules are not as complete as XSLT transformations

    (C) 2015, meisterluk, BSD 3-clause license
"""

__author__ = 'Lukas Prokop <admin@lukas-prokop.at>'
__version__ = '1.6.0'
__license__ = '3-clause BSD license'
__docformat__ = 'reStructuredText en'


# shorter names
from .core import read_rulesfile
from .xml import read as read_source_xml
from .xml import write as write_target_xml

# names with modified module ref
from .decorators import source, destination, foreach

# generic names
from .core import unique_function, required_exists
from .core import apply_rules, batch_run, run
from . import xml
from . import exceptions
from . import fs


__all__ = [
    'read_source_xml', 'read_rulesfile', 'write_target_xml',
    'source', 'destination', 'foreach',
    'unique_function', 'required_exists', 'batch_run', 'run'
    'xml', 'exceptions', 'fs'
]

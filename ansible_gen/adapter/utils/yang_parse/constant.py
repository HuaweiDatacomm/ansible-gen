#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""constant.py docstrings.
This module save the constant that project needs.
"""


BASE_INTEGER_TYPES = {"int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"}
MIN_MAX_MAP = {'int8': ['-128', '127'],
               'int16': ['-32768', '32767'],
               'int32': ['-2147483648', '2147483647'],
               'int64': ['-9223372036854775808', '9223372036854775807'],
               'uint8': ['0', '255'],
               'uint16': ['0', '65535'],
               'uint32': ['0', '4294967295'],
               'uint64': ['0', '18446744073709551615'],
               'string': ['0', '18446744073709551615']
               }

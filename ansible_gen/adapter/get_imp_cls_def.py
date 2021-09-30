#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import re


USER_CHECK_STMT = """class UserCheck(object):
    def __init__(self, params, infos):
        #  user configuration get from AnsibleModule().params
        self.params = params
        # leaf infos from yang files
        self.infos = infos

    # user defined check method need startswith "check_"
    # return 0 if not pass check logic, else 1
    def check_leaf_restrict(self):
        \"\"\"
            if leaf_1 configured, leaf2 shouble be configured
            and range shouble be in [10, 20]
        \"\"\"
        return 1   
"""


def get_imp_stmts(user_def_file):
    """Get 'import xxx' statement and 'from xxx import xxx' statement from userCheck.py.
    Args:
        user_def_file: The path of userCheck.py.
    Returns:
        xml_head_str: The import string of userCheck.py.
    """
    if not os.path.isfile(user_def_file):
        logging.error("%s is not exist or is not file", user_def_file)
        return

    logging.info("merge user check definitions from script %s", user_def_file)
    imp_decs = []
    idx = 0

    try:
        with open(user_def_file, encoding="utf-8") as file:
            lines = file.readlines()
            while idx < len(lines):
                line = lines[idx]
                # get 'import xxx' statement and 'from xxx import xxx' statement.
                if line.startswith("import ") or line.startswith("from "):
                    imp_dec = line
                    # The import have too many fun which need to change line.
                    while re.match(r".*\\\s+", line):
                        idx += 1
                        line = lines[idx]
                        imp_dec += line
                    imp_decs.append(imp_dec.rstrip())

                idx += 1
    except IOError as error:
        logging.error("can't process user define file %s, because %s", user_def_file, error)

    return "\n".join(imp_decs)


def get_user_check_cls_def(user_def_file):
    """Get 'class UserCheck(object):' statement from userCheck.py.
    Args:
        user_def_file: The path of userCheck.py.
    Returns:
        xml_head_str: The 'class UserCheck' statement of userCheck.py.
    """
    if not os.path.isfile(user_def_file):
        logging.error("%s is not exist or is not file", user_def_file)
        return

    logging.info("merge user check definitions from script %s", user_def_file)
    cls_str = "\n"
    is_cls_code = False
    idx = 0

    try:
        with open(user_def_file, encoding="utf-8") as file:
            lines = file.readlines()
            while idx < len(lines):
                line = lines[idx]
                # get code for class UserCheck
                if re.match(r"^class UserCheck\(object\):\s+$", line):
                    is_cls_code = True
                    cls_str += line
                    idx += 1
                    continue
                if is_cls_code:
                    if not re.match(r"\s+", line):
                        break
                    cls_str += line

                idx += 1
    except IOError as error:
        logging.error("can't process user define file %s, because %s", user_def_file, error)

    return cls_str

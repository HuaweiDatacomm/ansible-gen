#!/usr/bin/env python
# -*- coding: utf-8

import os
import logging
from collections import OrderedDict

def get_xml_feature_name(file):

    return os.path.basename(file).split('_')[0]

def get_config_xml_head(head_xpath):
    """Get xml head string when config.
    Args:
        head_xpath: The string of xpath_key.
    Returns:
        xml_head_str: The xml head str.
    """
    xml_head_str = "<config>"
    for item in head_xpath.split("/")[1:]:
        xml_head_str = xml_head_str + "<" + item + ">"
    return xml_head_str


def get_rpc_head(xml_dict):
    """Get the rpc head.
    Args:
        xml_dict: An OrderedDict. Recording the xml's structure.
    Returns:
        xml_head: The xml head str.
        feature_name: The child node name of config|filter.
        xml_type: The type of xml.
        if xml_type is config,generate the xml_head with xpath_key.
        if xml_type is filter,the xml_head is '<filter type="subtree">'.
    """
    xml_head = ""
    feature_name_list = []
    xml_type = ""
    try:
        for key, value in xml_dict.items():
            xml_type = key
            if (value is None):
                continue
            for feature_key in value.keys():
                feature_name_list.append(feature_key)
        if xml_type == "config":
            xml_head = '<config>'
        elif xml_type == "rpc":
            xml_head = ""
        else:
            xml_head = '<filter type="subtree">'
    except Exception:
        logging.error("fun get_rpc_head() run error.")

    return [xml_head, feature_name_list, xml_type]

def get_config_xml_tail(tail_xpath):
    """Get xml tail string when config.
    Args:
        tail_xpath: The string of xpath_key.
    Returns:
        xml_tail_str: The xml tail str.
    """
    xml_tail_str = ""
    tail_xpath_list = tail_xpath.split("/")[1:]
    for item in reversed(tail_xpath_list):
        xml_tail_str = xml_tail_str + "</" + item + ">"
    xml_tail_str += "</config>"
    return xml_tail_str


def get_rpc_tail(xml_dict):
    """Get the rpc tail.
    Args:
        xml_dict: An OrderedDict. Recording the xml's structure.
    Returns:
        xml_tail: The xml tail str.
        if xml_type is config,generate the xml_tail with xpath_key.
        if xml_type is filter,the xml_tail is '</filter>'.
    """
    xml_tail = ""
    try:
        for key, value in xml_dict.items():
            xml_type = key
        if xml_type == "config":
            xml_tail = '</config>'
        elif xml_type == "rpc":
            xml_tail = ""
        else:
            xml_tail = '</filter>'
    except Exception:
        logging.error("fun get_rpc_tail() run error.")
    return xml_tail

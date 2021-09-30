#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import logging
from collections import OrderedDict
from ansible_gen.adapter.utils.base_util import operation_warning_write
from ansible_gen.adapter.utils.xml_parse.xml_parser import is_sub_xml, xml_to_ordered_dict
from ansible_gen.adapter.utils.xml_parse.xml_parser import get_operations_attr

if sys.version < '3':
    str = unicode

EXAMPLE_STR = ''
LEVEL = 0
module_files = []

def get_module_file(xml_dir, mod_files):
    """Get instance-xml's path.
    Args:
        xml_dir: The path of full-xml.
    Returns:
        A list. Saving paths of instance-xml.
    """
    xml_files = os.listdir(xml_dir)
    for xml_file in xml_files:
        path = os.path.join(xml_dir, xml_file)
        if os.path.isdir(path):
            get_module_file(path, mod_files)
        else:
            if os.path.isfile(path):
                if xml_file.endswith("_example.xml"):
                    mod_files.append(path)
                elif len(xml_files) == 1:
                    mod_files.append(path)
    return mod_files


def gen_dict(xml_file, full_xml_file):
    """
    Get xml_structure info and operation info.
    """
    xml_filename = xml_file.split('.')[0].split('/')[-1]
    if is_sub_xml(xml_file, full_xml_file):
        xml_dict = xml_to_ordered_dict(xml_file)
        operation_dict = get_operations_attr(xml_file)
        return [{xml_filename: xml_dict}, {xml_filename: operation_dict}]
    else:
        operation_error_str = "EXAMPLE of instance-xml can not be generated," \
                    "because the instance-xml is not a substructure of full-xml,please check:" \
                    "\nthe path of instance-xml: %s." \
                    "\nthe path of full-xml: %s." % (xml_file, full_xml_file)
        operation_warning_write(operation_error_str)
        return [{}, {}]


def gen_examples(module_files_dict, script_name, pkg_type, operation_dict_result, argument_spec):
    """
    Generate example string.
    """
    global EXAMPLE_STR
    global LEVEL
    if pkg_type == "config":
        process = get_cfg_str
    elif pkg_type == "rpc":
        process = get_cfg_str
    else:
        process = get_filter_str
    examples_str = '---' + "\n"
    examples_str += '- name: %s' % script_name + '\n'
    examples_str += '  hosts: ne_test' + '\n'
    examples_str += '  connection: netconf' + '\n'
    examples_str += '  gather_facts: no' + '\n'
    examples_str += '  vars:' + '\n'
    examples_str += '    netconf:' + '\n'
    examples_str += '      host: "{{ inventory_hostname }}"' + '\n'
    examples_str += '      port: "{{ ansible_ssh_port }}"' + '\n'
    examples_str += '      username: "{{ ansible_user }}"' + '\n'
    examples_str += '      password: "{{ ansible_ssh_pass }}"' + '\n'
    examples_str += '      transport: netconf' + '\n'
    examples_str += '\n'
    examples_str += '  tasks:\n'
    examples_str += '\n'
    for file_dict in module_files_dict:
        for key, v in file_dict.items():
            examples_str += '  - name: ' + os.path.basename(key) + '\n'
            examples_str += '    %s:' % script_name + '\n'
            for xml_type, xml_dict in v.items():
                examples_str += '      operation_type: ' + xml_type + '\n'
                if xml_type == 'config':
                    # generate operation_specs
                    if operation_dict_result:
                        for operation_dict in operation_dict_result:
                            for operation_key, operation_value in operation_dict.items():
                                if operation_value:
                                    if operation_key == key:
                                        examples_str += '      operation_specs: ' + '\n'
                                        for xpath, value in operation_value.items():
                                            examples_str += '        - path: ' + xpath + '\n'
                                            examples_str += '          operation: ' + value + '\n'
                                        break

                if pkg_type == "config":
                    examples_str += process(xml_dict, argument_spec)
                else:
                    examples_str += process(xml_dict, argument_spec)
            EXAMPLE_STR = ''
            LEVEL = 0

        examples_str += '      provider: "{{ netconf }}"' + '\n'
        examples_str += '\n'
    return examples_str

def get_filter_str(data, argument_spec):
    """
    Generate the example of filter.
    """
    def get_leaf_str(data, indent, argument_spec, parent_node_type=None):
        leaf_str = ''
        list_flag = ""
        indent_str = "  "
        if parent_node_type and parent_node_type == "list":
            list_flag = "- "
            indent_str = "    "
        for k, v in data.items():
            if 'options' not in argument_spec[k]:
                print(argument_spec[k])
            current_argument_spec = argument_spec[k].get("options")
            parent_node_type = argument_spec[k].get("type")
            if v is None and argument_spec[k].get("type") == "list":
                container_end_flag = "- "
            else:
                container_end_flag = ""
            if not isinstance(v, list):
                v = [v]
            for node in v:
                if not isinstance(node, OrderedDict):
                    leaf_str += "".join(indent) + list_flag + k + ': \n'
                    indent.append(indent_str)
                    node_str = container_end_flag + 'get_all: True'
                    if node:
                        node_str = 'get_value: ' + node
                        if current_argument_spec.get("get_value") and current_argument_spec["get_value"].get("type") == "str":
                            node_str = 'get_value: \"' + node + '\"'
                    leaf_str += "".join(indent) + node_str + '\n'
                    indent.pop()
                else:
                    leaf_str += "".join(indent) + list_flag + k + ': ' + '\n'
                    indent.append(indent_str)
                    leaf_str += get_leaf_str(node, indent, current_argument_spec, parent_node_type)
                    indent.pop()
        return leaf_str

    indent = ["  ", "  ", "  "]
    task_str = ""
    if data:
        task_str += get_leaf_str(data, indent, argument_spec)
    else:
        task_str += '    ' + '  ' * LEVEL + 'get_all: True' + '\n'
    return task_str


def get_cfg_str(data, argument_spec, parent_node_type=None):
    """
    Generate the example of config.
    """
    if isinstance(data, OrderedDict):
        global LEVEL
        LEVEL += 1
        for k, v in data.items():
            global EXAMPLE_STR
            if not argument_spec.get(k):
                continue
            if argument_spec[k].get("options"):
                argument_spec_options = argument_spec[k]["options"]
            else:
                argument_spec_options = argument_spec
            if argument_spec[k].get("type"):
                parent_node_type_temp = argument_spec[k]["type"]
            else:
                parent_node_type_temp = None

            if isinstance(v, OrderedDict):
                if parent_node_type and parent_node_type == "list":
                    EXAMPLE_STR += '    ' + '  ' * LEVEL + '- ' + k + ': ' + '\n'
                    LEVEL += 1
                    get_cfg_str(v, argument_spec_options, parent_node_type_temp)
                    LEVEL -= 1
                else:
                    EXAMPLE_STR += '    ' + '  ' * LEVEL + k + ': ' + '\n'
                    get_cfg_str(v, argument_spec_options, parent_node_type_temp)
            elif isinstance(v, list):
                for item in v:
                    if parent_node_type and parent_node_type == "list":
                        EXAMPLE_STR += '    ' + '  ' * LEVEL + '- ' + k + ': ' + '\n'
                        LEVEL += 1
                        get_cfg_str(item, argument_spec_options, parent_node_type_temp)
                        LEVEL -= 1
                    else:
                        EXAMPLE_STR += '    ' + '  ' * LEVEL + k + ': ' + '\n'
                        get_cfg_str(item, argument_spec_options, parent_node_type_temp)
            else:
                if v:
                    if argument_spec[k].get("type") and argument_spec[k]["type"] == "str":
                        v = '\"' + v + '\"'
                    EXAMPLE_STR += '    ' + '  ' * LEVEL + k + ': ' + v + '\n'
                else:
                    if argument_spec[k].get("type") and argument_spec[k]["type"] == "dict":
                        value_empty = '{}'
                    elif argument_spec[k].get("type") and argument_spec[k]["type"] == "list":
                        value_empty = '[]'
                    else:
                        value_empty = '\"\"'
                    EXAMPLE_STR += '    ' + '  ' * LEVEL + k + ': ' + value_empty + '\n'

    LEVEL -= 1
    return EXAMPLE_STR


def create_example(full_xml_file_path, script_name, pkg_type, argument_spec):
    """Generate example.
    Args:
        full_xml_file_path: The path of full-xml.
        script_name: The file name of full-xml.
        pkg_type: Type of xml. The value is "config" or "filter".
    Returns:
        example_str: The example string.
        Compare the instance-xml's structure with full-xml,to make sure instance-xml is a subset of full-xml.
    """
    # Get all instance-xml.
    module_files = get_module_file(os.path.dirname(full_xml_file_path), [])
    module_files.sort()
    module_files_dict = []
    operation_dict_result = []
    for file in module_files:
        xml_res = gen_dict(file, full_xml_file_path)
        module_files_dict.append(xml_res[0])
        operation_dict_result.append(xml_res[1])
    example_str = gen_examples(module_files_dict, script_name, pkg_type, operation_dict_result, argument_spec)

    return example_str

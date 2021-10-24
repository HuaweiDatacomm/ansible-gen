#!/usr/bin/env python
# -*- coding: utf-8


import logging
import os
from ..adapter import gen_examples as gen_example
from ..adapter import get_imp_cls_def as get_imp_cls
from ..adapter.utils.xml_parse.xml_parser_get_xmlns import get_xmlns_info, xmlns_info_without_prefix, \
    get_xml_namespace
from ..adapter.get_argument_spec_documentation import get_xml_options, get_xml_dict, get_xml_descption, \
    gen_documentation, check_xpaths_exists, get_xml_key_leafs, get_xml_list_leafs, get_xml_leafinfos, gen_argument_spec
from ..adapter.get_rpc_head_tail import get_rpc_head, get_rpc_tail

yang_handler = None

head = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

"""


def gen_documentation_params(full_xml_file_path, full_xml_ordered_dict, script_name, xml_namespace, xmlns_info):
    """
     get params of the xml_file
    :param full_xml_file_path:
    :param full_xml_ordered_dict:
    :param script_name:
    :return:
    """
    xml_options = get_xml_options(full_xml_file_path, full_xml_ordered_dict, xmlns_info)
    if len(full_xml_ordered_dict) == 0:
        logging.error("xml file %s can't be tranport to OrderedDict", full_xml_file_path)
        return

    if not check_xpaths_exists(full_xml_ordered_dict, xmlns_info):
        logging.error("not all node defined in xml %s occured in yang files", os.path.basename(full_xml_file_path))
        return
    module_desc = get_xml_descption(xml_namespace)  # Get the overall description of the message
    xml_type = get_head_content(full_xml_ordered_dict)[2]
    documentation = gen_documentation(module_desc, xml_options, script_name, xml_type)
    return documentation


def get_head_content(full_xml_ordered_dict):
    """Get xml head"""
    head_content = get_rpc_head(full_xml_ordered_dict)
    return head_content


def get_xml_tail(full_xml_ordered_dict):
    """Get xml tail"""
    xml_tail = get_rpc_tail(full_xml_ordered_dict)
    return xml_tail


def get_user_check_stmts_module(user_def_dir, filename):
    """Get user-check script's content."""
    if user_def_dir:
        user_def_file = os.path.join(os.path.join(user_def_dir, filename + ".py"))
    else:
        user_def_file = ''
    if os.path.isfile(user_def_file):
        logging.info("%s exist, get UserCheck definaiton and import statements from it", user_def_file)
        module = get_imp_cls.get_imp_stmts(user_def_file)
        user_check_stmts = get_imp_cls.get_user_check_cls_def(user_def_file)
    else:
        module = ''
        user_check_stmts = get_imp_cls.USER_CHECK_STMT
    return [module, user_check_stmts]


def get_params(full_xml_file_path, script_name, output_file_path, user_def_dir=None):
    """Get params"""
    full_xml_ordered_dict = get_xml_dict(full_xml_file_path)
    if full_xml_ordered_dict is None:
        return {}
    if len(full_xml_ordered_dict) == 0:
        return {}
    # Get type of xml.
    pkg_type = list(full_xml_ordered_dict.keys())[0]
    if full_xml_ordered_dict[pkg_type] is None:
        return {}
    # Get xml namesapce.
    xml_namespace = get_xml_namespace(full_xml_file_path,pkg_type)
    # Get xmlns_info.
    namespace = get_xmlns_info(full_xml_file_path,pkg_type)
    xmlns_info = xmlns_info_without_prefix(namespace)

    # Get documentation
    documentation = gen_documentation_params(full_xml_file_path, full_xml_ordered_dict, script_name, xml_namespace, xmlns_info)
    # Get key_list
    key_list = get_xml_key_leafs(full_xml_ordered_dict, xmlns_info)
    # Get list_list
    list_list = get_xml_list_leafs(full_xml_ordered_dict, xmlns_info)
    # Get leaf_info
    leaf_info = get_xml_leafinfos(full_xml_ordered_dict, xmlns_info)
    # Get argument_spec
    argument_spec = gen_argument_spec(full_xml_ordered_dict, xmlns_info, key_list, list_list)
    # Get example
    example = gen_example.create_example(full_xml_file_path, script_name, pkg_type, argument_spec)
    # Get head_content
    head_content = get_head_content(full_xml_ordered_dict)
    # Get xml_tail
    xml_tail = get_xml_tail(full_xml_ordered_dict)
    # Get module
    module = get_user_check_stmts_module(user_def_dir, script_name)[0]
    # Get user_check_stmts
    user_check_stmts = get_user_check_stmts_module(user_def_dir, script_name)[1]
    return {"head": head,
            "leaf_info": leaf_info,
            "argument_spec": argument_spec,
            "documentation": documentation,
            "example": example,
            "namespace": namespace,
            "head_content": head_content,
            "xml_tail": xml_tail,
            "output_file_path": output_file_path,
            "filename": script_name,
            "module": module,
            "user_check_stmts": user_check_stmts,
            "key_list": key_list}

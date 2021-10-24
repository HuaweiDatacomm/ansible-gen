#!/usr/bin/env python
# -*- coding: utf-8


import re
import os
import logging
from lxml import etree
from collections import OrderedDict
from xml.parsers.expat import ExpatError
import xmltodict
from ..base_util import error_write, xml_structure_except

COMMON_XMLNS_MAP = {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}


def remove_namespace(file_name):
    """Get xml string without xmlns and prefix.
    Args:
        file_name: The path of xml file.
    Returns:
        remove_xmlns_str: The xml string without xmlns and prefix.
    Raises:
        Exception: Capture IO exception.
    """
    remove_xmlns_str = ''
    try:
        with open(file_name, 'r') as xml_file:
            xml_str = xml_file.read()
        if xml_str:
            attr_names = list()
            for item in re.findall(r'xmlns:(.*?)=".*?"', xml_str):
                attr_names.append(item)
            for item in re.findall(r"xmlns:(.*?)='.*?'", xml_str):
                attr_names.append(item)
            remove_xmlns_str = xml_str
            # if attr_name is not None:
            if attr_names:
                for attr_name in attr_names:
                    # remove: [xmlns:nc="xxx"] or [xmlns="xxx"]
                    remove_xmlns_str = re.sub(r'.xmlns(:' + attr_name + ')?=".*?"', '', remove_xmlns_str)
                    remove_xmlns_str = re.sub(r".xmlns(:" + attr_name + ")?='.*?'", "", remove_xmlns_str)
                for attr_name in attr_names:
                    # remove: [ nc: ] from <xxx nc:operation="merge">
                    remove_xmlns_str = re.sub(r'\s' + attr_name + ':', " ", remove_xmlns_str)
                    # remove: [ prefix: ] from <prefix:xxx>
                    remove_xmlns_str = re.sub(r'<' + attr_name + ':', "<", remove_xmlns_str)
                    # remove: [ prefix: ] from </prefix:xxx>
                    remove_xmlns_str = re.sub(r'</' + attr_name + ':', "</", remove_xmlns_str)
            else:
                # remove: [xmlns="xxx"]
                remove_xmlns_str = re.sub(r'.xmlns=".*?"', "", remove_xmlns_str)
                remove_xmlns_str = re.sub(r".xmlns='.*?'", "", remove_xmlns_str)
    except Exception as error_msg:
        error_write(str(error_msg))
    finally:
        return remove_xmlns_str

def xml_to_ordered_dict(file_name):
    """Parse the xml file to ordered dict.
    Args:
        file_name: The path of xml file.
    Returns:
        xml_structure_dict: An OrderedDict. Mapping the xml's structure.
        for example:
            xml_structure_dict:
                OrderedDict([('config',
                    OrderedDict([('interfaces',
                        OrderedDict([('interface',
                            OrderedDict([('name', None), ('ipv4',
                                OrderedDict([('address',
                                    OrderedDict([('prefix-length', None), ('ip', None)]))]))]))]))]))])
    Raises:
        Exception: Capture execution exception.
    """
    xml_structure_dict = OrderedDict()
    operation_name = os.path.abspath(os.path.join(file_name, os.pardir, os.pardir))
    input_action_match = operation_name.split(os.sep)[-1]
    xml_filtered_str = remove_namespace(file_name)
    if input_action_match == "rpcs":
        rpc_root = etree.fromstring(xml_filtered_str.encode('utf-8')).getroottree()
        root = rpc_root.xpath('//rpc')
        xml_type = root[0].tag
        root_string = etree.tostring(root[0])
        xml_dic = xmltodict.parse(root_string, xml_attribs=False)
        # xml_dic = xmltodict.parse(root_string)
        for value in xml_dic.values():
            temp_ordered_dict = value
        xml_structure_dict[xml_type] = temp_ordered_dict
        return xml_structure_dict
    if xml_filtered_str:
        # remove: [ type="subtree"  ] from <filter type="subtree">
        xml_filtered_str = re.sub(r'.type="(.*?)"', "", xml_filtered_str)
        xml_filtered_str = re.sub(r".type='(.*?)'", "", xml_filtered_str)
        # remove operation attribute.
        operations = list()
        for item in re.findall(r'.operation="(.*?)"', xml_filtered_str):
            operations.append(item)
        for item in re.findall(r".operation='(.*?)'", xml_filtered_str):
            operations.append(item)
        if operations:
            for operation in operations:
                xml_filtered_str = re.sub(r'.operation="(' + operation + ')"', "", xml_filtered_str)
                xml_filtered_str = re.sub(r".operation='(" + operation + ")'", "", xml_filtered_str)
        try:
            rpc_root = etree.fromstring(xml_filtered_str.encode('utf-8')).getroottree()
            root = rpc_root.xpath('//*/config|//*/get|//*/get-config')
            if root is None or len(root) == 0:
                return
            xml_type = root[0].tag
            if xml_type != "config":
                root = rpc_root.xpath('//*/filter')
            if root is None or len(root) == 0:
                return
            root_string = etree.tostring(root[0])
            xml_dic = xmltodict.parse(root_string)
            for value in xml_dic.values():
                temp_ordered_dict = value
            xml_structure_dict[xml_type] = temp_ordered_dict
        except etree.XMLSyntaxError as syntax_exception:
            xml_structure_except(syntax_exception, file_name)
        except Exception as exception_str:
            error_write(str(exception_str))
    return xml_structure_dict


def get_operations_attr(file_name):
    """Query all nodes which have operation attribute.
    Args:
        file_name: The path of xml file.
    Returns:
        operation_dict: A dict,keys record the node's xpath,
                        value record operation attribute's value.
        for example:
            operation_dict: {'/config/interfaces/interface/ipv4/address': 'create',
                             '/config/interfaces/interface': 'merge'}
    """
    operation_dict = OrderedDict()
    xml_str_without_xmlns = remove_namespace(file_name)
    if xml_str_without_xmlns != '':
        try:
            rpc_root = etree.fromstring(xml_str_without_xmlns.encode('utf-8')).getroottree()
            operation_elements = rpc_root.xpath('//*[@operation]')
            if operation_elements:
                for operation_element in operation_elements:
                    operation_xpath = rpc_root.getelementpath(operation_element)
                    operation_xpath = operation_xpath[len("edit-config"):]
                    operation_dict[operation_xpath] = operation_element.get('operation')
        except Exception as error_str:
            error_write(str(error_str))

    return operation_dict


def get_business_ordered_dict(file_path):
    result = OrderedDict()
    try:
        with open(file_path, 'r') as file_read:
            xml_ordered_dict = xmltodict.parse(file_read.read(), process_namespaces=True, xml_attribs=False)
        rpc_node = "{0}:{1}".format(COMMON_XMLNS_MAP["nc"], "rpc")
        edit_config_node = "{0}:{1}".format(COMMON_XMLNS_MAP["nc"], "edit-config")
        get_node = "{0}:{1}".format(COMMON_XMLNS_MAP["nc"], "get")
        get_config_node = "{0}:{1}".format(COMMON_XMLNS_MAP["nc"], "get-config")
        config_node = "{0}:{1}".format(COMMON_XMLNS_MAP["nc"], "config")
        filter_node = "{0}:{1}".format(COMMON_XMLNS_MAP["nc"], "filter")
        if xml_ordered_dict.get(rpc_node):
            if xml_ordered_dict[rpc_node].get(edit_config_node) and \
                    xml_ordered_dict[rpc_node][edit_config_node].get(config_node):
                result = OrderedDict([(config_node, xml_ordered_dict[rpc_node][edit_config_node][config_node])])
            elif xml_ordered_dict[rpc_node].get(get_node) and \
                    xml_ordered_dict[rpc_node][get_node].get(filter_node):
                result = OrderedDict([(filter_node, xml_ordered_dict[rpc_node][get_node][filter_node])])
            elif xml_ordered_dict[rpc_node].get(get_config_node) and \
                    xml_ordered_dict[rpc_node][get_config_node].get(filter_node):
                result = OrderedDict([(filter_node, xml_ordered_dict[rpc_node][get_config_node][filter_node])])
    except ExpatError as except_obj:
        xml_structure_except(except_obj, file_path)
    except Exception as error_mes:
        error_write(error_mes)
    finally:
        return result

def is_sub_xml(instance_xml_file, full_xml_file):
    """Determines whether instance_xml_file is a subElement of full_xml_file.
    Args:
        instance_xml_file: The path of instance-xml file.
        full_xml_file: The path of full-xml file.
    Returns:
        Bool.The result of comparison.
    """
    def _compare_ordered_dict(xml_ordered_dict, full_xml_ordered_dict):
        """In-depth traversal first principle, traversing instance_xml.(recursive function).
        Args:
            xml_ordered_dict: The OrderedDict of instance_xml.
            full_xml_ordered_dict: The OrderedDict of full_xml.
        Returns:
            result: Bool.The result of comparison.
        """
        result = True
        if result and isinstance(xml_ordered_dict, OrderedDict):
            for key, value in xml_ordered_dict.items():
                if "@" in key or "#" in key:
                    continue
                elif key in full_xml_ordered_dict.keys():
                    result = _compare_ordered_dict(xml_ordered_dict[key], full_xml_ordered_dict[key])
                else:
                    result = False
                    break
        return result

    compare_result = False
    try:
        instance_xml_order_dict = get_business_ordered_dict(instance_xml_file)
        full_xml_order_dict = get_business_ordered_dict(full_xml_file)
        compare_result = _compare_ordered_dict(instance_xml_order_dict, full_xml_order_dict)
    except Exception as except_str:
        error_write(str(except_str))

    return compare_result

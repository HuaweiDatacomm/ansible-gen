#!/usr/bin/env python
# -*- coding: utf-8


import re
import logging
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError
from collections import OrderedDict
import xmltodict
from ansible_gen.adapter.utils.base_util import error_write, xml_structure_except

CONFIG_OR_FILTER_CONTENT = OrderedDict()
XMLNS_INFO_LIST = []

def process_xml_dict(xml_dict,pkg_type):
    rpc_xml_dict = xml_dict['rpc']
    if pkg_type == 'config':
        edit_config_xml_dict = rpc_xml_dict['edit-config']
        return edit_config_xml_dict['config']
    elif pkg_type in ['get','get-config']:
        get_xml_dict = rpc_xml_dict[pkg_type]
        return  get_xml_dict['filter']
    else:
        return rpc_xml_dict

def get_config_or_filter(xml_dic):
    """Get filter/config's descendant node.(recursive function).
    Args:
        xml_dic: An OrderedDict. Mapping xml's structure.
    Returns:
        CONFIG_OR_FILTER_CONTENT: global var.Used to save [config] or [filter] content.
        for example:
            OrderedDict([('if:interfaces',
                OrderedDict([('@xmlns:if', 'urn:ietf:params:xml:ns:yang:ietf-interfaces'),
                             ('@xmlns:ni', 'urn:ietf:params:xml:ns:yang:ietf-network-instance'), ('if:interface',
                    OrderedDict([('if:name', None), ('ip:ipv4',
                        OrderedDict([('@xmlns:ip', 'urn:ietf:params:xml:ns:yang:ietf-ip'), ('ip:address',
                            OrderedDict([('ip:prefix-length', '24'), ('ip:ip', '10.1.1.2')]))]))]))]))])
    """
    for item in xml_dic:
        if item == 'config' or item == 'filter':
            global CONFIG_OR_FILTER_CONTENT
            CONFIG_OR_FILTER_CONTENT = xml_dic[item]
        else:
            if item.find("@") < 0 and item.find("#") < 0:
                # recursive when the value is instance of OrderedDict.
                if isinstance(xml_dic[item], OrderedDict):
                    get_config_or_filter(xml_dic[item])

def get_rpc_input(xml_dic):
    for item in xml_dic["rpc"]:
        if item.find("@") < 0 and item.find("#") < 0:
            global CONFIG_OR_FILTER_CONTENT
            if(xml_dic["rpc"] is None):
                print(xml_dic["rpc"])
            if CONFIG_OR_FILTER_CONTENT is None:
                print(CONFIG_OR_FILTER_CONTENT)
            CONFIG_OR_FILTER_CONTENT[item] = xml_dic["rpc"][item]
# def generate_xmlns_info(parent_xpath,parent_xmlns,xmlns_list,current_node_content):
#     if current_node_content is None or len(current_node_content) == 0:
#         return
#     for current_node_name in current_node_content:
#         # Whether is element node
#         if current_node_name.find("@") >= 0 or current_node_name.find("#") >= 0:
#             continue
#         xpath = parent_xpath + '/' + current_node_name

def generate_xmlns_info_with_recursive(current_node_content, xpath):
    """Generate xmlns_info with recursive.(recursive function).
    Args:
        current_node_content: An OrderedDict. Used to record current node's content.
        xpath: Used to record the node's xpath.
    Returns:
        XMLNS_INFO_LIST: global list.Recording all nodes's xmlns information.
        structure like:
            [
             { '/node1/prefix2:node2':['node2-value','xmlns2'] },
             { '/node1':['node1-value','xmlns1'] },
             { '/node1/prefix2:node2/prefix3:node3':['node3-value','xmlns3'] },
             ...
            ]
    """
    for current_node_name in current_node_content:
        # Whether is element node
        if current_node_name.find("@") < 0 and current_node_name.find("#") < 0:
            xpath = xpath + '/' + current_node_name
            xmlns_str = ''
            text_str = ''
            global XMLNS_INFO_LIST
            # case: ( 'currentElementNodeName',OrderedDict([(...)]) ):
            if isinstance(current_node_content[current_node_name], OrderedDict):
                for child_node_name in current_node_content[current_node_name]:
                    if child_node_name.find("@xmlns") >= 0:
                        xmlns_str = xmlns_str + child_node_name + '="' + \
                                    current_node_content[current_node_name][child_node_name] + '"'
                        continue
                    if child_node_name.find("#text") >= 0:
                        text_str = current_node_content[current_node_name][child_node_name]
                        continue
                    if child_node_name.find("@") < 0 and child_node_name.find("#") < 0:
                        child_xpath = xpath + '/' + child_node_name
                        # case: ( 'childElementNodeName',OrderedDict([(...)]) ):
                        if isinstance(current_node_content[current_node_name][child_node_name], OrderedDict):
                            # save child_xpath info before recursive.
                            child_xmlns_str = ''
                            child_text_str = ''
                            child_xpath_dict = dict()
                            # case: OrderedDict([('@xmlns:prefix1','http:xxxx'),('@xmlns:prefix2','urn:xxxx'),(...)])
                            for grandson_node_name in current_node_content[current_node_name][child_node_name]:
                                if grandson_node_name.find("@xmlns") >= 0:
                                    child_xmlns_str = child_xmlns_str + grandson_node_name + '="' + \
                                                      current_node_content[current_node_name][child_node_name][grandson_node_name] + '"'
                                    continue
                            # case: OrderedDict([(...),('#text','childTextContent')])
                            for grandson_node_name in current_node_content[current_node_name][child_node_name]:
                                if grandson_node_name.find("#text") >= 0:
                                    child_text_str = current_node_content[current_node_name][child_node_name][grandson_node_name]
                                    continue
                            child_xpath_dict[child_xpath] = [child_text_str, child_xmlns_str]
                            XMLNS_INFO_LIST.append(child_xpath_dict)
                            # recursive
                            generate_xmlns_info_with_recursive(current_node_content[current_node_name][child_node_name], child_xpath)
                        # case: ( 'childElementNodeName','childTextContent' )
                        elif isinstance(current_node_content[current_node_name][child_node_name], str):
                            child_text_str = current_node_content[current_node_name][child_node_name]
                            child_xpath_dict = dict()
                            if child_text_str:
                                child_xpath_dict[child_xpath] = [child_text_str, '']
                            else:
                                child_xpath_dict[child_xpath] = ['', '']
                            XMLNS_INFO_LIST.append(child_xpath_dict)
                        # case: ( 'childElementNodeName',None )
                        # current_node_content[current_node_name][child_node_name] is None:
                        else:
                            child_xpath_dict = dict()
                            child_xpath_dict[child_xpath] = ['', '']
                            XMLNS_INFO_LIST.append(child_xpath_dict)
            # case: ( 'currentElementNodeName','currentTextContent' ):
            else:
                text_str = current_node_content[current_node_name]
            if text_str is None:
                text_str = ''
            xpath_dict = dict()
            xpath_dict[xpath] = [text_str, xmlns_str]
            XMLNS_INFO_LIST.append(xpath_dict)
            xpath = xpath[:-(len(current_node_name)+1)]

def generate_xmlns_info(file,pkg_type):
    global XMLNS_INFO_LIST
    XMLNS_INFO_LIST = []
    try:
        with open(file, 'r') as read:
            xml_str = read.read()
            xml_dic = xmltodict.parse(xml_str)
            xml_dic = process_xml_dict(xml_dic,pkg_type)
            if xml_dic is None:
                return None
            xpath = ''
            generate_xmlns_info_with_recursive(xml_dic, xpath)
    except ExpatError as expat_exception:
        xml_structure_except(expat_exception, file)
    except Exception as error_str:
        error_write(error_str)
    finally:
        return XMLNS_INFO_LIST


# def generate_xmlns_info(file):
#     """Generate xmlns_info.
#     Args:
#         file: The path of xml file.
#     Returns:
#         XMLNS_INFO_LIST: global list.Recording all nodes's xmlns information.
#         structure like:
#             [
#              { '/node1/prefix2:node2':['node2-value','xmlns2'] },
#              { '/node1':['node1-value','xmlns1'] },
#              { '/node1/prefix2:node2/prefix3:node3':['node3-value','xmlns3'] },
#              ...
#             ]
#     Raises:
#         Exception: Capture execution exception.
#     """
#     global CONFIG_OR_FILTER_CONTENT
#     global XMLNS_INFO_LIST
#     CONFIG_OR_FILTER_CONTENT = OrderedDict()
#     XMLNS_INFO_LIST = []
#
#     try:
#         with open(file, 'r') as read:
#             xml_str = read.read()
#             xml_dic = xmltodict.parse(xml_str)
#             get_config_or_filter(xml_dic)
#             if not CONFIG_OR_FILTER_CONTENT:
#                 get_rpc_input(xml_dic)
#             xpath = ''
#             config_or_filter_content = CONFIG_OR_FILTER_CONTENT
#             if config_or_filter_content:
#                 generate_xmlns_info_with_recursive(config_or_filter_content, xpath)
#             else:
#                 logging.info("There is no <config> or <filter>, please check:" + file)
#     except ExpatError as expat_exception:
#         xml_structure_except(expat_exception, file)
#     except Exception as error_str:
#         error_write(error_str)
#     finally:
#         return XMLNS_INFO_LIST

def order_by_xpath(elem):
    """
    Sort the elem by length of xpathNode.
    """
    for key in elem:
        xpath_result = key.split("/")
    return len(xpath_result)


def get_xmlns_info(file,pkg_type):
    """Get sorted xmlns_info.
    Args:
        file: The path of xml file.
    Returns:
        sort_result: A list.Recording all nodes's xmlns information.
        structure like:
            [
             { '/node1':['node1-value','xmlns1'] },
             { '/node1/prefix2:node2':['node2-value','xmlns2'] },
             { '/node1/prefix2:node2/prefix3:node3':['node3-value','xmlns3'] },
             ...
            ]
    """
    sort_result = generate_xmlns_info(file,pkg_type)
    sort_result.sort(key=order_by_xpath)
    return sort_result


def xmlns_info_without_prefix(xmlns_info):
    """Remove prefix from xpath-key.
    Args:
        xmlns_info: The xmlns_info.
    Returns:
        new_xmlns_info_list: In xmlns_info,the xpath-key without prefix.
        for example:
            xmlns_info:
                [ { '/node1/prefix2:node2/prefix3:node3':[ 'node3-value','xmlns3' ] },... ]
            new_xmlns_info_list:
                [ { '/node1/node2/node3':[ 'node3-value','xmlns3','/node1/prefix2:node2/prefix3:node3' ] },... ]
    """
    new_xmlns_info_list = []
    for item in xmlns_info:
        new_dict = {}
        for xapth_key in item:
            xapth_key_list = xapth_key.split("/")[1:]
            new_xpath_key = ''
            for each_node in xapth_key_list:
                new_xpath_key = new_xpath_key + "/" + each_node.split(":")[-1]
            temp_list = item[xapth_key]
            temp_list.append(xapth_key)
        new_dict[new_xpath_key] = temp_list
        new_xmlns_info_list.append(new_dict)
    return new_xmlns_info_list


def get_xml_namespace(file_name,pkg_type):
    """Get xml's namespace.
    Args:
        file_name: The path of xml file.
    Returns:
        xml_namespace: The namespace of xml.
        for example:
            xml file content:
                ...
                <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                    <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces"
                                xmlns:ni="urn:ietf:params:xml:ns:yang:ietf-network-instance">
                        ...
                    </interfaces>
                </config>
            xml_namespace: 'urn:ietf:params:xml:ns:yang:ietf-interfaces'
    Raises:
        Exception: Capture execution exception.
    """
    feature_namespaces = []
    try:
        doc = parse(file_name)
        root = doc.documentElement
        if pkg_type in ['get','get-config']:
            if root.getElementsByTagNameNS("urn:ietf:params:xml:ns:netconf:base:1.0", "filter"):
                child_nodes = root.getElementsByTagNameNS("urn:ietf:params:xml:ns:netconf:base:1.0", "filter")[
                    0].childNodes
        elif pkg_type == 'config':
            if root.getElementsByTagNameNS("urn:ietf:params:xml:ns:netconf:base:1.0", "config"):
                child_nodes = root.getElementsByTagNameNS("urn:ietf:params:xml:ns:netconf:base:1.0", "config")[
                    0].childNodes
        else:
            child_nodes = root.childNodes
            logging.info("This is rpc-xml:" + file_name)
        for child_node in child_nodes:
            if child_node.nodeType == 1 and hasattr(child_node, 'namespaceURI'):
                feature_namespaces.append(child_node.namespaceURI)
    except ExpatError as expat_exception:
        xml_structure_except(expat_exception, file_name)
    except Exception as error_str:
        error_write(error_str)
    return feature_namespaces


def get_node_xmlns(xpath, xmlns_info, pre_element_node_prefix=""):
    """According the xmlns_info to query node's namespace.(recursive function).
    Args:
        xpath: The xpath node which need to find namespace.(without prefix).
        xmlns_info: The xmlns_info.
            structure like:
                [ { '/node1/node2/node3':[ 'node3-value','xmlns3','/node1/prefix2:node2/prefix3:node3' ] },... ].
        pre_element_node_prefix: Used to record the parent node prefix.
    Returns:
        The node's xmlns.
        for example:
            xpath: '/interfaces/interface'
            xmlns_info:
                [{'/interfaces': ['', '@xmlns:if="urn:ietf:params:xml:ns:yang:ietf-interfaces"', '/if:interfaces']},
                 {'/interfaces/interface': ['', '', '/if:interfaces/if:interface']},
                 ...]
            return: 'urn:ietf:params:xml:ns:yang:ietf-interfaces'
    """
    if xpath == '':
        return 'urn:ietf:params:xml:ns:netconf:base:1.0'
    for item in xmlns_info:
        if xpath in item.keys():
            xmlns = item[xpath][1]

            xpath_with_prefix = item[xpath][2]
            end_element_node_with_prefix = xpath_with_prefix.split("/")[-1]
            end_element_node_list = end_element_node_with_prefix.split(":")
            if len(end_element_node_list) == 1:
                element_node_prefix = ""
            elif len(end_element_node_list) == 2:
                element_node_prefix = end_element_node_list[0]
            else:
                logging.info("the len of element_node_prefix not equal 1 or 2,please check xpath: " +
                             str(xpath))

            if pre_element_node_prefix != "" and pre_element_node_prefix != element_node_prefix:
                element_node_prefix = pre_element_node_prefix
            if xmlns:
                if element_node_prefix == "":
                    search_obj_dual = re.search(r'xmlns="(.*?)"', xmlns)
                    search_obj_single = re.search(r"xmlns='(.*?)'", xmlns)
                    if search_obj_dual:
                        return search_obj_dual.group(1)
                    elif search_obj_single:
                        return search_obj_single.group(1)
                    else:
                        parent_node_xpath = xpath[:-(len(xpath.split("/")[-1])+1)]
                        return get_node_xmlns(parent_node_xpath, xmlns_info)
                else:
                    search_obj_dual = re.search(r'xmlns:' + element_node_prefix + '="(.*?)"', xmlns)
                    search_obj_single = re.search(r"xmlns:" + element_node_prefix + "='(.*?)'", xmlns)
                    if search_obj_dual:
                        return search_obj_dual.group(1)
                    if search_obj_single:
                        return search_obj_single.group(1)
            else:
                if element_node_prefix == "":
                    parent_node_xpath = xpath[:-(len(xpath.split("/")[-1])+1)]
                    return get_node_xmlns(parent_node_xpath, xmlns_info)
            parent_node_xpath = xpath[:-(len(xpath.split("/")[-1])+1)]
            return get_node_xmlns(parent_node_xpath, xmlns_info, element_node_prefix)

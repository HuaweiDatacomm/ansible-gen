__author__ = 'ansible_team'

from collections import OrderedDict
import os
import time
import logging
import re
from .utils.xml_parse.xml_parser import xml_to_ordered_dict
from .utils.yang_parse.yang_parser import YangParser
from .utils.yang_parse.interfaces import get_leaf_info_for_doc, get_leafinfos_from_xml_dict, \
    get_module_description, make_argument_spec, get_key_leafs, get_all_lists, check_all_node_exists
from .utils.base_util import error_write

YANG_HANDLER = ''  # define the global YANG_HANDLER
DEFAULT_INDENT = ' ' * 4


def get_xml_dict(xml_file):
    """
    get the xml_params of the xml
    :param xml_file: xml
    :return: the xml_params of the xml
    """
    return xml_to_ordered_dict(xml_file)


# get all xmlns from xxx_full.xml
def get_features_namespace(xml_dir):
    """
    :param xml_dir: the xml dir.
    :return:features_namespace: the set of all xmlns which need to be parsed.
    """
    features_namespace = set()
    files = os.listdir(xml_dir)
    for file in files:
        if os.path.isfile(os.path.join(xml_dir, file)):
            if not file.endswith("_example.xml"):
                with open(os.path.join(xml_dir, file), 'r') as xml_file:
                    xml_str = xml_file.read()
                if xml_str.strip() == '':
                    logging.error("%s is empty", file)
                else:
                    xmlns = list()
                    for item in re.findall(r'xmlns.*?="(.*?)"', xml_str):
                        xmlns.append(item)
                    for item in re.findall(r"xmlns.*?='(.*?)'", xml_str):
                        xmlns.append(item)
                    if xmlns:
                        for xmlns_item in xmlns:
                            features_namespace.add(xmlns_item)
                    else:
                        logging.error("%s has no xmlns", file)
        else:
            features_namespace = features_namespace | get_features_namespace(os.path.join(xml_dir, file))

    return features_namespace


def get_yang_handlers(yang_dir, xml_dir):
    """
    get the yang_handler of the yang_dir
    :param dir: the dir containing yang files
    :return:YANG_HANDLER
    """
    global YANG_HANDLER

    features = get_features_namespace(xml_dir)
    factory = YangParser(yang_dir, features)
    YANG_HANDLER = factory.parse()
    return YANG_HANDLER


def get_xml_descption(xml_namespace):
    """
    get the xml_description from yang_file of the xml_file
    :param xml_file: xml_file
    :return: the xml_description
    """
    parser = YANG_HANDLER
    return get_module_description(parser, xml_namespace)


def get_xml_options(full_xml_file_path, full_xml_ordered_dict, xmlns_info):
    """
    get the xml_params of the xml
    :param xml_file: xml_file
    :return:the xml_params of the xml
    """
    return get_leaf_info_for_doc(full_xml_file_path, full_xml_ordered_dict, YANG_HANDLER, xmlns_info)


def get_xml_leafinfos(full_xml_ordered_dict, xmlns_info):
    """
    get the xml_leafinfos of the xml
    :param xml_file: xml_file
    :return:the xml_leafinfos of the xml
    """
    yang_handlers = YANG_HANDLER
    xml_leafinfos = get_leafinfos_from_xml_dict(full_xml_ordered_dict, yang_handlers, xmlns_info)
    return xml_leafinfos


def get_xml_key_leafs(full_xml_ordered_dict, xmlns_info):
    """
    get the xml_leafinfos of the xml
    :param full_xml_ordered_dict:
    :return:the xml_leafinfos of the xml
    """
    yang_handlers = YANG_HANDLER
    xml_key_leafs = get_key_leafs(full_xml_ordered_dict, yang_handlers, xmlns_info)
    return xml_key_leafs


def get_xml_list_leafs(full_xml_ordered_dict, xmlns_info):
    """
    get the xml_leafinfos of the xml
    :param full_xml_ordered_dict:
    :return:the xml_leafinfos of the xml
    """
    yang_handlers = YANG_HANDLER
    xml_key_leafs = get_all_lists(full_xml_ordered_dict, yang_handlers, xmlns_info)
    return xml_key_leafs


def gen_argument_spec(full_xml_ordered_dict, xmlns_info, key_list, list_list):
    """
    get the argument_spec of the xml
    :param xml_leafinfos: xml_leafinfos
    :return:the argument_spec of the xml
    """
    return make_argument_spec(full_xml_ordered_dict, YANG_HANDLER, xmlns_info, key_list, list_list)


def gen_options(data, options_str, level=0):
    level += 1
    if isinstance(data, OrderedDict):
        for key, value in data.items():
            options_str += DEFAULT_INDENT + DEFAULT_INDENT * (level - 1) + key + ':' + '\n'
            if isinstance(value, tuple):
                if not value:
                    error_write("node %s has no value" % key)
                    return ""
                options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'description:\n'
                options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + DEFAULT_INDENT + '- ' + \
                               word_wrap(str(value[0]), 4 * (level + 2) + 3) + '\n'
                for when_must_check in value:
                    if when_must_check == "when:True":
                        str_out = "when: The configuration of this object takes effect only when certain conditions are met. For details, check the definition in the YANG model."
                        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + str_out + '\n'
                    elif when_must_check == "must:True":
                        str_out = "must: The configuration of this object takes effect only when certain conditions are met. For details, check the definition in the YANG model."
                        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + str_out + '\n'
                options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'required:' + str(value[1]) + '\n'
                if isinstance(value[-1], OrderedDict):
                    options_str += gen_options(value[-1], '', level)
                else:
                    options_str = option_check(options_str, value, level)
            elif isinstance(value, OrderedDict):
                options_str += gen_options(value, '', level)
    return options_str


def option_check(options_str, value, level):
    """
        get the documention of the value
        :return:the documention
        """
    if value[7] == True:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'key:' + str(value[7]) + '\n'
    if value[-4] == True:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'mandatory:' + str(value[8]) + '\n'
    if value[-2] == True:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'suppor-filter:' + str(value[10]) + '\n'
    if value[2] != None:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'default:' + str(value[2]) + '\n'
    if value[3] != []:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'pattern:' + str(value[3]) + '\n'
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'type:' + str(value[-1]) + '\n'
    if value[-1] == 'str' and value[6] != []:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'length:' + str(value[6]) + '\n'
    if value[-1] == 'int':
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'range:' + str(value[5]) + '\n'
    if value[-1] in ['enum', 'bool']:
        options_str += DEFAULT_INDENT + DEFAULT_INDENT * level + 'choices:' + str(value[4]) + '\n'
    return options_str


def line_wrap(desc, indent):
    wrapped_desc = []
    length = len(desc)
    line_len = 160 - indent
    while length > line_len:
        line = desc[0:line_len]
        if not line[-1].isspace():
            idx = line_len - 1
            while not line[idx].isspace():
                idx = idx - 1
            line = desc[:idx + 1]
            desc = desc[idx + 1:]
        else:
            desc = desc[line_len:]
        wrapped_desc.append(line + "\n")
        length = len(desc)
        if length <= line_len:
            wrapped_desc.append(desc)
    if not wrapped_desc:
        wrapped_desc.append(desc)

    return (" " * (indent - 1)).join(wrapped_desc)


def word_wrap(description, indent):
    descs = [section for section in description.split("\n") if section.strip()]
    wrapped_descs = []
    first = True
    for desc in descs:
        wrapped_desc = line_wrap(desc, indent)
        if not first:
            wrapped_desc = (" " * (indent - 1)) + wrapped_desc
        first = False
        wrapped_descs.append(wrapped_desc)

    return "\n".join(wrapped_descs)


def gen_documentation(module_desc, data, filename, xml_type):
    '''
    :param module_desc: module description
    :param data: xml_yang data
    :return:documentation
    '''
    documentation = ''
    documentation += '---' + '\n'
    documentation += 'module:' + filename + '\n'
    documentation += 'version_added: "2.6"' + '\n'
    documentation += 'short_description: ' + word_wrap(module_desc, 20) + '\n'
    documentation += 'description:' + '\n'
    documentation += '    - ' + word_wrap(module_desc, 7) + '\n'
    documentation += 'author:' + (__author__) + '@huawei' + '\n'
    now_time = (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))))
    documentation += 'time:' + str(now_time) + '\n'
    documentation += 'options:\n'
    options_str = get_options_str(xml_type)
    documentation += gen_options(data, options_str)
    try:
        return documentation
    except Exception as e:
        print(e)


def get_options_str(xml_type):
    options_str = ''
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * 0 + 'opreation_type:{}\n'.format(xml_type)
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * 1 + 'description:{}\n'.format(xml_type)
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * 1 + DEFAULT_INDENT + '- ' + \
                   word_wrap('This is a helper node ,Choose from config, get', 4 * 3 + 3) + '\n'
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * 1 + 'type: str\n'
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * 1 + 'required:{}\n'.format(True)
    options_str += DEFAULT_INDENT + DEFAULT_INDENT * 1 + 'choices: ["config","get","get-config","input_action"]\n'
    return options_str


def check_xpaths_exists(xml_dict, xmlns_info):
    return check_all_node_exists(xml_dict, YANG_HANDLER, xmlns_info)
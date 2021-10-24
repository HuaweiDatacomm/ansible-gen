#!/usr/bin/env python
# -*- coding: utf-8 -*-


import copy
import logging
from collections import OrderedDict

from . import pyang_util
from . import constant
from . import utils
from ..xml_parse.xml_parser_get_xmlns import get_node_xmlns
from ..base_util import operation_warning_write
from .constant import BASE_INTEGER_TYPES

LIST_KEY_SET = set()

def get_feature_info(xpath, parsed_data, xmlns_info):
    """Get the module from yang_handler.
    Args:
        xpath: The xpath-node which need to find module.(without prefix).
        parsed_data: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        feature_info: The module that xpath-node belong to.
        augment_flag: Whether the xpath-node is augment.
    """
    augment_flag = False
    # get xpath-node's xmlns.
    current_node_xmlns = get_node_xmlns(xpath, xmlns_info)

    feature_xpath = "/" + xpath.split("/")[1]
    xml_namespace = get_node_xmlns(feature_xpath, xmlns_info)

    # whether augment: xpath-node's xmlns not equal xml's xmlns.
    if current_node_xmlns != xml_namespace:
        augment_flag = True
    # use xpath-node's xmlns to get the feature_info.
    feature_info = None
    augment_break_out_flag = False
    for _, module in parsed_data.ctx.modules.items():
        if module.keyword == 'module':
            if augment_flag:
                if augment_break_out_flag:
                    break
                else:
                    val_namespace2 = module.search_one("namespace")
                    if val_namespace2 and val_namespace2.arg == current_node_xmlns:
                        for _augment, module_by_augment in module.i_ctx.modules.items():
                            val_namespace2 = module_by_augment.search_one("namespace")
                            if val_namespace2 and val_namespace2.arg == xml_namespace:
                                feature_info = module_by_augment
                                augment_break_out_flag = True
                                break
            else:
                val_namespace = module.search_one("namespace")
                if val_namespace and val_namespace.arg == xml_namespace:
                    feature_info = module
                    break
    return [feature_info, augment_flag]

def recursive_root(node_name, root):
    """Recursive to get xpath-node's root.(recursive function).
    Args:
        node_name: The node name that split by xpath.
        root: The module's root.
    Returns:
        root: The xpath-node's root.
    """
    if not hasattr(root, 'i_children'):
        return None
    for node in root.i_children:
        if node.keyword in  ['input','output','choice','case']:
            sub_root = recursive_root(node_name,node)
            if(sub_root is not None):
                return sub_root
        else:
            if (node.arg == node_name):
                return node
    return None

def get_xpaths_node(xpath, root):
    """Get the xpath-node from feature_info.
    Args:
        xpath: The xpath-node which need to find root.(without prefix).
        root: The module's root that xpath-node belong to.
    Returns:
        root: The xpath-node's root.
    """
    for node_name in xpath.split("/")[1:]:
        if root is None:
            break
        else:
            root = recursive_root(node_name, root)

    if root is None:
        return None
    else:
        return root

def recursive_root_of_augment(node_name, root):
    """Recursive to get xpath-node's root when augment.(recursive function).
    Args:
        node_name: The node name that split by xpath.
        root: The module's root.
    Returns:
        root: The xpath-node's root.
    """
    if not hasattr(root, 'i_children'):
        return None
    current_node_stmts = [node for node in root.i_children]
    for current_node in current_node_stmts:
        if current_node.keyword in ('input','output','choice','case'):
            root = recursive_root_of_augment(node_name,current_node)
            if root is not None:
                return root
            else:
                continue
        if node_name == current_node.arg:
            root = current_node
            return root
    return root

def get_xpaths_node_of_augment(xpath, root):
    """Get the xpath-node from feature_info when augment.
    Args:
        xpath: The xpath-node which need to find root.(without prefix).
        root: The module's root that xpath-node belong to.
    Returns:
        root: The xpath-node's root.
    """
    for node_name in xpath.split("/")[1:]:
        if root is None:
            break
        else:
            root = recursive_root_of_augment(node_name, root)

    if root is None:
        return None
    else:
        return root


def get_required(node):
    """Get xpath-node required information.
    Args:
        node: The xpath-node's root.
    Returns:
        A bool value.
        rule: The xpath-node that has a "mandatory" attr or is primary-key,it is required.else not required.
    """
    keys = []
    p_stmt = node.parent
    key_stmt = p_stmt.search_one("key")
    if key_stmt:
        keys = [name.strip() for name in key_stmt.arg.split() if name.strip()]
    if node.arg in keys:
        return True
    mandatory_stmt = node.search_one("mandatory")
    if mandatory_stmt and mandatory_stmt.arg.strip().lower() == "true":
        return True
    # when node is a case,the mandatory exist in parent's substmts.
    if node.arg == node.parent.arg:
        if node.parent.keyword == "case":
            if node.parent.parent.keyword == "choice":
                for choice_substmts in node.parent.parent.substmts:
                    if choice_substmts.keyword == "mandatory" and choice_substmts.arg.strip().lower() == "true":
                        return True
    return False

def get_default(node):
    """Get xpath-node default information.
    Args:
        node: The xpath-node's root.
    Returns:
        return xpath-node's default value.
    """

    default_stmt = node.search_one("default")
    if default_stmt:
        default = default_stmt.arg
        type_stmt = node.search_one("type")
        if not type_stmt.i_type_spec:
            return default
        if type_stmt.i_type_spec.name == "boolean":
            if default.lower() == "false":
                default = False
            elif default.lower() == "true":
                default = True
        elif type_stmt.i_type_spec.name in constant.BASE_INTEGER_TYPES:
            default = int(default)
        return default
    else:
        return None

def get_type(node):
    """Get xpath-node's type.(recursive function).
    Args:
        node: The xpath-node's root.
    Returns:
        return xpath-node's type.
    """
    if node.keyword not in ['leaf','leaf-list']:
        return None
    type_stmt = node.search_one("type")
    if not type_stmt:
        logging.info("leaf %s has no type defination", node.arg)
        return None
    type_spec = type_stmt.i_type_spec
    if not type_spec:
        return None
    if type_spec.name == "leafref":
        if hasattr(type_spec, "i_target_node"):
            target_node = type_spec.i_target_node
            return get_type(target_node)
        else:
            return None
    else:
        return type_stmt.i_type_spec.name

def get_pattern(node):
    """Get xpath-node's pattern.(recursive function).
    Args:
        node: The xpath-node's root.
    Returns:
        return xpath-node's pattern.
    """
    if node.keyword not in ['leaf','leaf-list']:
        return None
    type_stmt = node.search_one("type")
    if not type_stmt:
        logging.info("leaf %s has no type defination", node.arg)
        return None
    type_spec = type_stmt.i_type_spec
    if not type_spec:
        return []
    patterns = []
    if hasattr(type_stmt.i_type_spec, "res"):
        patterns.extend([pattern_stmt.spec for pattern_stmt in type_stmt.i_type_spec.res])
    elif type_spec.name == "leafref":
        patterns.extend(get_pattern(type_spec.i_target_node))
    return patterns

def get_restrict(node):
    """Get xpath-node's restrict.(recursive function).
    Args:
        node: The xpath-node's root.
    Returns:
        return xpath-node's restrict.
    """
    if node.keyword not in {'leaf','leaf-list'}:
        return None
    type_stmt = node.search_one("type")
    if not type_stmt:
        logging.info("leaf %s has no type defination", node.arg)
        return None
    type_spec = type_stmt.i_type_spec
    if not type_spec:
        return []
    if type_spec.name == "leafref":
        if not hasattr(type_spec,'i_target_node'):
            logging.error("leaf %s type is %s but no target node", node.arg,type_spec.name)
            return None
        target_node = type_spec.i_target_node
        return get_restrict(target_node)
    if type_spec.name == "string":
        rests = []
        if hasattr(type_spec, "lengths"):
            rests.extend(type_stmt.i_type_spec.lengths)
        base_def = type_spec.base
        while base_def:
            if hasattr(base_def, "lengths"):
                rests.extend(base_def.lengths)
            base_def = base_def.base
        return utils.Util.restrict_set_intersec(rests)
    elif type_spec.name == "enumeration":
        return [enum_t[0] for enum_t in type_spec.enums]
    elif type_spec.name in constant.BASE_INTEGER_TYPES:
        rests = []
        if hasattr(type_spec, "min") and hasattr(type_spec, "max"):
            rests.extend([(type_spec.min, type_spec.max)])
        elif hasattr(type_spec, "ranges"):
            rests.extend(type_spec.ranges)
        base_def = type_spec.base
        while base_def:
            if hasattr(type_spec, "min") and hasattr(type_spec, "max"):
                rests.extend([(type_spec.min, type_spec.max)])
            elif hasattr(base_def, "ranges"):
                rests.extend(base_def.ranges)
            base_def = base_def.base
        return utils.Util.restrict_set_intersec(rests)
    else:
        return []

def get_desc(node):
    """Get xpath-node's description.
    Args:
        node: The xpath-node's root.
    Returns:
        return xpath-node's description.
    """
    desc_stmt = node.search_one("description")
    if desc_stmt:
        return desc_stmt.arg
    else:
        return ""

def check_is_key(node):
    """Check the xpath-node whether is primary-key.
    Args:
        node: The xpath-node's root.
    Returns:
        A bool.
    """
    parent_stmt = node.parent
    key_stmt = parent_stmt.search_one("key")
    if key_stmt:
        a = node.arg in [name.strip() for name in key_stmt.arg.split() if name.strip()]
        return node.arg in [name.strip() for name in key_stmt.arg.split() if name.strip()]
    return False


def check_config(node):
    result = True
    config_stmt = node.search_one("config")
    if config_stmt and config_stmt.arg.lower() == "false":
        result = False
    return result
def when_must_check(node):
    """Get xpath-node default information.
       Args:
           node: The xpath-node's root.
       Returns:
           return xpath-node's default value.
       """
    when_stmt = node.search_one("when")
    must_stmt = node.search_one("must")
    if when_stmt:
        return "when:True"
    elif must_stmt:
        return "must:True"
    else:
        return None
def mandatory_check(node):
    """Get xpath-node default information.
       Args:
           node: The xpath-node's root.
       Returns:
           return xpath-node's default value.
       """
    when_stmt = node.search_one("mandatory")
    if when_stmt:
        return True
    else:
        return None

def suport_filter_check(node):
    """Get xpath-node default information.
       Args:
           node: The xpath-node's root.
       Returns:
           return xpath-node's default value.
       """
    support_filter = ('huawei-extension', 'support-filter')
    when_stmt = node.search_one(support_filter)
    if when_stmt:
        return True
    else:
        return None

def get_xpaths_infos(xpath, parsed_data, xmlns_info):
    """Get xpath-node information from yang_handler.
    Args:
        xpath: The xpath-node which need to get information.(without prefix).
        parsed_data: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        A dict.Saving xpath-node's information.
        for example:
            {'key': False,
             'desc': 'Network instance to which an interface is bound.',
             'restrict': [],
             'pattern': [],
             'required': False,
             'default': None,
             'type': 'string'
             }
    """

    # get_xpaths_infos() begin.
    if not parsed_data.ctx.modules:
        return {}
    # get module's root and augment_flag.
    feature_info_list = get_feature_info(xpath, parsed_data, xmlns_info)
    feature_info = feature_info_list[0]
    augment_flag = feature_info_list[1]

    feature = xpath.split("/")[1]
    if not feature_info:
        logging.error("module %s is not provided in yang directory", feature)
        return {}

    if augment_flag:
        # get xpath-node's root when augment.
        leaf = get_xpaths_node_of_augment(xpath, feature_info)
    else:
        # get xpath-node's root.
        leaf = get_xpaths_node(xpath, feature_info)

    if leaf:
        return {
            'required': get_required(leaf),
            'type': get_type(leaf),
            'restrict': get_restrict(leaf),
            "pattern": get_pattern(leaf),
            'default': get_default(leaf),
            'desc': get_desc(leaf),
            'key': check_is_key(leaf),
            'whether_config': check_config(leaf),
            'when_must_check':when_must_check(leaf),
            'mandatory_check':mandatory_check(leaf),
            'suport_filter_check':suport_filter_check(leaf)
        }
    else:
        return {}

def get_module_description(parser, xml_namespace):
    """Get module's description from yang_handler.
    Args:
        parser: The yang_handler.
        xml_namespace: The xml's namespace.
    Returns:
        first we try to get description statement in main module yang files, if there is no description
        statement, then we try to get description statement from root node.
    """
    result = ""
    feature_info_list = []
    if len(xml_namespace) == 0:
        return result
    # use the xml_namespace to find module.
    for key, val in parser.ctx.modules.items():
        if not val.keyword == 'module':
            continue
        module_ns = pyang_util.get_module_namespace(val)
        if module_ns in xml_namespace:
            feature_info_list.append(val)
    if not feature_info_list:
        logging.error("module %s is not provided in yang directory", xml_namespace)
        return result

    feature_info_list.sort(key=lambda x: x.arg)
    for feature_info in feature_info_list:
        desc_stmt = feature_info.search_one("description")
        if desc_stmt and desc_stmt.arg:
            result = result + desc_stmt.arg + "\n"
    return result


def check_all_node_exists(xml_dict, yang_parser, xmlns_info):
    """Check all node exists in yang_handler.
    Args:
        xml_dict: An OrderedDict. Recording the xml's structure.
        yang_parser: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        A bool.
    """

    def gen_xpaths(xpaths,xml_dict):
        if xml_dict is None:
            return  xpaths;
        if xpaths is None or len(xpaths) ==0 :
            last_xpath = ""
        else:
            last_xpath = xpaths[-1]
        for key,val in xml_dict.items():
            xpath = last_xpath + "/" +  key
            xpaths.append(xpath)
            if not isinstance(val, list):
                nodes = [val]
            else:
                nodes = val
            for node in nodes:
                gen_xpaths(xpaths,node)

    # check_all_node_exists() begin.
    xpaths=[]
    gen_xpaths(xpaths,list(xml_dict.values())[0])

    for xpath in xpaths:
        xpath_info = get_xpaths_infos(xpath,yang_parser,xmlns_info)
        if not xpath_info:
            logging.warning("xpath %s not exist in yang files", xpath)
            return False
    return True

def is_key_leaf(xpath, yang_parser, xmlns_info):
    """Whether the leaf-node is primary-key
    Args:
        xpath: The leaf-node's xpath.(without prefix).
        yang_parser: The yang_handler.
        xmlns_info:  The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        A bool.
    """
    global LIST_KEY_SET
    if xpath in LIST_KEY_SET:
        return True

    feature = xpath.split("/")[1]
    if not yang_parser.ctx.modules:
        return False

    # get module's root and augment_flag.
    feature_info_list = get_feature_info(xpath, yang_parser, xmlns_info)
    feature_info = feature_info_list[0]
    augment_flag = feature_info_list[1]

    if not feature_info:
        logging.error("module %s is not provided in yang directory", feature)
        return False

    if augment_flag:
        # get xpath's root when augment.
        leaf = get_xpaths_node_of_augment(xpath, feature_info)
    else:
        # get xpath's root.
        leaf = get_xpaths_node(xpath, feature_info)

    if not leaf:
        logging.warning("xpath %s has no correspond leaf find in yang files", xpath)
        return False

    if leaf.keyword == "list":
        key_stmt = leaf.search_one("key")
        if key_stmt:
            for name in key_stmt.arg.split():
                if name.strip():
                    LIST_KEY_SET.add(str(xpath) + "/" + str(name))

    return False

def is_list_node(xpath, yang_parser, xmlns_info):
    """Whether the node is list
    Args:
        xpath: The leaf-node's xpath.(without prefix).
        yang_parser: The yang_handler.
        xmlns_info:  The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        A bool.
    """
    feature = xpath.split("/")[1]
    if not yang_parser.ctx.modules:
        return False

    # get module's root and augment_flag.
    feature_info_list = get_feature_info(xpath, yang_parser, xmlns_info)
    feature_info = feature_info_list[0]
    augment_flag = feature_info_list[1]

    if not feature_info:
        logging.error("module %s is not provided in yang directory", feature)
        return False

    if augment_flag:
        # get xpath's root when augment.
        leaf = get_xpaths_node_of_augment(xpath, feature_info)
    else:
        # get xpath's root.
        leaf = get_xpaths_node(xpath, feature_info)

    if not leaf:
        logging.warning("xpath %s has no correspond leaf find in yang files", xpath)
        return False

    if leaf.keyword == "list":
        return True

    return False


def get_key_leafs(xml_dict, yang_parser, xmlns_info):
    """Traversing the xml_dict,get all leaf-node's xpath which is primary-key.
    Args:
        xml_dict: An OrderedDict. Recording the xml's structure.
        yang_parser: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        A list.
    """
    def get_keys(leaf_dict, xpath, yang_parser, leaf_path, xmlns_info):
        """Get all leaf-node's xpath which is primary-key.(recursive function).
        Args:
            leaf_dict: An OrderedDict. Recording the container-node's structure.
            xpath: container-node's xpath.
            yang_parser: The yang_handler.
            leaf_path: Used to record the leaf-node's xpath.
            xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
        Returns:
            A list.
        """
        if leaf_dict is None:
            return None
        keys = []
        for key, val in leaf_dict.items():
            container_leaf_xpath = leaf_path + "/" + key
            tmp_xpath = xpath + "/" + key
            if is_key_leaf(tmp_xpath, yang_parser, xmlns_info):
                #logging.info("xpath %s is key leaf", tmp_xpath)
                keys.append(leaf_path + "/" + key)
            if isinstance(val, OrderedDict):
                keys.extend(
                    get_keys(leaf_dict[key], tmp_xpath, yang_parser, container_leaf_xpath, xmlns_info))
        return keys

    # get_key_leafs() begin.
    tmp_dict = copy.deepcopy(list(xml_dict.values())[0])
    xpath = ""
    leaf_path = ""
    global LIST_KEY_SET
    LIST_KEY_SET = set()
    key_leafs = get_keys(tmp_dict, xpath, yang_parser, leaf_path, xmlns_info)

    return key_leafs

def get_all_lists(xml_dict, yang_parser, xmlns_info):
    """Traversing the xml_dict,get all list's xpath.
    Args:
        xml_dict: An OrderedDict. Recording the xml's structure.
        yang_parser: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        A list.
    """
    def get_lists(leaf_dict, xpath, yang_parser, leaf_path, xmlns_info):
        """Get all list's xpath which is primary-key.(recursive function).
        Args:
            leaf_dict: An OrderedDict. Recording the container-node's structure.
            xpath: container-node's xpath.
            yang_parser: The yang_handler.
            leaf_path: Used to record the leaf-node's xpath.
            xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
        Returns:
            A list.
        """
        all_lists = []
        if leaf_dict is None:
            return all_lists
        for key, val in leaf_dict.items():
            tmp_xpath = xpath
            container_leaf_xpath = leaf_path + "/" + key
            if isinstance(val, OrderedDict):
                tmp_xpath = tmp_xpath + "/" + key
                if is_list_node(tmp_xpath, yang_parser, xmlns_info):
                    all_lists.append(leaf_path + "/" + key)
                all_lists.extend(
                    get_lists(leaf_dict[key], tmp_xpath, yang_parser, container_leaf_xpath, xmlns_info))
            else:
                tmp_xpath = tmp_xpath + "/" + key
                if is_list_node(tmp_xpath, yang_parser, xmlns_info):
                    all_lists.append(leaf_path + "/" + key)
        return all_lists

    # get_key_leafs() begin.
    tmp_dict = copy.deepcopy(list(xml_dict.values())[0])
    xpath = ""
    leaf_path = ""
    all_lists = get_lists(tmp_dict, xpath, yang_parser, leaf_path, xmlns_info)

    return all_lists

def get_leafinfos_from_xml_dict(node_d, parser, xmlns_info):
    """Traversing the xml_dict,get all leaf-node's information.
    Args:
        node_d: An OrderedDict. Recording the xml's structure.
        parser: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        An OrderedDict.
        The information contain (key,desc,restrict,pattern,required,default,type) which come from each leaf-node.
        The output is for params check.
    """
    def get_leafinfos(xml_type, leaf_dict, xpath, parser, xmlns_info):
        """Get all leaf-node's information.(recursive function).
        Args:
            leaf_dict: An OrderedDict. Recording the container-node's structure.
            xpath: Used to record the leaf-node's xpath.
            parser: The yang_handler.
            xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
        Returns:
            An OrderedDict.
        """
        leaf_infos = OrderedDict()
        if leaf_dict is None:
            return leaf_infos;
        for key, val in leaf_dict.items():
            if not isinstance(val, list):
                # compatible the situation with list
                recurv_val = [val]
            else:
                recurv_val = val
            for item in recurv_val:
                if isinstance(item, OrderedDict):
                    tmp_xpath = xpath + "/" + key
                    if key not in leaf_infos:
                        leaf_infos[key] = OrderedDict()
                    leaf_infos[key].update(
                        get_leafinfos(xml_type, item, tmp_xpath, parser, xmlns_info))
                else:
                    tmp_xpath = xpath + "/" + key
                    yang_info = get_xpaths_infos(tmp_xpath, parser, xmlns_info)
                    # default = None
                    # yang_info['required'] = False
                    # default = {'default':None}
                    # yang_info.update(default)
                    if yang_info:
                        if xml_type == "config" and not yang_info.get("whether_config"):
                            continue
                        _d1 = trans_to_smiple_type(yang_info)
                        if not yang_info.__contains__('type'):
                            type = None
                        else:
                            type = yang_info["type"]
                        if not yang_info.__contains__('pattern'):
                            pattern = None
                        else:
                            pattern = yang_info["pattern"]
                        if not yang_info.__contains__('key'):
                            is_key = None
                        else:
                            is_key = yang_info["key"]
                        if not yang_info.__contains__('required'):
                            required = None
                        else:
                            required = yang_info["required"]
                        if not yang_info.__contains__('default'):
                            default = None
                        else:
                            default = yang_info["default"]

                        form_leaf = OrderedDict({
                            key: {'required': required,
                                  'type': type,
                                  "default": default,
                                  "pattern": pattern,
                                  'key': is_key
                                  }
                        })
                        form_leaf[key].update(_d1)
                        leaf_infos.update(form_leaf)
                    else:
                        logging.info(
                            "xpath %s not find in yang files", tmp_xpath)
        return leaf_infos

    xml_type = list(node_d.keys())[0]
    xml_dict = copy.deepcopy(list(node_d.values())[0])
    xpath = ""

    leaf_infos = get_leafinfos(xml_type, xml_dict, xpath, parser, xmlns_info)
    return leaf_infos


def trans_to_smiple_type(yang_info):
    if 'type' not in yang_info:
        return {}
    if yang_info['type'] in constant.BASE_INTEGER_TYPES:
        _d1 = {'range': yang_info["restrict"]}
        yang_info['type'] = 'int'
    elif yang_info['type'] == "string":
        _d1 = {'length': yang_info["restrict"]}
    elif yang_info['type'] == "enumeration":
        _d1 = {'choices': yang_info['restrict']}
    elif yang_info['type'] == "identityref":
        _d1 = {'type': "string", 'length': []}
    elif yang_info['type'] == "empty":
        _d1 = {'type': "string", 'length': []}
    elif yang_info['type'] == "union":
        _d1 = {'type': "string", 'length': []}
    else:
        _d1 = {}
    return _d1
def get_leaf_info_for_doc(full_xml_file_path, leaf_dict, parser, xmlns_info):
    """Traversing the xml_dict,get all leaf-node's information.
    Args:
        leaf_dict: An OrderedDict. Recording the xml's structure.
        parser: The yang_handler.
        xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
    Returns:
        An OrderedDict.
        The information contain (description, required , default) which come from each leaf-node.
        The output is for DOCUMENTATION's content.
    """
    def get_leafinfos(full_xml_file_path, xml_type, leaf_dict, xpath, parser, xmlns_info):
        """Get all leaf-node's information.(recursive function).
        Args:
            leaf_dict: An OrderedDict. Recording the container-node's structure.
            xpath: Used to record the leaf-node's xpath.
            parser: The yang_handler.
            xmlns_info: The xmlns_info.Saving all nodes's xmlns information.
        Returns:
            An OrderedDict.
        """
        doc_infos = OrderedDict()
        if leaf_dict is None:
            return None
        for key, val in leaf_dict.items():
            if not isinstance(val, list):
                # compatible the situation with list
                val = [val]
            if key not in doc_infos:
                doc_infos[key] = OrderedDict()
            for node in val:
                tmp_xpath = xpath
                if isinstance(node, OrderedDict):
                    tmp_xpath = tmp_xpath + "/" + key
                    if key == "@operation":
                        continue
                    doc_flag = True
                    leaf_info = get_xpaths_infos(tmp_xpath, parser, xmlns_info)
                    if leaf_info:
                        if xml_type == "config" and not leaf_info["whether_config"]:
                            msg = 'The node: %s is [config "false"],ansible-gen will ignore this node.' \
                                  '\nplease check the file: %s.' \
                                  '\nplease confirm the instance-xml synchronously.' % (tmp_xpath, full_xml_file_path)
                            operation_warning_write(msg)
                            doc_infos.pop(key)
                            continue
                        _c = put_doc_type(leaf_info)
                        doc_infos[key] = (
                            leaf_info["desc"], leaf_info["required"], leaf_info["default"],
                            leaf_info.get('pattern'),leaf_info.get('when_must_check'),
                            _c.get('type'))
                    else:
                        logging.warning(
                            "xpath %s not find in  yang files", tmp_xpath)
                        doc_infos[key] = tuple()
                    doc_infos[key] = list(doc_infos[key])
                    empty_orderdict = OrderedDict()
                    doc_infos[key].append(empty_orderdict)
                    doc_infos[key] = tuple(doc_infos[key])
                    doc_infos[key][-1].update(
                        get_leafinfos(full_xml_file_path, xml_type, node, tmp_xpath, parser, xmlns_info))
                else:
                    if key == "@operation":
                        continue
                    tmp_xpath = tmp_xpath + "/" + key
                    leaf_info = get_xpaths_infos(tmp_xpath, parser, xmlns_info)
                    if leaf_info:
                        if xml_type == "config" and not leaf_info["whether_config"]:
                            msg = 'The node: %s is [config "false"],ansible-gen will ignore this node.' \
                                  '\nplease check the file: %s.' \
                                  '\nplease confirm the instance-xml synchronously.' % (tmp_xpath, full_xml_file_path)
                            operation_warning_write(msg)
                            doc_infos.pop(key)
                            continue
                        _c = put_doc_type(leaf_info)
                        if leaf_info['type'] == 'enumeration':
                            leaf_info['choices'] = leaf_info.get('restrict')
                        if leaf_info['type'] == 'boolean':
                            leaf_info['choices'] = ['true','false']
                        if leaf_info['type'] in BASE_INTEGER_TYPES:
                            leaf_info['range'] = leaf_info.get('restrict')
                        if leaf_info['type'] == 'string':
                            leaf_info['length'] = leaf_info.get('restrict')
                        doc_infos[key] = (
                            leaf_info["desc"], leaf_info["required"], leaf_info["default"],
                            leaf_info.get('pattern'),leaf_info.get('choices'),leaf_info.get('range'),leaf_info.get('length'),leaf_info.get('key'),
                            leaf_info.get('mandatory_check'),leaf_info.get('when_must_check'),leaf_info.get('suport_filter_check'),
                            _c.get('type'))
                    else:
                        logging.warning(
                            "xpath %s not find in  yang files", tmp_xpath)
                        doc_infos[key] = tuple()
        return doc_infos

    xpath = ""
    xml_type = list(leaf_dict.keys())[0]
    xml_dict = copy.deepcopy(list(leaf_dict.values())[0])

    doc_infos = get_leafinfos(full_xml_file_path, xml_type, xml_dict, xpath, parser, xmlns_info)

    return doc_infos

def put_doc_type(leaf_info):
    """Generate the leaf-node's DOCUMENTATION.
    Args:
        leaf_infos: The result of get_leafinfos_from_xml_dict().
    Returns:
        A dict.The leaf-node's DOCUMENTATION.
        The leaf-node's DOCUMENTATION has (type, default, required) attribution which come from leaf_info.
    """
    dic = dict()
    try:
        if leaf_info['type'] in constant.BASE_INTEGER_TYPES:
            dic['type'] = 'int'
        elif leaf_info['type'] in ("union", "identityref", "empty", "string"):
            dic['type'] = 'str'
        elif leaf_info['type'] == "enumeration":
            dic['type'] = 'enum'
        elif leaf_info['type'] == "boolean":
            dic['type'] = 'bool'
    except:
        print(leaf_info)
    return dic

def make_simple_type_argument(leaf_info):
    """Generate the leaf-node's argument_spec.
    Args:
        leaf_infos: The result of get_leafinfos_from_xml_dict().
    Returns:
        A dict.The leaf-node's argument_spec.
        The leaf-node's argument_spec has (type, default, required) attribution which come from leaf_info.
    """
    leaf_args = {}
    if not leaf_info:
        return leaf_args
    if leaf_info['type'] == "enumeration":
        leaf_args["choices"] = leaf_info["choices"]
    else:
        leaf_args["type"] = leaf_info["type"]
        if leaf_args["type"] == "boolean":
            leaf_args["type"] = "bool"
        if leaf_args["type"] == "string":
            leaf_args["type"] = "str"

    if leaf_info["default"]:
        leaf_args["default"] = leaf_info["default"]

    leaf_args["required"] = leaf_info["required"]

    return leaf_args


# def make_arg_from_xpath(xpath, args):
#     """Add the xpath-key into argument_spec.
#     Args:
#         xpath: The xpath-key.
#         args: The argument_spec.
#     Returns:
#         A dict. The argument_spec of get.
#     """
#     sub_arg = args
#     nodes = xpath.split("/")
#     sub_arg["options"].update(dict(all=dict(type="bool", default=False)))
#     argument_spec = sub_arg = {nodes[-1]: sub_arg}
#     nodes = nodes[-2:0:-1]
#
#     for node in nodes:
#         sub_arg.update(dict(all=dict(type="bool", default=False)))
#         argument_spec = {node: dict(type="dict", options=sub_arg)}
#         sub_arg = argument_spec
#     return argument_spec

def make_argument_spec(xml_dict, yang_parser, xmlns_info, key_list, list_list):
    """Generate the argument_spec.
    Args:
        xml_dict: An OrderedDict. Recording the xml's structure.
        yang_parser: The yang_handler.
        xml_file:  The path of xml file.
    Returns:
        A dict.
        The output is for argument_spec.
        argument spec which is initial argument for class AnsibleModule
        Since netconf package for "get" and "config" support different operation scope. So for "get" package
        we will add two extra var to indicat:
            1. all: set True if we want get all data for while container/list, or we want get all instance of a leaf
            2. value: set it if we want get special instance of a leaf which's value equal to value we set
        And for "config" package we should make all leafs can be config no matter which level it is.
    """
    def _make_config_args(xpath, leaf_infos, list_list):
        """Use leaf_infos to generate config's argument_spec.(recursive function).
        Args:
            leaf_infos: The result of get_leafinfos_from_xml_dict().
        Returns:
            A dict.The config's argument_spec
        """
        argument_spec = OrderedDict()
        if isinstance(leaf_infos, OrderedDict):
            for node_name in leaf_infos:
                xpath = xpath + "/" + node_name
                complex_node = False
                for val in leaf_infos[node_name].values():
                    if isinstance(val, dict):
                        complex_node = True
                        break
                if not complex_node:
                    single_arg = make_simple_type_argument(
                        leaf_infos[node_name])
                    if not single_arg:
                        logging.warning(
                            "node %s has no defination in yang files", node_name)
                        continue
                    else:
                        argument_spec[node_name] = single_arg
                else:
                    node_spec = _make_config_args(xpath, leaf_infos[node_name], list_list)
                    list_flag = False
                    for sub_node_name in leaf_infos[node_name].keys():
                        temp_xpath = xpath + "/" + sub_node_name
                        if temp_xpath in list_list:
                            list_flag = True
                            break
                    if list_flag:
                        argument_spec[node_name] = dict(
                            type="list", elements="dict", options=node_spec)
                    else:
                        argument_spec[node_name] = dict(
                            type="dict", options=node_spec)
                xpath = xpath[:-(len(node_name) + 1)]

        return argument_spec

    def _make_get_args(xpath, leaf_infos, key_list, list_list):
        """Use leaf_infos to generate get's argument_spec.(recursive function).
        Args:
            xpath: The xpath-key.
            leaf_infos: The result of get_leafinfos_from_xml_dict().
        Returns:
            A dict. The argument_spec of get.
        """
        def _make_args_from_var_nodes(xpath, var_nodes, key_list, list_list):
            """Use leaf_infos to generate get's argument_spec.
            Args:
                var_nodes: The result of get_leafinfos_from_xml_dict().
            Returns:
                A dict. The get's argument_spec without xpath-key.
            """
            leafs = OrderedDict()
            leafs["options"] = OrderedDict()
            if not isinstance(var_nodes, OrderedDict):
                return None
            for key, v in var_nodes.items():
                xpath = xpath + "/" + key
                if isinstance(v, OrderedDict):
                    sub_arg = _make_args_from_var_nodes(xpath, v, key_list, list_list)
                    if xpath in list_list:
                        sub_arg["options"].update(
                            get_all=dict(type="bool", defalut=False))
                        leafs["options"].update({key: sub_arg})
                        leafs["type"] = "list"
                        leafs["elements"] = "dict"
                    else:
                        sub_arg["options"].update(
                            get_all=dict(type="bool", defalut=False))
                        leafs["options"].update({key: sub_arg})
                        leafs["type"] = "dict"
                else:
                    leaf_args = {'type': 'dict', "options": {
                        "get_all": dict(type="bool", defalut=False), "get_value": dict()}}
                    if v.get("required") and xpath not in key_list:
                        v["required"] = False
                    leaf_args["options"]["get_value"].update(make_simple_type_argument(v))
                    leafs["options"].update({key: leaf_args})
                    if xpath in list_list:
                        leafs["type"] = "list"
                        leafs["elements"] = "dict"
                    else:
                        leafs["type"] = "dict"
                xpath = xpath[:-(len(key) + 1)]
            return leafs

        argument_spec = _make_args_from_var_nodes(xpath, leaf_infos, key_list, list_list)

        return argument_spec["options"]

    schema_spec = None
    # Use leaf_info to generate argument_spec.
    leaf_infos = get_leafinfos_from_xml_dict(xml_dict, yang_parser, xmlns_info)
    for oper in xml_dict.keys():
        xpath = ""
        if oper == "config" or oper == "rpc":
            schema_spec = _make_config_args(xpath, leaf_infos, list_list)
        else:    # oper == "get" or oper == "get-config"
            schema_spec = _make_get_args(xpath, leaf_infos, key_list, list_list)

    return schema_spec
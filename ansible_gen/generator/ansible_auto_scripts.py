#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import codecs
import shutil
import hashlib
from jinja2 import Environment
from jinja2 import FileSystemLoader
import autopep8


class Operation():
    def __init__(self, **kwargs):

        self.head = kwargs.get("head", None)
        self.leaf_info = kwargs.get("leaf_info", None)
        self.documentation = kwargs.get("documentation", None)
        self.example = kwargs.get("example", None)
        self.namespace = kwargs.get("namespace", None)
        self.xml_tail = kwargs.get("xml_tail", None)
        self.head_content = kwargs.get("head_content", None)
        self.output_file_path = kwargs.get("output_file_path", None)
        self.filename = kwargs.get("filename", None)
        self.argument_spec = kwargs.get("argument_spec", None)
        self.key_list = kwargs.get("key_list", None)
        self.module = kwargs.get("module", None)
        self.user_check_stmts = kwargs.get("user_check_stmts", None)

    def gen_script(self):
        file_name = str(self.filename) + '.py'
        result = os.path.join(self.output_file_path, file_name)
        env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'), 'utf-8'),
                          auto_reload=True)
        template = env.get_template('module.html')
        kwarg = dict(head=self.head,
                     documentation=self.documentation,
                     example=self.example,
                     module=self.module,
                     user_check_stmts=self.user_check_stmts,
                     argument_spec=self.argument_spec,
                     key_list=self.key_list,
                     leaf_info=self.leaf_info,
                     namespaces=self.namespace,
                     xml_head=self.head_content[0] if self.head_content else None,
                     business_tag=self.head_content[1] if self.head_content else None,
                     #comm_module_path=os.path.join(self.output_file_path[1], 'common_module'),
                     message_type=self.head_content[2] if self.head_content else None,
                     xml_tail=self.xml_tail,
                     filename=self.filename,
                     )
        data = template.render(**kwarg)

        # Automatically generate ansible script file
        try:
            if sys.version < '3':
                handle = codecs.open(result, mode="w", encoding="utf-8")
            else:
                handle = open(result, mode="w", encoding="UTF-8")

            handle.writelines(data + '\n')
        except Exception as error:
            logging.error("write script failed: %s", str(error))

    # Main run function
    def run(self):
        # Output ansible automation to generate scripts to the path specified by the user
        logging.info("gen script:%s begin.",str(self.filename)+".py")
        self.gen_script()
        logging.info("gen script:%s end.", str(self.filename) + ".py")
        # Formatting script
        # os.system('autopep8 --in-place --aggressive --aggressive %s.py' %
        #           (os.path.join(self.output_file_path, self.filename)))
        # logging.info("script:%s has been formatted.",str(self.filename) + ".py")


def deploy(output_file_path):
    create_comm_file(output_file_path, get_files())


def get_files():
    file_set = {'checkparams.py',  'ne_base.py', '__init__.py', 'xml_build_with_xmlns.py'}
    path = os.path.dirname(__file__)
    files = {os.path.join(path, file_name) for file_name in file_set}
    return files


def create_comm_file(output_file_path, files):
    if not (output_file_path and files):
        return
    comm_path = os.path.join(output_file_path, 'common_module')
    for file in files:
        if not os.path.exists(comm_path):
            os.mkdir(comm_path)
            shutil.copy(file, comm_path)
        else:
            multi_user_operation(comm_path, file)


def multi_user_operation(comm_path, file):
    file_list = [i for i in os.listdir(comm_path)]
    if os.path.basename(file) in file_list and cmp_md5_value(comm_path, file):
        return
    else:
        shutil.copy(file, comm_path)


def get_tool_file_md5_set(file_path):
    if not file_path:
        return
    temp_set = set()
    try:
        file = open(file_path, 'rb')
        md5_obj = hashlib.md5()
        md5_obj.update(file.read())
        hash_code = md5_obj.hexdigest()
        file.close()
        temp_set.add(hash_code)
        return temp_set
    except IOError as ex:
        sys.stderr.write("error %s: %s\n" % (file_path, str(ex)))


def get_deploy_file_md5_set(output_path, file_path):
    if not (output_path and file_path):
        return
    temp_set = set()
    try:
        for deploy_file in os.listdir(output_path):
            if os.path.basename(file_path) == deploy_file:
                file = open(os.path.join(output_path, deploy_file), 'rb')
                md5_obj = hashlib.md5()
                md5_obj.update(file.read())
                hash_code = md5_obj.hexdigest()
                file.close()
                temp_set.add(hash_code)
        return temp_set
    except IOError as ex:
        sys.stderr.write("error %s: %s\n" % (output_path, str(ex)))



def cmp_md5_value(output_file_path, file):

    tool_md5_value_set = get_tool_file_md5_set(file)
    deploy_md5_value_set = get_deploy_file_md5_set(output_file_path, file)
    if (tool_md5_value_set - deploy_md5_value_set) or (deploy_md5_value_set - tool_md5_value_set):
        return False
    else:
        return True

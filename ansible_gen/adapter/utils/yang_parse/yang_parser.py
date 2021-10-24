#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import math
import logging
import codecs
import re

from . import pyang_util
from .. import base_util



class YangParser():
    """
    tool entrypoint class, for parse yang files use pyang in give yang_dir
    """
    parsed_datas = {}

    def __init__(self, yang_dir, features):
        self.yang_dir = yang_dir
        self.features = features
        self.ctx = pyang_util.init_ctx(yang_dir)

    # get yang files need to be parsed by self.features
    def get_yang_files(self):
        """Get the yang files that need to be parsed.
        Args:
            self.yang_dir: The path of yang file.
            self.features: A set(). Saving the namespace of module that need to be parsed.
        Returns:
            selected_files: The yang files that need to be parsed.
            Traversing yang files under the yang path,if the namespace in self.features,saving this yang file's name to
            selected_files.
        """
        selected_files = dict()
        for yang_file in os.listdir(self.yang_dir):
            try:
                if not os.path.isfile(os.path.join(self.yang_dir, yang_file)) or not yang_file.endswith(".yang"):
                    continue
                if sys.version < '3':
                    handle = codecs.open(os.path.join(self.yang_dir, yang_file), encoding="utf-8")
                else:
                    handle = open(os.path.join(self.yang_dir, yang_file), encoding="UTF-8")
                content = handle.read()
                # remove the remarks from the yang file.(The single line comment follow with code that can not remove)
                remove_comment_content = re.sub(r'\s+//[\s\S]*?\n|/\*{1,2}[\s\S]*?\*/|\s+description\s*"[^"]*?";',
                                                "", content)
                # get the yang module which need to be parsed.
                searchObj = re.search( r'\s+namespace\s+(.*?);', remove_comment_content, re.S)
                if searchObj:
                    xmlns = ""
                    # special scence: namespace "urn:ietf:params:xml:ns:"\n + "yang:ietf-isis-srv6";
                    split_result = searchObj.group(1).strip('"').split('"')
                    for item in split_result[::2]:
                        xmlns += item
                    if xmlns in self.features:
                        selected_files[os.path.splitext(yang_file)[0]] = xmlns

                handle.close()

            except (IOError, UnicodeDecodeError) as e:
                logging.error("parse yang file %s failed: %s", yang_file, e)

        return selected_files

    def parse(self):
        yang_files = self.get_yang_files()
        parser = self.parse_yang_files(yang_files)
        parser.ctx.validate()
        return parser

    def parse_yang_files(self, files):
        """
        We create only one instance to store parsed result. And we avoid of duplicate parse by record the
        yang file we have parsed and skip it in after parse.
        """
        average_progress = 0
        if files:
            completed_progress = 0
            average_progress = int(math.floor((49 - completed_progress) / len(files)))
            if average_progress == 0:
                average_progress = 1
        for yang_file, _ in files.items():
            yang_file += ".yang"
            logging.info("parse yang file %s", yang_file)
            path = os.path.join(self.yang_dir, yang_file)
            pyang_util.parse_yang_module(path, self.ctx)
            # progress_bar
            completed_progress += average_progress
            if completed_progress > 49:
                completed_progress = 49
            process_message = " {0} parse Completed.".format(yang_file)
            base_util.print_progress_bar(completed_progress, process_message)

        # modules = {}
        # main_yangs = [os.path.splitext(base_name)[0]
        #               for base_name in files.keys()]
        #
        # if self.ctx.modules:
        #     for t, stmt in self.ctx.modules.items():
        #         if t[0] in main_yangs:
        #             modules[(files[t[0]], t[0], t[1])] = stmt
        #         else:
        #             modules[(None, t[0], t[1])] = stmt
        #
        # self.ctx.modules = modules

        return self

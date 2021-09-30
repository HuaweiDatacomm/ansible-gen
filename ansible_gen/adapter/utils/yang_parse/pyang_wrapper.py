#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pyang_wrapper.py docstrings.
This module invoke mpyang.
"""
import re
import logging
import os
import io

from pyang.repository import FileRepository
from pyang.context import Context

class MockOpts:
    """
    MockOpts class.
    """
    def __init__(self):
        self.format = 'yang'
        self.yang_remove_unused_imports = False
        self.yang_canonical = True
        self.yin_canonical = True
        self.trim_yin = False
        self.yin_pretty_strings = True
        self.outfile = None
        self.xx = 0


def init_ctx(yang_dir):
    """
    init_ctx.
    """
    path = yang_dir
    repos = FileRepository(path)
    ctx = Context(repos)
    opts = MockOpts()
    ctx.opts = opts
    ctx.trim_yin = opts.trim_yin
    return ctx


class YangContext:
    """
    YangContext class.
    """
    def __init__(self, yang_dir):
        self.ctx = None
        self.files = set()
        try:
            self.ctx = init_ctx(yang_dir)
        except Exception:
            logging.error("get_module_context_pieces error")

    def parse_yang_module(self, filename):
        """
        parse_yang_module.
        """
        ctx = self.ctx
        in_base_name = os.path.basename(filename)
        if in_base_name in self.files:
            logging.info(
                "%s has been parsed, no need parse again", in_base_name)
        file_open = None
        yang_file_regular = re.compile(r"^(.*?)(\@(\d{4}-\d{2}-\d{2}))?\.(yang|yin)$")
        try:
            file_open = io.open(filename, "r", encoding="utf-8")
            text = file_open.read()
            yang_file = yang_file_regular.search(filename)
            ctx.yin_module_map = {}
            if yang_file is not None:
                (name, _dummy, rev, format) = yang_file.groups()
                name = os.path.basename(name)
                ctx.add_module(filename, text, format, name, rev,
                               expect_failure_error=False)
            else:
                ctx.add_module(filename, text)
        except Exception:
            logging.error("can not open the file %s" % filename)
        finally:
            if file_open is not None:
                file_open.close()
            if ctx.modules:
                self.files = self.files | set(
                    [t[0] for t in ctx.modules.keys()])

import logging
import os
import traceback
import re
import sys
from pyang.context import Context
from pyang.repository import FileRepository
import pyang

def init_ctx(path='./yang'):
    repos = FileRepository(path)
    ctx = Context(repos)
    return ctx


def parse_yang_module(yang_file_path, ctx):
    r = re.compile(r"^(.*?)(\@(\d{4}-\d{2}-\d{2}))?\.(yang|yin)$")
    try:
        with open(yang_file_path, "r", encoding="UTF-8") as fd:
            text = fd.read()
            m = r.search(yang_file_path)
            ctx.yin_module_map = {}
            if m is not None:
                (name, _dummy, rev, format) = m.groups()
                name = os.path.basename(name)
                ctx.add_module(yang_file_path, text, format, name, rev)
            else:
                ctx.add_module(yang_file_path, text)
    except Exception:
        yang_error_write("can not open the file %s" % yang_file_path)

    logging.info('parse yang module %s success!', yang_file_path)
    return ctx

def parse_yang_modules(yang_directory, ctx):
    if os.path.isfile(yang_directory):
        parse_yang_module(yang_directory, ctx)
    else:
        for yang_file in sorted(os.listdir(yang_directory)):
            yang_file_path = os.path.join(yang_directory, yang_file)
            if os.path.isdir(yang_file_path):
                parse_yang_modules(yang_file_path, ctx)
            parse_yang_module(yang_file_path, ctx)
    ctx.validate()
    return ctx

def get_module_namespace(main_module):
    for stmt in main_module.substmts:
        if stmt.keyword == 'namespace':
            return stmt.arg
    return None
def is_filter(node):
    if not node.keyword == 'leaf':
        return True
    if hasattr(node,'i_is_key'):
        if node.i_is_key:
            return True
    for sub_stmt in node.substmts:
        if hasattr(sub_stmt,'i_extension'):
            if sub_stmt.keyword == ('huawei-extension', 'support-filter'):
                return True

    return False
def yang_module_has_error(ctx,module_name=None):
    for p,t,a in ctx.errors:
        if module_name is None:
            if is_error(t):
                return True
        else:
            if (is_error(t) and check_error_if_need(p, module_name)):
                return True

    return False

def check_error_if_need(pos, module_name):
    yang_error_name = ''
    try:
        yang_error_name = pos.top.arg
    except:
        pass
    if yang_error_name == module_name:
        return True
    return False

def is_error(error_type):
    error_level = pyang.error.err_level(error_type)
    if pyang.error.is_error(error_level):
        return True
    else:
        return False
def print_yang_errors(ctx, module_name=None):
    for p, t, a in ctx.errors:
        error_str = None
        error_level = pyang.error.err_level(t)
        if pyang.error.is_error(error_level):
            error_level_str = "Error"
        else:
            error_level_str = "Warning"
        if module_name is not None:
            if is_error(t) and check_error_if_need(p, module_name):
                error_str = ''.join([p.label(), " ", error_level_str,': ',pyang.error.err_to_str(t, a)])
        else:
            error_str = ''.join([p.label(), " ", error_level_str,': ',pyang.error.err_to_str(t, a)])
        if error_str is not None:
            print(error_str)
            yang_error_write(error_str)
    return

def yang_error_write(error_string):
    exc_info = sys.exc_info()
    exc_value = exc_info[1]

    if exc_value and traceback.format_exc().strip() != 'None':
        logging.error(traceback.format_exc())
    logging.error("%s",error_string)
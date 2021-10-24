#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import codecs
import traceback
import logging
import shutil
import math
from optparse import OptionParser
from adapter import get_argument_spec_documentation as get_parser
from generator import var, ansible_auto_scripts as script_gen
from generator.move_file import *
from adapter.utils import base_util

if not sys.version > '3':
    import ConfigParser as configparser

    reload(sys)
    sys.setdefaultencoding('utf-8')
else:
    import configparser


USAGE = "Dynamically generate Ansible modules from yang and xml files, then deploy Ansible module"
__version__ = "0.5.0"

SCRIPT_GEN_LOG_FILE = "ansible_gen.log"
BASE_ERROR = r"##########ANSIBLE_GEN_ERROR_START##########"
END_ERROR = r"###########ANSIBLE_GEN_ERROR_END###########"
START_WARNING = r"##########USER_OPERATION_WARNING_START##########"
END_WARNING = r"###########USER_OPERATION_WARNING_END###########"
GENERATE_SCRIPT_MESSAGE = ""
SCRIPT_DIR_GLOBAL = ""

def parse_error_and_exit(filename):
    """Extract the error information from "ansible_gen.log".
    Args:
        filename: The path of "ansible_gen.log".
    """
    ret_val = 0
    handle = None
    try:
        handle = codecs.open(filename, encoding="utf-8")
        log_context = handle.read()
        findre = re.compile(r"%s.*?%s" % (BASE_ERROR, END_ERROR), re.DOTALL)
        error_list = findre.findall(log_context)
        warning_obj = re.compile(r"%s.*?%s" % (START_WARNING, END_WARNING), re.DOTALL)
        warning_list = warning_obj.findall(log_context)
        if error_list:
            print("Ansible-gen Execute Failed.")
            ret_val = 1
            for error_str in set(error_list):
                print(error_str)
        else:
            print("Ansible-gen Execute Success.")
        if warning_list:
            for operation_warning_str in set(warning_list):
                print(operation_warning_str)
    except Exception:
        ret_val = 1
    finally:
        if handle is not None:
            handle.close()
        sys.exit(ret_val)


def fill_args_from_cfg_file(args, options):
    """Config the OptionParser instance by default.cfg file.
    Args:
        args: The list record arguments.
        options: The instance record user input.
    """
    user_cfg_file = args[0] if args else ""
    default_cfg_file = os.path.join("/etc/ansible-gen/default.cfg")
    if options.default is not None:
        cfg_file = default_cfg_file
    else:
        cfg_file = user_cfg_file if user_cfg_file else default_cfg_file
    if not os.path.isfile(cfg_file):
        return
    cfg_info = configparser.ConfigParser()
    cfg_info.read(cfg_file)

    for name in ["yang_dir", "xml_dir", "log_dir", "script_dir"]:
        if not getattr(options, name):
            if cfg_info.has_option("defaults", name):
                setattr(options, name, cfg_info.get("defaults", name))
    if cfg_info.has_option("defaults", "log_level"):
        setattr(options, "log_level", cfg_info.get("defaults", "log_level"))
    else:
        options.log_level = "DEBUG"


def prepare_parser():
    """Get the parser default value.
    Returns:
        parser: OptionParser instance.
    """
    # if user dosn't give andy command line options, add -h manually
    if not sys.argv[1:]:
        sys.argv.append("-h")

    parser = OptionParser(description=USAGE, epilog="Ansible-gen {}".format(__version__))
    parser.add_option("-v", "--version", dest="version", default='',
                      action='store_true', help="version number info for program")

    return parser


def parse_args():
    """Parse the user input.
    Returns:
        options: The instance record user input.
        args: The list record arguments.
    """
    parser = prepare_parser()

    parser.add_option("-y", "--yang_dir", dest="yang_dir", default='',
                      help="the directory of yang_files.")
    parser.add_option("-r", "--resource", dest="xml_dir", default='',
                      help="the directory of xml files which contains netconf rpc message.")
    parser.add_option("-p", "--script", dest="script_dir", default='',
                      help="the directory of previous generated ansible module which may has user define"
                           " check implementation.")
    parser.add_option("-l", "--log", dest="log_dir", default='',
                      help="the log directory, name of log is ansible_gen.log")
    parser.add_option("-o", "--output", dest="output_dir", default='',
                      help="the output dir for generated scripts")
    parser.add_option("--default", dest="default", default='', action='store_true',
                      help="get parameters from default config file /etc/ansible-gen/default.cfg")

    (options, args) = parser.parse_args()

    if options.version:
        print("ansible-gen", __version__)
        sys.exit()

    fill_args_from_cfg_file(args, options)

    log_file_name = os.path.join(options.log_dir, SCRIPT_GEN_LOG_FILE)

    if os.path.isfile(log_file_name):
        os.remove(log_file_name)
    if hasattr(options, "log_level"):
        log_level = options.log_level
    else:
        log_level = "DEBUG"

    logging.basicConfig(filename=log_file_name,
                        format='%(asctime)s,%(levelname)s,%(filename)s,%(lineno)d:%(message)s',
                        level=log_level)

    return options, args


def env_parse():
    """Get user input from the command line.
    Returns:
        options: The instance record user input.
    """
    (options, args) = parse_args()

    for name in ["yang_dir", "xml_dir", "log_dir"]:
        if not os.path.isdir(getattr(options, name)):
            sys.stderr.write("[0x000001] : %s %s doesn't exists or not designated" % (
                name, getattr(options, name)))
            sys.exit(1)

    if options.script_dir and not os.path.isdir(options.script_dir):
        sys.stderr.write(
            "[0x000001] : previous script directory  %s doesn't exists or not designated" % options.script_dir)
        sys.exit(1)
    logging.info(
        "==============================START SCRIPT GENERATIONS=========================================")

    logging.info("option is: \nyang_directory:%s\n"
                 "xml_directory:%s\n"
                 "log_directory:%s",
                 os.path.abspath(options.yang_dir),
                 os.path.abspath(options.xml_dir),
                 os.path.abspath(options.log_dir))
    return options


def get_number_of_para_xml(xml_dir):
    """Get the number of "xxx_full.xml" under xml_dir path(recursive function).
    Args:
        xml_dir: Parser form command line -r.
    Returns:
        full_number: The number of "xxx_full.xml" under xml_dir path.
    """
    full_number = 0
    xml_files = os.listdir(xml_dir)
    for xml_file in xml_files:
        path = os.path.join(xml_dir, xml_file)
        if os.path.isdir(path):
            full_number += get_number_of_para_xml(path)
        else:
            if os.path.isfile(path) and not xml_file.endswith("_example.xml"):
                full_number = full_number + 1
    return full_number


def generate_netconf_script(xml_dir, output_dir, script_dir, direct_sub, completed_progress,
                            average_remaining_progress):
    """Generate netconf script(recursive function).
    Args:
        xml_dir: Parser form command line -r.
        output_dir: Script output path.
        script_dir: Parser form command line -p.
        direct_sub: Indicates whether it is a direct sub directory.
        completed_progress: Record the completed progress.
        average_remaining_progress: Add progress.
    Returns:
        completed_progress: Record the completed progress.
    Raises:
        Exception: Capture execution exception.
    """
    global GENERATE_SCRIPT_MESSAGE
    try:
        xml_files = os.listdir(xml_dir)
        for xml_file in xml_files:
            path = os.path.join(xml_dir, xml_file)
            if os.path.isdir(path):
                sub_xml_dir = os.path.join(xml_dir, xml_file)
                if direct_sub:
                    sub_output_dir = os.path.join(output_dir, xml_file)
                    if os.path.exists(sub_output_dir):
                        shutil.rmtree(sub_output_dir)
                        logging.warning(
                            "sub directory %s removed", sub_output_dir)
                    os.makedirs(sub_output_dir)
                    if script_dir:
                        script_dir = os.path.join(SCRIPT_DIR_GLOBAL, xml_file)
                    if script_dir and not os.path.isdir(script_dir):
                        logging.warning(
                            "no corresponding direcotory %s ", script_dir)
                else:
                    sub_output_dir = output_dir
                completed_progress = generate_netconf_script(sub_xml_dir, sub_output_dir, script_dir, False,
                                                                 completed_progress, average_remaining_progress)
            else:
                script_name = os.path.basename(xml_dir)
                if os.path.isfile(path) and xml_file.endswith(".xml") and not xml_file.endswith('_example.xml'):
                    logging.info("parse para file %s ", xml_file)
                    kwargs = var.get_params(
                        path, script_name, output_dir, script_dir)
                    if kwargs:
                        script_gen.Operation(**kwargs).run()
                    # progress_bar
                    completed_progress += average_remaining_progress
                    if completed_progress > 99:
                        completed_progress = 99
                    process_message = " {0} generated.".format(script_name)
                    base_util.print_progress_bar(completed_progress, process_message)
                    script_path = os.path.join(output_dir, script_name+'.py')
                    if os.path.exists(script_path):
                        GENERATE_SCRIPT_MESSAGE += "\nThe generated script has been saved to the path:{0}"\
                            .format(script_path)
                    else:
                        msg = "\n" + script_path + ". Cannot be generated."
                        base_util.error_write(msg)
    except Exception as error:
        logging.error("generate_netconf_script failed: %s",
                      traceback.format_exc())
    finally:
        return completed_progress


def main():
    """Main function.
    Raises:
        KeyboardInterrupt: Exit progress by keyboard:[ Ctrl + c ].
    """
    options = None
    try:
        options = env_parse()

        # Automatically deploy
        # if get_ansible_path():
        #     deploy(get_ansible_path()[1])
        xml_num = get_number_of_para_xml(options.xml_dir)
        if xml_num:
            get_parser.get_yang_handlers(options.yang_dir, options.xml_dir)
            # progress_bar
            completed_progress = 50
            process_message = " Yang Parser Completed."
            base_util.print_progress_bar(completed_progress, process_message)
            average_remaining_progress = int(math.floor((99 - completed_progress) / xml_num))
            if average_remaining_progress == 0:
                average_remaining_progress = 1
            output_dir = options.output_dir
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            if options.script_dir:
                global SCRIPT_DIR_GLOBAL
                SCRIPT_DIR_GLOBAL = options.script_dir
            generate_netconf_script(options.xml_dir, output_dir, options.script_dir, True, completed_progress,
                                    average_remaining_progress)
            logging.info(
                "==============================FINISH SCRIPT GENERATION==============================")
            process_message = " Finish Script Generation."
            base_util.print_progress_bar(100, process_message)
            sys.stdout.write(GENERATE_SCRIPT_MESSAGE+'\n')
            sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    except Exception:
        logging.error("ANSIBLE GEN ERROR !")
        sys.stderr.write("[0x000000]Ansible Gen ERROR \n!")
        traceback.print_exc()
        logging.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if options is not None:
            parse_error_and_exit(os.path.join(
                options.log_dir, SCRIPT_GEN_LOG_FILE))


if __name__ == "__main__":
    main()

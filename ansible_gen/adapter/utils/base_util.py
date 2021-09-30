import os
import sys
import logging
import traceback
if sys.version < '3':
    import Queue


START_ERROR = "\n##########ANSIBLE_GEN_ERROR_START##########\n"
END_ERROR = "\n###########ANSIBLE_GEN_ERROR_END###########"
START_OPERATION_WARNING = "\n##########USER_OPERATION_WARNING_START##########\n"
END_OPERATION_WARNING = "\n###########USER_OPERATION_WARNING_END###########"
OLD_PROCESS_MESSAGE_LEN = 0


def error_write(error_string):
    """Write the error message into log file.
    Args:
        error_string: The error message.
    """
    exc_info = sys.exc_info()
    exc_value = exc_info[1]
    if sys.version < '3':
        if type(exc_value) == Queue.Empty:
            exc_value = None

    if exc_value and traceback.format_exc().strip() != 'None':
        logging.error(traceback.format_exc())
    logging.error("%s%s%s" % (START_ERROR, error_string, END_ERROR))


def operation_warning_write(operation_warning_string):
    """Write the warning message into log file.
    Args:
        operation_warning_string: The warning message.
    """
    logging.error("%s%s%s" % (START_OPERATION_WARNING, operation_warning_string, END_OPERATION_WARNING))


def xml_structure_except(exception_object, file_path):
    file_name = os.path.basename(file_path)
    syntax_msg_str = ""
    for item in exception_object.args:
        syntax_msg_str = "\n " + syntax_msg_str + str(item)
    if not file_path.endswith("_example.xml"):
        script_name = ""
        if file_path.split(os.sep)[-2]:
            script_name = file_path.split(os.sep)[-2]
        error_msg = "Script of %s.py can not be generated,because the structure of xml is incorrect." \
                  "\nPlease check the file %s:" % (script_name, file_path) \
                  + syntax_msg_str
        error_write(error_msg)
    else:
        warning_msg = "EXAMPLE of %s can not be generated,because the structure of xml is incorrect." \
                  "\nPlease check the file %s:" % (file_name, file_path) \
                  + syntax_msg_str
        operation_warning_write(warning_msg)


def print_progress_bar(completed_progress, process_message):
    """Print current progress and prompt message.
    Args:
        completed_progress: The value of current progress.
        process_message: The prompt message.
    """
    global OLD_PROCESS_MESSAGE_LEN
    space_len = 0
    if OLD_PROCESS_MESSAGE_LEN > len(process_message):
        space_len = OLD_PROCESS_MESSAGE_LEN - len(process_message)
    process_bar = "Process:{0}% |{1}|".format(str(completed_progress),
                                              str(int(completed_progress) * '=' + int(100 - completed_progress) * '-'))
    sys.stdout.write(u'\r')
    if sys.version < '3':
        sys.stdout.write(process_bar.decode("utf-8") + process_message.decode('utf-8') + str(space_len * ' '))
    else:
        sys.stdout.write(process_bar + process_message + str(space_len * ' '))
    sys.stdout.flush()
    OLD_PROCESS_MESSAGE_LEN = len(process_message)

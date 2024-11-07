import sys

import logging

# Create a logger object
logger = logging.getLogger('my_logger')

# Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger.setLevel(logging.DEBUG)

# Create a file handler that logs even debug messages
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# Log some messages
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')


def trace_calls(frame, event, arg):
    if event != 'call':
        return
    co = frame.f_code
    func_name = co.co_name
    func_line_no = frame.f_lineno
    func_filename = co.co_filename
    
    if func_name == 'write':  # 忽略内置的 write 函数
        return
    if 'python3.10' in func_filename:
        return
    if 'python3.8' in func_filename:
        return

    logger.info(f'Call to {func_name} on line {func_line_no} of {func_filename}')
    return

def trace_lines(frame, event, arg):
    if event != 'line':
        return
    co = frame.f_code
    func_name = co.co_name
    line_no = frame.f_lineno
    logger.info(f'{func_name}: {line_no}')


def set_trace():
    sys.settrace(trace_calls)


def reset_trace():
    sys.settrace(None)
    
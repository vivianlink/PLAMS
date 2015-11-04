#!/usr/bin/env python

import os
import sys
import argparse
import threading
import traceback

_X_parser = argparse.ArgumentParser(description='PLAMS environment execution tool (master script)')
_X_parser.add_argument('-p', type=str, default=None, help='place where the main working folder is created', metavar='path')
_X_parser.add_argument('-f', type=str, default=None, help='name of the main working folder', metavar='name')
_X_parser.add_argument('-v', action='append', type=str, default=[], help="Declare a variable 'var' with a value 'value' in the global namespace. Multiple variables can be set this way, but each one requires separate '-v'", metavar='var=value')
_X_parser.add_argument('file', nargs='+', type=str, help='file with PLAMS script')
_X_args = _X_parser.parse_args()

#add -v variables to the global namespace
for _X_pair in _X_args.v:
    if '=' in _X_pair:
        var, val = _X_pair.split('=')
        globals()[var] = val

#read and concatenate input file(s)
_X_input = ''
for _X_input_file in _X_args.file:
    if os.path.isfile(_X_input_file):
        with open(_X_input_file, 'r') as f:
            _X_input += f.read()
    else:
        print('Error: File %s not found'%_X_input_file)
        sys.exit(1)



from scm.plams import *

#normpath prevents crash when f ends with slash
init(path=_X_args.p, folder=(os.path.normpath(_X_args.f) if _X_args.f else None))

with open(config.jm.input, 'w') as f:
    f.write(_X_input)
with open(config.jm.restart, 'w') as f:
    f.write(_X_input)

try:
    exec(compile(open(config.jm.input).read(), config.jm.input, 'exec'))
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    tb = traceback.extract_tb(exc_tb)
    fname, lineno, fn, text = tb[-1]
    err_msg = 'Execution interrupted by the following exception:\n'
    err_msg += '%s: %s\n' % (exc_type.__name__, str(e))
    err_msg += 'File: %s\n' % os.path.basename(fname)
    err_msg += 'Line %i: %s\n\n' % (lineno, text)
    err_msg += '==============Full traceback========================'
    for fname, lineno, fn, text in tb:
        err_msg += '\nFile: %s' % os.path.basename(fname)
        err_msg += '\nLine %i: %s' % (lineno, text)
        err_msg += '\n----------------------------------------------------'
    log(err_msg)

finish()

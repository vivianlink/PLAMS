#!/usr/bin/env python

from scm.plams import *

plams_namespace = globals().copy()

import os
import sys
import argparse
import traceback

_X_parser = argparse.ArgumentParser(description='PLAMS environment restart tool')
_X_parser.add_argument('-v', action='append', type=str, default=[], help="Declare a variable 'var' with a value 'value' in the global namespace. Multiple variables can be set this way, but each one requires separate '-v'", metavar='var=value')
_X_parser.add_argument('folder', nargs=1, type=str, help='the main working folder of the script to restart')
_X_args = _X_parser.parse_args()

#add -v variables to the plams_namespace
for _X_pair in _X_args.v:
    if '=' in _X_pair:
        var, val = _X_pair.split('=')
        plams_namespace[var] = val

#check folder and file
_X_folder = _X_args.folder[0]
if os.path.isdir(_X_folder):
    _X_folder = os.path.abspath(_X_folder)
    _X_path, _X_name = os.path.split(_X_folder)
    _X_restart_file = os.path.join(_X_folder, _X_name+'.res')
    if os.path.isfile(_X_restart_file):
        with open(_X_restart_file, 'r') as f:
            _X_input = f.read()
    else:
        print('Error: Folder %s does not contain %s.res file'%(_X_folder, _X_name))
        sys.exit(1)
else:
    print('Error: Folder %s not found'%_X_folder)
    sys.exit(1)

#modify the name
def _X_restartname(name):
    lst = name.split('.')
    if len(lst) > 1 and lst[-1].startswith('res') and lst[-1][3:].isdigit():
        n = int(lst[-1][3:])
        lst[-1] = 'res' + str(n+1)
        return '.'.join(lst)
    return name + '.res1'
_X_name = _X_restartname(_X_name)



init(path=_X_path, folder=_X_name)
load_all(_X_folder)

with open(config.jm.input, 'w') as f:
    f.write(_X_input)
with open(config.jm.restart, 'w') as f:
    f.write(_X_input)

try:
    exec(compile(open(config.jm.input).read(), config.jm.input, 'exec'), plams_namespace)
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

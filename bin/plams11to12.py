#!/usr/bin/env python

#Replaces v1.1 imports with correct v1.2 module names
#Replacement is done in place (files supplied as arguments will be modified!)
#Every change is logged to the standard output
#Usage: plams11to12.py file1 [file2 file3 ...]

import os, sys

rename = {
'plams.basejob'     :'plams.core.basejob',
'plams.basemol'     :'plams.core.basemol',
'plams.common'      :'plams.core.common',
'plams.errors'      :'plams.core.errors',
'plams.jobrunner'   :'plams.core.jobrunner',
'plams.jobmanager'  :'plams.core.jobmanager',
'plams.results'     :'plams.core.results',
'plams.settings'    :'plams.core.settings',
'plams.kftools'     :'plams.tools.kftools',
'plams.numdiff'     :'plams.tools.numdiff',
'plams.pdbtools'    :'plams.tools.pdbtools',
'plams.utils'       :'plams.tools.utils',
'plams.scmjob'      :'plams.interfaces.adfsuite',
'plams.cp2kjob'     :'plams.interfaces.cp2k',
'plams.diracjob'    :'plams.interfaces.dirac',
'plams.gamessjob'   :'plams.interfaces.gamess',
'plams.orcajob'     :'plams.interfaces.orca'
}

for arg in sys.argv[1:]:
    if os.path.isfile(arg):
        with open(arg, 'r') as f:
            old = f.readlines()
        new = []
        for i,line in enumerate(old):
            for k,v in rename.items():
                if k in line:
                    line = line.replace(k,v)
                    print('%s line %i: %s -> %s'%(arg,i+1,k,v))
            new.append(line)
        with open(arg, 'w') as f:
            f.writelines(new)

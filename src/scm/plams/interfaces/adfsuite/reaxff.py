import numpy
import os
import shutil

from os.path import join as opj

from ...core.basejob import SingleJob
from ...core.errors import FileError
from ...core.settings import Settings
from ...tools.units import Units
from .scmjob import SCMResults
from .scmjob import SCMJob, SCMResults

__all__ = ['ReaxFFJob', 'ReaxFFResults', 'load_reaxff_control']

class ReaxFFResults(SCMResults):
    _rename_map = {'reaxout.kf':'$JN.kf'}
    _kfext = '.kf'

    def _int2inp(self):
        return list(range(1, 1+len(self.job.molecule)))


class ReaxFFJob(SingleJob):
    _filenames = {'inp':'control', 'run':'$JN.run', 'out':'$JN.out', 'err': '$JN.err'}
    _result_type = ReaxFFResults
    ffield_path = opj('$ADFHOME','atomicdata','ForceFields','ReaxFF')
    check = SCMJob.check


    def __init__(self, **kwargs):
        SingleJob.__init__(self, **kwargs)
        self.settings.keep = ['$JN.*', 'geo', 'control', 'ffield']

    def get_input(self):
        s = self.settings.input.control
        ret = ''
        order = s._order if '_order' in s else iter(s)
        for key in order:
            ret += '{:>7} {:6}\n'.format(s[key], key)
        return ret


    def get_runscript(self):
        s = self.settings.runscript
        ret = ''
        if 'nproc' in s:
            ret += 'export NSCM={}\n'.format(s.nproc)
        ret += '$ADFBIN/reaxff'
        if s.stdout_redirect:
            ret += ' >'+self._filename('out')
        ret += '\n\n'
        return ret


    def _get_ready(self):
        SingleJob._get_ready(self)

        ffield = self.settings.input.ffield
        if os.path.isfile(ffield):
            shutil.copy(ffield, opj(self.path, 'ffield'))
        else:
            path = os.path.expandvars(opj(self.ffield_path, ffield))
            if os.path.isfile(path):
                shutil.copy(path, opj(self.path, 'ffield'))
            else:
                raise FileError('settings.input.ffield={} is neither a path to a file nor an existing force field from {}'.format(ffield, self.ffield_path))

        geo = self.settings.input.geo
        if isinstance(geo, str) and os.path.isfile(geo):
            shutil.copy(geo, opj(self.path, 'geo'))
        else:
            header = ['BIOGRF 200\n']

            descrp = geo.find_case('descrp')
            if descrp not in geo:
                geo.descrp = self.name

            for key, val in geo.items():
                if isinstance(val, list):
                    for el in val:
                        header.append('{:6} {}\n'.format(key.upper(), el))
                else:
                    header.append('{:6} {}\n'.format(key.upper(), val))


            self.molecule = self._align_lattice(self.molecule)

            header.append('CRYSTX  {:10.5f} {:10.5f} {:10.5f} {:10.5f} {:10.5f} {:10.5f}\n'.format(*self._convert_lattice(self.molecule.lattice)))

            atoms = []
            for i,at in enumerate(self.molecule):
                newline = 'HETATM {:>5d} {:<2}                 {: 8.5f}  {: 8.5f}  {: 8.5f} {:<2}     1 1  0.0\n'.format(i+1, at.symbol, *at.coords, at.symbol)
                atoms.append(newline)
            atoms.append('END\n')

            with open(opj(self.path,'geo'), 'w') as f:
                f.writelines(header)
                f.writelines(atoms)


    @staticmethod
    def _align_lattice(molecule):
        molecule.lattice = [[100,0,0],[0,100,0],[0,0,100]]
        return molecule


    @staticmethod
    def _convert_lattice(lattice):
        a, b, c = map(numpy.linalg.norm, lattice)
        al = numpy.dot(lattice[1], lattice[2])/(b*c)
        be = numpy.dot(lattice[0], lattice[2])/(a*c)
        ga = numpy.dot(lattice[0], lattice[1])/(a*b)
        al,be,ga = map(lambda x: Units.convert(numpy.arccos(x),'rad','deg'), [al,be,ga])
        return a, b, c, al, be, ga




def load_reaxff_control(filename, keep_order=True):
    if os.path.isfile(filename):
        filename = os.path.abspath(filename)
    else:
        raise FileError('No such file: {}'.format(filename))

    with open(filename, 'r') as f:
        lines = f.readlines()

    ret = Settings()
    if keep_order:
        ret._order = []

    for line in lines:
        if line.lstrip().startswith('#'):
            continue
        tmp = line.split()
        if len(tmp) > 1:
            value, key = tmp[:2]
            if len(key) > 6:
                log("load_reaxff_control: I am confused by this line:\n{}\nAre you sure {} is correct?".format(line, key), 3)
            if not value.replace('.','', 1).isdigit():
                 log("load_reaxff_control: I am confused by this line:\n{}\nAre you sure {} is correct?".format(line, value), 3)
            try:
                value = float(value) if '.' in value else int(value)
            except:
                pass
            ret[key] = value
            if keep_order:
               ret._order.append(key)
    return ret


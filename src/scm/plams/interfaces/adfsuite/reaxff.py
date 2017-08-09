import numpy
import os
import shutil

from os.path import join as opj

from ...core.basejob import SingleJob
from ...core.errors import FileError
from ...core.settings import Settings
from ...tools.units import Units
from ...tools.geometry import rotation_matrix
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
    default_cell_size = 100.0

    check = SCMJob.check


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
        self._write_ffield(self.settings.input.ffield)
        self._write_geofile(molecule=self.molecule, filename='geo', settings=self.settings.input.geo, description=self.name, lattice=True)

        if 'external' in self.settings.input:
            ext = self.settings.input.external
            if isinstance(ext, list):
                for val in ext:
                    if os.path.isfile(val):
                        shutil.copy(val, self.path)
                    else:
                        raise FileError('File {} not present'.format(val))
            elif isinstance(ext, dict):
                for key, val in ext.items():
                    if os.path.isfile(val):
                        shutil.copy(val, opj(self.path, key))
                    else:
                        raise FileError('File {} not present'.format(val))



    def _write_ffield(self, ffield):
        if os.path.isfile(ffield):
            shutil.copy(ffield, opj(self.path, 'ffield'))
        else:
            path = os.path.expandvars(opj(self.ffield_path, ffield))
            if os.path.isfile(path):
                shutil.copy(path, opj(self.path, 'ffield'))
            else:
                raise FileError('settings.input.ffield={} is neither a path to a file nor an existing force field from {}'.format(ffield, self.ffield_path))



    def _write_geofile(self, molecule, filename, settings, description, lattice=False):
        if isinstance(settings, str) and os.path.isfile(settings):
            shutil.copy(settings, opj(self.path, filename))
        else:
            header = ['BIOGRF 200\n']

            descrp = settings.find_case('descrp')
            if descrp not in settings:
                settings.descrp = description

            for key in settings:
                val = settings[key]
                if isinstance(val, list):
                    for el in val:
                        header.append('{:6} {}\n'.format(key.upper(), el))
                elif isinstance(val, tuple):
                    header.append(('{:6} '+'{} '*len(val)+'\n').format(key.upper(), *val))
                else:
                    header.append('{:6} {}\n'.format(key.upper(), val))
            if lattice:
                self._align_lattice(molecule, self.default_cell_size)
                header.append('CRYSTX  {:10.5f} {:10.5f} {:10.5f} {:10.5f} {:10.5f} {:10.5f}\n'.format(*self._convert_lattice(molecule.lattice)))

            atoms = []
            for i,at in enumerate(molecule):
                newline = 'HETATM {:>5d} {:<2}                 {: 8.5f}  {: 8.5f}  {: 8.5f} {:<2}     1 1  0.0\n'.format(i+1, at.symbol, *at.coords, at.symbol)
                atoms.append(newline)
            atoms.append('END\n')

            with open(opj(self.path, filename), 'w') as f:
                f.writelines(header)
                f.writelines(atoms)



    @staticmethod
    def _align_lattice(molecule, default_len):
        lattice = molecule.lattice
        dim = len(lattice)

        if dim >= 1 and (abs(lattice[0][1]) > 1e-10 or abs(lattice[0][2]) > 1e-10):
            mat = rotation_matrix(lattice[0], [1.0, 0.0, 0.0])
            molecule.rotate(mat)
            lattice = [tuple(numpy.dot(mat,i)) for i in lattice]

        if dim >= 2 and abs(lattice[1][2]) > 1e-10:
            mat = rotation_matrix([0.0, lattice[1][1], lattice[1][2]], [0.0, 1.0, 0.0])
            molecule.rotate(mat)
            lattice = [numpy.dot(mat,i) for i in lattice]

        f = lambda x: [default_len * int(i==x) for i in range(3)]
        while len(lattice) < 3:
            lattice.append(f(len(lattice)))

        molecule.lattice = lattice



    @staticmethod
    def _convert_lattice(lattice):
        a, b, c = map(numpy.linalg.norm, lattice)
        al = numpy.dot(lattice[1], lattice[2])/(b*c)
        be = numpy.dot(lattice[0], lattice[2])/(a*c)
        ga = numpy.dot(lattice[0], lattice[1])/(a*b)
        al,be,ga = map(lambda x: Units.convert(numpy.arccos(x),'rad','deg'), [al,be,ga])
        return a, b, c, al, be, ga


#===========================================================================


def load_reaxff_control(filename, keep_order=True):

    if not os.path.isfile(filename):
        raise FileError('File {} not present'.format(filename))

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


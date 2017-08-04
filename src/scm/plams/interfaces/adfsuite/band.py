from .scmjob import SCMJob, SCMResults

__all__ = ['BANDJob', 'BANDResults']


class BANDResults(SCMResults):
    _kfext = '.runkf'
    _rename_map = {'RUNKF':'$JN'+_kfext}

    def _int2inp(self):
        return self.readkf('geometry', 'Atom map new order')


class BANDJob(SCMJob):
    _result_type = BANDResults
    _command = 'band'

    def _parsemol(self):
        s = self.settings.input
        units = s.find_case('units')
        length = s[units].find_case('length')
        s[units][length] = 'angstrom'

        for i,atom in enumerate(self.molecule):
            s.atoms['_'+str(i+1)] = atom.str(symbol=self._atom_symbol(atom), space=18, decimal=10)

        if self.molecule.lattice:
            for i,vec in enumerate(self.molecule.lattice):
                s.lattice['_'+str(i+1)] = '{:16.10f} {:16.10f} {:16.10f}'.format(*vec)

    def _removemol(self):
        if 'atoms' in self.settings.input:
            del self.settings.input.atoms
        if 'lattice' in self.settings.input:
            del self.settings.input.lattice
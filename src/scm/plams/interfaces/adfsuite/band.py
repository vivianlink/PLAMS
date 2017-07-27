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
        for i,atom in enumerate(self.molecule):
            self.settings.input.atoms['_'+str(i+1)] = atom.str(symbol=self._atom_symbol(atom), space=18, decimal=10)

        if self.molecule.lattice:
            for i,vec in enumerate(self.molecule.lattice):
                self.settings.input.lattice['_'+str(i+1)] = '%16.10f %16.10f %16.10f'%vec

    def _removemol(self):
        if 'atoms' in self.settings.input:
            del self.settings.input.atoms
        if 'lattice' in self.settings.input:
            del self.settings.input.lattice
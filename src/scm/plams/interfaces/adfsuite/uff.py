from .scmjob import SCMJob, SCMResults

class UFFResults(SCMResults):
    _kfext = '.rkf'
    _rename_map = {'uff.rkf':'$JN'+_kfext}



class UFFJob(SCMJob):
    _result_type = UFFResults
    _command = 'uff'
    _top = ['title', 'units']
    _subblock_end = 'end'

    def _parsemol(self):
        s = self.settings.input
        system = s.find_case('system')

        printtypes = all(map(lambda at: ('uff' in at.properties and 'type' in at.properties.uff), self.molecule))

        for i,atom in enumerate(self.molecule):
            s[system]['atoms']['_'+str(i+1)] = atom.str(symbol=self._atom_symbol(atom), space=18, decimal=10)
        if self.molecule.lattice:
            for i,vec in enumerate(self.molecule.lattice):
                s[s.find_case('system')]['lattice']['_'+str(i+1)] = '%16.10f %16.10f %16.10f'%vec

    def _removemol(self):
        s = self.settings.input
        system = s.find_case('system')

        if system in s:
            if 'atoms' in s[system]:
                del s[system]['atoms']
            if 'lattice' in s[system]:
                del s[system]['lattice']
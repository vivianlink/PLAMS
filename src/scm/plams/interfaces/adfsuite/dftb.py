from .scmjob import SCMJob, SCMResults

__all__ = ['DFTBJob', 'DFTBResults']


class DFTBResults(SCMResults):
    _kfext = '.rkf'
    _rename_map = {'dftb.rkf':'$JN'+_kfext}

    def _int2inp(self):
        return list(range(1, 1+len(self.job.molecule)))

    def get_properties(self):
        n = self.readkf('Properties', 'nEntries')
        ret = {}
        for i in range(1, n+1):
            tp = self.readkf('Properties', 'Type({})'.format(i)).strip()
            stp = self.readkf('Properties', 'Subtype({})'.format(i)).strip()
            val = self.readkf('Properties', 'Value({})'.format(i))
            key = stp if stp.endswith('Energy') else '{} {}'.format(stp, tp)
            ret[key] = val
        return ret



class DFTBJob(SCMJob):
    _result_type = DFTBResults
    _command = 'dftb'
    _top = ['units', 'task']
    _subblock_end = 'end'

    def _serialize_mol(self):
        s = self.settings.input
        system = s.find_case('system')
        for i,atom in enumerate(self.molecule):
            s[system]['atoms']['_'+str(i+1)] = atom.str(symbol=self._atom_symbol(atom), space=18, decimal=10)
        if self.molecule.lattice:
            for i,vec in enumerate(self.molecule.lattice):
                s[system]['lattice']['_'+str(i+1)] = '{:16.10f} {:16.10f} {:16.10f}'.format(*vec)

    def _remove_mol(self):
        s = self.settings.input
        system = s.find_case('system')
        if system in s:
            if 'atoms' in s[system]:
                del s[system]['atoms']
            if 'lattice' in s[system]:
                del s[system]['lattice']
from .scmjob import SCMJob, SCMResults

__all__ = ['ADFJob', 'ADFResults']


class ADFResults(SCMResults):
    _kfext = '.t21'
    _rename_map = {'TAPE21':'$JN'+_kfext, 'TAPE13':'$JN.t13', 'TAPE10':'$JN.t10'}

    def _int2inp(self):
        aoi = self.readkf('Geometry', 'atom order index')
        n = len(aoi)//2
        return aoi[:n]


class ADFJob(SCMJob):
    _result_type = ADFResults
    _command = 'adf'

    def _parsemol(self):
        for i,atom in enumerate(self.molecule):
            smb = self._atom_symbol(atom)
            suffix = ''
            if hasattr(atom,'fragment'):
                suffix += 'f={fragment} '
            if hasattr(atom,'block'):
                suffix += 'b={block}'

            self.settings.input.atoms['_'+str(i+1)] = ('%5i'%(i+1)) + atom.str(symbol=smb, suffix=suffix)

    def _removemol(self):
        if 'atoms' in self.settings.input:
            del self.settings.input.atoms
from ..core.basejob import SingleJob
from ..core.results import Results

__all__ = ['MOPACJob', 'MOPACResults']


class MOPACResults(Results):
    _rename_map = {'results.rkf':'$JN.rkf'}


class MOPACJob(SingleJob):
    _result_type = MOPACResults

    def get_input(self):
        aux = self.settings.input.find_case('aux')
        if aux not in self.settings.input:
            self.settings.input[aux] = [0,'PRECISION=9']

        keylist = []
        for key, value in self.settings.input.items():
            if value is True:
                keylist.append(key)
            elif isinstance(value, tuple):
                keylist.append(key + '=(' + ','.join(map(str, value)) + ')' )
            elif isinstance(value, list):
                keylist.append(key + '(' + ','.join(map(str, value)) + ')' )
            else:
                keylist.append(key + '=' + str(value))
        ret = ' '.join(keylist) + '\n\n\n'

        for at in self.molecule:
            line = '{:7}'.format(at.symbol)
            for c in ['x', 'y', 'z']:
                num = at.__getattribute__(c)
                frz = 0 if ('mopac_freeze' in at.properties and c in at.properties.mopac_freeze) else 1
                line += '{: 11.8f} {:d}'.format(num,frz)
            ret += line + '\n'
        return ret


    def get_runscript(self):
        ret = '$ADFBIN/mopac.scm -o < ' + self._filename('inp')
        if self.settings.runscript.stdout_redirect:
            ret += ' >'+self._filename('out')
        return ret

    def check(self):
        s = self.results.grep_output('* JOB ENDED NORMALLY *')
        return len(s) > 0

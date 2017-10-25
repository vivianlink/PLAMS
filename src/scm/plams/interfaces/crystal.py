import os
import subprocess

from ..core.basejob  import SingleJob
from ..core.settings import Settings



class CrystalJob(SingleJob):
    """
    A class representing a single computational job with `CRYSTAL <https://www.crystal.unito.it/>`
    """
    def get_input(self):
        """
        Transform all contents of ``input`` branch of ``settings`` into string.
        """

        def parse(key, value, indent=''):
            ret = ''
            key = key.upper()
            if isinstance(value, Settings):
                pass
            elif isinstance(value, list):
                pass
            else:
                pass
            return ret

        inp = ''
        for item in self.settings.input:
            inp += parse(item, self.settings.input[item]) + '\n'

        return inp

    def get_runscript(self):
        """
        Run Crystal.
        """
        return ''

    def check(self):
        """
        Look for the normal termination signal in output
        """
        return True

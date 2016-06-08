from __future__ import unicode_literals

from .basejob import SingleJob
from .common import string
from .settings import Settings

try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess

# ======================<>===========================


class ORCAJob(SingleJob):
    """
    A class representing a single computational job with ORCA
    `Orca <https://orcaforum.cec.mpg.de>`
    todo:
       * print molecule in internal coordinates
       * print xyz including different basis set
    """

    def __init__(self, **kwargs):
        SingleJob.__init__(self, **kwargs)
        self.settings.runscript.orca   #$% what is this good for?

    def get_input(self):
        """
        Transform all contents of ``input`` branch of  ``settings`` into string with blocks, subblocks, keys and values. The branch self.settings.input.main corresponds to the lines starting with the special character ! in the Orca input.
        """
        def get_end(s):
            if (not isinstance(s, Settings)) or ('_end' not in s):
                return s
            else:
                return '{} end'.format(s['_end'])

        #$% a few words of explanation what's going with this _end and how to use it would be nice here

        def pretty_print_inner(s, indent):
            inp = ''
            for i, (key, value) in enumerate(s.items()):
                end = get_end(value)
                if i == 0:
                    inp += ' {} {}\n'.format(key, end)
                else:
                    inp += '{}{} {}\n'.format(indent, key, end)
            return inp

        def pretty_print_orca(s, indent=''):
            inp = ''
            if isinstance(s, Settings):
                for k, v in s.items():
                    if k == 'main':
                        inp += '! {}\n\n'.format(pretty_print_orca(v, indent))
                    else:
                        indent2 = (len(k) + 2) * ' '
                        if not isinstance(v, Settings):
                            block = pretty_print_orca(v)
                        else:
                            block = pretty_print_inner(v, indent2)
                        inp += '%{}{}{}end\n\n'.format(k, block, indent2)
            elif isinstance(s, list):
                for elem in s:
                    inp += '{}'.format(elem)
            else:
                inp += '{}'.format(s)
            return inp

        inp = pretty_print_orca(self.settings.input)
        inp_mol = self.print_molecule()

        return inp + inp_mol

    def print_molecule(self):
        """
        pretty print a molecule in the Orca format.
        """
        mol = self.molecule
        if mol:
            if 'charge' in mol.properties and isinstance(mol.properties.charge, int):
                charge = mol.properties.charge
            else:
                charge = 0
            if 'multiplicity' in mol.properties and isinstance(mol.properties.multiplicity, int):
                multi = mol.properties.multiplicity
            else:
                multi = 1
            xyz = ''.join(at.str(symbol=True, space=11, decimal=5) for at in mol.atoms)
            return '* xyz {} {}\n{}*\n\n'.format(charge, multi, xyz)
        else:
            return ''


    def get_runscript(self):
        """
        Running orca is straightforward, simply:
        */absolute/path/to/orca myinput.inp*
        """
        path = string(subprocess.check_output(['which', 'orca'])).rstrip()
        return '{} {}'.format(path, self._filename('inp'))


    def check(self):
        """
        Look for the normal termination signal in Orca output
        """
        s = self.results.grep_output("ORCA TERMINATED NORMALLY")
        return len(s) > 0


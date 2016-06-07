from __future__ import unicode_literals

from .basejob import SingleJob
from .results import Results
from .settings import Settings
from .utils import flatten

import subprocess as sp
import sys
# ======================<>===========================


class ORCAJob(SingleJob):
    """
    class for result of computation done with
    `Orca <https://orcaforum.cec.mpg.de>`
    todo:
       * print molecule in internal coordinates
       * print xyz including different basis set
    """

    def __init__(self, **kwargs):
        SingleJob.__init__(self, **kwargs)
        self.settings.runscript.orca

    def get_input(self):
        """
        Transform all contents of ``input`` branch of  ``settings`` into string
        with blocks, subblocks, keys and values.
        The branch self.settings.input.main corresponds to the lines starting
        with the special character ! in the Orca input.
        :returns: String containing the input
        """
        def get_end(s):
            if (not isinstance(s, Settings)) or ('_end' not in s):
                return s
            else:
                return '{} end'.format(s['_end'])

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
            charge = mol.properties.charge
            charge = (charge if isinstance(charge, int) else 0)
            multi = mol.properties.multiplicity
            multi = (multi if isinstance(multi, int) else 1)
            xs = flatten(
                '  {:3s}{:>11.5}{:>11.5}{:>11.5}\n'.format(at.symbol, *at.coords)
                for at in mol.atoms)
            return '* xyz {} {}\n{}*\n\n'.format(charge, multi, xs)
        else:
            return ''

    def get_runscript(self):
        """
        Running orca is straightforward, simply:
        */absolute/path/to/orca myinput.inp*
        """
        path = sp.check_output(['which', 'orca']).rstrip()
        if sys.version_info >= (3, 0):
            path = path.decode()
        return '{} {}'.format(path, self._filename('inp'))

    def check(self):
        """
        Look for the normal termination signal in Orca output
        """
        s = self.results.grep_output("ORCA TERMINATED NORMALLY")
        if s is not None:
            return True
        else:
            return False


class OrcaResults(Results):
    """
    A class representing a single computational job with CP2K.
    """
    pass

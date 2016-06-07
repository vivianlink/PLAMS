from __future__ import unicode_literals

from .basejob  import SingleJob
from .results  import Results
from .settings import Settings

import mmap
import os
import subprocess
# ======================<>===========================


class Cp2kJob(SingleJob):
    """
    class for result of computation done with `C2P2K <https://www.cp2k.org/>`
    """

    def __init__(self, **kwargs):
        SingleJob.__init__(self, **kwargs)
        self.settings.runscript.cp2k
        self.settings.pickle = False
        try:
            self.settings.input.force_eval.dft.basis_set_file_name = os.environ['BASISCP2K']
            self.settings.input.force_eval.dft.potential_file_name = os.environ['POTENTIALCP2K']

        except KeyError:
            msg = """The environmental variables BASISCP2K and POTENTIALCPK containing
                  the path to the Cp2k basis and potential basis, respectively,
                  Must be defined"""
            raise NameError(msg)

    def _get_ready(self):
        """
        Before generating runscript and input with parent method
        :meth:`SingleJob._get_ready<scm.plams.basejob.SingleJob._get_ready>`
        add proper ``mol`` and ``inp`` entries to ``self.settings.runscript.cp2k``.
        If already present there, ``mol`` will not be added.
        """
        s = self.settings.runscript.cp2k
        path = os.path.join(self.path, self.name + '.xyz')
        if self.molecule is not None:
            with open(path, 'w') as f:
                f.write(str(len(self.molecule)) + '\n\n')
                for atom in self.molecule:
                    suffix = 'b={block}' if hasattr(atom, 'block') else ''
                    f.write(atom.str(suffix=suffix) + '\n')
        s.i = self._filename('inp')
        s.o = self._filename('out')
        SingleJob._get_ready(self)

    def get_input(self):
        """
        Transform all contents of ``input`` branch of ``settings`` into string
        with blocks, subblocks, keys and values.
        :returns: String containing the input
        """

        _reserved_keywords = ["KIND", "XC", "JOB"]

        def parse(key, value, indent=''):
            ret = ''
            key = key.upper()
            if isinstance(value, Settings):
                if not any(k in key for k in _reserved_keywords):
                    ret += '{}&{}\n'.format(indent, key)
                    for el in value:
                        ret += parse(el, value[el], indent + '  ')
                    ret += '{}&END\n'.format(indent)

                elif key == "XC":
                    ret += '{}&{}\n'.format(indent, key)
                    for el in value:
                        if el.upper() == "XC_FUNCTIONAL":
                            v = value[el]
                            ret += '  {}&XC_FUNCTIONAL {}\n'.format(indent, v)
                            ret += '  {}&END\n'.format(indent)
                        else:
                            ret += parse(el, value[el], indent + '  ')
                    ret += '{}&END\n'.format(indent)

                elif "KIND" in key:
                    for el in value:
                        ret += '{}&{}  {}\n'.format(indent, key, el.upper())
                        for v in value[el]:
                            ret += parse(v, value[el][v], indent + '  ')
                        ret += '{}&END\n'.format(indent)
                elif "JOB" in key:
                    work_dirs = value['directories']
                    job_names = value['input_file_names']
                    job_ids = value['job_ids']

                    for k, (jobID, name, wd) in \
                        enumerate(zip(job_ids, job_names, work_dirs)):
                        ret += '{}&JOB\n'.format(indent)
                        if k > 0:
                            ret += '  {}DEPENDENCIES {}\n'.format(indent, jobID - 1)
                        ret += '  {}DIRECTORY {}\n'.format(indent, wd)
                        ret += '  {}INPUT_FILE_NAME {}\n'.format(indent, name)
                        ret += '  {}JOB_ID {}\n'.format(indent, jobID)
                        ret += '{}&END JOB\n\n'.format(indent)

            elif isinstance(value, list):
                for el in value:
                    ret += parse(key, el, indent)

            elif value is '' or value is True:
                ret += '{}{}\n'.format(indent, key)
            else:
                ret += '{}{}  {}\n'.format(indent, key, str(value))
            return ret

        inp = ''
        for item in self.settings.input:
            inp += parse(item, self.settings.input[item]) + '\n'

        return inp

    def get_runscript(self):
        """
        Run parallel version of Cp2k using srun. Returned string is a ``srun cp2k.popt``
        call followed by option flags generated based on ``self.settings.runscript.cp2k``
        contents.
        """
        r = self.settings.runscript.cp2k
        # try to cp2k using srun
        try:
            subprocess.run(["srun", "--help"], stdout=subprocess.DEVNULL)
            ret = 'srun cp2k.popt'
        except OSError:
            ret = 'cp2k.popt'

        for k, v in r.items():
            if v is not None:
                ret += ' -{} {}'.format(k, v)
            else:
                ret += ' -{}'.format(k)

        if self.settings.runscript.stdout_redirect:
            ret += ' >{}'.format(self._filename('out'))
        ret += '\n\n'
        return ret

    def check(self):
        """Check if the calculation was successful."""
        return True
        # outFile = self._filename('out')
        # path_file = os.path.join(self.path, outFile)
        # with open("plams_out", "a") as f:
        #     f.write("Filename: {}\n".format(path_file))
        #     f.write("File Exist: {}\n".format(os.path.exists(path_file)))
        # if not os.path.exists(path_file):
        #     return False
        # else:
        #     with open(outFile, 'r') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as s:
        #         if s.find(b'PROGRAM ENDED AT') != -1:
        #             return True
        #         else:
        #             return False

class Cp2kResults(Results):
    """
    A class representing a single computational job with CP2K.
    """

    def collect(self):
        """Collect files present in the job folder Using parent method from |Results|.
        """
        Results.collect(self)


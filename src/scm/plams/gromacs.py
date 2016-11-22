from __future__ import unicode_literals
from .basejob  import SingleJob

import os
import subprocess


class Cp2kJob(SingleJob):
    """
    A class representing a single computational job with `Gromacs http://www.gromacs.org/`
    """
    def get_input(self):
        """
        Transform all contents of ``input`` branch of ``settings`` into string
        with blocks, subblocks, keys and values.
        """

    def get_runscript(self):
        """
        Run parallel version of Cp2k using srun.
        """
        s = self.settings.runscript
        try:
            cmd = "gmx_mpi mdrun"
            with open(os.devnull, 'wb') as null:
                subprocess.run(cmd.split(), stdout=null)
        except OSError:
            cmd = "gmx mdrun"

        cmd += ' -deffnm {} '.format(self.name)

        return cmd

    def check(self):
        """
        Look for the normal termination signal in Cp2k output
        """
        pass

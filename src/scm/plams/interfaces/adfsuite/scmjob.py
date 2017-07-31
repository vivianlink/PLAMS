import os

from os.path import join as opj

from ...core.basejob import SingleJob
from ...core.common import log
from ...core.errors import PlamsError
from ...core.results import Results
from ...core.settings import Settings
from ...tools.kftools import KFFile

class SCMResults(Results):
    """Abstract class gathering common mechanisms for results of ADFSuite programs."""
    _kfext = ''


    def collect(self):
        """Collect files present in the job folder. Use parent method from |Results|, then create an instance of |KFFile| for the main KF file and store it as ``_kf`` attribute.
        """
        Results.collect(self)
        kfname = self.job.name + self.__class__._kfext
        if kfname in self.files:
            self._kf = KFFile(opj(self.job.path, kfname))
        else:
            log('WARNING: Main KF file {} not present in {}'.format(kfname, self.job.path), 1)


    def refresh(self):
        """Refresh the contents of ``files`` list. Use parent method from |Results|, then look at all attributes that are instances of |KFFile| and check if they point to existing files. If not, try to reinstantiate them with current job path (that can happen while loading a pickled job after the entire job folder was moved).
        """
        Results.refresh(self)
        to_remove = []
        for attr,val in self.__dict__.items():
            if isinstance(val, KFFile) and os.path.dirname(val.path) != self.job.path:
                guessnewpath = opj(self.job.path, os.path.basename(val.path))
                if os.path.isfile(guessnewpath):
                    self.__dict__[attr] = KFFile(guessnewpath)
                else:
                    to_remove.append(attr)
        for i in to_remove:
            del self.__dict__[i]


    def readkf(self, section, variable):
        """readkf(section, variable)
        Read data from *section*/*variable* of the main KF file.

        The type of the returned value depends on the type of *variable* defined inside KF file. It can be: single int, list of ints, single float, list of floats, single boolean, list of booleans or string. """
        if self._kf:
            return self._kf.read(section, variable)
        raise FileError('File {} not present in {}'.format(self.job.name+self.__class__._kfext, self.job.path))


    def newkf(self, filename):
        """newkf(filename)
        Create new |KFFile| instance using file *filename* in the job folder.

        Example usage::

            >>> res = someadfjob.run()
            >>> tape13 = res.newkf('$JN.t13')
            >>> print(tape13.read('Geometry', 'xyz'))

        """
        self.refresh()
        filename = filename.replace('$JN', self.job.name)
        if filename in self.files:
            return KFFile(opj(self.job.path, filename))
        else:
            raise FileError('File {} not present in {}'.format(filename, self.job.path))


    def get_molecule(self, section, variable, unit='bohr', internal=False, n=1):
        """get_molecule(section, variable, unit='bohr', internal=False, n=1)
        Read molecule coordinates from *section*/*variable* of the main KF file.

        Returned |Molecule| instance is created by copying a molecule from associated |SCMJob| instance and updating atomic coordinates with values read from *section*/*variable*. The format in which coordinates are stored is not consistent for all programs or even for different sections of the same KF file. Sometimes coordinates are stored in bohr, sometimes in angstrom. The order of atoms can be either input order or internal order. These settings can be adjusted with *unit* and *internal* parameters. Some variables store more than one geometry, in those cases *n* can be used to choose the preferred one.
        """
        if self.job.molecule:
            m = self.job.molecule.copy()
            natoms = len(m)
            coords = self.readkf(section, variable)
            coords = [coords[i:i+3] for i in range(0,len(coords),3)]
            if len(coords) > natoms:
                coords = coords[(n-1)*natoms:n*natoms]
            if internal:
                mapping = self._int2inp()
                coords = [coords[mapping[i]-1] for i in range(len(coords))]
            for at,coord in zip(m,coords):
                at.move_to(coord, unit)
            return m
        raise PlamsError('get_molecule() failed. Corresponding job has no molecule associated')


    def _kfpath(self):
        """_kfpath()
        Return an absolute path to the main KF file.
        """
        return opj(self.job.path, self.job.name + self.__class__._kfext)


    def _settings_reduce(self):
        """_settings_reduce()
        When this object is present as a value in some |Settings| instance and string representation is needed, use the absolute path to the main KF file. See :meth:`Settings.__reduce__<scm.plams.core.settings.Settings.__reduce__>` for details.
        """
        return self._kfpath()


    def _export_attribute(self, attr, other):
        """_export_attribute(attr, other)
        If *attr* is a KF file take care of a proper path. Otherwise use parent method. See :meth:`Results._copy_to<scm.plams.core.results.Results._copy_to>` for details.
        """
        if isinstance(attr, KFFile):
            oldname = os.path.basename(attr.path)
            newname = Results._replace_job_name(oldname, self.job.name, other.job.name)
            newpath = opj(other.job.path, newname)
            return KFFile(newpath) if os.path.isfile(newpath) else None
        else:
            return Results._export_attribute(self, attr, other)


    def _int2inp(self):
        """_int2inp()
        Obtain mapping from internal atom order to the input one. Abstract method.
        """
        raise PlamsError('Trying to run an abstract method SCMResults._int2inp()')



class SCMJob(SingleJob):
    """Abstract class gathering common mechanisms for jobs with ADF Suite programs."""
    _result_type = SCMResults
    _top = ['title','units','define']
    _command = ''
    _subblock_end = 'subend'


    def get_input(self):
        """Transform all contents of ``setting.input`` branch into string with blocks, keys and values.

        On the highest level alphabetic order of iteration is modified: keys occuring in attribute ``_top`` are printed first.

        Automatic handling of ``molecule`` can be disabled with ``settings.ignore_molecule = True``.
        """

        def parse(key, value, indent=''):
            ret = ''
            if isinstance(value, Settings):
                ret += indent + key
                if '_h' in value:
                    ret += ' ' + value['_h']
                ret += '\n'

                i = 1
                while ('_'+str(i)) in value:
                    ret += parse('', value['_'+str(i)], indent+'  ')
                    i += 1

                for el in value:
                    if not el.startswith('_'):
                        ret += parse(el, value[el], indent+'  ')

                if indent == '':
                    ret += 'end\n'
                else:
                    ret += indent + self._subblock_end + '\n'
            elif isinstance(value, list):
                for el in value:
                    ret += parse(key, el, indent)
            elif isinstance(value, (SCMJob, SCMResults, KFFile)):
                ret += parse(key, value._settings_reduce(), indent)
            elif value is '' or value is True:
                ret += indent + key + '\n'
            elif value is False:
                pass
            else:
                value = str(value)
                ret += indent + key
                if key != '' and not value.startswith('='):
                    ret += ' '
                ret += value + '\n'
            return ret

        inp = ''
        use_molecule = ('ignore_molecule' not in self.settings) or (self.settings.ignore_molecule == False)
        if use_molecule:
            self._parsemol()
        for item in self._top:
            item = self.settings.input.find_case(item)
            if item in self.settings.input:
                inp += parse(item, self.settings.input[item]) + '\n'
        for item in self.settings.input:
            if item.lower() not in self._top:
                inp += parse(item, self.settings.input[item]) + '\n'
        inp += 'end input\n'
        if use_molecule:
            self._removemol()
        return inp


    def get_runscript(self):
        """Generate a runscript. Returned string is of the form::

            $ADFBIN/name [-n nproc] <jobname.in [>jobname.out]

        ``name`` is taken from the class attribute ``_command``. ``-n`` flag is added if ``settings.runscript.nproc`` exists. ``[>jobname.out]`` is used based on ``settings.runscript.stdout_redirect``.
        """
        s = self.settings.runscript
        ret = '$ADFBIN/'+self._command
        if 'nproc' in s:
            ret += ' -n ' + str(s.nproc)
        ret += ' <'+self._filename('inp')
        if s.stdout_redirect:
            ret += ' >'+self._filename('out')
        ret += '\n\n'
        return ret


    def check(self):
        """Check if ``termination status`` variable from ``General`` section of main KF file equals ``NORMAL TERMINATION``."""
        try:
            status = self.results.readkf('General', 'termination status')
        except:
            return False
        if 'NORMAL TERMINATION' in status:
            if 'errors' in status:
                return False
            if 'warnings' in status:
                log('Job {} reported warnings. Please check the the output'.format(self.name), 1)
            return True
        return False


    def _parsemol(self):
        """Process |Molecule| instance stored in ``molecule`` attribute and add it as relevant entries of ``settings.input`` branch. Abstract method."""
        raise PlamsError('Trying to run an abstract method SCMJob._parsemol()')


    def _removemol(self):
        """Remove from ``settings.input`` all entries added by :meth:`_parsemol`. Abstract method."""
        raise PlamsError('Trying to run an abstract method SCMJob._removemol()')


    def _settings_reduce(self):
        """When this object is present as a value in some |Settings| instance and string representation is needed, use the absolute path to the main KF file. See :meth:`Settings.__reduce__<scm.plams.core.settings.Settings.__reduce__>` for details."""
        return self.results._kfpath()


    @staticmethod
    def _atom_symbol(atom):
        """Return the atomic symbol of *atom*. Ensure proper formatting for ADFSuite input taking into account ``ghost`` and ``name`` entries in ``properties`` of *atom*."""
        smb = atom.symbol if atom.atnum > 0 else ''  #Dummy atom should have '' instead of 'Xx'
        if 'ghost' in atom.properties and atom.properties.ghost:
            smb = ('Gh.'+smb).rstrip('.')
        if 'name' in atom.properties:
            smb = (smb+'.'+str(atom.properties.name)).lstrip('.')
        return smb


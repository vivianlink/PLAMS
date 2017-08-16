from .scmjob import SCMJob, SCMResults
from ...core.basemol import Molecule, Atom
from ...tools.units import Units

__all__ = ['DFTBJob', 'DFTBResults']



class DFTBResults(SCMResults):
    _kfext = '.rkf'
    _rename_map = {'dftb.rkf':'$JN'+_kfext}


    def _int2inp(self):
        """_int2inp()
        In DFTB the internal order is always the same as the input order. Returns an identity permutation of length equal to the number of atoms
        """
        return list(range(1, 1+self.readkf('Molecule', 'nAtoms')))


    def get_properties(self):
        """get_properties()
        Return a dictionary with all the entries from ``Properties`` section in the main KF file (``$JN.rkf``).
        """
        n = self.readkf('Properties', 'nEntries')
        ret = {}
        for i in range(1, n+1):
            tp = self.readkf('Properties', 'Type({})'.format(i)).strip()
            stp = self.readkf('Properties', 'Subtype({})'.format(i)).strip()
            val = self.readkf('Properties', 'Value({})'.format(i))
            key = stp if stp.endswith('Energy') else '{} {}'.format(stp, tp)
            ret[key] = val
        return ret


    def get_main_molecule(self):
        """get_main_molecule()
        Return a |Molecule| instance based on the ``Molecule`` section in the main KF file (``$JN.rkf``).

        For runs with multiple geometries (geometry optimization, transition state search, molecular dynamics) this is the **final** geometry. In such a case, to access the initial (or any intermediate) coordinates please extract them from section ``History``, variable ``Coords(i)``. Mind the fact that all coordinates written by DFTB to ``.rkf`` file are in bohr::

            mol = results.get_molecule(section='History', variable='Coords(1)', unit='bohr')
        """
        ret = self.get_molecule(section='Molecule', variable='Coords', unit='bohr')
        ret.properties.charge = self.readkf('Molecule', 'Charge')
        if ('Molecule', 'LatticeVectors') in self._kf:
            lattice = self.readkf('Molecule', 'LatticeVectors')
            lattice = Units.convert(lattice, 'bohr', 'angstrom')
            ret.lattice = [tuple(lattice[i:i+3]) for i in range(0,len(lattice),3)]
        return ret


    def get_input_molecule(self):
        """get_input_molecule()
        Return a |Molecule| instance with initial coordinates.

        All data used by this method is taken from ``$JN.rkf`` file. The ``molecule`` attribute of the corresponding job is ignored.
        """
        if ('History', 'nEntries') in self._kf:
            return self.get_molecule(section='History', variable='Coords(1)', unit='bohr')
        return self.get_main_molecule()


    def _atomic_numbers_input_order(self):
        """_atomic_numbers_input_order()
        Return a list of atomic numbers, in the input order.
        """
        return self.readkf('Molecule', 'AtomicNumbers')



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
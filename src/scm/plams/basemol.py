from __future__ import unicode_literals

import copy
import math
import numpy
import types

from .errors import MoleculeError, PTError, FileError
from .pdbtools import PDBHandler, PDBRecord
from .settings import Settings
from .utils import Units, PT

__all__ = ['Atom', 'Bond', 'Molecule']

#===================================================================================================
#===================================================================================================
#===================================================================================================

class Atom(object):
    """A class representing a single atom in three dimensional space.

    An instance of this class has the following attributes:

        *   ``atnum`` -- atomic number (zero for "dummy atoms")
        *   ``coords`` -- tuple of length 3 storing spatial coordinates
        *   ``bonds`` -- list of bonds (see |Bond|) this atom is a part of
        *   ``mol`` -- a |Molecule| this atom belongs to
        *   ``properties`` -- a |Settings| instance storing all other information about this atom (initially it is populated with *\*\*other* keyword arguments passed to the constructor)

        All the above attributes can be accessed either directly or using one of the following properties:

        *   ``x``, ``y``, ``z`` -- allow to read or modify each coordinate separately
        *   ``symbol`` -- allows to read or write atomic symbol directly. Atomic symbol is not stored as an attribute, instead of that atomic number (``atnum``) indicates the type of atom. In fact, ``symbol`` this is just a wrapper around ``atnum`` that uses |PeriodicTable| as a translator::

                >>> a = Atom(atnum=8)
                >>> print a.symbol
                O
                >>> a.symbol = 'Ca'
                >>> print a.atnum
                20

        *   ``mass`` -- atomic mass, obtained from |PeriodicTable|, read only
        *   ``radius`` -- atomic radius, obtained from |PeriodicTable|, read only
        *   ``connectors`` -- number of connectors, obtained from |PeriodicTable|, read only

        Values stored in ``coords`` tuple do not necessarily have to be numeric, you can also store any string there. This might come handy for programs that allow parametrization of coordinates in the input file (to enforce some geometry constraints for example)::

            >>> a = Atom(atnum=6, coords=(1,2,3))
            >>> print a
                     C       1.00000       2.00000       3.00000
            >>> a.y = 'param1'
            >>> print a
                     C       1.00000        param1       3.00000

        However, non-numerical coordinates cannot be used together with some methods (for example :meth:`distance_to` or :meth:`move_by`). Trying to do this will raise an exception.

        Internally, atomic coordinates are always expressed in angstroms. Most of methods that read or modify atomic coordinates accept keyword argument ``unit`` allowing to choose unit in which results and/or arguments are expressed (see |Units| for details). Throughout the entire code angstrom is the default length unit. If you don't specify ``unit`` parameter in any place of your script, all automatic unit handling described above boils down to occasional multiplication/division by 1.0.
    """
    def __init__(self, atnum=0, coords=None, unit='angstrom', bonds=None, mol=None, **other):
        self.atnum = atnum
        self.mol = mol
        self.bonds = bonds or []
        self.properties = Settings(other)

        if coords is None:
            self.coords = (0.0, 0.0, 0.0)
        elif len(coords) == 3:
            tmp = []
            for i in coords:
                try:
                    i = Units.convert(float(i), unit, 'angstrom')
                except ValueError: pass
                tmp.append(i)
            self.coords = tuple(tmp)
        else:
            raise TypeError('Atom: Invalid coordinates passed')


    def str(self, symbol=True, suffix='', unit='angstrom', space=14, decimal=6):
        """Return a string representation of this atom.

        Returned string is a single line (no newline characters) that always contains atomic coordinates (and maybe more). Each atomic coordinate is printed using *space* characters, with *decimal* characters reserved for decimal digits. Coordinates values are expressed in *unit*.

        If *symbol* is ``True``, atomic symbol is added at the beginning of the line. If *symbol* is a string, this exact string is printed there.

        *suffix* is an arbitrary string that is appended at the end of returned line. It can contain identifiers in curly brackets (like for example ``f={fragment}``) that will be replaced by values of corresponding attributes (in this case ``self.fragment``). It is done via new string formatting and entire ``self.__dict__`` is passed to formating method. See :ref:`new-string-formatting` for details.

        Example:

            >>> a = Atom(atnum=6, coords=(1,1.5,2))
            >>> print a.str()
                     C      1.000000      1.500000      2.000000
            >>> print a.str(unit='bohr')
                     C      1.889726      2.834589      3.779452
            >>> print a.str(symbol=False)
                  1.000000      1.500000      2.000000
            >>> print a.str(symbol='C2.13')
                 C2.13      1.000000      1.500000      2.000000
            >>> print a.str(suffix='protein1')
                     C      1.000000      1.500000      2.000000 protein1
            >>> a.info = 'membrane'
            >>> print a.str(suffix='subsystem={info}')
                     C      1.000000      1.500000      2.000000 subsystem=membrane

        """
        strformat = '{:>%is}'%space
        numformat = '{:>%i.%if}'%(space,decimal)
        f = lambda x: numformat.format(Units.convert(x, 'angstrom', unit)) if isinstance(x, (int,float)) else strformat.format(str(x))
        if symbol is False:
            return ('{0}{1}{2} '+suffix).format(*map(f,self.coords), **self.__dict__)
        if symbol is True:
            symbol = self.symbol
        return ('{0:>10s}{1}{2}{3} '+suffix).format(symbol, *map(f,self.coords), **self.__dict__)

    def __str__(self):
        """Return a string representation of this atom. Simplified version of :meth:`str` to work as a magic method."""
        return self.str()

    def __iter__(self):
        """Iteration through atom yields coordinates. Thanks to that instances of |Atom| can be passed to any method requiring point or vector as an argument"""
        return iter(self.coords)

    def _setx(self, value): self.coords = (value, self.coords[1], self.coords[2])
    def _sety(self, value): self.coords = (self.coords[0], value, self.coords[2])
    def _setz(self, value): self.coords = (self.coords[0], self.coords[1], value)
    def _getx(self): return self.coords[0]
    def _gety(self): return self.coords[1]
    def _getz(self): return self.coords[2]
    x = property(_getx, _setx)
    y = property(_gety, _sety)
    z = property(_getz, _setz)

    def _getsymbol(self):
        return PT.get_symbol(self.atnum)
    def _setsymbol(self, symbol):
        self.atnum = PT.get_atomic_number(symbol)
    symbol = property(_getsymbol, _setsymbol)

    def _getmass(self):
        return PT.get_mass(self.atnum)
    mass = property(_getmass)

    def _getradius(self):
        return PT.get_radius(self.atnum)
    radius = property(_getradius)

    def _getconnectors(self):
        return PT.get_connectors(self.atnum)
    connectors = property(_getconnectors)

    def move_by(self, vector, unit='angstrom'):
        """Move this atom in space by *vector*, expressed in *unit*.

        *vector* should be an iterable container of length 3 (usually tuple, list or numpy array). *unit* describes unit of values stored in *vector*.

        This method requires all coordinates to be numerical values, :exc:`~exceptions.TypeError` is raised otherwise.
        """
        ratio = Units.conversion(unit, 'angstrom')
        self.coords = tuple(i + j*ratio for i,j in zip(self, vector))


    def move_to(self, point, unit='angstrom'):
        """Move this atom to a given *point* in space, expressed in *unit*.

        *point* should be an iterable container of length 3 (for example: tuple, |Atom|, list, numpy array). *unit* describes unit of values stored in *point*.

        This method requires all coordinates to be numerical values, :exc:`~exceptions.TypeError` is raised otherwise.
        """
        ratio = Units.conversion(unit, 'angstrom')
        self.coords = tuple(i*ratio for i in point)


    def distance_to(self, point, unit='angstrom', result_unit='angstrom'):
        """Measure the distance between this atom and *point*.

        *point* should be an iterable container of length 3 (for example: tuple, |Atom|, list, numpy array). *unit* describes unit of values stored in *point*. Returned value is expressed in *result_unit*.

        This method requires all coordinates to be numerical values, :exc:`~exceptions.TypeError` is raised otherwise.
        """
        ratio = Units.conversion(unit, 'angstrom')
        res = 0.0
        for i,j in zip(self,point):
            res += (i - j*ratio)**2
        return Units.convert(math.sqrt(res), 'angstrom', result_unit)


    def vector_to(self, point, unit='angstrom', result_unit='angstrom'):
        """Calculate a vector from this atom to *point*.

        *point* should be an iterable container of length 3 (for example: tuple, |Atom|, list, numpy array). *unit* describes unit of values stored in *point*. Returned value is expressed in *result_unit*.

        This method requires all coordinates to be numerical values, :exc:`~exceptions.TypeError` is raised otherwise.
        """
        ratio = Units.conversion(unit, 'angstrom')
        resultratio = Units.conversion('angstrom', result_unit)
        return tuple((i*ratio-j)*resultratio for i,j in zip(point, self))


    def angle(self, point1, point2, point1unit='angstrom', point2unit='angstrom',result_unit='radian'):
        """Calculate an angle between vectors pointing from this atom to *point1* and *point2*.

        *point1* and *point2* should be iterable containers of length 3 (for example: tuple, |Atom|, list, numpy array). Values stored in them are expressed in, respectively, *point1unit* and *point2unit*. Returned value is expressed in *result_unit*.

        This method requires all coordinates to be numerical values, :exc:`~exceptions.TypeError` is raised otherwise.
        """
        num = numpy.dot(self.vector_to(point1, point1unit), self.vector_to(point2, point2unit))
        den = self.distance_to(point1, point1unit) * self.distance_to(point2, point2unit)
        return Units.convert(math.acos(num/den), 'radian', unit)


#===================================================================================================
#===================================================================================================
#===================================================================================================

class Bond (object):
    """A class representing a bond between two atoms.

    An instance of this class has the following attributes:

        *   ``atom1`` and ``atom2`` -- two instances of |Atom| that form this bond
        *   ``order`` -- order of the bond. It is either an integer number or the floating point value stored in ``Bond.AR``, indicating aromatic bond
        *   ``mol`` -- a |Molecule| this bond belongs to
        *   ``properties`` -- a |Settings| instance storing all other  information about this bond (initially it is populated with *\*\*other* keyword arguments passed to the constructor)
    """
    AR = 1.5
    def __init__(self, atom1, atom2, order=1, mol=None, **other):
        self.atom1 = atom1
        self.atom2 = atom2
        self.order = order
        self.mol = mol
        self.properties = Settings(other)


    def __str__(self):
        """Return string representation of this bond."""
        return '(%s)--%1.1f--(%s)'%(str(self.atom1), self.order, str(self.atom2))


    def __iter__(self):
        """Iterate over bonded atoms (``atom1`` first, then ``atom2``)."""
        yield self.atom1
        yield self.atom2


    def is_aromatic(self):
        """Check if this bond is aromatic."""
        return self.order == Bond.AR


    def length(self, unit='angstrom'):
        """Return bond's length, expressed in *unit*."""
        return self.atom1.distance_to(self.atom2, result_unit=unit)


    def other_end(self, atom):
        """Return the atom on the other end of this bond with respect to *atom*.

        *atom* has to be either ``atom1`` or ``atom2``, otherwise an exception is raised.
        """
        if atom is self.atom1:
            return self.atom2
        elif atom is self.atom2:
            return self.atom1
        else:
            raise MoleculeError('Bond.other_end: invalid atom passed')


    def resize(self, atom, length, unit='angstrom'):
        """Change the length of the bond to *length*.

        This method works in the following way: one of two atoms forming this bond is moved along the bond in such a way that new length is *length*, in *unit* (direction of the bond in space does not change). Atom indicated by *atom* has to be one of bond's atoms and it is the atom that is **not** moved.
        """
        ratio = 1.0 - Units.convert(length, unit, 'angstrom')/self.length()
        moving = self.other_end(atom)
        moving.move_by(tuple(i*ratio for i in moving.vector_to(atom)))


#===================================================================================================
#===================================================================================================
#===================================================================================================

class Molecule (object):

    def __init__(self, filename=None, inputformat=None):
        self.atoms = []
        self.bonds = []
        self.lattice = []
        self.charge = 0
        self.spin = 0
        self.properties = {}

        if filename is not None :
            self.read(filename, inputformat)


    def __len__(self):
        """Return the number of atoms."""
        return len(self.atoms)

    def __str__(self):
        """Return string representation of this molecule.

        Information about atoms are printed in ``.xyz`` format fashion -- each atom in a separate, enumerated line. Then, if the molecule contains any bonds, they are printed. Each bond is printed in a separate line, with information about both atoms and bond order. Example::

                  Atoms:
                    1         N       0.00000       0.00000       0.38321
                    2         H       0.94218       0.00000      -0.01737
                    3         H      -0.47109       0.81595      -0.01737
                    4         H      -0.47109      -0.81595      -0.01737
                  Bonds:
                    (1)----1----(2)
                    (1)----1----(3)
                    (1)----1----(4)
        """
        s = '  Atoms: \n'
        for i,atom in enumerate(self.atoms):
            s += ('%5i'%(i+1)) + str(atom) + '\n'
        if len(self.bonds) > 0:
            for j,atom in enumerate(self.atoms):
                atom._tmpid = j+1
            s += '  Bonds: \n'
            for bond in self.bonds:
                s += '(%d)--%1.1f--(%d)\n'%(bond.atom1._tmpid, bond.order, bond.atom2._tmpid)
            for atom in self.atoms:
                del atom._tmpid
        if self.lattice:
            s += "  Lattice:\n"
            for vec in self.lattice:
               s += '    %10.6f %10.6f %10.6f\n'%vec
        return s


    def __iter__(self):
        """Iterate over atoms."""
        return iter(self.atoms)

    def __getitem__(self, key):
        """Bracket notation (``mymol[i]``) can be used to access the atom list directly. Read only."""
        #allow key to be an atom
        return self.atoms[key]

        #__setitem__ __delitem__

    def __add__(self, other):
        """Create new molecule that is a sum of this molecule and *other*.

        Both base molecules are copied, so the newly created "sum-molecule" has atoms, bonds and all other
        """
        m = copy.deepcopy(self)
        m += other
        return m


    def __iadd__(self, other):
        othercopy = copy.deepcopy(other)
        self.atoms += othercopy.atoms
        self.bonds += othercopy.bonds
        for atom in self.atoms:
            atom.mol = self
        for bond in self.bonds:
            bond.mol = self
        self.charge += othercopy.charge
        self.spin += othercopy.spin
        self.properties.update(othercopy.properties)
        return self

    def copy(self, atoms=None):
    #TOFIX
        return copy.deepcopy(self)

    def deepcopy(self, atoms=None):
        if atoms is None:
            return copy.deepcopy(self)

    def __copy__(self):
        return self.copy(atoms=None)




#===================================================================================================
#==== Atoms/bonds manipulation =====================================================================
#===================================================================================================


    def add_bond(self, bond):
        bond.mol = self
        self.bonds.append(bond)
        bond.atom1.bonds.append(bond)
        bond.atom2.bonds.append(bond)

    def delete_bond(self, bond):
        bond.atom1.bonds.remove(bond)
        bond.atom2.bonds.remove(bond)
        self.bonds.remove(bond)

    def delete_all_bonds(self):
        while self.bonds:
            self.delete_bond(self.bonds[0])



    def add_atom(self, atom, adjacent=None, orders=None):
        self.atoms.append(atom)
        atom.mol = self
        if adjacent is not None:
            for i, adj in enumerate(adjacent):
                newbond = Bond(atom, adj)
                if orders is not None:
                    newbond.order = orders[i]
                self.add_bond(newbond)

    def delete_atom(self, atom):
        try:
            self.atoms.remove(atom)
        except:
            raise MoleculeError('delete_atom: invalid argument passed as atom')
        for b in atom.bonds:
            b.other_end(atom).bonds.remove(b)
            self.bonds.remove(b)



    def set_atoms_id(self):
        for i,at in enumerate(self.atoms):
            at.id = i+1

    def unset_atoms_id(self):
        for at in self.atoms:
            try:
                del at.id
            except:
                pass


    def get_atoms(self, atomlist):
    #translate index list into atom list
        if atomlist is None:
            return self.atoms
        else:
            if isinstance(atomlist, list):
                if len(atomlist)>0 and isinstance(atomlist[0], int):
                    return [self.atoms[i-1] for i in atomlist]
                else:
                    return atomlist
            else:
                raise MoleculeError('get_atoms: passed argument is not a list')


    def get_fragment(self, atoms, ghosts=True):
        atoms = self.get_atoms(atoms)
        atoms = [atom for atom in atoms if ghosts or not atom.ghost]
        m = Molecule()
        for atom in atoms:
            newatom = Atom(atnum=atom.atnum, coords=atom.coords, unit=atom.unit, mol=m, ghost=atom.ghost)
            newatom.properties = dict(atom.properties)
            m.atoms.append(newatom)
            atom.bro = newatom
        for bond in self.bonds:
            if hasattr(bond.atom1, 'bro') and hasattr(bond.atom2, 'bro'):
                m.add_bond(Bond(bond.atom1.bro, bond.atom2.bro, order=bond.order, **bond.properties))
        for atom in atoms:
            del atom.bro
        return m


    def separate(self):
    #all returned fragments have default spin, charge, props etc.
        frags = []
        clone = copy.deepcopy(self)
        for at in clone.atoms:
            at.visited = False

        def dfs(v, mol):
            v.visited = True
            v.mol = mol
            for e in v.bonds:
                e.mol = mol
                u = e.other_end(v)
                if not u.visited:
                    dfs(u, mol)

        for src in clone.atoms:
            if not src.visited:
                m = Molecule()
                dfs(src, m)
                frags.append(m)

        for at in clone.atoms:
            del at.visited
            at.mol.atoms.append(at)
        for b in clone.bonds:
            b.mol.bonds.append(b)

        del clone
        return frags


    def wrap_me(self, lenght, angle=2*numpy.pi, unit='angstrom'):
    # Wraps a molecule along the x axis

        # Convert all coordinates to the input unit:
        original_units = [atom.unit for atom in self.atoms]
        for atom in self.atoms:
            atom.convert(unit)

        xs = [atom.x for atom in self.atoms]
        if max(xs)-min(xs) > lenght:
            raise MoleculeError('wrap_me: x-extension of the molecule is larger than lenght')

        if angle < 0 or angle > 2*numpy.pi:
            raise MoleculeError('wrap_me: angle must be between 0 and 2*pi')

        # Tranlate the molecule so that the center of mass is (0,0,0):
        t = tuple([-i for i in self.get_center_of_mass()])
        self.translate(t)

        # Coodinate transformation:

        r = lenght / angle

        def map_ring_x (x, y):
            return (r + y*(r+y)/r) * numpy.cos(2*numpy.pi*x/(lenght))
        def map_ring_y (x, y):
            return (r + y*(r-y)/r) * numpy.sin(2*numpy.pi*x/(lenght))

        for atom in self.atoms:
            atom.x, atom.y = map_ring_x(atom.x, atom.y), map_ring_y(atom.x, atom.y)

        # Convert the coordinates back:
        for atom, original_unit in zip(self.atoms, original_units):
            atom.convert(original_unit)



#===================================================================================================
#==== File/format IO ===============================================================================
#===================================================================================================


    def readxyz(self, f, frame):

        def newatom(line):
            lst = line.split()
            shift = 1 if (len(lst) > 4 and lst[0] == str(i)) else 0
            num = lst[0+shift]
            if isinstance(num, str):
                num = PT.get_atomic_number(num)
            self.add_atom(Atom(atnum=num, coords=(lst[1+shift],lst[2+shift],lst[3+shift])))

        def newlatticevec(line):
            lst = line.split()
            self.lattice.append((float(lst[1]),float(lst[2]),float(lst[3])))

        fr = frame
        begin, first, nohead = True, True, False
        for line in f:
            if first:
                if line.strip() == '' : continue
                first = False
                try:
                    n = int(line.strip())
                    fr -= 1
                except ValueError:
                    nohead = True
                    newatom(line)
            elif nohead:
                if line.strip() == '' : break
                if 'VEC' in line.upper():
                    newlatticevec(line)
                else:
                    newatom(line)
            elif fr != 0:
                try:
                    n = int(line.strip())
                    fr -= 1
                except ValueError:
                    continue
            else:
                if begin:
                    begin = False
                    i = 1
                    if line:
                        self.properties['comment'] = line.rstrip()
                else:
                    if i <= n:
                        newatom(line)
                        i += 1
                    elif 'VEC' in line.upper():
                       newlatticevec(line)
                    else:
                        break
        if not nohead and fr > 0:
            raise MoleculeError('readxyz: There are only %i frames in %s' % (frame - fr, f.name))


    def writexyz(self, f):
        f.write(str(len(self)) + '\n')
        if 'comment' in self.properties:
            comment = self.properties['comment']
            if isinstance(comment, list):
                comment = comment[0]
            f.write(comment)
        f.write('\n')
        for at in self.atoms:
            f.write(str(at) + '\n')


    def readmol(self, f, frame):
        if frame != 1:
            raise MoleculeError('readmol: .mol files do not support multiple geometries')

        comment = []
        for i in range(4):
            line = f.readline().rstrip()
            if line:
                spl = line.split()
                if spl[len(spl)-1] == 'V2000':
                    natom = int(spl[0])
                    nbond = int(spl[1])
                    for j in range(natom):
                        atomline = f.readline().split()
                        crd = tuple(map(float, atomline[0:3]))
                        symb = atomline[3]
                        try:
                            num = PT.get_atomic_number(symb)
                        except PTError:
                            num = 0
                        self.add_atom(Atom(atnum=num, coords=crd))
                    for j in range(nbond):
                        bondline = f.readline().split()
                        at1 = self.atoms[int(bondline[0]) - 1]
                        at2 = self.atoms[int(bondline[1]) - 1]
                        ordr = int(bondline[2])
                        if ordr == 4:
                            ordr = Bond.AR
                        self.add_bond(Bond(atom1=at1, atom2=at2, order=ordr))
                    break
                elif spl[len(spl)-1] == 'V3000':
                    raise MoleculeError('readmol: Molfile V3000 not supported. Please convert')
                else:
                    comment.append(line)
        if comment:
            self.properties['comment'] = comment



    def writemol(self, f):
        commentblock = ['\n']*3
        if 'comment' in self.properties:
            comment = self.properties['comment']
            if isinstance(comment, str):
                commentblock[0] = comment + '\n'
            elif isinstance(comment, list):
                comment = comment[0:3]
                while len(comment) < 3:
                    comment.append('')
                commentblock = [a+b for a,b in zip(comment,commentblock)]
        f.writelines(commentblock)

        self.set_atoms_id()

        f.write('%3i%3i  0  0  0  0  0  0  0  0999 V2000\n' % (len(self.atoms),len(self.bonds)))
        for at in self.atoms:
            f.write('%10.4f%10.4f%10.4f %-3s 0  0  0  0  0  0\n' % (at.x,at.y,at.z,at.symbol))
        for bo in self.bonds:
            order = bo.order
            if order == Bond.AR:
                order = 4
            f.write('%3i%3i%3i  0  0  0\n' % (bo.atom1.id,bo.atom2.id,order))
        self.unset_atoms_id()
        f.write('M  END\n')



    def readmol2(self, f, frame):
        if frame != 1:
            raise MoleculeError('readmol: .mol2 files do not support multiple geometries')

        bondorders = {'1':1, '2':2, '3':3, 'am':1, 'ar':Bond.AR, 'du':0, 'un':1, 'nc':0}
        mode = ('', 0)
        for i, line in enumerate(f):
            line = line.rstrip()
            if not line:
                continue
            elif line[0] == '#':
                continue
            elif line[0] == '@':
                line = line.partition('>')[2]
                if not line:
                    raise MoleculeError('readmol2: Error in %s line %i: invalid @ record' % (f.name, str(i+1)))
                mode = (line, i)

            elif mode[0] == 'MOLECULE':
                pos = i - mode[1]
                if pos == 1:
                    self.properties['name'] = line
                elif pos == 3:
                    self.properties['type'] = line
                elif pos == 4:
                    self.properties['charge_type'] = line
                elif pos == 5:
                    self.properties['flags'] = line
                elif pos == 6:
                    self.properties['comment'] = line

            elif mode[0] == 'ATOM':
                spl = line.split()
                if len(spl) < 6:
                    raise MoleculeError('readmol2: Error in %s line %i: not enough values in line' % (f.name, str(i+1)))
                symb = spl[5].partition('.')[0]
                try:
                    num = PT.get_atomic_number(symb)
                except PTError:
                    num = 0
                crd = tuple(map(float, spl[2:5]))
                newatom = Atom(atnum=num, coords=crd, name=spl[1], type=spl[5])
                if len(spl) > 6:
                    newatom.properties['subst_id'] = spl[6]
                if len(spl) > 7:
                    newatom.properties['subst_name'] = spl[7]
                if len(spl) > 8:
                    newatom.properties['charge'] = float(spl[8])
                if len(spl) > 9:
                    newatom.properties['flags'] = spl[9]
                self.add_atom(newatom)

            elif mode[0] == 'BOND':
                spl = line.split()
                if len(spl) < 4:
                    raise MoleculeError('readmol2: Error in %s line %i: not enough values in line' % (f.name, str(i+1)))
                try:
                    atom1 = self.atoms[int(spl[1])-1]
                    atom2 = self.atoms[int(spl[2])-1]
                except IndexError:
                    raise MoleculeError('readmol2: Error in %s line %i: wrong atom ID' % (f.name, str(i+1)))
                newbond = Bond(atom1, atom2, order=bondorders[spl[3]])
                if len(spl) > 4:
                    for flag in spl[4].split('|'):
                        newbond.properties[flag] = True
                self.add_bond(newbond)



    def writemol2(self, f):
        bondorders = ['1','2','3','ar']

        def write_prop(name, obj, separator, space=0, replacement=None):
            form_str = '%-' + str(space) + 's'
            if name in obj.properties:
                f.write(form_str % str(obj.properties[name]))
            elif replacement is not None:
                f.write(form_str % str(replacement))
            f.write(separator)

        f.write('@<TRIPOS>MOLECULE\n')
        write_prop('name', self, '\n')
        f.write('%i %i\n' % (len(self.atoms),len(self.bonds)))
        write_prop('type', self, '\n')
        write_prop('charge_type', self, '\n')
        write_prop('flags', self, '\n')
        write_prop('comment', self, '\n')

        f.write('\n@<TRIPOS>ATOM\n')
        for i,at in enumerate(self.atoms):
            f.write('%5i ' % (i+1))
            write_prop('name', at, ' ', 5, at.symbol+str(i+1))
            f.write('%10.4f %10.4f %10.4f ' % at.coords)
            write_prop('type', at, ' ', 5, at.symbol)
            write_prop('subst_id', at, ' ', 5)
            write_prop('subst_name', at, ' ', 7)
            write_prop('charge', at, ' ', 6)
            write_prop('flags', at, '\n')
            at.id = i+1

        f.write('\n@<TRIPOS>BOND\n')
        for i,bo in enumerate(self.bonds):
            f.write('%5i %5i %5i %4s' % (i+1, bo.atom1.id, bo.atom2.id, bondorders[bo.order]))
            write_prop('flags', bo, '\n')

        self.unset_atoms_id()



    def readpdb(self, f, frame):
        pdb = PDBHandler(f)
        models = pdb.get_models()
        if frame > len(models):
            raise MoleculeError('readpdb: There are only %i frames in %s' % (len(models), f.name))

        for i in models[frame-1]:
            if i.name in ['ATOM  ','HETATM']:
                x = float(i.value[0][24:32])
                y = float(i.value[0][32:40])
                z = float(i.value[0][40:48])
                atnum = PT.get_atomic_number(i.value[0][70:72].strip())
                self.add_atom(Atom(atnum=atnum,coords=(x,y,z)))

        return pdb



    def writepdb(self, f):
        pdb = PDBHandler()
        pdb.add_record(PDBRecord('HEADER'))
        model = []
        for i,at in enumerate(self.atoms):
            s = 'ATOM  %5i                   %8.3f%8.3f%8.3f                      %2s  ' % (i+1,at.x,at.y,at.z,at.symbol.upper())
            model.append(PDBRecord(s))
        pdb.add_model(model)
        pdb.add_record(pdb.calc_master())
        pdb.add_record(PDBRecord('END'))
        pdb.write(f)


    def read(self, filename, inputformat=None, frame=1):
        if inputformat is None:
            fsplit = filename.rsplit('.',1)
            if len(fsplit) == 2:
                inputformat = fsplit[1]
            else:
                inputformat = 'xyz'
        if inputformat in self._iodict:
            try:
                with open(filename, 'rU') as f:
                    ret = self._iodict[inputformat][0](self, f, frame)
            except:
                raise FileError('read: Error reading file %s' % filename)
            return ret
        else:
            raise MoleculeError('read: Unsupported file format')



    def write(self, filename, outputformat=None):
        if outputformat is None:
            fsplit = filename.rsplit('.',1)
            if len(fsplit) == 2:
                outputformat = fsplit[1]
            else:
                outputformat = 'xyz'
        if outputformat in self._iodict:
            with open(filename, 'w') as f:
                self._iodict[outputformat][1](self, f)
        else:
            raise MoleculeError('write: Unsupported file format')

    _iodict = {'xyz':(readxyz,writexyz), 'mol':(readmol,writemol), 'mol2':(readmol2,writemol2), 'pdb': (readpdb,writepdb)}

#===================================================================================================
#==== Geometry operations ==========================================================================
#===================================================================================================

    def get_mass(self):
        return sum([at.mass for at in self.atoms])


    def get_formula(self):
        atnums = [at.atnum for at in self.atoms]
        s = set(atnums)
        formula = ''
        for i in s:
            formula += PT.get_symbol(i) + str(atnums.count(i))
        return formula



    def get_center_of_mass(self):
        center = [0.0,0.0,0.0]
        total_mass = 0.0
        for at in self.atoms:
            mass = at.mass
            total_mass += mass
            for i in range(3):
                center[i] += mass*at.coords[i]
        for i in range(3):
            center[i] /= total_mass
        return tuple(center)


#============== RETHINK AND REWRITE ME================================
    def distance_to_mol(self, other, ghosts=True):
        dist = float('inf')
        for at1 in self.atoms:
            if ghosts or not at1.ghost:
                for at2 in other.atoms:
                    if not at2.ghost:
                        dist = min(dist, (at1.x-at2.x)**2 + (at1.y-at2.y)**2 + (at1.z-at2.z)**2)
        return dist**(0.5)



    def distance_to_point(self, point, ghosts=True):
        if isinstance(point, Atom):
            point = point.coords
        dist = float('inf')
        for at in self.atoms:
            if ghosts or not at.ghost:
                dist = min(dist, (at.x-point[0])**2 + (at.y-point[1])**2 + (at.z-point[2])**2)
        return dist**(0.5)

    def closest_atom(self, point, ghosts=True):
        if isinstance(point, Atom):
            point = point.coords
        dist = float('inf')
        for at in self.atoms:
            if ghosts or not at.ghost:
                newdist = (at.x-point[0])**2 + (at.y-point[1])**2 + (at.z-point[2])**2
                if newdist < dist:
                    dist = newdist
                    ret = at
        return ret

#====================================================================

    def translate(self, vec, unit='angstrom'):
        for at in self.atoms:
            at.move_by(vec, unit)



    def rotate(self, rotmat):
        rotmat = numpy.array(rotmat).reshape(3,3)
        for at in self.atoms:
            at.coords = tuple(numpy.dot(rotmat, numpy.array(at.coords)))



    def align(self, other, atoms, atoms_other=None):

        def quaternion_fit (coords_r, coords_f) :
            # this function is based on the algorithm described in
            # Molecular Simulation 7, 113-119 (1991)

            x = numpy.zeros((3, 3))
            for r, f in zip(coords_r, coords_f) :
                x = x + numpy.outer(f, r)

            c = numpy.zeros((4, 4))

            c[0, 0] = x[0, 0] + x[1, 1] + x[2, 2]
            c[1, 1] = x[0, 0] - x[1, 1] - x[2, 2]
            c[2, 2] = x[1, 1] - x[2, 2] - x[0, 0]
            c[3, 3] = x[2, 2] - x[0, 0] - x[1, 1]

            c[1, 0] = x[2, 1] - x[1, 2]
            c[2, 0] = x[0, 2] - x[2, 0]
            c[3, 0] = x[1, 0] - x[0, 1]

            c[0, 1] = x[2, 1] - x[1, 2]
            c[2, 1] = x[0, 1] + x[1, 0]
            c[3, 1] = x[2, 0] + x[0, 2]

            c[0, 2] = x[0, 2] - x[2, 0]
            c[1, 2] = x[0, 1] + x[1, 0]
            c[3, 2] = x[1, 2] + x[2, 1]

            c[0, 3] = x[1, 0] - x[0, 1]
            c[1, 3] = x[2, 0] + x[0, 2]
            c[2, 3] = x[1, 2] + x[2, 1]

            # diagonalize c
            d, v = numpy.linalg.eig(c)

            # extract the desired quaternion
            q = v[:, d.argmax()]

            # generate the rotation matrix

            u = numpy.zeros((3, 3))
            u[0, 0] = q[0]*q[0] + q[1]*q[1] - q[2]*q[2] - q[3]*q[3]
            u[1, 1] = q[0]*q[0] - q[1]*q[1] + q[2]*q[2] - q[3]*q[3]
            u[2, 2] = q[0]*q[0] - q[1]*q[1] - q[2]*q[2] + q[3]*q[3]

            u[1, 0] = 2.0 * (q[1] * q[2] - q[0] * q[3])
            u[2, 0] = 2.0 * (q[1] * q[3] + q[0] * q[2])

            u[0, 1] = 2.0 * (q[2] * q[1] + q[0] * q[3])
            u[2, 1] = 2.0 * (q[2] * q[3] - q[0] * q[1])

            u[0, 2] = 2.0 * (q[3] * q[1] - q[0] * q[2])
            u[1, 2] = 2.0 * (q[3] * q[2] + q[0] * q[1])

            return u

        frag_mv  = self.get_fragment(atoms)
        if atoms_other is None :
            frag_ref = other.get_fragment(atoms)
        else:
            frag_ref = other.get_fragment(atoms_other)

        com_mv  = numpy.array(frag_mv.get_center_of_mass())
        com_ref = numpy.array(frag_ref.get_center_of_mass())

        # move both fragments to center of mass
        frag_ref.translate(-com_ref)
        frag_mv.translate(-com_mv)

        rotmat = quaternion_fit(frag_ref.get_coordinates(), frag_mv.get_coordinates())

        transvec = com_ref - numpy.dot(rotmat, com_mv)

        self.rotate(rotmat)
        self.translate(transvec)

        return rotmat, transvec



    def guess_bonds(self, eff=1.15, addd=0.9):
    #still in dev mode a bit!
        from math import floor
        import heapq

        def element(order, ratio, atom1, atom2):
            eford = order
            if order == Bond.AR:
                eford = eff
            if order == 1 and ((atom1.symbol == 'N' and atom2.symbol == 'C') or (atom1.symbol == 'C' and atom2.symbol == 'N')):
                eford = 1.11
            return ((eford+addd)*ratio, order, ratio, atom1, atom2)

        self.delete_all_bonds()

        dmax = 1.28

        cubesize = dmax*2.1*max([at.radius for at in self.atoms])

        cubes = {}
        for i,at in enumerate(self.atoms):
            at._id = i+1
            at.free = at.connectors
            at.cube = tuple(map(lambda x: int(floor(x/cubesize)), at.coords))
            if at.cube in cubes:
                cubes[at.cube].append(at)
            else:
                cubes[at.cube] = [at]

        neighbors = {}
        for cube in cubes:
            neighbors[cube] = []
            for i in range(cube[0]-1, cube[0]+2):
                for j in range(cube[1]-1, cube[1]+2):
                    for k in range(cube[2]-1, cube[2]+2):
                        if (i,j,k) in cubes:
                            neighbors[cube] += cubes[(i,j,k)]

        heap = []
        for at1 in self.atoms:
            if at1.free > 0:
                for at2 in neighbors[at1.cube]:
                    if (at2.free > 0) and (at1._id < at2._id):
                        ratio = at1.distance_to(at2)/(at1.radius+at2.radius)
                        if (ratio < dmax):
                            heap.append(element(0, ratio, at1, at2))
                            #I hate to do this, but I guess there's no other way :/ [MH]
                            if (at1.atnum == 16 and at2.atnum == 8):
                                at1.free = 6
                            elif (at2.atnum == 16 and at1.atnum == 8):
                                at2.free = 6
                            elif (at1.atnum == 7):
                                at1.free += 1
                            elif (at2.atnum == 7):
                                at2.free += 1
        heapq.heapify(heap)

        for at in filter(lambda x: x.atnum == 7, self.atoms):
            if at.free > 6:
                at.free = 4
            else:
                at.free = 3

        while heap:
            val, o, r, at1, at2 = heapq.heappop(heap)
            step = 0.5
            if o%2 == 0:
                step = 1
            if at1.free >= step and at2.free >= step:
                o += step
                at1.free -= step
                at2.free -= step
                if o < 3.0:
                    heapq.heappush(heap, element(o,r,at1,at2))
                else:
                    if o == 1.5:
                        o = Bond.AR
                    self.add_bond(Bond(at1,at2,o))
            elif o > 0:
                if o == 1.5:
                    o = Bond.AR
                self.add_bond(Bond(at1,at2,o))

        def dfs(atom, par):
            atom.arom += 1000
            for b in atom.bonds:
                oe = b.other_end(atom)
                if b.is_aromatic() and oe.arom < 1000:
                    if oe.arom > 2:
                        return False
                    if par and oe.arom == 1:
                        b.order = 2
                        return True
                    if dfs(oe, 1-par):
                        b.order = 1 + par
                        return True

        for at in self.atoms:
            at.arom = len(list(filter(Bond.is_aromatic, at.bonds)))

        for at in self.atoms:
            if at.arom == 1:
                dfs(at, 1)
                pass

        for at in self.atoms:
            del at.cube,at.free,at._id,at.arom


# The following methods are here for no reason yet:

    def find_adjacent_hydrogens(self, atoms):
        atoms = self.get_atoms(atoms)
        hydrogens = []
        for at in atoms:
            for b in at.bonds:
                adj = b.other_end(at)
                if adj.atnum == 1:
                    hyrdogens.append(adj)
        return hydrogens


    def get_nuclear_dipole_moment(self, atoms=None):
        printsum = (atoms is None)
        atoms = self.get_atoms(atoms)
        nucdip = [(at.atnum*at.x, at.atnum*at.y, at.atnum*at.z) for at in atoms]
        if printsum:
            return list(map(sum, zip(*nucdip)))
        return nucdip


    def get_nuclear_efield_in_point(self, pointcoord):
        E = [0.0]*3
        dummy = Atom(coords=tuple(pointcoord))
        for at in self.atoms:
            dist = dummy.distance_to(at)
            vec = dummy.vector_to(at)
            E = [e + (at.atnum*c)/dist**3 for e,c in zip(E,vec)]
        return numpy.array(E)*(Units.conversion('bohr','angstrom')**2)


###=================================================================================================
###=================================================================================================
###=================================================================================================


from __future__ import unicode_literals

import copy
import numpy
import types

from .utils import Units, PT
from .pdbtools import PDBHandler, PDBRecord
from .errors import MoleculeError, PTError, FileError

__all__ = ['Atom', 'Bond', 'Molecule']

#===================================================================================================
#===================================================================================================
#===================================================================================================

class Atom(object):
    def __init__(self, atnum=0, coords=None, unit='angstrom', bonds=None, mol=None, ghost=False, **other):
        self.atnum = atnum
        self.unit = unit
        self.mol = mol
        self.ghost = ghost
        self.bonds = bonds or []
        self.properties = other

        if coords is None:
            self.coords = (0.0, 0.0, 0.0)
        elif len(coords) == 3:
            try:
                self.coords = tuple(map(float,coords))
            except:
                self.coords = tuple(coords)
        else:
            raise TypeError('__init__: Invalid coords passed')


    def str(self, symbol=True, suffix=''):
        if symbol is True:
            symbol = self.symbol
        f = lambda x: '{:>14s}'.format(x) if isinstance(x, str) else '{:>14.5f}'.format(x)
        if symbol:
            return ('{0:>10s}{1}{2}{3} '+suffix).format(symbol, *map(f,self.coords), **self.__dict__)
        return ('{0}{1}{2} '+suffix).format(*map(f,self.coords), **self.__dict__)

    def __str__(self):
        if hasattr(self,'_bondstrid'):
            return str(self._bondstrid)
        return self.str()

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

    def _check_coords(self):
        for i in self.coords:
            if not isinstance(i, (int, float, complex)):
                raise TypeError('Atom: to use this method coords should be a tuple of three numerical values')

    def convert(self, unit):
        self._check_coords()
        ratio = Units.conversion(self.unit, unit)
        self.coords = tuple(i*ratio for i in self.coords)
        self.unit = unit


    def move_by(self, vector, unit='angstrom'):
        self._check_coords()
        ratio = Units.conversion(unit, self.unit)
        self.coords = tuple(i + j*ratio for i,j in zip(self.coords, vector))


    def move_to(self, coords, unit='angstrom'):
        self._check_coords()
        ratio = Units.conversion(unit, self.unit)
        self.coords = tuple(i*ratio for i in coords)


    def distance_to(self, atom):
    #in self.unit
        self._check_coords()
        ratio = Units.conversion(atom.unit, self.unit)
        res = (atom.x*ratio - self.x)**2 + (atom.y*ratio - self.y)**2 + (atom.z*ratio - self.z)**2
        return res**(0.5)


    def vector_to(self, atom):
    #in self.unit
        self._check_coords()
        ratio = Units.conversion(atom.unit, self.unit)
        return ((atom.x*ratio - self.x), (atom.y*ratio - self.y), (atom.z*ratio - self.z))


    def distance_square(self, atom):
    #fast but does not care about units or safety; be careful
        return (self.x - atom.x)**2 + (self.y - atom.y)**2 + (self.z - atom.z)**2



#===================================================================================================
#===================================================================================================
#===================================================================================================

class Bond (object):
    AR = 1.5
    def __init__(self, atom1, atom2, order=1, mol=None, **other):
        self.atom1 = atom1
        self.atom2 = atom2
        self.order = order
        self.mol = mol
        self.properties = other


    def __str__(self):
        return '(%s)--%1.1f--(%s)'%(str(self.atom1), self.order, str(self.atom2))


    def is_aromatic(self):
        return self.order == Bond.AR


    def length(self):
    #in units of atom1
        return self.atom1.distance_to(self.atom2)


    def other_end(self, atom):
    #'hard' identity required
        if atom is self.atom1:
            return self.atom2
        elif atom is self.atom2:
            return self.atom1
        else:
            raise MoleculeError('Bond.other_end: invalid atom passed')


    def resize(self, atom, length, unit='angstrom'):
        ratio = 1.0 - Units.convert(length, unit, self.atom1.unit)/self.length()
        moving = self.other_end(atom)
        moving.move_by(tuple(i*ratio for i in moving.vector_to(atom)), moving.unit)


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
        return len(self.atoms)

    def __str__(self):
        s = '  Atoms: \n'
        for i,atom in enumerate(self.atoms):
            s += ('%5i'%(i+1)) + str(atom) + '\n'
            atom._bondstrid = i+1
        if len(self.bonds) > 0:
            s += '  Bonds: \n'
            for bond in self.bonds:
                s += str(bond) + '\n'
        for atom in self.atoms:
            del atom._bondstrid
        if self.lattice:
            s += "  Lattice:\n"
            for vec in self.lattice:
               s += '    %10.6f %10.6f %10.6f\n'%vec
        return s


    def __iter__(self):
        return iter(self.atoms)

    def __getitem__(self, key):
        return self.atoms[key]

    def __add__(self, other):
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


    def __copy__(self):
        return copy.deepcopy(self)

    copy = __copy__



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



    def distance(self, other):
        dist = float('inf')
        for at1 in self.atoms:
            for at2 in other.atoms:
                dist = min(dist, (at1.x-at2.x)**2 + (at1.y-at2.y)**2 + (at1.z-at2.z)**2)
        return dist**(0.5)



    def distance_to_point(self, point, ghosts=True):
        dist = float('inf')
        for at in self.atoms:
            if ghosts or not at.ghost:
                dist = min(dist, (at.x-point[0])**2 + (at.y-point[1])**2 + (at.z-point[2])**2)
        return dist**(0.5)



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
        dmax2 = dmax**2
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
                        ratio = at1.distance_square(at2)/((at1.radius+at2.radius)**2)
                        if (ratio < dmax2):
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


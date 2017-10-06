import collections
import math
import numpy

from ..core.errors import UnitsError


__all__ = ['Units']


class Units(object):
    """Singleton class for units converter.

    All values are based on `2014 CODATA recommended values <http://physics.nist.gov/cuu/Constants>`_.

    The following constants and units are supported:

    *   constants:

        -   ``speed_of_light`` (also ``c``)
        -   ``elementary_charge`` (also ``e`` and ``electron_charge``)
        -   ``avogadro_constant`` (also ``NA``)
        -   ``bohr_radius``

    *   distance:

        -   ``Angstrom``, ``angstrom``, ``A``
        -   ``bohr``, ``a0``, ``au``
        -   ``nm``
        -   ``pm``

    *   angle:

        -    ``degree``, ``deg``,
        -    ``radian``, ``rad``,
        -    ``grad``
        -    ``circle``

    *   energy:

        -   ``au``, ``hartree``, ``Hartree``
        -   ``ev``, ``eV``
        -   ``kcal/mol``
        -   ``kJ/mol``
        -   ``cm^-1``

    *   dipole moment:

        -   ``au``
        -   ``Cm``
        -   ``D``, ``Debye``, ``debye``

    Example::

        >>> print(Units.constants['speed_of_light'])
        299792458
        >>> print(Units.constants['e'])
        1.6021766208e-19
        >>> print(Units.convert(123, 'angstrom', 'bohr'))
        232.436313431
        >>> print(Units.convert(23.32, 'kJ/mol', 'kcal/mol'))
        5.57361376673
        >>> print(Units.conversion_ratio('kcal/mol', 'kJ/mol'))
        4.184


    """

    constants = {}
    constants['bohr_radius'] = 0.52917721067   #http://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0
    constants['avogadro_constant'] = 6.022140857e23   #http://physics.nist.gov/cgi-bin/cuu/Value?na
    constants['speed_of_light'] = 299792458   #http://physics.nist.gov/cgi-bin/cuu/Value?c
    constants['electron_charge'] = 1.6021766208e-19   #http://physics.nist.gov/cgi-bin/cuu/Value?e

    constants['NA'] = constants['avogadro_constant']
    constants['c'] = constants['speed_of_light']
    constants['e'] = constants['electron_charge']
    constants['elementary_charge'] = constants['electron_charge']

    dicts = []

    distance = {}
    distance['A'] = 1.0
    distance['angstrom'] = distance['A']
    distance['Angstrom'] = distance['A']
    distance['nm'] = distance['A'] / 10.0
    distance['pm'] = distance['A'] * 100.0
    distance['bohr'] = 1.0 / constants['bohr_radius']
    distance['a0'] = distance['bohr']
    distance['au'] = distance['bohr']
    dicts.append(distance)

    energy = {}
    energy['au'] = 1.0
    energy['hartree'] = energy['au']
    energy['Hartree'] = energy['au']
    energy['eV'] = 27.21138602   #http://physics.nist.gov/cgi-bin/cuu/Value?hrev
    energy['ev'] = energy['eV']
    energy['kJ/mol'] = 4.359744650e-21 * constants['NA']  #http://physics.nist.gov/cgi-bin/cuu/Value?hrj
    energy['kcal/mol'] = energy['kJ/mol'] / 4.184
    energy['cm^-1'] = 219474.6313702   #http://physics.nist.gov/cgi-bin/cuu/Value?hrminv
    dicts.append(energy)

    angle = {}
    angle['degree'] = 1.0
    angle['deg'] = angle['degree']
    angle['radian'] = math.pi / 180.0
    angle['rad'] = angle['radian']
    angle['grad'] = 100.0 / 90.0
    angle['circle'] = 1.0 / 360.0
    dicts.append(angle)

    dipole = {}
    dipole['au'] = 1.0
    dipole['Cm'] = constants['e'] * constants['bohr_radius'] * 1e-10
    dipole['Debye'] = dipole['Cm'] * constants['c']* 1e21
    dipole['debye'] = dipole['Debye']
    dipole['D'] = dipole['Debye']
    dicts.append(dipole)


    def __init__(self):
        raise UnitsError('Instances of Units cannot be created')


    @classmethod
    def conversion_ratio(cls, inp, out):
        """Return conversion ratio from unit *inp* to *out*."""
        for d in cls.dicts:
            if inp in d.keys() and out in d.keys():
                return d[out]/d[inp]
        raise UnitsError('Invalid conversion_ratio call: unsupported units')


    @classmethod
    def convert(cls, value, inp, out):
        """Convert *value* from unit *inp* to *out*.

        *value* can be a single number or a container (list, tuple, numpy.array etc.). In the latter case a container of the same type and length is returned. Conversion happens recursively, so this method can be used to convert, for example, a list of lists of numbers, or any other hierarchical container structure. Conversion is applied on all levels, to all values that are numbers (also numpy number types). All other values (strings, bools etc.) remain unchanged.
        """
        if value is None or isinstance(value, (bool, str)):
            return value
        if isinstance(value, collections.Iterable):
            t = type(value)
            if t == numpy.ndarray:
                t = numpy.array
            v = [cls.convert(i, inp, out) for i in value]
            return t(v)
        if isinstance(value, (int, float, numpy.generic)):
            return value * cls.conversion_ratio(inp,out)
        return value


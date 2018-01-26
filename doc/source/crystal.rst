Crystal
-------------------------

.. currentmodule:: scm.plams.interfaces.crystal

More information about CRYSTAL can be found on its `official website <http://www.crystal.unito.it>`_.

PLAMS offers a simple CRYSTAL interface which does not offer access to all possible input types of CRYSTAL just most. CRYSTAL14 was used by the developer, but as far as the developer can tell the new input features from CRYSTAL17 can be achieved with this interface. Older CRYSTAL versions are more restrictive with the input, so they have not been tested. The relevant classes are |CrystalJob| and |CrystalResults|.

.. adfsuite::

    CRYSTAL is not a part of ADF Suite. To run CRYSTAL calculations with PLAMS you need to obtain and install CRYSTAL manually.

Preparing a calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preparing an instance of |CRYSTALJob| follows the general principles for |SingleJob|. Information adjusting the input file is stored in the ``myjob.settings.input`` branch. The geometry of your system can *NOT* be supplied via the class |Molecule|. It needs to be supplied to the ``myjob.settings.input`` branch. You can use the function |mol2CrystalConf| to create a CRYSTAL-type input of your structure.
See `the manual <http://http://www.crystal.unito.it/documentation.php>`_ for further information on the different input options.



.. crystal-input:

Input
+++++

Settings must contain at least (case insensitive):

- one geometry key ('CRYSTAL','SLAB','POLYMER','HELIX','MOLECULE','EXTERNAL','DLVINPUT') (use |mol2CrystalConf|).
- one basis key ('BASISSET')
- one option_key ('options' and anything else)

The ordering inside the geometry-, basis- and option-block can be controlled:

    >>> settings.input.crystal._h = 'top line'
    >>> settings.input.crystal._1 = 'first line'
    >>> settings.input.crystal._2 = 'second line'

and so on. Note that you can also pass lists with to the ordered version. Every item will end up in one line.

To make input nicer, the 'options' key will never be printed, since the input does not allow an opening statement for this block. This way you can use

    >>> settings.input.options.bla = 'bla'
    >>> settings.input.options.test = ''
    >>> settings.input.options._h = 'FIRST'

without the 'options' beeing printed, but the section will still be closed with an 'END'.


.. crystal-runscript:


Runscript
+++++++++

The command ``crystal`` should point to the crystal binary or a runscript (so make sure it is in your ``$PATH``), that the input can be piped to. Modify ``CrystalJob._command`` if necessary. PLAMS will not clean up the mess of files that crystal produces, if you want that your runscript should do it for you. Standard output is written to ``$JN.out``.

Molecule conversion
~~~~~~~~~~~~~~~~~~~~~~~~~
Call |mol2CrystalConf| to create a CRYSTAL-type input of your structure.

Returns a given |Molecule| object as a geomkey and a list of strings that can be used to create a Settings instance for Crystal.

        >>> print(crystalMol2Conf(mol))
        'GEOMKEY', ['0 0 0', '1', 'lattice', 'nAtoms', 'ElementNumber1 X1 Y1 Z1','ElementNumber2 X2 Y2 Z2', ...]

- IFLAG,IFHR and IFSO are returned as 0,0,0 by default with Symmetry group P1 (number 1). This should allow most calculations to run. The user needs to change them if he wants to take advantage of symmetry.
- The geometry key is guessed from the number of lattice vectors. For special stuff change it by hand.
- The number of lattice vectors in the given molecule should correspond to the dimensionality of the system. Do not fill them with zeros or unit vectors, this will result in a 3D-Periodic system with wrong fractional coordinates. So stick with the standard PLAMS way of doing things.

Results extraction
~~~~~~~~~~~~~~~~~~~~~~~~~
There is no special results extraction yet, use the standard methods from the |Results| class.

Example
~~~~~~~~~~~~~~~~~~~~~~~~~
::


     common = Settings()
     geom = ['0 0 0',
     '194',
     '2.456 6.696',
     '2',
     '6 0.0     0.0     0.25',
     '6 0.333333  0.666667  0.75',
     'SLAB',
     '0 0 1',
     '1 1',
     'OPTGEOM',
     'FULLOPTG',
     'ENDGEOM']
     common.input.crystal = geom
     common.input.basisset = 'STO-3G'
     common.input.options.shrink = '9 18'
     common.input.options.scfdir = ''
     common.input.options._h = 'RHF'
     common.input.options.dft.exchange = 'PBE'
     common.input.options.dft.correlat = 'PBE'
     common.input.options.maxcycle = 250
     common.input.options.fmixing = 90
     #common.input.options.test = True

     job = CrystalJob(name='crystaltest', settings=common)
     jobres = job.run()


API
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: CrystalJob(name='plamsjob', settings=None, depend=None)
    :exclude-members: _result_type
.. autoclass:: CrystalResults
.. autofunction:: mol2CrystalConf(molecule)

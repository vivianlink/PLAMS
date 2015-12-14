Introduction
=========================


What is PLAMS
-------------------------

PLAMS (Python Library for Automating Molecular Simulation) is a collection of tools that aim at providing powerful, flexible and easily extendable Python interface to molecular modeling programs. It takes care of input preparation, job execution, file management and output processing as well as helps with building more advanced data workflows.

Usually the daily work of a computational chemist consists of running a number of calculations. Those calculations are done using one or more molecular modeling programs, like for example ADF, BAND, Turbomole or Dirac (we will call such programs *external binaries*). Obtaining results with one of such programs requires a series of steps. First, the subject of the problem (description of a molecular system, set of desired simulation parameters) has to be presented in the format understandable by molecular modeling program and written to an *input file* which is usually some sort of a text file. Then the program is executed, it runs and produces *output* which is a collection of text or binary files. That output usually contains much more information than is required for a particular problem so data of interest has to be extracted and (possibly) postprocessed. Needless to say that different computational tools use different input and output formats and are executed differently. And on top of that, in most cases many of such *single calculations* need to be performed to solve the problem of interest. That requires significant effort to be put into data hygiene to avoid confusing or overwriting input and output files from distinct calculations.

Each of the above steps, apart from actual calculation done by a molecular modeling program, needs to be performed by a human. Preparing and editing text files, creating folders in the filesystem, copying files between them and reading data from output all sum up to significant amount of tedious, repetitive and highly error-prone work. Some users deal with it using various types of automation, usually in form of ad hoc shell scripts. A few programs, like ADF Suite, offer graphical user interface to help with this kind of work, but again, input preparation and output examination, even though assisted with convenient tools, have to be done by a human. Quite often that turns out to be a performance bottleneck if we want to create big  automatic computational workflows, where output data of one calculation is used (usually after some processing) as an input to another calculation, sometimes done with different program on a different machine.

PLAMS was created to solve all these problems. It takes responsibility of all tiresome and monotonous technical details allowing you to focus on real science and your problem. It lets you do all the things mentioned above (and many more) using simple Python scripts. It gives you a helping hand with automating repetitive or complicated tasks in your daily work while still leaving you with 100% control over what is really happening with your files, disks and CPUs.


What can be done with PLAMS
----------------------------

The key design principle of PLAMS is *flexibility*. If something (by something we mean: adjusting an input parameter, executing binary with particular options, extracting a value from output etc.) can be done by hand, it can be done with PLAMS. The internal structure of the library was designed in highly modular, object-oriented manner. Thanks to that it takes very little effort to adjust its behavior to one's personal needs or to extend its functionality.


Most important features of PLAMS:
    * preparing, running and examining results of molecular modeling job from within a single Python script
    * convenient automatic file and folder management
    * running jobs in parallel without a need to prepare a special script
    * integration with popular job schedulers (OGE, SLURM, TORQUE)
    * reading and writing molecular coordinates using various formats (``xyz``, ``mol``, ``mol2``, ``pdb``)
    * prevention of multiple runs of the same job
    * easy data transfer between separate runs
    * efficient restarting in case of crash
    * full coverage of all input options and output data in ADF, BAND and DFTB
    * support for Dirac (and more coming soon)
    * easy extendable for other programs, job schedulers, file formats etc.


.. _simple_example:

Simple example
----------------------------

To provide some real life example: here is a simple PLAMS script which calculates a potential energy curve of a diatomic system::

    #type of atoms (atomic number)
    atom1 = 1
    atom2 = 1

    #interatomic distance values
    dmin = 0.3
    dmax = 1.5
    step = 0.05

    #create a list with interatomic distances
    distances = []
    dist = dmin
    while dist < dmax:
        distances.append(dist)
        dist += step

    #set single calculation parameters (single point, TZ2P/PW91)
    sett = Settings()
    sett.input.basis.type = 'TZ2P'
    sett.input.geometry.sp = True
    sett.input.xc.gga = 'PW91'

    #create a list of jobs
    jobs = []
    for d in distances:
        mol = Molecule()
        mol.add_atom(Atom(atnum=atom1, coords=(0,0,0)))
        mol.add_atom(Atom(atnum=atom2, coords=(d,0,0)))
        job = ADFJob(molecule=mol, settings=sett)
        jobs.append(job)

    #run jobs
    results = [j.run() for j in jobs]

    #extract bond energy from each calculation
    energies = [r.readkf('Energy', 'Bond Energy') for r in results]

    #convert to kcal/mol and print
    energies = [Units.convert(e, 'au', 'kcal/mol') for e in energies]
    print('d[A]    E[kcal/mol]')
    for d,e in zip(distances, energies):
        print('%.2f    %.3f' % (d,e))

Don't worry if something in the above code is incomprehensible or confusing. Everything you need to know to understand how PLAMS is working and how to write your own scripts is explained in next chapters of this documentation.

When executed, the above script creates uniquely named working folder, then runs 24 independent ADF single point calculations, each in a separate subfolder of the working folder. All files created by each run are saved in the corresponding subfolder for future reference. Finally, the following table describing the potential energy curve of a hydrogen molecule is written to the standard output::

    d[A]    E[kcal/mol]
    0.30    143.301
    0.35    36.533
    0.40    -33.410
    0.45    -79.900
    0.50    -110.823
    0.55    -131.120
    0.60    -143.997
    0.65    -151.598
    0.70    -155.418
    0.75    -156.492
    0.80    -155.572
    0.85    -153.205
    0.90    -149.793
    0.95    -145.635
    1.00    -140.959
    1.05    -135.937
    1.10    -130.699
    1.15    -125.344
    1.20    -119.950
    1.25    -114.576
    1.30    -109.267
    1.35    -104.055
    1.40    -98.967
    1.45    -94.021


What PLAMS is *not*
-------------------------

It should be stressed here that PLAMS is not a *program*, it's a *library*. That means it's not a standalone tool, it doesn't run or do anything by itself. To work it needs both an external binary on one side and properly written Python script on the other. Being a library means that PLAMS is in fact just a collection of commands and objects that can be used from within a regular Python script to perform common molecular modeling tasks.

Because of the above PLAMS won't take your hand and guide you, it won't detect and warn you if you are about to do something stupid and it won't do anything except the things you explicitly asked for. You have to understand what you are doing, you have to know how to use the binary you want PLAMS to work with and you have to have at least basic knowledge of Python programming language.


About this documentation
-------------------------

This documentation tries to be a combination of tutorial and API reference. Whenever possible, discussed concepts are explained in a "know-how" manner, with example code snippets illustrating practical aspects and possible applications of a particular class or method. On the other hand, an introduction of each object is followed by a rigorous description of its semantics (arguments taken, value returned, exceptions raised etc.). We believe that this way the right balance between comprehensiveness and intelligibility can be achieved.

The documentation was written keeping in mind users with various level of technical expertise, from programming newcomers to professional developers. Therefore some readers will find some parts trivial and redundant, while for others other parts will appear mysterious and incomprehensible. Please do not get discouraged by this fact, reading and understanding every single line of this document is not necessary for the majority of users.

The following special text formatting appears within this document:

.. note::

    Usually used to stress especially important piece of information that user needs to keep in mind while using a particular object or mechanism.

.. warning::

    Information absolutely critical for correct and secure work of the whole library. You should never violate rules given here.

.. technical::

    More detailed technical explanation of some part of the code aimed at users with better technical background. Understanding it may require advanced Python knowledge. These parts can be safely skipped without a harm to general comprehension.

.. adfsuite::

    Information for users who obtained PLAMS as a part of ADF Modeling Suite. Describes how PLAMS is integrated with other tools from the suite.


It is assumed that the reader has some basic understanding of Python programming language. Gentle introduction to Python can be found in the excellent :ref:`Python Tutorial<tutorial-index>` and other parts of the official Python documentation.

Majority of examples presented within this document uses as an external binary either ADF, BAND or DFTB. Please refer to the corresponding program's manual if some clarification is needed.

The last section presents a collection of real life example scripts that cover various possible applications of PLAMS. Due to early stage of the project this section is not yet too extensive. Users are warmly welcome to help with enriching it, as well as to provide any kind of feedback regarding either PLAMS itself or this documentation to support@scm.com

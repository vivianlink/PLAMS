Getting started
=========================

This section contains general information about installing and running PLAMS.

Library contents
-------------------------

PLAMS comes in form of a Python 2 package installed in the Python interpreter that is shipped with the ADF Suite. There is no need to install anything manually, everything is already there. If you have the ADF Suite properly installed you can invoke its Python interpreter by typing ``startpython`` in your command line. From there PLAMS is visible as a subpackage of the ``scm`` package, so you can import it with::

    from scm.plams import *

All PLAMS modules are then imported and the following identifiers are added to the main namespace:

.. hlist::
    :columns: 5

    * ``ADFJob``
    * ``ADFNumGradJob``
    * ``ADFResults``
    * ``Atom``
    * ``BANDJob``
    * ``BANDResults``
    * ``Bond``
    * ``DFTBJob``
    * ``DFTBNumGradJob``
    * ``DFTBResults``
    * ``DensfJob``
    * ``DensfResults``
    * ``DiracJob``
    * ``DiracResults``
    * ``FCFJob``
    * ``FCFResults``
    * ``GridRunner``
    * ``JobRunner``
    * ``KFFile``
    * ``KFReader``
    * ``Molecule``
    * ``MultiJob``
    * ``PDBHandler``
    * ``PDBRecord``
    * ``PeriodicTable`` or (``PT``)
    * ``Results``
    * ``Settings``
    * ``Units``
    * ``init``
    * ``finish``
    * ``log``
    * ``load``
    * ``load_all``
    * ``add_to_class``
    * ``add_to_instance``

.. technical::

    Usually in Python ``import *`` is considered a bad practice and discouraged. However, PLAMS internally takes care about namespace cleanliness and imports only necessary things with ``import *``. Importing with ``import *`` allows you to use identifiers like ``Molecule`` or ``BANDJob`` instead of ``scm.plams.Molecule`` or ``scm.plams.BANDJob`` which makes your scripts shorter and more readable. Throughout this documentation it is assumed that ``import *`` is used so identifiers are not prefixed with ``scm.plams.`` in any example.

Besides regular modules PLAMS consists of three following files:

    * defaults file: ``$ADFHOME/scripting/plams_defaults.py``
    * master script: ``$ADFBIN/plams``
    * restart script: ``$ADFBIN/plams_restart``

The defaults file contains a list of commands that adjust various aspects of PLAMS behavior. If you wish to globally change one of those you can do it by modifying this file. Defaults file is self-explanatory in such a way that each command is preceded with a comment describing what it does. It is a good idea to read this file at some point to have an overview of what and how can be tweaked.

The master script is explained in details further in this chapter. For the description of the restart script see :ref:`restarting`.

.. note::

    If you have an access to the development version of ADF Suite you can find PLAMS source code in ``$ADFHOME/scripting/python/scmlib/src/scm/plams/``. Moreover, master and restart scripts are located in ``$ADFHOME/Install/plams`` rather than ``$ADFBIN/plams``.



Running PLAMS
-------------------------

A PLAMS script is in fact a general Python script that makes use of classes and functions defined in the PLAMS library. To work properly such a script has to follow two simple restrictions. At the very beginning of the script one must initialize PLAMS environment by calling public function |init|. Without this initialization almost every PLAMS function or class call results in a crash. Similarly, at the end of the script public function |finish| needs to be called to properly clean the main working folder and ensure proper closure of parallel scripts. You can find more detailed information about these two functions in :ref:`public-functions` section.

To sum up, a proper PLAMS script needs to look like this::

    from scm.plams import *
    init()
    # =========
    # actual script here
    # ...
    # =========
    finish()

and it has to be executed from the command line with ``startpython [filename]``. Keeping these restrictions in mind can be a bit inconvenient, so PLAMS comes with an executable script called master script that takes care of proper initialization and exit. See the next section for details.

Of course PLAMS can be also run interactively using Python interpreter. After starting the proper Python interpreter with ``startpython`` command you need to manually import and initialize the environment with ``from scm.plams import *`` and
|init|. Then you can interactively run any Python command relying on PLAMS. If you run any jobs in the interactive mode make sure to use |finish| before closing the interpreter to ensure that all jobs are gently finished and the main working folder is cleaned.



.. _master-script:

Master script
-------------------------

The master script is an executable file called ``plams``. It is located in ``$ADFBIN`` folder and thus it can be directly executed from you command line. You can type ``plams -h`` or ``plams --help`` for a short help message.

The master script takes care of all the important things mentioned earlier in this chapter, namely using the right Python interpreter, properly importing and initializing PLAMS and cleaning after all the work is done. Thanks to that your actual script does not need to contain import, init or finish commands.

Without the master script::

    from scm.plams import *
    init()
    # =========
    # actual script here
    # ...
    # =========
    finish()

executed with ``startpython [filename]``.

With the master script::

    # =========
    # actual script here
    # ...
    # =========

executed with ``plams [filename]``.

In general it is recommended to use the master script because it is just easier and more convenient than "manual" execution, but from the technical standpoint there is no difference.

Optional arguments
~~~~~~~~~~~~~~~~~~~~~~~~~

The master script accepts a few optional arguments that may come handy in some situations. It allows to pick custom name and location for the main working folder. The main working folder is an initially empty folder that is created on |init|. All files produced by PLAMS and other programs executed by it are saved in the main working folder (usually in some of its subfolders). Each separate run of PLAMS has its separate main working folder.

By default the main working folder is located in the directory where your script was executed and is called ``plams.[number]`` where *[number]* is a PID of Python process. You can change this behavior by supplying ``-p`` and ``-f`` arguments to master script to choose, respectively, the location and the name of the main working folder. For example the command::

    plams -p /home/user/science -f polymers myscript.plms

will use ``/home/user/science/polymers`` as the main working folder regardless where this command was executed.

.. note::

    If you wish to use custom main working folder name make sure to pick a name that is not present in the particular location. Trying to use an existing folder as PLAMS main working folder results in an error.

With the master script you can also pass variables to your script directly from the command line. This can be done with ``-v`` parameter that follows the syntax ``-v variable=value`` (mind the lack of spaces around equal sign, it is a must). For a script executed that way there is an additional global string variable with the name ``variable`` and the value ``'value'`` visible in script's namespace. For example if the script in file ``script1.plms`` looks like this::

    print 'Chosen basis: ', basis
    print 'Number of points: ', n
    print type(n)
    # do something depending on n and basis

and you execute it with::

    plams -v n=10 -v basis=DZP script1.plms

the standard output will be::

    Chosen basis: DZP
    Number of points: 10
    str
    [output of "do something"]

Three important things to keep in mind about ``-v`` parameter:

    * no spaces around equal sign,
    * each variable requires separate ``-v``,
    * the type of the variable is **always** string (like in the example above). If you want to pass some numerical values make sure to convert them from strings to numbers inside your script.

Finally, the master script can be called with more than one positional argument, like for example::

    plams script1.plms script2.plms script3.plms

All files supplied that way are concatenated into one script and then executed (that means things declared in script1 are visible in script2 and script3). Using this feature for completely unrelated scripts is probably not a good idea, but it can be useful for example when first files contain just definitions of your own functions, derived classes, settings tweaks etc. that are then used in the last file::

    plams config/debug_run.plms settings/adf/adf_fde.plms actual_script.plms

That way you can build your own library of reusable code snippets for tasks that are most frequently occurring in your daily work, customize PLAMS according to your personal preferences and make your working environment truly modular.

By the way, your scripts do not need to have ``.plms`` file extension, it is just a convention. They can be any text files.

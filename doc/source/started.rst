Getting started
=========================

This section contains general information about installing and running PLAMS.

Library contents
-------------------------

PLAMS comes in form of a Python package compatible with both Python 2 and Python 3.
The root folder of the package contains the following subfolders: ``src`` for source files of all the modules, ``utils`` for additional utilities (see below) and ``doc`` for the source of this documentation. If you wish to run PLAMS with your own Python, you need to add ``src`` subfolder to your ``$PYTHONPATH`` environmental variable (or make Python look for packages in that location in any other way).

PLAMS requires the following Python packages to work properly: `numpy <http://www.numpy.org>`_, `dill <https://pypi.python.org/pypi/dill>`_ (enhanced pickling) and `six <https://pypi.python.org/pypi/six>`_ (Python 2/3 compatibility). If you are using reasonably recent Python, these packages can be automatically fetched from official Python repositories by typing ``pip install dill six`` in your command line (on some systems you need to use ``pip2`` instead of ``pip`` to install packages for Python 2). More information about installing packages manually can be found `here <http://python-packaging-user-guide.readthedocs.org/en/latest/installing/>`_.

.. adfsuite::

    ADF Suite comes with a built-in Python 2 interpreter equipped with some preinstalled useful packages (including ``dill`` and ``six``) and configured to work with PLAMS out of the box. You can invoke this interpreter by typing ``startpython`` in your command line.


Inside Python interpreter or in Python scripts PLAMS is visible as a subpackage of the ``scm`` package, so you can import it with::

    from scm.plams import *

All PLAMS modules are then imported and all useful identifiers are added to the main namespace.

.. technical::

    Usually in Python ``import *`` is considered a bad practice and discouraged. However, PLAMS internally takes care of namespace cleanliness and imports only necessary things with ``import *``. Importing with ``import *`` allows you to use identifiers like ``Molecule`` or ``BANDJob`` instead of ``scm.plams.Molecule`` or ``scm.plams.BANDJob`` which makes your scripts shorter and more readable. Throughout this documentation it is assumed that ``import *`` is used so identifiers are not prefixed with ``scm.plams.`` in any example.


Besides regular modules PLAMS consists of three following files located in the ``utils`` subfolder:
    *   defaults file: ``plams_defaults.py``
    *   master script: ``plams.py`` (executable)
    *   restart script: ``plams_restart.py`` (executable)


The defaults file contains a list of commands that adjust various aspects of PLAMS behavior. If you wish to globally change some setting you can do it by modifying this file. Defaults file is self-explanatory in such a way that each command is preceded with a comment describing what it does. It is a good idea to read this file at some point to have an overview of what and how can be tweaked. See also |init| if you wish to use several different defaults files.

Master script and restart script are executables that provide a convenient way of running PLAMS scripts. The master script is explained in details further in this chapter. For the description of the restart script see :ref:`restarting`. If you wish to use them, it's a good idea to add ``utils`` subfolder to your ``$PATH`` variable so that you can call them directly from your command line.

.. note::

    You can edit ``plams.py`` and ``plams_restart.py`` to make them use your preferred Python interpreter. Just adjust the first line.

.. adfsuite::

    In ADF Suite there are two additional executables (``plams`` and ``plams_restart``) placed directly in ``$ADFBIN`` folder (so they should be accessible from your command line without any ``$PATH`` manipulation). They are just shortcuts for ``plams.py`` and ``plams_restart.py`` that always use ADF Suite Python.


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

and it has to be executed from the command line with ``python [filename]`` (or ``python2 [filename]`` or ``startpython [filename]``, depending on your setup). Keeping these restrictions in mind can be a bit inconvenient, so PLAMS comes with an executable script called master script that takes care of proper initialization and exit. See the next section for details.

Of course PLAMS can be also run interactively using Python interpreter. After starting your favorite Python interpreter you need to manually import and initialize the environment with ``from scm.plams import *`` and |init|. Then you can interactively run any Python command relying on PLAMS. If you run any jobs in the interactive mode make sure to use |finish| before closing the interpreter to ensure that all jobs are gently finished and the main working folder is cleaned.



.. _master-script:

Master script
-------------------------

The master script is an executable file called ``plams.py`` located in ``utils`` subfolder. You can type ``plams.py -h`` or ``plams.py --help`` for a short help message.

The master script takes care of all the important things mentioned earlier in this chapter, like properly importing and initializing PLAMS and cleaning after all the work is done. Thanks to that your actual script does not need to contain import, init or finish commands.

Without the master script::

    from scm.plams import *
    init()
    # =========
    # actual script here
    # ...
    # =========
    finish()

executed with ``python [filename]``.

With the master script::

    # =========
    # actual script here
    # ...
    # =========

executed with ``plams.py [filename]``.

In general it is recommended to use the master script because it is just easier and more convenient than "manual" execution, but from the technical standpoint there is no difference.

.. adfsuite::

    In ADF Suite you can use ``plams`` instead of ``plams.py``. Note that this way your scripts are always run with ADF Suite Python, ignoring first line of ``plams.py``.

Optional arguments
~~~~~~~~~~~~~~~~~~~~~~~~~

The master script accepts a few optional arguments that may come handy in some situations. It allows to pick custom name and location for the main working folder. The main working folder is an initially empty folder that is created on |init|. All files produced by PLAMS and other programs executed by it are saved in the main working folder (usually in some of its subfolders). Each separate run of PLAMS has its separate main working folder.

By default the main working folder is located in the directory where your script was executed and is called ``plams.xxxxx`` where *xxxxx* is the PID of the Python process. You can change this behavior by supplying ``-p`` and ``-f`` arguments to master script to choose, respectively, the location and the name of the main working folder. For example the command::

    plams.py -p /home/user/science -f polymers myscript.plms

will use ``/home/user/science/polymers`` as the main working folder regardless where this command was executed.

.. note::

    It is **strongly recommended** to perform each PLAMS run in a fresh, empty folder (i.e. supplying a non-existing folder name and letting PLAMS automatically create it). Using an existing folder is possible for various compatibility reasons with other tools, but can lead to unpredictable behavior if the folder was not empty.

With the master script you can also pass variables to your script directly from the command line. This can be done with ``-v`` parameter that follows the syntax ``-v variable=value`` (mind the lack of spaces around equal sign, it is a must). For a script executed that way there is an additional global string variable with the name ``variable`` and the value ``'value'`` visible in script's namespace. For example if the script in file ``script1.plms`` looks like this::

    print('Chosen basis: ' + basis)
    print('Number of points: ' + n)
    print(type(n))
    # do something depending on n and basis

and you execute it with::

    plams.py -v n=10 -v basis=DZP script1.plms

the standard output will be::

    Chosen basis: DZP
    Number of points: 10
    str
    [output of "do something"]

Three important things to keep in mind about ``-v`` parameter:
    *   no spaces around equal sign,
    *   each variable requires separate ``-v``,
    *   the type of the variable is **always** string (like in the example above). If you want to pass some numerical values make sure to convert them from strings to numbers inside your script.

Finally, the master script can be called with more than one positional argument, like for example::

    plams.py script1.plms script2.plms script3.plms

All files supplied that way are concatenated into one script and then executed (that means things declared in script1 are visible in script2 and script3). Using this feature for completely unrelated scripts is probably not a good idea, but it can be useful for example when first files contain just definitions of your own functions, derived classes, settings tweaks etc. that are then used in the last file::

    plams.py config/debug_run.plms settings/adf/adf_fde.plms actual_script.plms

That way you can build your own library of reusable code snippets for tasks that are most frequently occurring in your daily work, customize PLAMS according to your personal preferences and make your working environment truly modular.

By the way, your scripts do not need to have ``.plms`` file extension, it is just a convention. They can be any text files.

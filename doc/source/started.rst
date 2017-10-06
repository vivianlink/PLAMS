Getting started
=========================

This section contains general information about installing and running PLAMS.



Library contents
-------------------------

PLAMS comes in a form of Python 3 package (earlier versions were also compatible with Python 2, but as Python 3 becomes more and more popular, we decided to drop Python 2 compatibility).

The root folder of the package contains the following subfolders: ``src`` for source files of all the modules, ``bin`` for executable scripts and ``doc`` for the source of this documentation. The source of the package is divided into subpackages:

*   ``core``: all the essential modules defining the skeleton of the library
*   ``interfaces``: modules with interfaces to external binaries
*   ``tools``: modules with small utilities like periodic table, file readers etc.
*   ``plams_defaults``: a separate file defining all the adjustable options (see below for details)

Another imporant part of PLAMS is the executable script used for running or restarting your workflows. It is called simply ``plams`` and it's located in the ``bin`` folder. We refer to it as the *master script*. Further in this section you can find the dedicated chapter explaining the usage of the master script.



Installing PLAMS
-------------------------

You can install PLAMS on your computer using one of the following ways:

1.  If you are using ADFSuite, PLAMS is already intalled there (``$ADFHOME/scripting/plams``) and configured to work with a built-in Python coming with ADFSuite (you can access it with ``startpython`` command). The master script is added to ``$ADFBIN``, so it should be directly visible from your command line.

2. The latest PLAMS stable release can be installed directly from PyPi by typing ``pip install plams`` in your command line. The master scipt will be installed along other global system executables (platform dependent) and should be visible from your command line.

3. Any current or historic version can be downloaded or cloned from PLAMS `github page <https://github.com/SCM-NV/PLAMS>`_. The ``release`` branch points to the latests stable release, while the ``master`` branch is the most recent development snapshot. Please don't forget to adjust your environment: add the ``src`` subfolder to your ``$PYTHONPATH`` and the ``bin`` subfloder to ``$PATH``.


.. note::

    You can combine methods 2 and 3 and fetch PLAMS from GitHub using ``pip``:
    ``pip install git+https://github.com/SCM-NV/PLAMS.git@master``
    (make sure to have Git installed and to choose the proper branch)

PLAMS requires the following Python packages as dependencies: `numpy <http://www.numpy.org>`_ and `dill <https://pypi.python.org/pypi/dill>`_ (enhanced pickling).
When you install PLAMS using ``pip``, these packages will be installed automatically. If you use ADFSuite, they are already there. In any other case you can install them with ``pip install [package name]``.

Inside your Python interpreter or in Python scripts PLAMS is visible as a subpackage of the ``scm`` package, so you can import it with::

    from scm.plams import *

All PLAMS modules are then imported and all useful identifiers are added to the main namespace.

.. note::

    Usually in Python ``import *`` is considered a bad practice and discouraged. However, PLAMS internally takes care of namespace cleanliness and imports only necessary things with ``import *``. Importing with ``import *`` allows you to use identifiers like ``Molecule`` or ``BANDJob`` instead of ``scm.plams.Molecule`` or ``scm.plams.BANDJob`` which makes your scripts shorter and more readable. Throughout this documentation it is assumed that ``import *`` is used so identifiers are not prefixed with ``scm.plams.`` in any example. If, for some reason, you don't like it, feel free to use ``import scm.plams`` or ``from scm import plams``.



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

and it has to be executed from the command line with ``python [filename]`` (``startpython [filename]`` in case of ADFSuite Python). Keeping these restrictions in mind can be a bit inconvenient, so PLAMS comes with an executable script called master script that takes care of the proper initialization and exit. See :ref:`master-script` for details.

Of course PLAMS can be also run interactively using Python interpreter. After starting your favorite Python interpreter you need to manually import and initialize the environment with ``from scm.plams import *`` and |init|. Then you can interactively run any Python command relying on PLAMS. If you run any jobs in the interactive mode make sure to use |finish| before closing the interpreter to ensure that all the jobs are gently finished and the main working folder is cleaned.



.. _plams-defaults:

Defaults file
-------------------------

The defaults file is called ``plams_defaults`` and it is located in ``src/scm/plams``. If you installed PLAMS using ``pip``, the defaults file could be a bit difficult to find (usually somewhere in ``site-packages`` subfolder of your Python). If you can't find it, just get a fresh copy from `GitHub <https://github.com/SCM-NV/PLAMS/blob/master/src/scm/plams/plams_defaults>`_, put it somewhere on your disk and set ``$PLAMSDEFAULTS`` environmental variable pointing to it. See |init| to see how PLAMS looks for the defaults file.

The defaults file contains a list of commands that adjust various aspects of PLAMS behavior. The file is self-explanatory: each command is preceded with a comment explaining what it does. We **strongly recommend** to read this file to have an overview of what and how can be tweaked (it's not long, I promise).

If you wish to globally change some setting you can do it by modifying the defaults file. Changes you make there are going to affect all further PLAMS runs. To tweak a particular setting just for a single script, it is better do introduce this change at inside the script itself. This is done by copying corresponding lines from the defaults file at the top of your script, for example::

    config.log.stdout = 1
    config.job.pickle = False
    config.default_jobrunner = JobRunner(parallel=True, maxjobs=8)



.. _master-script:

Master script
-------------------------

The master script is an executable file called simply ``plams`` located in the ``bin`` subfolder. If your ``$PATH`` variable is configured properly, you can type in your command line ``plams -h`` or ``plams --help`` for a short help message.

The master script takes care of all the important things mentioned earlier in this chapter, like properly importing and initializing PLAMS and cleaning after all the work is done. Thanks to that your actual script does not need to contain import, init or finish commands.

Without the master script::

    from scm.plams import *
    init()
    # =========
    # actual script here
    # ...
    # =========
    finish()

executed with ``python [filename]`` (or ``startpython [filename]``).

With the master script::

    # =========
    # actual script here
    # ...
    # =========

executed with ``plams [filename]``.

Besides that, the master script offers several convenient command line arguments allowing you to tune the behavior of your script without a need to edit the script itself.


Working folder location
~~~~~~~~~~~~~~~~~~~~~~~~~

The master script allows you to pick custom name and location for the main working folder. The main working folder is an initially empty folder that is created on |init|. All files produced by PLAMS and other programs executed by it are saved in the main working folder (usually in some of its subfolders). Each separate run of PLAMS has its separate main working folder.

By default the main working folder is located in the directory where your script was executed and is called ``plams.xxxxx`` where *xxxxx* is the PID of the Python process. You can change this behavior by supplying ``-p`` and ``-f`` (alternatively, ``--path`` and ``--folder``) arguments to the master script to choose, respectively, the location and the name of the main working folder. For example the command::

    plams -p /home/user/science -f polymers myscript.plms

will use ``/home/user/science/polymers`` as the main working folder regardless where this command was executed.

.. note::

    It is **strongly recommended** to perform each PLAMS run in a fresh, empty folder (i.e. supplying a non-existing folder name and letting PLAMS automatically create it). Using an existing folder is possible for various compatibility reasons with other tools, but can lead to unpredictable behavior if the folder was not empty.


Passing variables
~~~~~~~~~~~~~~~~~~~~~~~~~

With the master script you can also pass variables to your script directly from the command line. This can be done with ``-v`` (or ``--var``) parameter that follows the syntax ``-v variable=value`` (mind the lack of spaces around equal sign, it is a must). For a script executed that way, there is an additional global string variable with the name ``variable`` and the value ``'value'`` visible in the script's namespace. For example if the script in file ``script1.plms`` looks like this::

    print('Chosen basis: ' + basis)
    print('Number of points: ' + n)
    print(type(n))
    # do something depending on n and basis

and you execute it with::

    plams -v n=10 -v basis=DZP script1.plms

the standard output will be::

    Chosen basis: DZP
    Number of points: 10
    str
    # [output of "do something"]

Three important things to keep in mind about ``-v`` parameter:

*   no spaces around equal sign,
*   each variable requires separate ``-v``,
*   the type of the variable is **always** string (like in the example above). If you want to pass some numerical values make sure to convert them from strings to numbers inside your script.


Importing past jobs
~~~~~~~~~~~~~~~~~~~~~~~~~

You can instruct the master script to load the results of some previously run jobs by supplying the path to the main working folder of a finished PLAMS run with ``-l`` (or ``--load``) parameter. To find out why this could be useful, please see |pickling| and |RPM|.

This mechanism is equivalent to using |load_all| function at the beginning of your script. That means executing your script with ``plams -l /some/path myscript.plms`` works just like putting ``load_all(/some/path)`` at the beginning of ``myscript.plms`` and running it with ``plams myscript.plms``. The only difference is that, when using |load_all| inside the script, you can access each of the loaded jobs separately by using the dictionary returned by |load_all|. This is not possible with ``-l`` parameter, but all the loaded jobs will be visible to |RPM|.

Multiple different folders can be supplied with ``-l`` parameter, but each of them requires a separate ``-l`` flag::

    plams -l /some/path -l /other/path myscript.plms


Restarting failed script
~~~~~~~~~~~~~~~~~~~~~~~~~

The master script can be called with an additional argumentless ``-r`` parameter (or ``--restart``). That way the master script is executed in "restart mode". The restart mode requires specifying ``-f`` flag and it has to point to an existing folder (otherwise ``-r`` flag is ignored).

In the restart mode PLAMS will import all the successful jobs from the given folder and then use the same folder for the current run. For example, after::

    $ plams myscript.plms
    [17:28:40] PLAMS working folder: /home/user/plams.12345
    #[some successful work]
    [17:56:22] Execution interrupted by the following exception:
    #[exception details]

you can edit ``myscript.plms``, remove the cause of crash and restart your script with::

    $ plams -r -f plams.12345 myscript.plms

(the above command needs to be executed in ``/home/user``. Otherwise, you need to add ``-p /home/user`` to tell the master script where to look for ``plams.12345``).

For more detailed explanation of the restarting mechanism, please see |RPM|, |pickling| and |restarting|.


Multiple input scripts
~~~~~~~~~~~~~~~~~~~~~~~~~

The master script can be called with more than one positional argument, like for example::

    plams script1.plms script2.plms script3.plms

All the files supplied that way are concatenated into one script and then executed (that means things declared in script1 are visible in script2 and script3). Using this feature for completely unrelated scripts is probably not a good idea, but it can be useful for example when first files contain just definitions of your own functions, derived classes, settings tweaks etc. that are then used in the last file::

    plams config/debug_run.plms settings/adf/adf_fde.plms actual_script.plms

That way you can build your own library of reusable code snippets for tasks that are most frequently occurring in your daily work, customize PLAMS according to your personal preferences and make your working environment truly modular.

By the way, your scripts do not need to have ``.plms`` file extension, it is just a convention. They can be any text files.



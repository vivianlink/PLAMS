Results
-------------

.. currentmodule:: scm.plams.core.results

Every |Job| instance has an associated |Results| instance created automatically on job creation and stored in ``results`` attribute. The goal of |Results| is to take care of the job folder after the execution of the job is finished: gather information about produced files, help to manage them and extract data of interest from them. From the technical standpoint, |Results| is the part of the job running mechanism that is responsible for thread safety and proper synchronization in parallel job execution.


Files in the job folder
~~~~~~~~~~~~~~~~~~~~~~~~~

Directly after execution of a job is finished (see :ref:`job-life-cycle`), the job folder gets scanned by :meth:`~Results.collect` method. All files present there, including files in subfolders, are gathered in a list stored in ``files`` attribute of the |Results| instance. Entries in this list correspond to paths to files relative to the job folder, so files on the top level are stored by their names and files in subfolders by something like ``childjob/childjob.out``.

.. note::

    Files produced by :ref:`pickling` are excluded from this mechanism. Every file with ``.dill`` extension is simply ignored by |Results|.

If you need an absolute path to some file, the bracket notation known from dictionaries is defined for |Results| objects. When supplied with an entry from ``files`` list, it returns the absolute path to that file. This mechanism is read-only::

    >>> r = j.run()
    >>> print(r.files)
    ['plamsjob.err', 'plamsjob.in', 'plamsjob.out', 'plamsjob.run']
    >>> print(r['plamsjob.out'])
    /home/user/plams.12345/plamsjob/plamsjob.in
    >>> r['newfile.txt'] = '/home/user/abc.txt'
    TypeError: 'Results' object does not support item assignment

In the bracket notation and in every other context regarding |Results|, whenever you need to pass a string with a filename, shortcut ``$JN`` can be used for the job name::

    >>> r.rename('$JN.out', 'outputfile')
    >>> r.grep_file('$JN.err', 'NORMAL TERMINATION')
    >>> print(r['$JN.run'])
    /home/user/plams.12345/plamsjob/plamsjob.run

Some external binaries produce fixed name files during execution (like for example ADF's ``TAPE21``). If one wants to automatically rename those files it can be done with ``_rename_map`` class attribute::

    >>> print(ADFResults._rename_map)
    {'TAPE13': '$JN.t13', 'TAPE21': '$JN.t21'}

As presented in the above example, ``_rename_map`` is a dictionary defining which files should be renamed and how. Renaming is done only once, on :meth:`~Results.collect`. In generic |Results| class ``_rename_map`` is an empty dictionary.



.. _parallel:

Synchronization of parallel job executions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the main advantages of PLAMS is the ability to run jobs in parallel. The whole job execution mechanism is designed in such a way that there is no need to prepare a special parallel script, the same scripts can be used for both serial and parallel execution. However, it is important to have a basic understanding of how parallelism in PLAMS works to avoid deadlocks and maximize the performance of your scripts.

To run your job in parallel you need to use a parallel job runner::

    >>> pjr = JobRunner(parallel=True)
    >>> myresults = myjob.run(jobrunner=pjr)

Parallelism is not something that is "enabled" or "disabled" for the entire script: within one script you can use multiple job runners, some of them may be parallel and some may be serial. However, if you wish to always use the same |JobRunner| instance, it is convenient to set is as a default at the beginning of your script::

    >>> config.default_jobrunner = JobRunner(parallel=True)

All |run| calls without ``jobrunner`` argument supplied will now use this instance.

When you run a job using a serial job runner, all steps of |run| (see :ref:`job-life-cycle`) are done in the main thread and |Results| instance is returned at the end. On the other hand, when a parallel job runner is used, a new thread is spawned at the beginning of |run| and all further work is done in this thread. Meanwhile the main thread proceeds with execution of the script. The important thing is that |run| method called in the main thread returns |Results| instance and allows the whole script to proceed even though the job is still running in a separate thread. This |Results| instance acts as a "guardian" protecting the job from being accessed while it is still running. Every time you call a method of any |Results| instance, the guardian checks the status of associated job and if the job is not yet finished, it forces the thread from which the call was done to wait. Thanks to that there is no need to explicitly put synchronization points in the script -- results requests serve for that purpose.

.. warning::

    You should **NEVER** access results in any other way than by a **method** of |Results| instance.

The |Results| class is designed in such a way, that each of its methods automatically gets wrapped with the access guardian when |Results| instance is created. That behavior holds for any |Results| subclasses and new methods defined by user, so no need to worry about guardian when extending |Results| functionality. Also |binding_decorators| recognize when you try to use them with |Results| and act accordingly. Methods whose names end with two underscores, as well as :meth:`~Results.refresh`, :meth:`~Results.collect`, :meth:`~Results._clean` are not wrapped with the guardian. The guardian gives special privileges (earlier access) to |postrun| and :meth:`~scm.plams.core.basejob.Job.check` (see :ref:`prerun-postrun`).

.. technical::

    The behavior described above is implemented using Python mechanism called metaclasses. The guardian is simply a decorator wrapping instance methods.

If you never request any results of your job and just want to run it, |finish| method works as a global synchronization point. It waits for all spawned threads to end before cleaning the environment and exiting your script.

Examples
++++++++

This section provides a handful of examples together with an explanation of common pitfalls and good practices one should keep in mind when writing parallel PLAMS scripts.

Let us start with a simple parallel script that takes all ``.xyz`` files in a given folder and for each one calculates a dipole moment magnitude using a single point ADF calculation:

.. code-block:: python
    :linenos:

    import os
    config.default_jobrunner = JobRunner(parallel=True)

    folder = '/home/user/xyz'
    filenames = sorted(filter(lambda x: x.endswith('.xyz'), os.listdir(folder)))

    s = Settings()
    s.input.basis.type = 'DZP'
    s.input.geometry.SP = True
    s.input.xc.gga = 'PBE'

    jobs = [ADFJob(molecule=Molecule(os.path.join(folder,f)), name=f.rstrip('.xyz'), settings=s) for f in filenames]
    results = [job.run() for job in jobs]

    for r in results:
        dipole_vec = r.readkf('Properties', 'Dipole')
        dipole_magn = sum([a*a for a in dipole_vec])**0.5
        print(r.job.name + '\t\t' + str(dipole_magn))

For an explanation purpose let us assume that folder ``/home/user/xyz`` contains three files: ``Ammonia.xyz``, ``Ethanol.xyz``, ``Water.xyz``. When you run this script the standard output will look something like::

    [14:34:17] Job Ammonia started
    [14:34:17] Job Ethanol started
    [14:34:17] Job Water started
    [14:34:17] Waiting for job Ammonia to finish
    [14:34:20] Job Water finished with status 'successful'
    [14:34:20] Job Ammonia finished with status 'successful'
    Ammonia         0.594949300726
    [14:34:21] Waiting for job Ethanol to finish
    [14:34:25] Job Ethanol finished with status 'successful'
    Ethanol         0.594626131104
    Water       0.708226707277

As you can see, ``print`` statements from line 18 are mixed with automatic logging messages. Let us examine in more detail what causes such a behavior. To do so we will follow what happens in the main thread. In line 5 an alphabetically sorted list of ``.xyz`` files from the given directory is created.  The list of jobs prepared in line 12 follows the same order so the job named "Ethanol" will come after "Ammonia" and before "Water". Line 13 is in fact a for loop that goes along the list of jobs, runs each of them and collects returned |Results| instances in a list called ``results``. If we were using a serial job runner all work would happen in this line: the "Ethanol" job would start only when "Ammonia" was finished, "Water" would wait for "Ethanol" and the main thread would proceed only when "Water" is done.

In our case we are using a parallel job runner so the first job is started and quickly moves to a separate thread allowing the main thread to proceed to another instruction, which in this case is |run| of the "Ethanol" job (and so on). Thanks to that all jobs are started almost immediately one after another, corresponding |Results| are gathered and the main thread proceeds to line 15 while all three jobs are running "in the background", handled by separate threads. Now the main thread goes along ``results`` list (which follows the same order as ``filenames`` and ``jobs``) and tries to obtain a dipole vector for each job. It uses ``readkf`` method of |Results| instance associated with the "Ammonia" job and since this job is still running, the main thread hangs and waits for the job to finish. Meanwhile we can see that the "Water" job ends and this fact is logged. Quickly after that also the "Ammonia" job finishes and the main thread obtains ``dipole_vec``, calculates ``dipole_magn`` and prints it. Now the ``for`` loop in line 15 continues, this time for the "Ethanol" job. This job seems to be a bit longer than "Ammonia", so it is still running and the main thread again hangs on the ``readkf`` method. After finally obtaining the dipole vector, calculating the magnitude and printing it, the ``for`` loop goes on with its last iteration, the "Water" job. This time there is no need to wait since the job is already finished - the result is calculated and printed immediately.

Knowing that, let us wonder what would happen if the order of jobs was different. If "Ethanol" was the first job on the list, by the time its results would be obtained and printed, both other jobs would have finished, so no further waiting would be needed. On the other hand, if the order was "Water"--"Ammonia"--"Ethanol", the main thread would have to wait every time when executing line 16.

The most important lesson from the above is: the order in which you start jobs does not matter (too much), it is the order of results requests that makes a difference. Of course in our very simple example it influences only the way in which results are mixed with log messages, but in more complicated setups it can directly affect the runtime of your script.

By the way, to solve the problem with mixed ``print`` statements and logging messages one could first store data and print it when all results are ready::

    to_print = []
    for r in results:
        dipole_vec = r.readkf('Properties', 'Dipole')
        dipole_magn = sum([a*a for a in dipole_vec])**0.5
        to_print += [(r.job.name, dipole_magn)]
    for nam, dip in to_print:
        print(nam + '\t\t' + str(dip))

Another way could be disabling logging to standard output by putting ``config.log.stdout = 0`` at the beginning of the script (see |log|).

Coming back to the main topic of our considerations, as we have seen above, parallelism in PLAMS is driven by results request. Not only the order of requests is important, but also (probably even more important) the place from which they are made. To picture this matter we will use the following script that performs geometry optimization followed by frequencies calculation of the optimized geometry:

.. code-block:: python
    :linenos:

    config.default_jobrunner = JobRunner(parallel=True)

    go = ADFJob(name='GeomOpt', molecule=Molecule('geom.xyz'))
    go.settings.input.geometry.go = True
    ... #other settings adjustments for geometry optimisation
    go_results = go.run()

    opt_geo = go_results.get_molecule('Geometry', 'xyz')

    freq = ADFJob(name='Freq', molecule=opt_geo)
    freq.settings.input.geometry.frequencies = True
    ... #other settings adjustments for frequency run
    freq_results = freq.run()

    do_other_work() # further part of the script, independent of GeomOpt and Freq

Again let us follow the main thread. In line 8 we can see a results request for optimized geometry from "GeomOpt" job. The main thread will then wait for this job to finish before preparing "Freq" job and running it. That means ``do_other_work()``, whatever it is, will not start before "GeomOpt" is done, even though it could, since it is independent of GeomOpt and Freq results. This is bad. The main thread wastes time that could be used for ``do_other_work()`` on idle waiting. We need to fix our script:

.. code-block:: python
    :linenos:

    config.default_jobrunner = JobRunner(parallel=True)

    go = ADFJob(name='GeomOpt', molecule=Molecule('geom.xyz'))
    go.settings.input.geometry.go = True
    ... #other settings adjustments for geometry optimisation
    go_results = go.run()

    freq = ADFJob(name='Freq')
    freq.settings.input.geometry.frequencies = True
    ... #other settings adjustments for frequency run

    @add_to_instance(freq)
    def prerun(self):
        self.molecule = go_results.get_molecule('Geometry', 'xyz')

    freq_results = freq.run()

    do_other_work() # further part of the script, independent of GeomOpt and Freq

Now the results request have been moved from main script to the |prerun| method of "Freq" job. This simple tweak changes everything since job's |prerun| is executed in job's thread rather than the main thread. That means the main thread starts the "Freq" job immediately after starting "GeomOpt" job and then directly proceeds to ``do_other_work()``. Meanwhile in the thread spawned for "Freq" the results request for molecule is made and that thread waits for "GeomOpt" to finish.

As seen in the above example, it is extremely important to properly configure jobs that are dependent (setup of one depends on results of another). Resolving all such dependencies in job's thread rather than the main thread guarantees that waiting for results is done only by the code that really needs them.

.. note::

    In some cases dependencies between job are not easily expressed via methods of |Results| (for example, one job sets up some environment that is later used by another job). In such cases one can use job's ``depend`` attribute to explicitly tell the job about other jobs which it has to wait for. Adding ``job2`` to ``job1.depend`` is roughly equivalent to putting ``job2.results.wait()`` in ``job1`` |prerun|.


To sum up all the above considerations, here is the rule of thumb how to write properly working parallel PLAMS scripts:

1.  Request results as late as possible, preferably just before using them.
2.  If possible, avoid requesting results in the main thread.
3.  Place the result request in the thread in which this data is later used.



.. _cleaning:

Cleaning job folder
~~~~~~~~~~~~~~~~~~~~~~~~~

|Results| instance associated with a job is responsible for cleaning the job folder (removing files that are no longer needed). Cleaning is done automatically, twice for each job, so usually there is no need to manually invoke it.

First cleaning is done during job execution, just after :meth:`~scm.plams.core.basejob.Job.check` and before |postrun|. The value adjusting first cleaning is taken from ``myjob.settings.keep`` and should be either string or list (see below). This cleaning will usually be used rather rarely. It is intended for purposes when your jobs produce large files that you don't need for further processing. Running many of such jobs could then deplete disk quota and cause the whole script to crash. If you wish to immediately get rid of some files produced by your jobs (without having a chance to do anything with them), use this cleaning.

In the majority of cases it is sufficient to use second cleaning, which is performed at the end of your script, when |finish| method is called. It is adjusted by ``myjob.settings.save``. You can use second cleaning to remove files that you no longer need after you extracted relevant data earlier in your script.

The argument passed to :meth:`~Results._clean` (in other words the value that is supposed to be kept in ``myjob.settings.keep`` and ``myjob.settings.save``) can be one of the following:

*   ``'all'`` -- nothing is removed, cleaning is skipped.
*   ``'none'`` or ``[]`` or ``None`` -- everything is removed from the job folder.
*   list of strings -- list of filenames to be kept. Shortcut ``$JN`` can be used here, as well as \*-wildcards. For example ``['geo.*', '$JN.out', 'logfile']`` will keep ``[jobname].out``, ``logfile`` and all files whose names start with ``geo.`` and remove everything else from the job folder.
*   list of strings with the first element ``'-'`` -- reversed behavior to the above, listed files will be removed. For example ``['-', 't21.*', '$JN.err']`` will remove ``[jobname].err`` and all files whose names start with ``t21.``

Cleaning for multijobs
+++++++++++++++++++++++++

Cleaning happens for every job run with PLAMS, either single or multi. That means that if you have, for example, a single job that is a child of some multijob, its job folder will be cleaned two times by two different |Results| instances that can interfere with each other. Hence it is a good practice to set cleaning only on one level (either parent job or children jobs) and disable cleaning on the other level by using ``'all'``.

Another shortcut can be used for cleaning in multijobs. ``$CH`` is expanded with every possible child name. So for example if you have a multijob ``mj`` with 5 single job children (``child1``, ``child2`` and so on) and you wish to keep only input and output files of children jobs you can set::

    >>> mj.settings.save = ['$CH/$CH.in', '$CH/$CH.out']

It is equivalent to using::

    >>> mj.settings.save = ['child1/child1.in', 'child2/child2.in', ... , 'child1/child1.out', 'child2/child2.out', ...]

As you can see in the above example, when cleaning a multijob folder you have to keep in mind the fact that files in subfolders are kept as relative paths.

API
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Results
    :exclude-members: __weakref__, __metaclass__

.. technical::

    Other parts of ``results`` module described below are responsible for giving |Results| class its unique behavior described in :ref:`parallel`. They are presented here for the sake of completeness, from user's perspective this information is rather irrelevant.

    .. autoclass:: _MetaResults
    .. autofunction:: _restrict
    .. autofunction::  _caller_name_and_arg
    .. autofunction:: _privileged_access



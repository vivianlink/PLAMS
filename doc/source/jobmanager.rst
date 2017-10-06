Job manager
-------------

.. currentmodule:: scm.plams.core.jobmanager

Job manager is the "director" of PLAMS environment. It keeps track of all jobs you run, manages the main working folder, allocates job folders to jobs and prevents multiple runs of the same job.

Every instance of |JobManager| is tied to a working folder. This folder is created when |JobManager| instance is initialized and all jobs managed by this instance have their job folders in the working folder. You should not change the job manager's working folder after it has been created.

When you initialize PLAMS environment with |init| function, an instance of |JobManager| is created and stored in ``config.jm``. This instance is tied to PLAMS main working folder (see :ref:`master-script` for details) and used by default every time some interaction with job manager is required. In a normal situation you would never explicitly touch any |JobManager| instance (create it manually, call any of its methods, explore its data etc.). All interactions are handled automatically from |run| or other methods.

.. note::

   Usually there is no need to use any other job manager than the default one. Splitting work between multiple instances of |JobManager| may lead to some problems (different instances don't communicate, so |RPM| does not work properly).

   However, it is possible to manually create another instance of |JobManager| (with a different working folder) and use it for part of your jobs (by passing it as ``jobmanager`` keyword argument to |run|). If you decide to do so, make sure to pass all instances of |JobManager| you manually created to |finish| (as a list).

   An example application for that could be running jobs within your script on many different machines (for example via SSH) and having a separate |JobManager| on each of them.



.. _rerun-prevention:

Rerun prevention
~~~~~~~~~~~~~~~~~~~~~~~~~

In some applications regarding running large numbers of automatically generated jobs (especially in subsystem methods) it may occur that two or more jobs are identical. PLAMS has built-in mechanism to detect such situations and avoid unnecessary work.

During |run|, just before the actual job execution, an unique identifier of a job (called *hash*) is calculated. Job manager stores all hashes of previously run jobs and checks if the hash of the job you are attempting to execute is not yet present. If such a situation is detected, no execution happens and results of the previous job are used. Results from previous job's folder can be either copied or linked to the current job's folder, based on ``link_files`` key in **previous** job's ``settings``.

.. note::

    Linking is done using hard links. Windows machines do not support hard links and hence, if you are running PLAMS under Windows, results are always copied.

The crucial part of the whole rerun prevention mechanism is properly working :meth:`~scm.plams.core.basejob.Job.hash` function. It needs to produce different hashes for different jobs and exactly the same hashes for jobs that do exactly the same work. It is difficult to come up with the scheme that works well for all kind of external binaries, since the technical details about job preparation can differ a lot. Currently implemented method works based on calculating SHA256 hash of input and/or runscript contents. The value of ``hashing`` key in job manager's ``settings`` can be one of the following: ``'input'``, ``'runscript'``, ``'input+runscript'`` (or ``None`` to disable the rerun prevention).

If you decide to implement your own hashing method, it can be done by overriding :meth:`~scm.plams.core.basejob.SingleJob.hash_input` and/or meth:`~scm.plams.core.basejob.SingleJob.hash_runscript`.

.. warning::

    It may happen that two jobs with exactly the same input and runscript files correspond to different jobs (for example if they rely on some external file that is supplied using relative path). Pay special attention to that. If you are experiencing problems (PLAMS sees two different jobs as the same one), disable the rerun prevention (``config.jm.settings.hashing = None``)

In the current implementation hashing is disabled for |MultiJob| instances since they don't have inputs and runscripts. Of course single jobs that are children of multijobs are hashed in a normal way, so trying to run exactly the same multijob as the one run before will not trigger rerun prevention on multijob level but rather for every children single job separately.



.. _pickling:

Pickling
~~~~~~~~~~~~~~~~~~~~~~~~~

The lifespan of all elements that are parts of PLAMS environment is limited to a single script. That means every script you run uses its own independent job manager, working folder or ``config`` settings. These objects are initialized at the beginning of the script with |init| command and they cease to exist when the script ends. Also all settings adjustments (apart from those done by editing ``plams_defaults``) are local just for one script.

As a consequence of that, the job manager you are using in the current script is not aware of any jobs that had been run in past scripts. However, in some cases it would be very useful to be able to import previously run job to the current script and use its results or build new jobs based on it. For that purpose PLAMS offers data preserving mechanism for job objects. Every time execution of a job successfully finishes (see :ref:`job-life-cycle`) the whole job object is saved to a ``.dill`` file using Python mechanism called :mod:`pickling<pickle>`.

.. note::

    The default Python pickling package, :mod:`pickle<pickle>`, is not powerful enough to handle some of common PLAMS objects. Fortunately, the `dill <https://pypi.python.org/pypi/dill>`_ package provides an excellent replacement for ``pickle``, following the same interface and being able to save and load almost everything. It is strongly recommended to use ``dill`` to ensure proper work of PLAMS data preserving mechanism. However, if ``dill`` is not installed in the Python interpreter you're using to run PLAMS, the regular ``pickle`` package will be used instead (which can work if your |Job| objects are not too fancy, but in most cases it will most likely fail). Please use ``dill``, it's free, easy to get and awesome.


Such a ``.dill`` file can be loaded in future scripts using |load| function::

    >>> oldjob = load('/home/user/science/plams.12345/myjob/myjob.dill')

This operation brings back the old |Job| instance in (almost) the same state it was just after its execution finished.

.. technical::

    Python pickling mechanism follows references in pickled object. That means if an object you are trying to pickle contains a reference to another object (just like a |Job| instance has a reference to |Results| instance), this another object is saved too. Thanks to that after unpickling there are no "empty" references in your objects.

    However, every |Job| instance in PLAMS has a reference to job manager, which in turns has references to all other jobs, so pickling one job would effectively mean pickling almost the whole environment. To avoid that, every |Job| instance needs to be prepared for pickling by removing references to "global" objects, as well as some purely local attributes (path to the job folder for example). During loading, all removed data is replaced with "proper" values (current job manager, current path to the job folder etc.).

.. note::

    There is a way of expanding the mechanism explained in the box above. If your |Job| object has an attribute containing a reference to some other object you don't want to save together with the job, you may add this object's name to job's ``_dont_pickle`` list::

        myjob.something = some_big_and_clumsy_object_you_dont_want_to_pickle
        myjob._dont_pickle = ['something'] #or myjob._dont_pickle.append('something')

    That way big clumsy object will not be stored in the ``.dill`` file. After loading such a ``.dill`` file the value of ``myjob.something`` will simply be ``None``.

    ``_dont_pickle`` is an attribute of each |Job| instance, initialized by the constructor to an empty list. It does not contain names of attributes that are always removed ( like ``jobmanager``, for example), only additional ones defined by the user (see :meth:`Job.__getstate__<scm.plams.core.basejob.Job.__getstate__>`)


As mentioned above, saving a job happens at the very end of |run|. The decision if a job should be pickled is based on ``pickle`` key in job's ``settings``, so it can be adjusted for each job separately. If you wish not to pickle a particular job just set ``myjob.settings.pickle = False``. Of course global default setting in ``config.job.pickle`` can also be used.

If you modify a job or its corresponding |Results| instance afterwards, those changes are not going to be reflected in the ``.dill`` file, since it was created before your changes happened. To store such changes you need to repickle the job manually by calling ``myjob.pickle()`` after doing your changes.

.. note::

    Not all Python objects can be properly pickled, so you need to be careful of references to external objects your job or its results store.

A |Results| instance associated with a job is saved together with it. However, results do not contain all files produced by job execution, but only relative paths to them. For that reason the ``.dill`` file is not enough to fully restore the state if you want to process the results. All other files present in job's folder are needed so that |Results| instance can relate to them. So if you want to copy previously executed job to another location make sure to copy *the whole* job folder (including subdirectories).

A loaded job is **not** registered in the current job manager. That means it does not get its own subfolder in the main working folder, it never gets renamed and no :ref:`cleaning` is done on |finish|. However, it is added to hash registry so it is visible to |RPM|.

In case of |MultiJob| all information about children jobs is stored in parent's ``.dill`` file so loading a |MultiJob| results in loading all its children jobs. Each children job can have its own ``.dill`` file containing information about that particular job only. ``parent`` attribute of a children job is erased, so loading a children job does not result in loading its parent (and all other children).



.. _restarting:

Restarting crashed scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pickling and rerun prevention combine nicely to produce a convenient restart mechanism. When a script tries to do something "illegal" it gets stopped by the Python interpreter. Usually it is caused by a mistake in the script (a typo, using wrong variable, accessing wrong element of a list etc.). In such a case one would like to correct the script and run it again. But some jobs in the "wrong" script may had already been run and successfully finished before the crash occurred. It would be a waste of time to run those jobs again in the corrected script if they are meant to produce exactly the same results as previously. The solution is to load all successfully finished jobs from the crashed script at the beginning of the corrected one and let |RPM| do the rest. However, having to go to the previous script's working folder and manually get paths to all ``.dill`` files there would be cumbersome. Fortunately, one can use |load_all| function which, given the path to the main working folder of some finished PLAMS run, loads all ``.dill`` files stored there. So when you edit your crashed script to remove mistakes you can just add one |load_all| call at the beginning and when you run your corrected script no unnecessary work will be done.

If you're executing your PLAMS scripts using the |master_script|, restarting is even easier. It can be done in two ways:

1.  If you wish to perform the restart run in a fresh, empty working folder, all you need to do is simply to import the contents of the previous working folder (from the crashed run) using ``-l`` flag::

        plams myscript.plms
        [17:28:40] PLAMS working folder: /home/user/plams.12345
        #[crashed]
        #[correct myscript.plms]
        plams -l plams.12345 myscript.plms
        [17:35:44] PLAMS working folder: /home/user/plams.23456

2.  If you would rather prefer to do an in-place restart and use the same working folder, you can use ``-r`` flag::

        plams myscript.plms
        [17:28:40] PLAMS working folder: /home/user/plams.12345
        #[crashed]
        #[correct myscript.plms]
        plams -r -f plams.12345 myscript.plms
        [17:35:44] PLAMS working folder: /home/user/plams.12345

    In this case the master script will temporarily move all the contents of ``plams.12345`` to ``plams.12345.res``, import all the jobs from there and start a regular run in now empty ``plams.12345``. At the end of the script ``plams.12345.res`` will be deleted.



.. note::
    Please remember that rerun prevention checks the hash of the job after the |prerun| method is executed. So when you attempt to run a job identical to the one previously run (in the same script, or imported from a previous run), its |prerun| method is executed anyway, even if the rest of :ref:`job-life-cycle` is skipped.


API
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: JobManager
    :exclude-members: __weakref__
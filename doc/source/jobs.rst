Jobs
-------------

.. currentmodule:: scm.plams.basejob

Without any doubt job is the most important object in PLAMS library. Job is the basic piece of computational work and running jobs is the main goal of PLAMS scripts.

Various jobs may differ in details quite a lot, but they all follow the common set of rules defined in the abstract class |Job|.

.. note::
    Being an abstract class means that |Job| class has some abstract methods -- methods that are declared but not implemented (they do nothing). Those methods are supposed to be defined in subclasses of |Job|. When a subclass of an abstract class defines all required abstract methods, it is called a *concrete class*. You should never create an instance of an abstract class, because when you try to use it, empty abstract methods are called and your script crashes.

Every job has its own unique name and a separate folder (called job folder, with the same name as the job) located in the main working folder. All files regarding that particular job (input, output, runscript, other files produced by job execution) end up in the job folder.

In general a job can be of one of two types: a single job or a multijob. These types are defined as subclasses of the |Job| class: |SingleJob| and |MultiJob|.

Single job is a job representing a single calculation, usually done by executing an external binary (ADF, Dirac etc.). Single job creates a runscript that is then either executed locally or submitted to some external queueing system. As a result of running a single job a handful of files is created, including dumps of the standard output and standard error streams together with any other files produced by the external binary. |SingleJob| is still an abstract class that is further subclassed by program-specific concrete classes like for example |ADFJob|.

Multijob, on the other hand, does not run any calculation by itself. It is a container for other jobs, used to aggregate smaller jobs into bigger ones. There is no runscript produced by a multijob. Instead, it contains a list of subjobs called *children* that are run together when the parent job is executed. Children jobs can in turn be either single or multijobs. Job folder of each child job is a subfolder of its parent's job folder, so folder hierarchy fully corresponds to job child/parent hierarchy. |MultiJob| is a concrete class so you can create its instances and run them.



Preparing a job
~~~~~~~~~~~~~~~~~~~~~~~~~

The first step to run a job using PLAMS is to create a job object. You need to pick a concrete class that defines a type of job you want to run (|ADFJob| will be used as an example in our case) and create its instance::

    >>> myjob = ADFJob(name='myfirstjob')

Various keyword arguments (arguments of the form ``arg=value``, like ``name`` in the example above) can be passed to a job constructor, depending on the type of your job. However, the following keyword arguments are common for all types of jobs:
    *   ``name`` -- a string containing the name of the job. If not supplied, default name ``plamsjob`` is used. Job's name cannot contain path separator (``\`` in Linux, ``/`` in Windows).
    *   ``settings`` -- a |Settings| instance to be used by this job. It gets copied (using :meth:`~scm.plams.settings.Settings.copy`) so you can pass the same instance to several different jobs and changes made afterwards won't interfere. Any instance of |Job| can be also passed as a value of this argument. In that case |Settings| associated with the passed job are copied.
    *   ``depend`` -- a list of jobs that need to be finished before this job can start. This is useful when you want to execute your jobs in parallel. Usually there is no need to use this argument, since dependencies between jobs are resolved automatically (see |parallel|). However, sometimes one needs to explicitly state such a dependency and this option is then helpful.

Those values do not need to be passed to the constructor, they can be set or changed later (but they should be fixed before the job starts to run)::

    >>> myjob = ADFJob()
    >>> myjob.name = 'myfirstjob'
    >>> myjob.settings.runscript.pre = 'echo HelloWorld'

Single jobs can be supplied with another keyword argument, ``molecule``. It is supposed to be a |Molecule| object. Multijobs, in turn, accept keyword argument ``children`` that stores the list of children jobs.

The most meaningful part of each job object is its |Settings| instance. It is used to store information about contents of job's input file, runscript as well as other tweaks of job's behavior. Thanks to tree-like structure of |Settings|, this information is organized in a convenient way: the top level (``myjob.settings.``) stores general settings, ``myjob.settings.input.`` is a branch for specifying input settings, ``myjob.settings.runscript.`` holds information for runscript creation and so on. Some types of jobs will make use of their own ``myjob.settings`` branches and not every kind of job will always require ``input`` or ``runscript`` branches (like multijob for example). The nice thing is that all the unnecessary data present in job's settings is simply ignored, so accidentally plugging settings with too much data will not cause any problem (except some cases where the whole content of some branch is used, like for example the ``input`` branch in |SCMJob|).

.. _job-settings:

Contents of job's settings
++++++++++++++++++++++++++

The following keys and branches of job's settings are meaningful for all kinds of jobs:
    *   ``myjob.settings.input.`` is a branch storing settings regarding input file of a job. The way data present in this branch is used depends on the type of job and is specified in respective subclasses of |Job|.
    *   ``myjob.settings.runscript.`` holds runscript information, either program-specific or general:

        -   ``myjob.settings.runscript.shebang`` -- the first line of the runscript, starting with ``#!``, describing interpreter to use
        -   ``myjob.settings.runscript.pre`` -- an arbitrary string that will be placed in the runscript file just below the shebang line, before the actual contents
        -   ``myjob.settings.runscript.post`` -- an arbitrary string to put at the end of the runscript.
        -   ``myjob.settings.runscript.stdout_redirect`` -- boolean flag defining if standard output redirection should be handled inside the runscript. If set to ``False``, the redirection will be done by Python outside the runscript. If set to ``True``, standard output will be redirected inside the runscript using ``>``.

    *   ``myjob.settings.run.`` branch stores run flags for the job (see below)
    *   ``myjob.settings.pickle`` is a boolean defining if job object should be pickled after finishing
    *   ``myjob.settings.keep`` and ``myjob.settings.save`` are keys adjusting |cleaning|.
    *   ``myjob.settings.link_files`` decides if files from job folder can be linked rather than copied when copying is requested


.. _default-settings:

Default settings
++++++++++++++++

Every job instance has an attribute called ``default_settings`` that stores a list of |Settings| instances that serve as default templates for that job. Initially this list contains only one element, global defaults for all jobs stored in ``config.job``. You can add other templates just like adding elements to a list::

    >>> myjob.default_settings.append(sometemplate)
    >>> myjob.default_settings += [temp1, temp2]

During job execution (just after ``prerun()`` is finished) job's own ``settings`` are soft-updated with all elements of ``default_settings`` list, one by one, starting with **last**. That way if you want to adjust some setting for all jobs run in your script you don't need to go to each job and set it there every time, one change in ``config.job`` is enough. Similarly, if you have a group of jobs that need the same ``settings`` adjustments, you can create an empty |Settings| instance, put those adjustments in it and add it to each job's ``default_settings``. Keep in mind that :meth:`~scm.plams.settings.Settings.soft_update` is used so any key in a template in ``default_settings`` will end up in job's ``settings`` only if such a key is not yet present there. Thanks to that the order of templates in ``default_settings`` somehow defines their importance: data from a preceding template will never override the following one, it can only enrich it.


.. _job-life-cycle:

Running a job
~~~~~~~~~~~~~~~~~~~~~~~~~

After creating a job instance and adjusting its settings you can finally run it. It is done by invoking job's |run| method, which returns a |Results| instance::

    >>> myresults = myjob.run()

Again, various keyword arguments can be passed here. With ``jobrunner`` and ``jobmanager`` you can specify which |JobRunner| and |JobManager| to use for your job. If those arguments are omitted, the default instances stored in ``config.default_jobrunner`` and ``config.jm`` are taken. All other keyword arguments passed here are collected and stored in ``myjob.settings.run`` branch as one flat level. They can be used later by various objects involved in running your job, for example |GridRunner| uses them to build command executed to submit runscript to the queueing system.

The following steps are taken after the |run| method is called:
    1. ``myjob.settings.run`` is soft-updated with |run| keyword arguments.
    2. If a parallel |JobRunner| was used, a new thread is spawned and all further steps of this list happen in this thread.
    3. Explicit dependencies from ``myjob.depend`` are resolved. This means waiting for all jobs listed there to finish.
    4. Job's name gets registered in the job manager and the job folder is created.
    5. Job's |prerun| method is called.
    6. ``myjob.settings`` are updated according to contents of ``myjob.default_settings``.
    7. The hash of a job is calculated and checked (see |RPM|). If the same job was found as previously run, its results are copied (or linked) to the current job's folder and |run| finishes.
    8. Now the real job execution happens. If your job is a single job, an input file and a runscript are produced and passed to job runner's method :meth:`~scm.plams.jobrunner.JobRunner.call`. In case of multijob, |run| method is called for all children jobs.
    9. After the execution is finished, result files produced by the job are collected and :meth:`~Job.check` is used to test if the execution was successful.
    10. The job folder is cleaned using ``myjob.settings.keep``. See |cleaning| for details.
    11. Job's |postrun| method is called.
    12. If ``myjob.settings.pickle`` is true, the whole job instance gets pickled and saved to the ``[jobname].dill`` file in the job folder.


Name conflicts
++++++++++++++

Jobs are identified by their names and hence those names need to be unique. This is obligatory also because job's name corresponds to the name of its folder. Usually it is recommended to manually set unique names for jobs for easier navigation through results. But for part of applications, especially those requiring running large numbers of similar jobs, this is neither convenient nor necessary.

PLAMS automatically resolves conflicts between jobs' names. During step 4. of the above list, if a job with the same name was already registered, the new job is renamed. The new name is created by appending some number to the old one. For example, the second job with the name ``plamsjob`` will be renamed to ``plamsjob.002``, third to ``plamsjob.003`` and so on. Number of digits used in this counter can be adjusted in ``config.jobmanager.counter_len`` and the default value is 3. Overflowing the counter will not cause any problems, the job coming after ``plamsjob.999`` will be called ``plamsjob.1000``.


.. _prerun-postrun:

Prerun and postrun methods
++++++++++++++++++++++++++

|prerun| and |postrun| methods are intended for further customization of your jobs. They can contain arbitrary pieces of code that are executed before and after the actual execution of your job. |prerun| takes place after job's folder is created but before hash checking. Here are some ideas what can be put there:
    *   adjusting job ``settings``
    *   copying to job folder some files required for running
    *   extracting results of some other job, processing them and plugging to job
    *   generating children jobs in multijobs

See also |parallel| for explanation how to use |prerun| to automatically handle dependencies in parallel workflows.

The other method, |postrun|, is called after job execution is finished, the results are collected and the job folder is cleaned. It is supposed to contain any kind of essential results postprocessing that needs to be done before results of this job can be pushed further in the workflow. For that purpose code contained in |postrun| has some special privileges. At the time the method is executed the job is not yet considered done, so all threads requesting its results are waiting. However, the guardian restricting the access to results of unfinished jobs can recognize code coming from |postrun| and allow it to access and modify results. So calling |Results| methods can be safely done there and you can be sure that everything you put in |postrun| is done before other jobs have access to this job's results.

|prerun| and |postrun| methods can be added to your jobs in multiple ways:
    *   you can create a tiny subclass which redefines the method::

            >>> class MyJobWithPrerun(MyJob):
            >>>     def prerun(self):
            >>>         #do stuff


        It can be done right inside you script. After the above definition you can create instances of the new class and treat them in exactly the same way you would treat ``MyJob`` instances. The only difference is that they will be equipped with |prerun| method you just defined.
    *   you can bind the method to an existing class using |add_to_class| decorator::

            >>> @add_to_class(MyJob)
            >>> def prerun(self):
            >>>     #do stuff

        That change affects all instances of ``MyJob``, even those created before the above code was executed (obviously it won't affect instances previously run and finished).
    *   you can bind the method directly to an instance using |add_to_instance| decorator::

            >>> j = MyJob(...)
            >>> @add_to_instance(j)
            >>> def prerun(self):
            >>>     #do stuff

        Only one specified instance (``j``) is affected this way.

All the above works for |postrun| as well.

Preview mode
++++++++++++++++++++++++++

Preview mode is a special way of running jobs without the actual runscript execution. In this mode the procedure of running a job is interrupted just after input and runscript files are written to job folder. Preview mode can be used to check if your jobs generate proper input and runscript files, without having to run the full calculation.

You can enable preview mode by putting the following line at the beginning of your script::

    >>> config.preview = True


Job API
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Job
    :exclude-members: __weakref__, _result_type



Single jobs
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SingleJob(molecule=None, name='plamsjob', settings=None, depend=None)
    :exclude-members: __weakref__


Subclassing SingleJob
+++++++++++++++++++++

|SingleJob| class was designed in a way that makes subclassing it quick and easy. Thanks to that it takes very little effort to create PLAMS interface for a new external binary.

Your new class has to, of course, be a subclass of |SingleJob| and define methods :meth:`~SingleJob.get_input` and :meth:`~SingleJob.get_runscript`::

    >>> class MyJob(SingleJob):
    >>>     def get_input(self):
    >>>         ...
    >>>         return 'string with input file'
    >>>     def get_runscript(self):
    >>>         ...
    >>>         return 'string with runscript'

.. note::

    :meth:`~SingleJob.get_runscript` method should properly handle output redirection based on the value of ``myjob.settings.runscript.stdout_redirect``. When ``False``, no redirection should occur inside runscript. If ``True``, runscript should be constructed in such a way that all standard output is redirected (using ``>``) to the proper file (its name is "visible" as ``self._filename('out')`` from inside :meth:`~SingleJob.get_runscript` body).

This is sufficient for your new job to work properly with other PLAMS components. However, there are other useful attributes and methods that can be overridden:
    *   :meth:`~Job.check` -- the default version of this method defined in |Job| always returns ``True`` and hence effectively disables correctness checking. If you wish to enable checking for your new class, you need to define :meth:`~Job.check` method in it, just like :meth:`~SingleJob.get_input` and :meth:`~SingleJob.get_runscript` in the example above. It should take no other arguments than ``self`` and return a boolean value indicating if job execution was successful. This method is privileged to have an early access to |Results| methods in exactly the same way as |postrun|.
    *   if you wish to create a special |Results| subclass for results of your new job, make sure to let it know about it::

        >>> class MyResults(Results):
        >>>     def some_method(self, ...):
        >>>         ...
        >>>
        >>> class MyJob(SingleJob):
        >>>     _result_type = MyResults
        >>>     def get_input(self):
        >>>         ...
        >>>         return 'string with input file'
        >>>     def get_runscript(self):
        >>>         ...
        >>>         return 'string with runscript'

    *   :meth:`~Job.hash` -- see |RPM| for details
    *   if your new job requires some special preparations regarding input or runscript files these preparations can be done for example in |prerun|. However, if you wish to leave |prerun| clean for further subclassing or adjusting in instance-based fashion, you can use another method called :meth:`~SingleJob._get_ready`. This method is responsible for input and runscript creation, so if you decide to override it you **must** call its parent version in your version::

        >>> def _get_ready(self):
        >>>     # do some stuff
        >>>     SingleJob._get_ready()
        >>>     # do some other stuff


.. warning::

    Whenever you are subclassing any kind of job, either single of multi, and you wish to override its constructor (``__init__`` method) it is **absolutely essential** to call the parent constructor and pass all unused keyword arguments to it::

        >>> class MyJob(SomeOtherJob):
        >>>     def __init__(self, myarg1, myarg2=default2, **kwargs):
        >>>         SomeOtherJob.__init__(self, **kwargs)
        >>>         # do stuff with myarg1 and myarg2

.. technical::

    Usually when you need to call some method from a parent class it is a good idea to use :func:`super`. However, there exists a known bug in Python 3 that causes the ``dill`` package to crash when :func:`super` is used. For that reason, if you're using Python 3, please do not use :func:`super`.


Multijobs
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: MultiJob(children=None, name='plamsjob', settings=None, depend=None)
    :exclude-members: __weakref__

Using MultiJob
+++++++++++++++++++++

Since |MultiJob| is a concrete class, it can be used in two ways: either by creating instances of it or subclassing it. The simplest application is just to use an instance of |MultiJob| as a container grouping similar jobs that you wish to run at the same time using the same job runner::

    >>> mj = MultiJob(name='somejobs', children=[job1, job2, job3])
    >>> mj.children.append(job4)
    >>> mj.run(...)

You can of course use it together with :ref:`prerun-postrun` to further customize the behavior of ``mj``.

More flexible way of using multijobs is subclassing. You can subclass directly from |MultiJob| or from any of its subclasses. Defining your own multijob is the best solution when you need to run many similar jobs and later compare their results. In that case |prerun| method can be used for populating ``children`` and |postrun| for extracting results and merging them.

Job runners
-------------

.. currentmodule:: scm.plams.jobrunner

Job runners have already been mentioned in previous chapters, in parts regarding job running. The aim of this chapter is to sum up all this information and to introduce various subclasses of |JobRunner|.

Job runners in PLAMS are very simple objects, both from user's perspective and in terms of internal architecture. They have no methods that are meant to be explicitly called, they are just supposed to be created and passed to |run| as parameters. |JobRunner| class defines a basic local job runner and serves as a base class for further subclassing.

Local job runner
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: JobRunner
    :exclude-members: __weakref__, __metaclass__

.. autoclass:: _MetaRunner
.. autofunction:: _limit
.. autofunction:: _in_thread

Remote job runner
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: GridRunner
    :exclude-members: __weakref__, __metaclass__
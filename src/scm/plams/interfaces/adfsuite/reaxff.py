from ...core.basejob import SingleJob
from .scmjob import SCMResults

__all__ = ['ReaxFFJob', 'ReaxFFResults']

class ReaxFFResults(SCMResults):
    pass

class ReaxFFJob(SingleJob):
    _result_type = ReaxFFResults

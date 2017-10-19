import copy


__all__ = []



def smart_copy(obj, owncopy=[], without=[]):
    """Return a copy of *obj*. Attributes of *obj* listed in *without* are ignored. Attributes listed in *owncopy* are copied by calling their own ``copy()`` methods. All other attributes are copied using :func:`python3:copy.deepcopy`."""

    ret = obj.__class__()
    for k in owncopy:
        ret.__dict__[k] = obj.__dict__[k].copy()
    for k in obj.__dict__:
        if k not in (without + owncopy):
            ret.__dict__[k] = copy.deepcopy(obj.__dict__[k])
    return ret


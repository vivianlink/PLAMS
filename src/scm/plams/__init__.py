"""
What follows is a somewhat hacky way to set up an automatic plug'n'play import mechanism. If you experience any problems with importing, remove this and bring back good old explicit imports:

        from .core.basejob import *
        from .core.basemol import *
        ...
        from .tools.geometry import *
        from .tools.kftools import *
        ...
        from .interfaces.adfsuite import *
        from .interfaces.cp2k import *
"""

def __import_all(path):
    """Traverse the directory tree rooted in *path* and find all Python modules living there. For each module, import everything given by its __all__ variable to the globals() namespace."""
    import os
    is_module = lambda x: x.endswith('.py') and not x.startswith('__init__')

    ret = []
    for dirpath, dirnames, filenames in os.walk(path):
        modules = [os.path.splitext(f)[0] for f in filter(is_module, filenames)]
        relpath = dirpath.replace(path, '').split(os.sep)[1:]
        for mod in modules:
            imp = '.'.join(relpath + [mod])
            tmp = __import__(imp, globals=globals(), fromlist=['*'], level=1)
            if hasattr(tmp, '__all__'):
                ret += tmp.__all__
                for name in tmp.__all__:
                    globals()[name] = vars(tmp)[name]
    return ret

__all__ = __import_all(__path__[0])

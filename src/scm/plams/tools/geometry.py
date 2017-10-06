import numpy

__all__ = ['rotation_matrix']

def rotation_matrix(vec1, vec2):
    """
    Calculates the rotation matrix rotating *vec1* to *vec2*. Vectors can be any containers with 3 numerical values. They don't need to be normalized. Returns 3x3 numpy array.
    """
    a = numpy.array(vec1)/numpy.linalg.norm(vec1)
    b = numpy.array(vec2)/numpy.linalg.norm(vec2)
    v1,v2,v3 = numpy.cross(a,b)
    M = numpy.array([[0, -v3, v2], [v3, 0, -v1], [-v2, v1, 0]])
    return (numpy.identity(3) + M + numpy.dot(M,M)/(1+numpy.dot(a,b)))
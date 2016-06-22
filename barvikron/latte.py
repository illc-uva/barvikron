from __future__ import absolute_import
import os, re, subprocess, tempfile
from . import LONG_INTEGER, EvaluatorBase

__all__ = ['LatteEvaluator']


def prepare_input(A, b):
    """
    Prepare vector partition function query in the format expected by LattE's count tool.
    """
    nrows, ncols = A.shape
    s = '%s %s\n' % (nrows, ncols + 1)

    # A[i] * x - b[i] = 0
    for i, row in enumerate(A):
        s += '%s   %s\n' % (-b[i], ' '.join(map(str, row)))
    s += 'linearity     %s   %s\n' % (nrows,
                                      ' '.join(map(str, range(1, 1 + nrows))))

    # x[i] >= 0
    s += 'nonnegative   %s   %s\n' % (ncols,
                                      ' '.join(map(str, range(1, 1 + ncols))))
    return s


class LatteEvaluator(EvaluatorBase):
    """
    Evaluate vector partition functions at given point using LattE's count tool (https://www.math.ucdavis.edu/~latte/).
    """

    def __init__(self, path):
        assert os.path.isfile(
            path), '"%s" not found (should be path to LattE\'s count binary)' % path
        self.path = path

    def eval(self, vpn, b):
        # save input in temporary file
        handle, input_path = tempfile.mkstemp('.in', 'kronecker-latte-')
        try:
            os.write(handle, prepare_input(vpn.A, b).encode('ascii'))
            os.close(handle)

            # run count
            stdout = subprocess.check_output([self.path, input_path],
                                             stderr=subprocess.STDOUT,
                                             cwd=os.path.dirname(input_path))

            # parse output
            stdout = stdout.decode('ascii')
            if 'Empty polytope or unbounded polytope' in stdout:
                return 0
            match = re.search('number of lattice points(?: is)?(?::)? (\d+)',
                              stdout)
            if not match:
                raise Exception('Could not parse LattE output: %s' % stdout)
            return LONG_INTEGER(match.group(1))
        finally:
            os.remove(input_path)
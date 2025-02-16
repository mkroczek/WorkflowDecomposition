import numpy as np
from QHyper.solvers import SolverResult

from decomposition.qhyper.solver import WorkflowSchedulingSolverDecorator


def test_highest_probability_solution():
    dtype = [('x1', 'i4'), ('probability', 'f8')]

    data = np.recarray((4,), dtype=dtype)
    data.x1 = [1, 0, 1, 0]
    data.probability = [0.56, 0.91, 0.23, 0.88]

    best_solution = WorkflowSchedulingSolverDecorator._get_highest_probability_solution(SolverResult(data, {}, []))

    assert best_solution.probability == 0.91

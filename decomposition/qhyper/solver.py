from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
from QHyper.problems.workflow_scheduling import WorkflowSchedulingOneHot, Workflow
from QHyper.solvers import Solver, SolverResult

from decomposition.qhyper.algorithm import Division
from decomposition.qhyper.problem import decorate, WorkflowSchedulingOneHotEnhanced


@dataclass(frozen=True)
class WorkflowSchedule:
    cost: float
    time: float
    deadline: float
    machine_assignment: dict[str, str]
    workflow: Workflow
    parts: list[WorkflowSchedule] = field(default_factory=list)


class WorkflowSchedulingSolverDecorator:
    def __init__(self, solver: Solver):
        self.solver: Solver = solver
        if not isinstance(solver.problem, WorkflowSchedulingOneHot):
            raise TypeError(
                f"Problem is expected to be WorkflowSchedulingOneHot instance, but is {type(solver.problem)}")
        self.problem: WorkflowSchedulingOneHot = decorate(solver.problem)

    def solve(self) -> WorkflowSchedule:
        solver_result: SolverResult = self.solver.solve()
        best_solution = self._get_highest_probability_solution(solver_result)
        solution = {var: best_solution[var] for var in best_solution.dtype.names if var != 'probability'}
        machine_assignment = self.problem.decode_solution(solution)

        return WorkflowSchedule(
            cost=self.problem.calculate_solution_cost(machine_assignment),
            time=self.problem.calculate_solution_timespan(machine_assignment),
            deadline=self.problem.workflow.deadline,
            machine_assignment=machine_assignment,
            workflow=self.problem.workflow
        )

    @staticmethod
    def _get_highest_probability_solution(solver_result: SolverResult) -> np.record:
        probabilities_descending = np.sort(solver_result.probabilities, order='probability')[::-1]
        return probabilities_descending[0]


class DecomposedWorkflowSchedulingSolver:
    def __init__(self, solvers: list[WorkflowSchedulingSolverDecorator], division: Division):
        self.solvers: list[WorkflowSchedulingSolverDecorator] = solvers
        self.division: Division = division

    def pick_faster_machine(self, task: str, machine1: str, machine2: str) -> str:
        machine1_time = self.division.complete_workflow.time_matrix.loc[task, machine1]
        machine2_time = self.division.complete_workflow.time_matrix.loc[task, machine2]
        return machine1 if machine1_time <= machine2_time else machine2

    def merge_machine_assignments(self, machine_assignments: Iterable[dict[str, str]]):
        final_assignment: dict[str, str] = {}
        for assignment in machine_assignments:
            for task, machine in assignment.items():
                if not task in final_assignment:
                    final_assignment[task] = machine
                else:
                    final_assignment[task] = self.pick_faster_machine(task, final_assignment[task], machine)
        return final_assignment

    def verify_deadline_is_not_exceeded(self, time, deadline):
        assert time <= deadline, "Scheduling result exceeds the deadline!"

    def calculate_time_and_cost(self, workflow: Workflow, machine_assignment: dict[str, str]):
        problem: WorkflowSchedulingOneHot = decorate(WorkflowSchedulingOneHotEnhanced(workflow))
        time = problem.calculate_solution_timespan(machine_assignment)
        cost = problem.calculate_solution_cost(machine_assignment)
        deadline = workflow.deadline
        self.verify_deadline_is_not_exceeded(time, deadline)
        return time, cost

    def solve(self) -> WorkflowSchedule:
        partial_schedules = [s.solve() for s in self.solvers]
        [self.verify_deadline_is_not_exceeded(schedule.time, schedule.deadline) for schedule in partial_schedules]
        machine_assignments = map(lambda s: s.machine_assignment, partial_schedules)
        merged_machine_assignment = self.merge_machine_assignments(machine_assignments)

        original_workflow = self.division.original_workflow
        machine_assignment_without_artificial_nodes = {task: machine for task, machine
                                                       in merged_machine_assignment.items()
                                                       if task in original_workflow.task_names}

        original_time, original_cost = self.calculate_time_and_cost(original_workflow,
                                                                    machine_assignment_without_artificial_nodes)

        return WorkflowSchedule(
            cost=original_cost,
            time=original_time,
            deadline=original_workflow.deadline,
            machine_assignment=merged_machine_assignment,
            workflow=self.division.complete_workflow,
            parts=partial_schedules
        )

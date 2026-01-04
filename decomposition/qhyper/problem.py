from QHyper.constraint import Constraint, Operator, MethodsForInequalities
from QHyper.polynomial import Polynomial
from QHyper.problems.workflow_scheduling import WorkflowSchedulingOneHot


def decorate(problem: WorkflowSchedulingOneHot):
    def calculate_solution_cost(machine_assignment: dict):
        cost: float = 0.0
        for task, machine in machine_assignment.items():
            cost += problem.workflow.cost_matrix.loc[task, machine]
        return cost

    def calculate_solution_timespan(machine_assignment: dict):
        def path_timespan(path):
            path_time = 0
            for task_name in path:
                machine_name = machine_assignment[task_name]
                path_time += problem.workflow.time_matrix.loc[task_name, machine_name]
            return path_time

        return max(map(path_timespan, problem.workflow.paths))

    problem.calculate_solution_cost = calculate_solution_cost
    problem.calculate_solution_timespan = calculate_solution_timespan
    return problem


class WorkflowSchedulingOneHotEnhanced(WorkflowSchedulingOneHot):
    def _set_objective_function(self):
        expression_dict = {}
        cost_per_variable = zip(self.variables, self.workflow.cost_matrix.to_numpy().flatten())
        cost_per_variable = sorted(cost_per_variable, key=lambda x: str(x[0]))
        for variable, cost in cost_per_variable:
            cost_str = "{:.15g}".format(cost)
            expression_dict[tuple([str(variable)])] = float(cost_str)
        self.objective_function: Polynomial = Polynomial(expression_dict)

    def _set_constraints(self):
        self.constraints: list[Constraint] = []

        # machine assignment constraint
        for task_id in range(len(self.workflow.time_matrix.index)):
            machine_assignment_expr_dict = {}
            for machine_id in range(len(self.workflow.time_matrix.columns)):
                variable = self.variables[machine_id + task_id * len(self.workflow.time_matrix.columns)]
                machine_assignment_expr_dict[tuple([str(variable)])] = 1
            self.constraints.append(Constraint(Polynomial(machine_assignment_expr_dict), 1, Operator.EQ))

        # deadline constraint
        for path in self.workflow.paths:
            path_expr_dict = {}
            for task_id, task_name in enumerate(self.workflow.time_matrix.index):
                for machine_id, machine_name in enumerate(
                        self.workflow.time_matrix.columns
                ):
                    if task_name in path:
                        time = self.workflow.time_matrix[machine_name][task_name]
                        variable = self.variables[machine_id + task_id * len(self.workflow.time_matrix.columns)]
                        time_str = "{:.15g}".format(time)
                        path_expr_dict[tuple([str(variable)])] = float(time_str)

            # todo add constraints unbalanced penalization
            self.constraints.append(
                Constraint(
                    Polynomial(path_expr_dict),
                    self.workflow.deadline,
                    Operator.LE,
                    MethodsForInequalities.UNBALANCED_PENALIZATION,
                )
            )

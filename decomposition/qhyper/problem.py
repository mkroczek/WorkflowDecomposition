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

from QHyper.problems.workflow_scheduling import Workflow, WorkflowSchedulingOneHot

from decomposition.qhyper.problem import decorate


def test_solution_cost_and_timespan():
    # given
    workflow = load_workflow()
    wsp = WorkflowSchedulingOneHot(workflow)
    machine_assignment = {
        "Task1": "MachineB",
        "Task2": "MachineC",
        "Task3": "MachineA",
        "Task4": "MachineA",
        "Task5": "MachineA",
        "Task6": "MachineA",
        "Task7": "MachineA",
        "Task8": "MachineA",
        "Task9": "MachineA",
        "Task10": "MachineA"
    }

    # when
    wsp = decorate(wsp)
    cost = wsp.calculate_solution_cost(machine_assignment)
    timespan = wsp.calculate_solution_timespan(machine_assignment)

    # then
    assert cost == 75
    assert timespan == 28


def load_workflow():
    tasks_file = "resources/workflows/complex_workflow_old.json"
    machines_file = "resources/machines/3_machines.json"
    deadline = 50
    return Workflow(tasks_file, machines_file, deadline)

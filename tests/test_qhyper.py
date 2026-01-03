from QHyper.problems.workflow_scheduling import Workflow

from decomposition.qhyper.algorithm import WorkflowDecompositionQHyperAdapter, QHyperWorkflow, Division


def test_qhyper_decomposition(resources_dir):
    workflow = load_workflow(resources_dir)
    max_subgraph_size = 4
    adapter = WorkflowDecompositionQHyperAdapter(workflow)
    division: Division = adapter.decompose(max_subgraph_size)
    assert len(division.workflows) == 4
    assert {w.deadline for w in division.workflows} == {50.0, 25.0, 25.0, 25.0}


def test_qhyper_workflow(resources_dir):
    workflow = load_workflow(resources_dir)
    new_workflow = QHyperWorkflow(workflow.wf_instance.workflow, workflow.machines, workflow.deadline)
    assert new_workflow.machines == workflow.machines


def load_workflow(resources_dir):
    tasks_file = resources_dir / "workflows/complex_workflow.json"
    machines_file = resources_dir / "machines/3_machines.json"
    deadline = 50
    return Workflow(tasks_file, machines_file, deadline)

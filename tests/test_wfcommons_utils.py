import networkx as nx
from wfcommons import Instance

from decomposition.wfcommons_utils import wrap_in_workflow


def test_wrap_in_workflow(resources_dir):
    tasks_file = resources_dir / "workflows/complex_workflow.json"
    old_workflow = Instance(tasks_file).workflow
    subworkflow = nx.DiGraph([('Task1', 'Task2'), ('Task2', 'NewTask')])

    wf_subworkflow = wrap_in_workflow(old_workflow, subworkflow)

    assert wf_subworkflow.tasks['Task1'] == old_workflow.tasks['Task1']
    assert wf_subworkflow.tasks['Task2'] == old_workflow.tasks['Task2']
    assert wf_subworkflow.tasks['NewTask'].runtime == 0

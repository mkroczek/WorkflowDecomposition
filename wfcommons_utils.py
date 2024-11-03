import networkx as nx
from wfcommons.common import Workflow, Task, TaskType
from wfcommons.common.machine import Machine


class ArtificialMachine(Machine):
    def __init__(self):
        super().__init__(
            name="Artificial machine",
            cpu={
                "speed": 1,
                "count": 1
            })


class ArtificialTask(Task):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            task_type=TaskType.COMPUTE,
            runtime=0,
            cores=1,
            machine=ArtificialMachine(),
            category="artificial"
        )


def get_task(old_workflow: Workflow, name: str):
    if name in old_workflow.tasks:
        return old_workflow.tasks[name]
    else:
        return ArtificialTask(name)


def wrap_in_workflow(old_workflow: Workflow, subworkflow: nx.DiGraph) -> Workflow:
    node_mapping: dict[str, Task] = {name: get_task(old_workflow, name) for name in subworkflow.nodes}
    new_workflow = Workflow()
    for node in subworkflow.nodes:
        new_workflow.add_task(node_mapping[node])
    for node1, node2 in subworkflow.edges:
        task1_name, task2_name = node_mapping[node1].name, node_mapping[node2].name
        new_workflow.add_dependency(task1_name, task2_name)
    return new_workflow

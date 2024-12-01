import pathlib
import tempfile

from QHyper.problems.workflow_scheduling import Workflow, TargetMachine
from wfcommons.common import Workflow as WfWorkflow

from decomposition.algorithm import WorkflowDecompositionAlgorithm
from decomposition.wfcommons_utils import wrap_in_workflow


class QHyperWorkflow(Workflow):
    def __init__(self, wf_workflow: WfWorkflow, machines: dict[str, TargetMachine], deadline: float):
        with tempfile.NamedTemporaryFile() as temp:
            wf_workflow.write_json(pathlib.Path(temp.name))
            super().__init__(pathlib.Path(temp.name), machines, deadline)

    def _get_machines(self, machines: dict[str, TargetMachine]) -> dict[str, TargetMachine]:
        return machines


class WorkflowDecompositionQHyperAdapter:
    def __init__(self, qhyper_workflow: Workflow):
        self.qhyper_workflow = qhyper_workflow

    def decompose(self, max_subgraph_size: int):
        workflow = self.qhyper_workflow.wf_instance.workflow
        workload: dict = self.qhyper_workflow.time_matrix.mean(axis=1).to_dict()
        deadline = self.qhyper_workflow.deadline
        algorithm = WorkflowDecompositionAlgorithm()
        return self.decode_solution(algorithm.decompose(workflow, workload, deadline, max_subgraph_size))

    def decode_solution(self, solution):
        workflows = []
        for subworkflow, deadline in solution:
            wf_subworkflow = wrap_in_workflow(self.qhyper_workflow.wf_instance.workflow, subworkflow)
            workflows.append(QHyperWorkflow(wf_subworkflow, self.qhyper_workflow.machines, deadline))
        return workflows

import pathlib
import tempfile
from dataclasses import dataclass

import networkx as nx
from QHyper.problems.workflow_scheduling import Workflow, TargetMachine
from wfcommons.common import Workflow as WfWorkflow

from decomposition.algorithm import WorkflowDecompositionAlgorithm, Decomposition
from decomposition.tree import SPTreeNode
from decomposition.wfcommons_utils import wrap_in_workflow


class QHyperWorkflow(Workflow):
    def __init__(self, wf_workflow: WfWorkflow, machines: dict[str, TargetMachine], deadline: float):
        with tempfile.NamedTemporaryFile() as temp:
            wf_workflow.write_json(pathlib.Path(temp.name))
            super().__init__(pathlib.Path(temp.name), machines, deadline)

    def _get_machines(self, machines: dict[str, TargetMachine]) -> dict[str, TargetMachine]:
        return machines


@dataclass
class Division:
    complete_workflow: Workflow
    original_workflow: Workflow
    workflows: list[Workflow]


@dataclass
class SeriesParallelSplitDivision(Division):
    tree: SPTreeNode


class WorkflowDecompositionQHyperAdapter:
    def __init__(self, qhyper_workflow: Workflow):
        self.qhyper_workflow = qhyper_workflow

    def decompose(self, max_subgraph_size: int) -> SeriesParallelSplitDivision:
        workflow = self.qhyper_workflow.wf_instance.workflow
        workload: dict = self.qhyper_workflow.time_matrix.mean(axis=1).to_dict()
        deadline = self.qhyper_workflow.deadline
        algorithm = WorkflowDecompositionAlgorithm()
        return self.decode_solution(algorithm.decompose(workflow, workload, deadline, max_subgraph_size))

    def map_to_qhyper_workflow(self, workflow: nx.DiGraph, deadline: float):
        wf_workflow = wrap_in_workflow(self.qhyper_workflow.wf_instance.workflow, workflow)
        return QHyperWorkflow(wf_workflow, self.qhyper_workflow.machines, deadline)

    def decode_solution(self, solution: Decomposition) -> SeriesParallelSplitDivision:
        return SeriesParallelSplitDivision(
            complete_workflow=self.map_to_qhyper_workflow(solution.complete_workflow, self.qhyper_workflow.deadline),
            original_workflow=self.map_to_qhyper_workflow(solution.original_workflow, self.qhyper_workflow.deadline),
            workflows=[self.map_to_qhyper_workflow(subworkflow, deadline)
                       for subworkflow, deadline in solution.workflows],
            tree=solution.tree
        )

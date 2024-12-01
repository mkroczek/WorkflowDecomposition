import networkx as nx

from decomposition.sp_graph import get_sp_decomposition_tree
from decomposition.spization import JavaFacadeSpIzationAlgorithm
from decomposition.tree import distribute_weights, distribute_deadline, prune_tree_by_max_subgraph_size, modify_series_nodes


class WorkflowDecompositionAlgorithm:
    def decompose(self, workflow: nx.DiGraph, workload: dict[str, float], deadline: float, max_subgraph_size: int):
        sp_workflow = JavaFacadeSpIzationAlgorithm().run(workflow)
        tree = get_sp_decomposition_tree(sp_workflow)
        distribute_weights(tree, workload)
        tree = prune_tree_by_max_subgraph_size(tree, max_subgraph_size)
        tree = modify_series_nodes(tree, workload, sp_workflow)
        distribute_deadline(tree, deadline)
        return [(sp_workflow.subgraph(leaf.get_graph_nodes()), leaf.deadline) for leaf in tree.leaves]

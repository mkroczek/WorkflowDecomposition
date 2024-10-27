import networkx as nx

from sp_graph import get_sp_decomposition_tree
from spization import JavaFacadeSpIzationAlgorithm
from tree import distribute_weights, distribute_deadline, prune_tree_by_max_subgraph_size


class WorkflowDecompositionAlgorithm:
    def __init__(self):
        pass

    def decompose(self, workflow: nx.DiGraph, workload: dict[str, float], deadline: float, max_subgraph_size: int):
        sp_workflow = JavaFacadeSpIzationAlgorithm().run(workflow)
        tree = get_sp_decomposition_tree(sp_workflow)
        distribute_weights(tree, workload)
        tree = prune_tree_by_max_subgraph_size(tree, max_subgraph_size)
        distribute_deadline(tree, deadline)
        subgraphs = [workflow.subgraph(leaf.get_graph_nodes()) for leaf in tree.leaves]
        return subgraphs

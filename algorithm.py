from collections import defaultdict

import networkx as nx
import pandas as pd

from sp_graph import get_sp_decomposition_tree
from spization import JavaFacadeSpIzationAlgorithm
from tree import distribute_weights, distribute_deadline, prune_tree_by_max_subgraph_size


class WorkflowDecompositionAlgorithm:
    def __init__(self):
        pass

    def decompose(self, workflow: nx.DiGraph, time_matrix: pd.DataFrame, deadline: float, max_subgraph_size: int):
        sp_workflow = JavaFacadeSpIzationAlgorithm().run(workflow)
        vertex_weights: dict = time_matrix.mean(axis=1).to_dict(defaultdict(float))
        tree = get_sp_decomposition_tree(sp_workflow)
        distribute_weights(tree, vertex_weights)
        tree = prune_tree_by_max_subgraph_size(tree, max_subgraph_size)
        distribute_deadline(tree, deadline)

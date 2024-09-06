from collections import defaultdict

import networkx as nx
import pandas as pd

from spization import JavaFacadeSpIzationAlgorithm
from tree import WeightDistributionVisitor, SPTreeNode


class WorkflowDecompositionAlgorithm:
    def __init__(self):
        pass

    def decompose(self, workflow: nx.DiGraph, time_matrix: pd.DataFrame, deadline: float, max_subgraph_size: int):
        sp_workflow = JavaFacadeSpIzationAlgorithm().run(workflow)
        vertex_weights: dict = time_matrix.mean(axis=1).to_dict(defaultdict(float))
        distribute_weights(tree, vertex_weights)

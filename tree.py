import uuid
from abc import abstractmethod, ABC
from collections.abc import Callable

from anytree import Node, PostOrderIter, PreOrderIter


class SPTreeNode(Node, ABC):
    def __init__(self, **kwargs):
        super().__init__(name=uuid.uuid1(), **kwargs)
        self.weight: float = None
        self.deadline: float = None

    @abstractmethod
    def accept(self, visitor):
        pass


class CompositionNode(SPTreeNode, ABC):
    def __init__(self, left_child=None, right_child=None):
        super().__init__(children=[left_child, right_child])
        self.left_child: SPTreeNode = left_child
        self.right_child: SPTreeNode = right_child


class SeriesNode(CompositionNode):
    def __init__(self, left_child, right_child, connecting_node):
        super().__init__(left_child, right_child)
        self.connecting_node = connecting_node

    def accept(self, visitor):
        visitor.visit_series_node(self)


class ParallelNode(CompositionNode):
    def __init__(self, left_child, right_child, source, sink):
        super().__init__(left_child, right_child)
        self.source = source
        self.sink = sink

    def accept(self, visitor):
        visitor.visit_parallel_node(self)


class LeafNode(SPTreeNode):
    def __init__(self, edge: (str, str)):
        super().__init__()
        self.edge: (str, str) = edge

    def accept(self, visitor):
        visitor.visit_leaf_node(self)


class PruneNode(SPTreeNode):
    def __init__(self, node_to_override: SPTreeNode):
        super().__init__()
        self.weight = node_to_override.weight
        self.deadline = node_to_override.deadline

    def accept(self, visitor):
        pass

    @staticmethod
    def replace_in_tree(node: SPTreeNode):
        parent = node.parent
        node.parent = None
        prune_node = PruneNode(node)
        prune_node.parent = parent
        return prune_node


class SPTreeVisitor(ABC):
    @abstractmethod
    def visit_series_node(self, node: SeriesNode):
        pass

    @abstractmethod
    def visit_parallel_node(self, node: ParallelNode):
        pass

    @abstractmethod
    def visit_leaf_node(self, node: LeafNode):
        pass


class WeightDistributionVisitor(SPTreeVisitor):
    def __init__(self, vertex_weights: dict[str, float]):
        self.vertex_weights = vertex_weights

    def visit_series_node(self, node: SeriesNode):
        node.weight = node.left_child.weight + node.right_child.weight - self.vertex_weights[node.connecting_node]

    def visit_parallel_node(self, node: ParallelNode):
        node.weight = max(node.left_child.weight, node.right_child.weight)

    def visit_leaf_node(self, node: LeafNode):
        u, v = node.edge
        node.weight = self.vertex_weights[u] + self.vertex_weights[v]


class DeadlineDistributionVisitor(SPTreeVisitor):
    def __init__(self, deadlines: dict[str, float]):
        self.deadlines = deadlines

    def visit_series_node(self, node: SeriesNode):
        node.deadline = self.deadlines[node.name]
        children_weights = sum(child.weight for child in node.children)
        for child in node.children:
            self.deadlines[child.name] = child.weight / children_weights * node.deadline

    def visit_parallel_node(self, node: ParallelNode):
        node.deadline = self.deadlines[node.name]
        for child in node.children:
            self.deadlines[child.name] = node.deadline

    def visit_leaf_node(self, node: LeafNode):
        node.deadline = self.deadlines[node.name]


def distribute_weights(tree: SPTreeNode, vertex_weights: dict):
    visitor: WeightDistributionVisitor = WeightDistributionVisitor(vertex_weights)
    for node in PostOrderIter(tree):
        node.accept(visitor)


def distribute_deadline(tree: SPTreeNode, deadline: float):
    deadlines = {tree.name: deadline}
    visitor: DeadlineDistributionVisitor = DeadlineDistributionVisitor(deadlines)
    for node in PreOrderIter(tree):
        node.accept(visitor)


class PruneTreeVisitor(SPTreeVisitor):
    def __init__(self, prune_predicate: Callable, predicate_not_satisfied_action: Callable = None):
        self.prune_predicate = prune_predicate
        self.predicate_not_satisfied_action: Callable = predicate_not_satisfied_action
        if not self.predicate_not_satisfied_action:
            self.predicate_not_satisfied_action = self._default_predicate_not_satisfied_action

    def _default_predicate_not_satisfied_action(self):
        raise ValueError("Required prune tree predicate couldn't be satisfied")

    def visit_composition_node(self, node: CompositionNode):
        if self.prune_predicate(node):
            PruneNode.replace_in_tree(node)
        else:
            for child in node.children:
                child.accept(self)

    def visit_series_node(self, node: SeriesNode):
        self.visit_composition_node(node)

    def visit_parallel_node(self, node: ParallelNode):
        self.visit_composition_node(node)

    def visit_leaf_node(self, node: LeafNode):
        if self.prune_predicate(node):
            PruneNode.replace_in_tree(node)
        else:
            self.predicate_not_satisfied_action()


def prune_tree(tree: SPTreeNode, prune_predicate: Callable,
               predicate_not_satisfied_action: Callable = None) -> SPTreeNode:
    if prune_predicate(tree):
        return PruneNode(tree)
    visitor = PruneTreeVisitor(prune_predicate, predicate_not_satisfied_action)
    tree.accept(visitor)
    return tree


def prune_tree_by_max_subgraph_size(tree: SPTreeNode, max_subgraph_size: int):
    if max_subgraph_size < 2:
        raise ValueError("Max subgraph size must be grater than 1")

    def max_subgraph_size_predicate(node: SPTreeNode):
        raise NotImplementedError()

    def max_subgraph_size_not_satisfied_action():
        raise ValueError("Required prune tree predicate couldn't be satisfied")

    prune_tree(
        tree,
        max_subgraph_size_predicate,
        max_subgraph_size_not_satisfied_action
    )

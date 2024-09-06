import uuid
from abc import abstractmethod, ABC

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

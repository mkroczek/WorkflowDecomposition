import math

import networkx as nx

from sp_graph import get_sp_decomposition_tree
from tree import LeafNode, SeriesNode, ParallelNode, distribute_weights, distribute_deadline


def test_leaf_node():
    edge = ("Task1", "Task2")
    node = LeafNode(edge)

    assert node.edge == edge
    assert node.name


def test_series_node():
    left_child = LeafNode(("Task1", "Task2"))
    right_child = LeafNode(("Task2", "Task3"))
    node = SeriesNode(left_child, right_child, "Task2")

    assert left_child in node.children and right_child in node.children
    assert node.connecting_node == "Task2"
    assert node.name


def test_parallel_node():
    left_child = LeafNode(("Task1", "Task2"))
    right_child = LeafNode(("Task1", "Task2"))
    node = ParallelNode(left_child, right_child, "Task2", "Task3")

    assert left_child in node.children and right_child in node.children
    assert node.source == "Task2"
    assert node.sink == "Task3"
    assert node.name


def test_weights_distribution():
    graph = create_non_trivial_sp_dag()
    tree = get_sp_decomposition_tree(graph)
    vertices_weights = {
        "Task1": 6,
        "Task2": 8,
        "Task3": 4,
        "Task4": 4,
        "Task5": 6,
        "Task6": 2,
        "Task7": 6,
        "Task8": 0
    }

    distribute_weights(tree, vertices_weights)

    assert tree.weight == 22


def test_deadline_distribution():
    graph = create_non_trivial_sp_dag()
    tree = get_sp_decomposition_tree(graph)
    vertices_weights = {
        "Task1": 6,
        "Task2": 8,
        "Task3": 4,
        "Task4": 4,
        "Task5": 6,
        "Task6": 2,
        "Task7": 0,
        "Task8": 0
    }
    deadline = 20
    expected_deadlines = {
        ('Task8', 'Task1'): 5,
        ('Task8', 'Task2'): 5,
        ('Task8', 'Task3'): 8,
        ('Task1', 'Task7'): 5,
        ('Task2', 'Task7'): 5,
        ('Task7', 'Task4'): 4,
        ('Task7', 'Task5'): 4.28,
        ('Task3', 'Task6'): 12,
        ('Task4', 'Task6'): 6,
        ('Task5', 'Task6'): 5.71
    }

    distribute_weights(tree, vertices_weights)
    distribute_deadline(tree, deadline)

    for leaf in tree.leaves:
        assert math.isclose(expected_deadlines[leaf.edge], leaf.deadline, rel_tol=0, abs_tol=0.01)

def create_non_trivial_sp_dag():
    return nx.DiGraph([('Task8', 'Task1'),
                       ('Task8', 'Task2'),
                       ('Task8', 'Task3'),
                       ('Task1', 'Task7'),
                       ('Task2', 'Task7'),
                       ('Task7', 'Task4'),
                       ('Task7', 'Task5'),
                       ('Task3', 'Task6'),
                       ('Task4', 'Task6'),
                       ('Task5', 'Task6')])

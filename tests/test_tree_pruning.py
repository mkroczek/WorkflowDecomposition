from collections.abc import Callable

import networkx as nx
import pytest

from decomposition.sp_graph import get_sp_decomposition_tree
from decomposition.tree import prune_tree, PruneNode, LeafNode, prune_tree_by_max_subgraph_size


def rise_value_error_action(message: str) -> Callable:
    def _raise_action():
        raise ValueError(message)

    return _raise_action


@pytest.mark.parametrize("action, expected_message", [
    (None, "Required prune tree predicate couldn't be satisfied"),
    (rise_value_error_action("This message overrides default"), "This message overrides default")
])
def test_unsatisfied_prune_predicate_action(action: Callable, expected_message: str):
    graph = create_non_trivial_sp_dag()
    tree = get_sp_decomposition_tree(graph)
    always_fail_predicate = lambda node: False

    with pytest.raises(ValueError, match=expected_message):
        prune_tree(tree, always_fail_predicate, action)


def test_prune_with_depth_predicate():
    graph = create_non_trivial_sp_dag()
    tree = get_sp_decomposition_tree(graph)

    new_tree = prune_tree(tree, lambda node: node.depth >= 2)

    assert new_tree.height == 2
    for leaf in new_tree.leaves:
        assert isinstance(leaf, PruneNode)


def test_prune_single_node():
    tree = LeafNode(("Task1", "Task2"))

    new_tree = prune_tree(tree, lambda node: True)

    assert isinstance(new_tree, PruneNode)


def test_prune_by_max_subgraph_size():
    graph = create_non_trivial_sp_dag()
    tree = get_sp_decomposition_tree(graph)

    new_tree = prune_tree_by_max_subgraph_size(tree, 4)

    for leaf in new_tree.leaves:
        assert isinstance(leaf, PruneNode)
        assert len(leaf.get_graph_nodes()) <= 4


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

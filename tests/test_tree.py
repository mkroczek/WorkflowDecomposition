from tree import LeafNode, SeriesNode, ParallelNode


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

from decomposition.tree import PruneNode, SeriesNodesModifier


def test_new_weight_calculation():
    node = PruneNode(
        graph_source="Task1",
        graph_sink="Task5",
        graph_nodes={"Task1", "Task2", "Task3", "Task4", "Task5"}
    )
    vertex_weights = {'Task1': 6, 'Task2': 8, 'Task3': 4, 'Task4': 4, 'Task5': 6}
    override_vertices = {"Task2": "Task2_substitute", "Task3": "Task3_substitute"}
    node.weight = 28

    modifier = SeriesNodesModifier(node, vertex_weights, None)
    new_weight = modifier.new_weight(node, override_vertices)

    assert new_weight == 16

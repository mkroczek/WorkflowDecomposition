import networkx as nx

from algorithm import WorkflowDecompositionAlgorithm


def test_decomposition_for_sp_dag():
    graph = create_non_trivial_sp_dag()
    workload = {
        'Task1': 6,
        'Task2': 8,
        'Task3': 4,
        'Task4': 4,
        'Task5': 6,
        'Task6': 2,
        'Task7': 6,
        'Task8': 0,
    }
    deadline = 20
    max_subgraph_size = 4
    algorithm = WorkflowDecompositionAlgorithm()
    expected_divisions = [
        ({"Task8", "Task3", "Task6"}, 20),
        ({"Task8", "Task1", "Task2", "Task7"}, 12.73),
        ({"Task7_substitute", "Task4", "Task5", "Task6"}, 7.27)
    ]

    divisions = algorithm.decompose(graph, workload, deadline, max_subgraph_size)

    assert len(divisions) == 3
    for subgraph, deadline in divisions:
        assert (set(subgraph.nodes), round(deadline, 2)) in expected_divisions


def test_decomposition_for_non_sp_dag():
    graph = create_non_sp_dag()
    workload = {
        'Task1': 6,
        'Task2': 8,
        'Task3': 4,
        'Task4': 4,
        'Task5': 6,
        'Task6': 2,
        'Task7': 6,
    }
    deadline = 20
    max_subgraph_size = 4
    algorithm = WorkflowDecompositionAlgorithm()
    expected_divisions = [
        ({"NewNode7", "Task3", "Task6"}, 20),
        ({"NewNode7", "Task1", "Task2", "Task7"}, 12.73),
        ({"Task7_substitute", "Task4", "Task5", "Task6"}, 7.27),
    ]

    divisions = algorithm.decompose(graph, workload, deadline, max_subgraph_size)

    assert len(divisions) == 3
    for subgraph, deadline in divisions:
        assert (set(subgraph.nodes), round(deadline, 2)) in expected_divisions


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


def create_non_sp_dag():
    return nx.DiGraph([('Task1', 'Task7'),
                       ('Task2', 'Task7'),
                       ('Task7', 'Task4'),
                       ('Task7', 'Task5'),
                       ('Task3', 'Task6'),
                       ('Task4', 'Task6'),
                       ('Task5', 'Task6')])

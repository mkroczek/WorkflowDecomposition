import networkx as nx

from decomposition.sp_graph import is_trivial_sp_dag, reduce_graph, is_sp_dag, get_sp_decomposition_tree


def test_trivial_sp_dag_recognition():
    trivial_sp_dag = nx.DiGraph([('Task1', 'Task2')])
    non_trivial_sp_dag = create_non_trivial_sp_dag()

    assert is_trivial_sp_dag(trivial_sp_dag)
    assert not is_trivial_sp_dag(non_trivial_sp_dag)


def test_graph_reduction():
    non_trivial_sp_dag = create_non_trivial_sp_dag()
    n_nodes = non_trivial_sp_dag.number_of_nodes()
    n_edges = non_trivial_sp_dag.number_of_edges()

    reduced = reduce_graph(non_trivial_sp_dag)

    assert is_trivial_sp_dag(reduced)
    assert non_trivial_sp_dag.number_of_edges() == n_edges
    assert non_trivial_sp_dag.number_of_nodes() == n_nodes


def test_sp_dag_recognition():
    non_trivial_sp_dag = create_non_trivial_sp_dag()
    trivial_sp_dag = nx.DiGraph([('Task1', 'Task2')])
    empty_graph = nx.DiGraph()
    non_sp_dag = create_non_sp_dag()

    assert is_sp_dag(non_trivial_sp_dag)
    assert is_sp_dag(trivial_sp_dag)
    assert not is_sp_dag(empty_graph)
    assert not is_sp_dag(non_sp_dag)


def test_get_sp_decomposition_tree():
    non_trivial_sp_dag = create_non_trivial_sp_dag()

    tree = get_sp_decomposition_tree(non_trivial_sp_dag)

    assert tree.height == 4
    assert [leaf.edge[:2] in non_trivial_sp_dag.edges for leaf in tree.leaves]

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
    return nx.DiGraph([('Task8', 'Task1'),
                       ('Task8', 'Task2'),
                       ('Task8', 'Task3'),
                       ('Task1', 'Task7'),
                       ('Task2', 'Task7'),
                       ('Task2', 'Task5'),
                       ('Task7', 'Task4'),
                       ('Task7', 'Task5'),
                       ('Task3', 'Task6'),
                       ('Task4', 'Task6'),
                       ('Task5', 'Task6')])

import subprocess
from abc import ABC, abstractmethod
from dataclasses import field, dataclass
from importlib import resources

import networkx as nx


class SpIzationAlgorithm(ABC):
    @abstractmethod
    def run(self, graph: nx.DiGraph):
        pass


class Parser:
    def __init__(self, graph: nx.DiGraph):
        self.graph: nx.DiGraph = graph
        self.node_indexing: dict[str, int] = self._create_node_indexing()
        self.reverse_node_indexing: dict[int, str] = {idx: name for name, idx in self.node_indexing.items()}

    def _create_node_indexing(self) -> dict[str, int]:
        return {name: idx for idx, name in enumerate(self.graph.nodes)}

    def encode_n_tasks(self) -> str:
        return f'T: {len(self.graph.nodes)}'

    def append_line(self, text: str, line: str):
        return text + line + "\n"

    def encode_node(self, node):
        task = f't{self.node_indexing[node]}'
        task_load = 1.0
        successors_ids = list(map(lambda s: str(self.node_indexing[s]), self.graph.successors(node)))
        successors_key = f's{len(successors_ids)}'
        successors_value = ' '.join(successors_ids)
        return f'{task}: m1, {task_load} {successors_key}: {successors_value}'

    def encode(self):
        encoded: str = ""
        encoded = self.append_line(encoded, self.encode_n_tasks())
        for node in self.graph.nodes:
            encoded = self.append_line(encoded, self.encode_node(node))
        return encoded

    def decode_node_line(self, line: str, out_graph: nx.DiGraph):
        task, _, neighbors = line.split(':')
        task_idx = int(task[1:])
        neighbors_idx = map(lambda n: int(n), neighbors.split())

        task_name = self.reverse_node_indexing.get(task_idx, f"NewNode{task_idx}")
        neighbors_names = map(lambda idx: self.reverse_node_indexing.get(idx, f"NewNode{idx}"), neighbors_idx)
        out_graph.add_node(task_name)
        for neighbor_name in neighbors_names:
            out_graph.add_edge(task_name, neighbor_name)

    def decode(self, graph: str) -> nx.DiGraph:
        out_graph: nx.DiGraph = nx.DiGraph()
        lines = graph.splitlines()
        nodes_lines = lines[2:]
        for line in nodes_lines:
            self.decode_node_line(line, out_graph)
        return out_graph


@dataclass
class RunnerConfiguration:
    jar_file: str
    args: list[str] = field(default_factory=list)


FORMAT_97_CONFIGURATION = RunnerConfiguration(
    jar_file=str(resources.files("resources").joinpath("SPizationAlgorithm-1.0-SNAPSHOT-jar-with-dependencies.jar")),
    args=["-fmt97"]
)


class SpIzationException(Exception):
    pass


class Runner:
    def __init__(self, config: RunnerConfiguration):
        self.config = config

    def run(self, program_input: str) -> str:
        args: list[str] = ["java", "-jar", self.config.jar_file] + self.config.args
        process = subprocess.Popen(args,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)

        stdout, stderr = process.communicate(input=program_input, timeout=600)
        if process.returncode != 0:
            raise SpIzationException(f"Execution of SpIzation algorithm failed: {stderr}")
        return stdout


class JavaFacadeSpIzationAlgorithm(SpIzationAlgorithm):
    def __init__(self):
        self.runner = Runner(FORMAT_97_CONFIGURATION)

    def run(self, graph: nx.DiGraph):
        parser: Parser = Parser(graph)
        input: str = parser.encode()
        output: str = self.runner.run(input)
        return parser.decode(output)

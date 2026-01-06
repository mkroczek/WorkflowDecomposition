from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field

from decomposition.qhyper.solver import WorkflowSchedule


@dataclass(frozen=True)
class Solution:
    cost: float
    time: float
    deadline: float
    machine_assignment: dict[str, str]
    parts: list[Solution] = field(default_factory=list)

    @classmethod
    def from_workflow_schedule(cls, schedule: WorkflowSchedule):
        return cls(
            cost=schedule.cost,
            time=schedule.time,
            deadline=schedule.deadline,
            machine_assignment=schedule.machine_assignment,
            parts=[cls.from_workflow_schedule(part) for part in schedule.parts]
        )


@dataclass
class ExecutionReport:
    workflow_file: str
    machines_file: str
    deadline: int
    solver: str
    solution: Solution
    max_graph_size: int = None
    timestamp: str = field(default=datetime.datetime.now().isoformat())

    def write_json(self, file_path):
        with open(file_path, 'w') as file:
            def filter_empty(d):
                def is_empty(x):
                    return x is None or x == {} or x == []

                return {k: v for k, v in d.items() if not is_empty(v)}

            json.dump(obj=filter_empty(self.__dict__), fp=file, default=lambda o: filter_empty(o.__dict__), indent=4)

import sys
import os
import time
import glob
from dataclasses import dataclass, field
from collections import defaultdict

sys.setrecursionlimit(50000)

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.insert(0, PROJECT_ROOT)

import networkx as nx
import numpy as np
import pandas as pd
import gurobipy as gp

from QHyper.problems.workflow_scheduling import Workflow
from QHyper.solvers.classical.gurobi.gurobi import Gurobi, polynomial_to_gurobi
from QHyper.solvers.base import SolverResult
from QHyper.constraint import Operator

from decomposition.qhyper.algorithm import WorkflowDecompositionQHyperAdapter
from decomposition.qhyper.problem import WorkflowSchedulingOneHotEnhanced

WORKFLOW_DIR = os.path.join(SCRIPT_DIR, "workflows")
MACHINES = os.path.join(SCRIPT_DIR, "../resources/machines/ec2_machines_normalized.json")
RESULTS_CSV = os.path.join(SCRIPT_DIR, "results.csv")
DEADLINE_MULTIPLIER = 1
MAX_SUB_FRACTION = 0.01
SPWD_SUB_TIME_LIMIT_S = 1 * 60 * 60
GUROBI_TIME_LIMIT_S   = 6 * 60 * 60

_GUROBI_STATUS = {
    2: "optimal", 
    3: "infeasible",
    4: "inf_or_unbd",
    5: "unbounded",
    9: "time_limit",
    11: "interrupted",
}

@dataclass
class TimedGurobi(Gurobi):
    """Source: https://github.com/qc-lab/QHyper/blob/main/QHyper/solvers/classical/gurobi/gurobi.py"""
    
    time_limit_s: float | None = None

    last_status:        str   | None = field(default=None, init=False, repr=False)
    last_runtime_s:     float | None = field(default=None, init=False, repr=False)
    last_model_build_s: float | None = field(default=None, init=False, repr=False)
    last_sol_count:     int          = field(default=0,    init=False, repr=False)
    last_mip_gap_pct:   float | None = field(default=None, init=False, repr=False)

    def solve(self) -> SolverResult:
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        if self.time_limit_s is not None:
            env.setParam("TimeLimit", self.time_limit_s)
        env.start()

        gpm = gp.Model(self.model_name, env=env)
        gpm.setParam("Threads", 1)
        if self.mip_gap:
            gpm.Params.MIPGap = self.mip_gap


        t_build = time.time()
        all_vars = self.problem.objective_function.get_variables()
        for con in self.problem.constraints:
            all_vars |= con.get_variables()

        gvars = {
            str(v): gpm.addVar(vtype=gp.GRB.BINARY, name=str(v))
            for v in all_vars
        }
        gpm.setObjective(
            polynomial_to_gurobi(gvars, self.problem.objective_function),
            gp.GRB.MINIMIZE,
        )
        for i, con in enumerate(self.problem.constraints):
            lhs = polynomial_to_gurobi(gvars, con.lhs)
            rhs = polynomial_to_gurobi(gvars, con.rhs)
            if con.operator == Operator.EQ:
                gpm.addConstr(lhs == rhs, f"constr_{i}")
            elif con.operator == Operator.LE:
                gpm.addConstr(lhs <= rhs, f"constr_{i}")
            elif con.operator == Operator.GE:
                gpm.addConstr(lhs >= rhs, f"constr_{i}")
        gpm.update()
        self.last_model_build_s = round(time.time() - t_build, 5)

        optimize_time = time.time()
        gpm.optimize()
        self.optimize_time = round(time.time() - optimize_time, 5)
        print("+", self.optimize_time)

        self.last_status = _GUROBI_STATUS.get(gpm.status, f"status_{gpm.status}")
        self.last_runtime_s = round(gpm.Runtime, 5)
        self.last_sol_count = gpm.SolCount
        try:
            self.last_mip_gap_pct = round(gpm.MIPGap * 100, 2) if gpm.SolCount > 0 else None
        except Exception:
            self.last_mip_gap_pct = None

        if gpm.SolCount == 0:
            raise Exception(f"Gurobi found no feasible solution (status={self.last_status})")

        vars_list = list(gvars.keys())
        solution  = {v.VarName: v.X for v in gpm.getVars()}
        recarray  = np.recarray(
            (1,), dtype=[(var, "i4") for var in vars_list] + [("probability", "f8")]
        )
        recarray[0] = *(int(round(solution[var])) for var in vars_list), 1.0
        return SolverResult(recarray, {}, [])


def count_paths_dp(workflow):
    """Count root-to-leaf paths"""
    G = workflow.wf_instance.workflow
    count = defaultdict(int)
    for root in [n for n in G if G.in_degree(n) == 0]:
        count[root] = 1
    for node in nx.topological_sort(G):
        for succ in G.successors(node):
            count[succ] += count[node]
    leaves = [n for n in G if G.out_degree(n) == 0]
    return sum(count[leaf] for leaf in leaves)


def critical_path_time(workflow):
    """Longest path using mean machine times"""
    G = workflow.wf_instance.workflow
    mean_t = workflow.time_matrix.mean(axis=1).to_dict()
    dist = defaultdict(float)
    for node in nx.topological_sort(G):
        for succ in G.successors(node):
            dist[succ] = max(dist[succ], dist[node] + mean_t.get(node, 0))
    leaves = [n for n in G if G.out_degree(n) == 0]
    return max(dist[leaf] + mean_t.get(leaf, 0) for leaf in leaves)


def schedule_makespan(workflow, assignment):
    """Makespan via topological"""
    G = workflow.wf_instance.workflow
    completion = {}
    for node in nx.topological_sort(G):
        exec_time = (
            workflow.time_matrix.loc[node, assignment[node]]
            if node in assignment else 0
        )
        earliest_start = max(
            (completion[pred] for pred in G.predecessors(node)), default=0
        )
        completion[node] = earliest_start + exec_time
    leaves = [n for n in G if G.out_degree(n) == 0]
    return max(completion[leaf] for leaf in leaves) if leaves else 0.0


def decode_solver_result(solver_result: SolverResult, problem) -> dict:
    """Decode SolverResult recarray to {task: machine}"""
    best = solver_result.probabilities[0]
    raw  = {var: int(best[var]) for var in best.dtype.names if var != "probability"}
    return problem.decode_solution(raw)


def run_spwd(workflow, max_sub_fraction, time_limit_per_sub_s):
    n_tasks = len(workflow.tasks)
    max_subgraph_size = max(2, int(max_sub_fraction * n_tasks))
    out = {"max_subgraph_size": max_subgraph_size}

    # Phase 1: SPization
    t_spization = time.time()
    try:
        division = WorkflowDecompositionQHyperAdapter(workflow).decompose(max_subgraph_size)
    except Exception as e:
        return {**out, "spwd_status": "decompose_error", "spwd_error": str(e)[:120]}
    out["spwd_spization_sec"] = round(time.time() - t_spization, 5)
    out["spwd_num_subworkflows"] = len(division.workflows)
    out["spwd_max_tasks_subworkflow"] = max(
        (len(list(wf.tasks)) for wf in division.workflows), default=0
    )
    out["spwd_max_paths_subworkflow"] = max((count_paths_dp(wf) for wf in division.workflows), default=0)

    # Phase 2: sub-problem construction
    t_problem_encoding_qhyper = time.time()
    try:
        problems = [WorkflowSchedulingOneHotEnhanced(w) for w in division.workflows]
        print("NUM: ", len(problems))
    except Exception as e:
        return {**out, "spwd_status": "problem_init_error", "spwd_error": str(e)[:120]}
    out["spwd_problem_encoding_qhyper_sec"] = round(time.time() - t_problem_encoding_qhyper, 5)

    t_timed_gurobi_subproblems_creation = time.time()
    timed_gurobi_list = [
        TimedGurobi(p, time_limit_s=time_limit_per_sub_s) for p in problems
    ]
    out["t_timed_gurobi_subproblems_creation_sec"] = round(time.time() - t_timed_gurobi_subproblems_creation, 5)
    # Phase 3: solve each sub-problem
    t_total_solver = time.time()
    all_assignments = []
    for i, tg in enumerate(timed_gurobi_list):
        try:
            solver_result = tg.solve()
        except Exception as e:
            return {**out, "spwd_status": "solver error", "spwd_error": str(e)[:120]}
        all_assignments.append(decode_solver_result(solver_result, tg.problem))
    out["spwd_total_solver_sec"] = round(time.time() - t_total_solver, 5)
    out["spwd_gurobi_model_build_for_all_sum_sec"] = round(sum(g.last_model_build_s or -1000000 for g in timed_gurobi_list), 5)
    out["spwd_gurobi_runtime_for_all_sum_sec"] = round(sum(g.last_runtime_s or -1000000 for g in timed_gurobi_list), 5)
    out["spwd_gurobi_optimize_sum_sec"] = round(sum(g.optimize_time or -1000000 for g in timed_gurobi_list), 5)


    # Merge: pick faster machine for tasks shared across sub-workflows
    t_merge_time = time.time()
    complete_wf = division.complete_workflow
    merged = {}
    for assignment in all_assignments:
        for task, machine in assignment.items():
            if task not in merged:
                merged[task] = machine
            else:
                t1 = complete_wf.time_matrix.loc[task, merged[task]]
                t2 = complete_wf.time_matrix.loc[task, machine]
                if t2 < t1:
                    merged[task] = machine
    out["spwd_gurobi_merge_time"] = round(time.time() - t_merge_time, 5)

    time_schedule = time.time()
    orig_wf = division.original_workflow
    orig_assignment = {t: m for t, m in merged.items() if t in orig_wf.task_names}

    # schedule_makespan replaces calculate_solution_timespan — exponential path enumeration avoided
    makespan = schedule_makespan(orig_wf, orig_assignment)
    cost = sum(orig_wf.cost_matrix.loc[t, m] for t, m in orig_assignment.items())
    out["t_schedule_sec"] = round(time.time() - time_schedule, 5)

    out["spwd_status"] = "solved" if makespan <= orig_wf.deadline else "deadline_exceeded"
    
    out["spwd_total_time_sec"] = round(out["spwd_spization_sec"]
        + out["spwd_problem_encoding_qhyper_sec"]
        + out["t_timed_gurobi_subproblems_creation_sec"]
        + out["spwd_total_solver_sec"]
        + out["spwd_gurobi_merge_time"]
        + out["t_schedule_sec"], 5
    )
        
    out["spwd_cost"] = round(cost, 5)
    out["spwd_makespan"] = round(makespan, 5)
    return out


def run_gurobi(workflow, time_limit_s):
    row = {}
    try:
        # Phase 1: problem construction
        t_problem_encoding_qhyper = time.time()
        problem = WorkflowSchedulingOneHotEnhanced(workflow)
        row["gurobi_problem_encoding_qhyper_sec"] = round(time.time() - t_problem_encoding_qhyper, 5)

        t_class_creation = time.time()
        timed_gurobi = TimedGurobi(problem=problem, time_limit_s=time_limit_s)
        row["t_timed_gurobi_problem_creation_sec"] = round(time.time() - t_class_creation, 5)


        # Phase 2+3: model build + gpm.optimize
        t_gurobi_solver_solve = time.time()
        solver_result = timed_gurobi.solve()
        row["gurobi_total_time_sec"] = round(time.time() - t_gurobi_solver_solve, 5)

        t_schedule = time.time()
        machine_assignment = decode_solver_result(solver_result, problem)
        row["gurobi_cost"] = round(sum(workflow.cost_matrix.loc[t, m] for t, m in machine_assignment.items()), 5)
        row["gurobi_makespan"] = round(schedule_makespan(workflow, machine_assignment), 5)
        row["t_gurobi_decode_schedule_sec"] = round(time.time() - t_schedule, 5)
        
        
        row["gurobi_model_build_sec"] = timed_gurobi.last_model_build_s
        row["gurobi_runtime_sec"]     = timed_gurobi.last_runtime_s
        row["optimize_sec"]     = timed_gurobi.optimize_time
        row["gurobi_status"]        = timed_gurobi.last_status
        row["gurobi_sol_count"]     = timed_gurobi.last_sol_count
        row["gurobi_mip_gap_pct"]   = timed_gurobi.last_mip_gap_pct

    except Exception as e:
        return {**row, "gurobi_status": "error", "error": str(e)[:120]}

    return row

def append_row(row, csv_path):
    df_row = pd.DataFrame([row])
    write_header = not os.path.exists(csv_path)
    df_row.to_csv(csv_path, mode="a", header=write_header, index=False)


def main():
    workflow_files = sorted(glob.glob(os.path.join(WORKFLOW_DIR, "*.json")))
    if not workflow_files:
        print(f"No .json files found in {WORKFLOW_DIR}")
        return

    print(f"Found {len(workflow_files)} workflow(s)  →  {RESULTS_CSV}")
    print(
        f"Config: DEADLINE_MULTIPLIER={DEADLINE_MULTIPLIER} | MAX_SUB_FRACTION={MAX_SUB_FRACTION} | "
        f"SPWD_SUB_LIMIT={SPWD_SUB_TIME_LIMIT_S}s | GUROBI_LIMIT={GUROBI_TIME_LIMIT_S/3600:.0f}h"
    )

    for tasks_file in workflow_files:
        label = os.path.basename(tasks_file).removesuffix(".json")
        print(f"\n{'='*72}\n  {label}\n{'='*72}")

        row = {"instance": label, "machine": MACHINES.removesuffix(".json").split("/")[-1]}

        t0 = time.time()
        try:
            workflow = Workflow(tasks_file, MACHINES, 100000)
            deadline = int(critical_path_time(workflow) * DEADLINE_MULTIPLIER)
            workflow.deadline = deadline
        except Exception as e:
            row["error"] = str(e)[:120]
            print(f"  ERROR loading: {e}")
            append_row(row, RESULTS_CSV)
            continue
        row["workflow_init_from_file_sec"] = round(time.time() - t0, 2)

        n_tasks    = len(workflow.tasks)
        n_machines = len(workflow.machines)
        n_paths    = count_paths_dp(workflow)
        row.update({
            "n_tasks": n_tasks,
            "n_machines": n_machines,
            "n_paths": n_paths,
            "n_vars": n_tasks * n_machines,
            "deadline": deadline,
        })
        print(f"  tasks={n_tasks}  machines={n_machines}  paths={n_paths}  deadline={deadline}")

        # 1. SPWD
        print(f"\n  [1/2] SPWD  (max_sub_fraction={MAX_SUB_FRACTION})")
        row.update(run_spwd(workflow, MAX_SUB_FRACTION, SPWD_SUB_TIME_LIMIT_S))
        print(
            f"        status={row.get('spwd_status')}  cost={row.get('spwd_cost')}"
            f"  n_subs={row.get('spwd_num_subworkflows')}"
        )
        print(
            f"        spization={row.get('spwd_spization_sec')}s"
            f"  problem_encoding={row.get('spwd_problem_encoding_qhyper_sec')}s"
            f"  model_build={row.get('spwd_gurobi_model_build_for_all_sum_sec')}s"
            f"  gurobi={row.get('spwd_gurobi_runtime_for_all_sum_sec')}s"
            f"  total={row.get('spwd_total_time_sec')}s"
        )

        # 2. Pure Gurobi
        print(f"\n  [2/2] Gurobi")
        row.update(run_gurobi(workflow, GUROBI_TIME_LIMIT_S))
        print(
            f"        status={row.get('gurobi_status')}  cost={row.get('gurobi_cost')}"
            f"  gap={row.get('gurobi_mip_gap_pct')}%"
        )
        print(
            f"        problem_encoding={row.get('gurobi_problem_encoding_qhyper_sec')}s"
            f"  model_build={row.get('gurobi_model_build_sec')}s"
            f"  gurobi={row.get('gurobi_runtime_sec')}s"
            f"  total_solve={row.get('gurobi_total_time_sec')}s"
        )

        # Comparison
        g_cost, s_cost = row.get("gurobi_cost"), row.get("spwd_cost")
        if g_cost and s_cost:
            row["cost_ratio"] = round(s_cost / g_cost, 4)

        gurobi_solved = (
            row.get("gurobi_status") in ("optimal", "time_limit")
            and row.get("gurobi_sol_count", 0) > 0
        )
        spwd_solved = row.get("spwd_status") == "solved"

        if not gurobi_solved and spwd_solved:
            row["advantage"] = "SPWD enables solution"
        elif gurobi_solved and spwd_solved:
            if row.get("gurobi_status") == "time_limit":
                row["advantage"] = f"SPWD vs suboptimal Gurobi (gap={row.get('gurobi_mip_gap_pct')}%)"
            else:
                row["advantage"] = "both optimal — cost ratio shows overhead"
        elif gurobi_solved and not spwd_solved:
            row["advantage"] = "Gurobi only"
        else:
            row["advantage"] = "neither solved"

        print(f"\n  → advantage={row.get('advantage')}  cost_ratio={row.get('cost_ratio')}")

        append_row(row, RESULTS_CSV)
        print(f"  Saved to {RESULTS_CSV}")

    print(f"\n{'='*72}\nDone.  Full results in {RESULTS_CSV}")


if __name__ == "__main__":
    main()

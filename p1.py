# First we import all required library

import streamlit as st
import random
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use("Agg")         
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


random.seed(42)


#  Here We build dependency-aware start times for one graph

def compute_start_times(G):
    """Return {node: earliest_start} respecting DAG precedence."""
    start = {}
    for node in nx.topological_sort(G):       # guaranteed valid order
        preds = list(G.predecessors(node))
        start[node] = max((start[p] + 1 for p in preds), default=0)
    return start


#STEP:1
#  POPULATION INITIALISATION

def initialize_population(graphs, M, pop_size=30):
    population = []
    for _ in range(pop_size):
        schedule = []
        for g_id, G in enumerate(graphs):
            start_times = compute_start_times(G)
            for node in nx.topological_sort(G):
                mechanic = random.randint(0, M - 1)
                schedule.append({
                    "task":     f"G{g_id}_T{node}",
                    "mechanic": mechanic,
                    "time":     start_times[node],
                    "graph":    g_id,
                    "node":     node,
                })
        population.append(schedule)
    return population

#STEP:2
#  FITNESS FUNCTION

def evaluate(schedule, M, k):
    mechanic_slots = {i: [] for i in range(M)}
    for entry in schedule:
        mechanic_slots[entry["mechanic"]].append(entry["time"])

    penalty  = 0
    makespan = 0

    for m_slots in mechanic_slots.values():
        if not m_slots:
            continue
        times = sorted(m_slots)
        makespan = max(makespan, times[-1] + 1)  

        # FIX 3: count consecutive tasks correctly
        consec = 1
        for i in range(1, len(times)):
            if times[i] == times[i - 1] + 1:
                consec += 1
                if consec > k:
                    penalty += 10              
            else:
                consec = 1                      
    return makespan + penalty


#STEP:3
#  SELECTION  

def selection(population, fitnesses):
    selected = []
    for _ in range(len(population)):
        i, j = random.sample(range(len(population)), 2)
        winner = population[i] if fitnesses[i] < fitnesses[j] else population[j]
        selected.append(winner)
    return selected

#STEP:4
#  CROSSOVER

def crossover(p1, p2):
    if len(p1) < 2:
        return list(p1)

    #We Group by graph id, crossover within each group, then merge
    graphs_p1 = {}
    graphs_p2 = {}
    for e in p1:
        graphs_p1.setdefault(e["graph"], []).append(e)
    for e in p2:
        graphs_p2.setdefault(e["graph"], []).append(e)

    child = []
    for gid in graphs_p1:
        g1 = graphs_p1[gid]
        g2 = graphs_p2.get(gid, g1)
        n  = len(g1)
        pt = random.randint(1, max(1, n - 1))
        child.extend(g1[:pt] + g2[pt:])
    return child


#STEP:5
#  MUTATION

def mutation(schedule, M, rate=0.1):
    new_schedule = []
    for entry in schedule:
        e = dict(entry)                          # shallow copy
        if random.random() < rate:
            e["mechanic"] = random.randint(0, M - 1)
        new_schedule.append(e)
    return new_schedule


#STEP:6
#  GENETIC ALGORITHM

def run_ga(graphs, M, k, generations=60, pop_size=30):
    population = initialize_population(graphs, M, pop_size)

    best_solution = None
    best_fitness  = float("inf")
    history       = []

    for gen in range(generations):
        fitnesses = [evaluate(ind, M, k) for ind in population]

        gen_best_idx = fitnesses.index(min(fitnesses))
        gen_best_fit = fitnesses[gen_best_idx]
        history.append(gen_best_fit)

        # FIX 8: update global best
        if gen_best_fit < best_fitness:
            best_fitness  = gen_best_fit
            best_solution = population[gen_best_idx]

        selected = selection(population, fitnesses)

        next_pop = [best_solution]             
        for i in range(0, len(selected) - 1, 2):
            c1 = mutation(crossover(selected[i],     selected[i + 1]), M)
            c2 = mutation(crossover(selected[i + 1], selected[i]),     M)
            next_pop.extend([c1, c2])

        population = next_pop[:pop_size]

    return best_solution, best_fitness, history



# Here We Implement STREAMLIT UI

st.set_page_config(page_title="Garage Scheduler", page_icon="🚗", layout="wide")
st.title("🚗 Garage Scheduling — Meta Heuristic:-Genetic Algorithm")
st.markdown("First We,Configure car DAGs, mechanics, and fatigue limit, then run the GA.")

# ── Sidebar controls 
with st.sidebar:
    st.header("⚙️ Settings")
    num_graphs  = st.number_input("Car types (graphs)", 1, 5, 2, step=1)
    M           = st.number_input("Number of mechanics", 1, 10, 2, step=1)
    k           = st.number_input("Fatigue limit k", 1, 10, 3, step=1)
    generations = st.number_input("GA generations", 10, 500, 60, step=10)
    pop_size    = st.number_input("Population size", 10, 200, 30, step=10)
    st.markdown("---")
    st.caption("k = max consecutive tasks before mandatory break")

# ── Graph builder
graphs = []
all_valid = True

for g in range(int(num_graphs)):
    with st.expander(f"🔧 Car / Graph {g + 1}", expanded=(g == 0)):
        col1, col2 = st.columns(2)
        with col1:
           
            n_nodes = st.number_input(f"Nodes", 1, 15, 3,
                                      key=f"nodes_{g}", step=1)
        with col2:
            n_nodes_int = int(n_nodes)

        st.markdown("**Edges** — one per line: `source destination probability`")
        st.caption("Example:  `0 1 0.8`  means node 0 → node 1 with spawn-prob 0.8")

        default_edges = "0 1 0.7\n1 2 0.5" if g == 0 else "0 1 0.6"
        edge_text = st.text_area(
            "Edges",
            value=default_edges,
            key=f"edges_{g}",
            height=120,
            label_visibility="collapsed",
        )

        G = nx.DiGraph()
        G.add_nodes_from(range(n_nodes_int))

        parse_ok = True
        for line_no, line in enumerate(edge_text.strip().splitlines(), 1):
            line = line.strip()
            if not line:
                continue                         
            parts = line.split()
         
            if len(parts) != 3:
                st.error(f"Graph {g+1}, line {line_no}: expected 'u v prob', got '{line}'")
                parse_ok = False
                all_valid = False
                continue
            try:
                u, v, prob = int(parts[0]), int(parts[1]), float(parts[2])
                if u >= n_nodes_int or v >= n_nodes_int:
                    st.error(f"Graph {g+1}, line {line_no}: node index out of range (max {n_nodes_int-1})")
                    parse_ok = False; all_valid = False; continue
                if not (0.0 <= prob <= 1.0):
                    st.warning(f"Graph {g+1}, line {line_no}: probability {prob} clipped to [0,1]")
                    prob = max(0.0, min(1.0, prob))
                G.add_edge(u, v, prob=prob)
            except ValueError:
                st.error(f"Graph {g+1}, line {line_no}: cannot parse '{line}'")
                parse_ok = False; all_valid = False

       #(topological_sort crashes on cyclic graphs)
        if parse_ok and not nx.is_directed_acyclic_graph(G):
            st.error(f"Graph {g+1}: edges form a cycle — DAG must be acyclic.")
            all_valid = False
            parse_ok = False

        if parse_ok:
            # WE Preview the graph
            fig_g, ax_g = plt.subplots(figsize=(3.5, 2.2))
            try:
                pos = nx.spring_layout(G, seed=0)
            except Exception:
                pos = {n: (n, 0) for n in G.nodes()}
            nx.draw(G, pos, ax=ax_g, with_labels=True,
                    node_color="#2E75B6", font_color="white",
                    node_size=500, font_size=10, arrows=True,
                    edge_color="#555", width=1.5)
            edge_labels = {(u, v): f"{d['prob']:.1f}"
                           for u, v, d in G.edges(data=True)}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                         font_size=8, ax=ax_g)
            ax_g.set_title(f"Graph {g+1}", fontsize=9)
            st.pyplot(fig_g, use_container_width=False)
            plt.close(fig_g)

        graphs.append(G)

# ── Run button 
st.markdown("---")
run_col, _ = st.columns([1, 3])
with run_col:
    run_clicked = st.button("▶ Run Genetic Algorithm", type="primary",
                            disabled=not all_valid)

if run_clicked and all_valid:
    with st.spinner("Running GA…"):
        best_sol, best_fit, history = run_ga(
            graphs, int(M), int(k),
            generations=int(generations),
            pop_size=int(pop_size),
        )

    st.success(f"✅ Best makespan (+ penalty): **{best_fit}**")

    # ── Schedule table ────────────────────────────────────────────
    st.subheader("📋 Final Schedule")
    df = pd.DataFrame([
        {"Task": e["task"], "Mechanic": f"M{e['mechanic']}", "Start": e["time"], "End": e["time"] + 1}
        for e in best_sol
    ]).sort_values(["Mechanic", "Start"]).reset_index(drop=True)
    st.dataframe(df, use_container_width=True)

    col_left, col_right = st.columns(2)

    # ── Fitness curve 
    with col_left:
        st.subheader("📈 Fitness over Generations")
        fig1, ax1 = plt.subplots(figsize=(5, 3))
        ax1.plot(history, color="#2E75B6", linewidth=2)
        ax1.fill_between(range(len(history)), history, alpha=0.15, color="#2E75B6")
        ax1.set_xlabel("Generation", fontsize=10)
        ax1.set_ylabel("Fitness (lower = better)", fontsize=10)
        ax1.set_title("GA Convergence", fontsize=11)
        ax1.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

    # ── Gantt chart 
    with col_right:
        st.subheader("📊 Gantt Chart")

        n_mechs  = int(M)
        colors   = plt.cm.get_cmap("tab10", len(graphs))
        fig2, ax2 = plt.subplots(figsize=(5, max(3, n_mechs * 0.8 + 1)))

        for entry in best_sol:
            g_id  = entry["graph"]
            mech  = entry["mechanic"]
            t     = entry["time"]
            task  = entry["task"]
            ax2.barh(f"M{mech}", 0.9, left=t, height=0.5,
                     color=colors(g_id), edgecolor="white", linewidth=0.5)
            ax2.text(t + 0.45, mech, task.split("_T")[1],
                     ha="center", va="center", fontsize=7, color="white")

        patches = [mpatches.Patch(color=colors(i), label=f"Graph {i+1}")
                   for i in range(len(graphs))]
        ax2.legend(handles=patches, fontsize=8, loc="upper right")
        ax2.set_xlabel("Time", fontsize=10)
        ax2.set_ylabel("Mechanic", fontsize=10)
        ax2.set_title("Task Gantt Chart", fontsize=11)
        ax2.set_yticks([f"M{m}" for m in range(n_mechs)])
        ax2.grid(True, axis="x", linestyle="--", alpha=0.4)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

     # Here We can See Per-mechanic summary 
    st.subheader("👷 Mechanic Workload Summary")
    summary = df.groupby("Mechanic").agg(
        Tasks=("Task", "count"),
        Earliest_Start=("Start", "min"),
        Latest_End=("End", "max"),
    ).reset_index()
    summary["Idle_Time"] = summary["Latest_End"] - summary["Tasks"]
 
    # We Styled HTML table 
    col_labels = {
        "Mechanic":       "🔧 Mechanic",
        "Tasks":          "📋 Tasks",
        "Earliest_Start": "⏱ Earliest Start",
        "Latest_End":     "🏁 Latest End",
        "Idle_Time":      "💤 Idle Time",
    }
    row_colors = ["#EBF4FA", "#FFFFFF"]
    header_bg  = "#1F4E79"
    header_fg  = "#FFFFFF"
    border_clr = "#B0C4D8"
    idle_neg_bg = "#FDECEA"
    idle_neg_fg = "#C0392B"
 
    header_cells = "".join(
        f'<th style="background:{header_bg};color:{header_fg};'
        f'font-weight:700;font-size:13px;padding:11px 18px;'
        f'border:1px solid {border_clr};text-align:center;white-space:nowrap;">'
        f'{col_labels.get(c, c)}</th>'
        for c in summary.columns
    )
 
    data_rows = ""
    for i, row in summary.iterrows():
        bg = row_colors[i % 2]
        cells = ""
        for col, val in row.items():
            if col == "Idle_Time" and int(val) < 0:
                extra = f"background:{idle_neg_bg};color:{idle_neg_fg};font-weight:600;"
            else:
                extra = f"background:{bg};color:#1A1A2E;"
            cells += (
                f'<td style="{extra}font-size:13px;padding:10px 18px;'
                f'border:1px solid {border_clr};text-align:center;">'
                f'{val}</td>'
            )
        data_rows += f"<tr>{cells}</tr>"
 
    html_table = f"""
    <style>
      .ws-table {{
        border-collapse: collapse; width: 100%;
        border-radius: 10px; overflow: hidden;
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
        font-family: sans-serif;
      }}
      .ws-table tbody tr:hover td {{
        filter: brightness(0.94);
        transition: filter 0.15s;
      }}
    </style>
    <table class="ws-table">
      <thead><tr>{header_cells}</tr></thead>
      <tbody>{data_rows}</tbody>
    </table>
    <br/>
    """
    st.markdown(html_table, unsafe_allow_html=True)
 
elif run_clicked and not all_valid:
    st.error("⚠️ Fix the graph errors above before running.")
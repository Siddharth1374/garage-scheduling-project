# 🚗 Garage Scheduling using Genetic Algorithm

# Overview
This project implements a **Genetic Algorithm (GA)** to solve a **garage task scheduling problem**.

- Multiple **car types** are represented as **Directed Acyclic Graphs (DAGs)**
- Each node represents a **task**
- Edges represent **dependencies between tasks**
- Tasks are assigned to **mechanics** while respecting:
  - Task dependencies
  - Fatigue constraints

The goal is to **minimize total completion time (makespan)**.

---

## 🧠 Problem Description

### 🔹 Input
- **N graphs** → each represents a car type
- Each graph contains:
  - Nodes → tasks
  - Edges → dependencies with probabilities
- **M mechanics**
- **Fatigue limit (k)**

### 🔹 Constraints
- Each task takes **1 time unit**
- After **k consecutive tasks**, a mechanic must rest
- Tasks must follow **dependency order (DAG)**

---

## ⚙️ Genetic Algorithm Approach

### 1. Initialization
Generate random schedules assigning tasks to mechanics.

### 2. Fitness Function
Minimize:
- Total completion time (makespan)
- Penalty for fatigue violation

### 3. Selection
Tournament selection to choose best schedules.

### 4. Crossover
Combine two schedules to create offspring.

### 5. Mutation
Randomly change mechanic assignments.

### 6. Termination
Run for fixed generations (e.g., 50).

---

## 📊 Features

- Handles multiple DAGs (car types)
-  Fatigue constraint handling
- Genetic Algorithm optimization
- Streamlit-based UI
- Visualization:
- Fitness vs Generations
- Gantt Chart (Task Timeline)

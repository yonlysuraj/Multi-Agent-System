# Multi-Agent System 🤖

An advanced, production-grade multi-agent AI system powered by Groq (`llama-3.3-70b-versatile`).
This repository implements two complex enterprise capabilities utilizing specialized, cooperating AI agents.

## 🎯 Assessments

### 1. War Room (`war_room/`) — Product Launch Decision
A high-stakes product launch simulation taking place 2 hours before a major release.
- **Goal:** Decide whether to launch or delay based on conflicting inputs.
- **Agents:** Data Analyst, PM, Marketing, Risk, Finance, Growth.
- **Focus:** Consensus-building, financial risk analysis, and structured debate.

### 2. Bug Triage (`bug_triage/`) — Automated Reproduction
An automated pipeline to detect, analyze, and reproduce P0 software bugs.
- **Goal:** Automatically pinpoint the root cause of a crash and generate a working reproduction script.
- **Agents:** Triage, LogAnalyst, Reproduction, FixPlanner, Critic.
- **Features:** 
  - Actually executes the code locally to verify reproduction.
  - Subprocess file writing and execution via strict timeouts.
  - Stateful orchestrated execution filtering log noise.

## ⚙️ Shared Infrastructure (`shared/`, `tools/`)
- Tooling for statistical analysis (z-scores, metrics), sentiment analysis (NLP clustering).
- Custom Regex log parsing and execution Sandboxing.
- Resilient API handlers (`groq_client.py`) with automatic backoff.
- Tracing logger for granular agent execution timing.

## 🚀 Usage

Execute assessments via the CLI entrypoint:
```bash
# Run Bug Triage
python main.py --task a2

# Run War Room
python main.py --task a1
```

# 🧠 Multi-Agent Assessment System

An advanced, production-grade multi-agent AI system powered by **Groq** (`llama-3.3-70b-versatile`). 
This repository implements two complex enterprise capabilities utilizing specialized, cooperating AI agents. Each agent acts on isolated data domains and passes structured JSON to a state-machine orchestrator.

---

## 🗺️ High-Level Architecture

The system embraces a **shared-tool, specialized-agent** architecture. The heavy lifting (statistical analysis, regex parsing, file operations) is done purely in python to keep token counts low and latency blazing fast, while the LLM acts as the orchestrating reasoning engine.

```text
┌─────────────────────────────────────────────────────────┐
│                     ENTRY POINT                         │
│                     main.py / CLI                       │
└────────────────────────┬────────────────────────────────┘
                         │
             ┌───────────▼───────────┐
             │     ORCHESTRATOR      │  ← State machine controller
             │  orchestrator.py      │  ← Drives agent pipeline
             └───┬───┬───┬───┬───┬──┘
                 │   │   │   │   │
         ┌───────┘   │   │   │   └────────┐
         ▼           ▼   ▼   ▼            ▼
      Agent 1    Agent 2  ...          Agent N
     (LLM call) (LLM call)           (LLM call)
         │           │                    │
         └──────┬────┴────────────────────┘
                │
         ┌──────▼──────┐
         │    TOOLS    │  ← Pure Python functions (no LLM)
         │  tools/     │  ← Called BY agents programmatically
         └─────────────┘
```

---

## 🎯 Task 1: The "War Room" (Product Launch Decision)

A high-stakes product launch simulation taking place post-launch where user sentiment is clashing with error tracking. 
The Multi-Agent system acts as a virtual boardroom to decide if the launch should **Proceed**, **Pause**, or **Roll Back**.

### Agents Involved:
1. 📊 **Data Analyst:** Analyzes 14-day time-series metrics & triggers Z-score anomaly detection.
2. 🗣️ **Marketing:** Performs sentiment analysis on user feedback, extracts themes without ML models via TF-IDF, and drafts comms.
3. 💼 **Product Manager:** Weighs the analytical and marketing outputs against predefined SLAs, producing user impact summaries.
4. 💰 **Finance (Bonus):** Projects daily revenue at risk based on checkout dropoff and payment gateway failure metrics.
5. 📈 **Growth (Bonus):** Segregates funnel/retention metrics from pure error metrics to prevent over-reacting to transactional bugs.
6. ⚠️ **Risk Critic:** Adversarially challenges assumptions from the PM & Analyst, formulating a Risk Register.

**Orchestrator Output:** Aggregates a tallied vote, computes a weighted confidence score, and structures an Action Plan into `outputs/a1_decision.json`.

---

## 🐛 Task 2: The Bug Triage Bot

An automated pipeline aimed at solving a P0 software bug (checkout crashing for orders >$500). Instead of just analyzing logs, this team of agents actually **writes code to reproduce the bug**, runs it dynamically, and evaluates the stack trace.

### Agents Involved:
1. 🩺 **Triage Agent:** Parses the messy markdown bug report, pulling out typed symptoms, and asserting initial hypotheses.
2. 🕵️ **Log Analyst:** Greps raw `app_logs.txt`, strips noise, and matches stack traces to the Triage Agent's hypotheses.
3. ⚙️ **Reproduction Agent:** Writes a minimal reproducible Python test script (`outputs/a2_repro_test.py`), executes it in a subprocess, and reports if the exit code correlates to the bug.
4. 🔧 **Fix Planner:** Maps the successfully reproduced trace to a root cause and drafts a specific patch methodology.
5. 🛡️ **Critic Agent:** Reviews the patch plan specifically to surface edge cases or unsafe system assumptions.

**Orchestrator Output:** Assembles a fully structured diagnosis complete with root cause confidence, impact scope, and code references into `outputs/a2_diagnosis.json`.

---

## ⚙️ Environment & Setup

### Prerequisites
- Python 3.11+
- A [Groq API Key](https://console.groq.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yonlysuraj/Multi-Agent-System.git
cd Multi-Agent-System

# 2. Create and activate a Virtual Environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup Environment Variables
cp .env.example .env
# Edit .env and insert your GROQ_API_KEY
```

---

## 🚀 Execution

Both assessments are executed via the `main.py` entrypoint. The terminal outputs rich formatting, progress spinners, and summarized vote tallies.

```bash
# Run Task 1 (War Room)
python main.py --task a1

# Run Task 2 (Bug Triage)
python main.py --task a2

# (Optional) Run both sequentially
python main.py --task both
```

> **Note:** To avoid rate-limits on Groq's free tier, it is recommended to run the assessments individually with a slight delay between them, rather than chained together.

---

## 📁 Traceability & Output Logs

Multi-step AI pipelines can feel like black boxes. To counter this, every single agent turn, LLM latency, token count, and pure-python tool execution is recorded.

All outputs are structured and saved in the `outputs/` directory:
- `a1_decision.json`: The War Room consensus, action plan, and vote tally.
- `a2_diagnosis.json`: The bug execution, root cause, and patch plan.
- `a2_repro_test.py`: Generated by the AI dynamically during Bug Triage to ensure the bug is real.
- `trace.log`: A comprehensive, millisecond-accurate event journal detailing everything the multi-agent system does under the hood.

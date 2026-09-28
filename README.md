# 🧠 PipelineSage

**AI DevOps Pipeline Agent with persistent memory**

PipelineSage helps DevOps engineers diagnose CI/CD failures by remembering previous deployment incidents, successful fixes, and confirmed outcomes.

Instead of treating every pipeline failure as a new problem, PipelineSage retrieves relevant historical incidents from Hindsight and uses that experience to ground its diagnosis and recommendation.

## The problem

CI/CD failures often repeat.

A deployment may fail because of a database migration timeout, dependency conflict, configuration issue, or infrastructure change that has already caused problems before. The useful knowledge about how the issue was resolved is often buried in previous incidents.

PipelineSage gives an AI agent persistent memory of those incidents.

## How it works

```text
CI/CD Failure
      ↓
PipelineSage Agent
      ↓
Hindsight RECALL
      ↓
Relevant Historical Incidents
      ↓
Groq LLM Diagnosis
      ↓
Recommended Fix
      ↓
Human Confirmation
      ↓
Hindsight RETAIN
      ↓
Future Failures Learn From the Outcome
```

## Example

Deployment **#1057** of `payment-service` fails:

```text
Database migration timed out after 30 seconds
while updating historical transaction rows.
```

PipelineSage recalls a previous successful deployment:

```text
Deployment #1017

Database migration timeout

Resolution:
Split the migration into batches of 500 records.

Outcome:
Deployment succeeded.
```

The agent uses that historical experience when diagnosing #1057 and recommends processing the historical transaction rows in **500-record batches**.

After a human confirms the recommended resolution, PipelineSage retains the outcome in Hindsight so the experience can be recalled during future diagnoses.

## Hindsight memory

Hindsight is the central memory layer of PipelineSage.

The application uses:

* **RETAIN** — stores deployment incidents and confirmed outcomes.
* **RECALL** — retrieves relevant historical incidents for a new failure.
* **Persistent memory** — allows previous deployment experiences to influence future diagnoses.

Hindsight documentation: https://hindsight.vectorize.io/

Hindsight GitHub: https://github.com/vectorize-io/hindsight/

## Architecture

```text
                    ┌─────────────────────┐
                    │   Streamlit UI      │
                    │  Pipeline Dashboard │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  PipelineSage Agent │
                    └───────┬─────┬───────┘
                            │     │
                 RECALL ◄──┘     └──► Groq LLM
                    │                  │
                    ▼                  ▼
             ┌─────────────┐   ┌─────────────┐
             │  Hindsight   │   │  Diagnosis  │
             │    Memory    │   │  + Fix      │
             └──────┬──────┘   └──────┬──────┘
                    │                  │
                    └────── RETAIN ◄───┘
```

## Project structure

```text
PipelineSage/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── architecture.md
│
├── agent/
│   ├── __init__.py
│   └── pipeline_agent.py
│
├── memory/
│   ├── __init__.py
│   └── hindsight_memory.py
│
├── services/
│   ├── __init__.py
│   └── pipeline_service.py
│
└── data/
    └── pipeline_history.json
```

## Technology stack

* Python
* Streamlit
* Hindsight Cloud
* Groq
* `openai/gpt-oss-120b`
* Synthetic CI/CD incident data

## Running locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd pipelinesage
```

### 2. Create a virtual environment

Windows:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```cmd
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=pipelinesage-clean
```

Never commit `.env` to GitHub.

### 5. Run PipelineSage

```cmd
streamlit run app.py
```

## Demo workflow

1. Select a failed deployment.
2. Click **Analyze with PipelineSage**.
3. PipelineSage recalls similar incidents from Hindsight.
4. Review the historical evidence.
5. Review the diagnosis and recommended fix.
6. Confirm whether the recommended fix succeeded.
7. PipelineSage retains the outcome in Hindsight.
8. Run another diagnosis and observe the learned experience being recalled.

## Current demo scenario

The included demo data contains seven realistic deployment incidents covering:

* Database migration timeouts
* Dependency conflicts
* Container memory issues
* Missing production configuration
* Successful and failed deployment outcomes

The main memory demonstration uses:

```text
#1017
Successful database migration resolution
500-record batching
        ↓
Hindsight
        ↓
#1057
Similar migration timeout
        ↓
Recall historical experience
        ↓
Recommend 500-record batching
        ↓
Human confirmation
        ↓
Retain outcome
```

## Safety and responsibility

PipelineSage is a decision-support prototype.

It recommends troubleshooting actions based on current deployment information and historical memory. Production changes remain under human control.

## License

This project is provided for demonstration and development purposes.

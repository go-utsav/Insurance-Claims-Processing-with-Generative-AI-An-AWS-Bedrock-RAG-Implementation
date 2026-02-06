# Insurance Claims Processing with AWS Gen AI

**AWS Gen AI Developer Certification — Task 1.1: Analyze requirements and design Gen AI solutions**

This guide is for **beginners and non-technical readers**. No prior AWS experience needed. We focus on one case study: **Auto Insurance — First Notice of Loss (FNOL)**.

---

## Project layout (code organization)

The claim-processing code is split into a small package so it’s easy to follow:

| Folder / file | Purpose |
|---------------|---------|
| **claim_processor/** | Main package: prompts, S3 document read, Bedrock calls, process + compare logic. |
| **claim_processor/prompts.py** | Prompt templates (extract info, generate summary). |
| **claim_processor/document.py** | Read claim document from S3 (PDF or text). |
| **claim_processor/bedrock.py** | Call Claude 3 on Bedrock (Messages API). |
| **claim_processor/processor.py** | `process_document` (extract + summary) and `compare_models` (run same prompt on multiple models). |
| **claim-process.py** or **run_claim_process.py** | Entry scripts: run process and/or model comparison from the command line. |

**Run from command line:**

- Process one claim (extract + summary):  
  `python claim-process.py` or `python claim-process.py --process`
- Compare Claude 3 models on the same document:  
  `python claim-process.py --compare`
- Run both:  
  `python claim-process.py --process --compare`
- Use a different S3 key:  
  `python claim-process.py --key "claim-documents/2026-02-06/Claim - CL-2024-002.pdf"`

---

## Local PoC: Frontend + Backend (no serverless)

You can run the full flow **locally**: React frontend + Python backend + policy/claim data files. Bedrock is still called from the backend (AWS API).

| Folder / file | Purpose |
|---------------|---------|
| **frontend/** | React app: paste or load claim text, submit, display result (status, reasoning, extracted_data). |
| **backend/** | Flask API: reads policy + claim, calls Bedrock with system prompt, returns JSON. |
| **data/policy_document.txt** | Policy rules (SwiftCover Auto, coverage, 14-day filing, commercial exclusion). |
| **data/claim_valid.txt** | Happy path sample (CL-2024-001, Sarah Jenkins — should be APPROVED). |
| **data/claim_invalid.txt** | Rejection sample (CL-2024-002, Mike Ross — late filing + commercial use). |

**Run locally:**

1. **Backend** (from project root):  
   `python -m backend.app`  
   API runs at **http://localhost:5001** (GET /api/health, GET /api/samples/claim_valid|claim_invalid, POST /api/process-claim).  
   Note: Port 5000 is often used by macOS AirPlay Receiver, so we use 5001 by default. Set `FLASK_PORT=5000` in `.env` if you want 5000.

2. **Frontend:**  
   `cd frontend && npm install && npm start`  
   App runs at **http://localhost:3000**. Use “Load Happy Path” or “Load Rejection”, then “Submit” to see status, reasoning, and extracted data.

3. **Environment:**  
   Backend uses `.env` (BUCKET_NAME not required for PoC; AWS credentials for Bedrock). Optional: `BEDROCK_MODEL_ID` (default Claude 3 Sonnet).

---

## Case Study: Auto Insurance (First Notice of Loss — FNOL)

### The Pain Point

You get into a car accident. You’re stressed. You take photos and fill out a form. Usually, you have to wait for an **adjuster** to call you back — often **24–48 hours** — just to know if you’re covered for a rental car.

**Result:** The driver is left wondering what to do, sometimes stranded, with no immediate answer.

---

### How Your Solution Fixes It

| Step | What happens |
|------|----------------|
| **Input** | The user uploads a **photo of the crash** and the **police report**. |
| **AI action** | **Amazon Bedrock** analyzes the police report (e.g. who was at fault) and reads the **policy** to see if “Rental Reimbursement” is included. |
| **Outcome** | The app **instantly** tells the driver: *“We have received your claim. You are approved for a rental car. Here is a voucher.”* |

**Impact:** The driver gets an immediate answer instead of waiting 24–48 hours. They’re not left stranded wondering what to do.

---

## Key AWS Services (Simple Definitions)

| Term | What it means |
|------|----------------|
| **Amazon S3** | Secure “storage in the cloud.” You upload files (e.g. crash photo, police report, policy) into a **bucket** (like a folder). |
| **Amazon Bedrock** | AWS service that lets you use **foundation models** (AI that reads documents and generates text) without managing servers. |
| **Foundation model** | A pre-trained AI model (e.g. Claude) that can read reports, understand policy terms, and generate responses. |
| **RAG** | “Retrieval-Augmented Generation” — giving the AI extra context (e.g. policy document) so it can answer “Is rental covered?” accurately. |

You don’t need to remember every detail. Just keep in mind: **S3 = storage**, **Bedrock = AI**.

---

## Your Learning Path (4 Steps)

Follow these in order. Each step builds on the previous one — all focused on the **FNOL** case (photo + police report → fault + policy check → instant rental approval/voucher).

### Step 1 — Design the architecture

- Draw a **simple diagram** with:
  - **Input** → User uploads crash photo + police report (e.g. into **Amazon S3**).
  - **Processing** → How does the document move to the AI? Where does the policy (for RAG) live?
  - **AI** → Where does **Bedrock** sit? (Analyze report for fault; check policy for rental coverage.)
  - **Output** → Where does the response go? (e.g. “Approved for rental — here’s your voucher.”)
- Choose **Bedrock models** for:
  - Understanding the police report and extracting fault/incident details  
  - Reading policy and answering “Is rental reimbursement included?”  
  - Generating the instant message/voucher text  

*Goal: You understand the big picture for FNOL before coding.*

### Step 2 — Implement a proof-of-concept

- **Set up AWS:** Create an S3 bucket (e.g. `claim-documents-poc-<your-initials>`).
- **Build a small Python app** that can:
  - Accept uploads (crash photo + police report)  
  - Call **Amazon Bedrock** to analyze the report and check policy (simple RAG with policy info)  
  - Return an instant outcome (e.g. “Claim received. You are approved for a rental car. Here is a voucher.”)  

*Goal: You see a real flow from upload → AI (fault + policy) → instant outcome.*

### Step 3 — Create reusable components

- **Standardize** these parts so they’re easy to reuse:
  - **Prompt template manager** — e.g. “extract fault from police report”, “check if rental is covered”, “generate voucher message”.
  - **Model invoker** — one place that calls Bedrock.
  - **Content validator** — basic checks on AI output (e.g. length, format, safe wording).

*Goal: Your FNOL solution is easier to maintain and extend.*

### Step 4 — Test and evaluate

- Use **2–3 sample scenarios**: e.g. different police reports and policy snippets (with and without rental coverage).
- Upload crash photo + report to your S3 bucket and run your processor.
- Try **different Bedrock models** and compare:
  - Speed (time to “instant” response)  
  - Quality (correct fault summary, correct rental yes/no, clear voucher message)  
- **Document** what works best and what you’d improve.

*Goal: You can explain your choices and suggest next steps for FNOL.*

---

## Quick Reference

- **Official blog (automated insurance claims with Bedrock):**  
  [Automated insurance claims processing using Amazon Bedrock](https://aws.amazon.com/blogs/industries/automated-insurance-claims-processing-using-amazon-bedrock-knowledge-base-and-agents/)

- **Certification context:** AWS Gen AI Developer — Module 1, Task 1.1.

---

## After You Finish

- Share your work (e.g. LinkedIn, blog, GitHub) and tag **#awsexamprep** so the AWS Exam Prep team can see it.
- **Costs:** This uses real AWS services. Set billing alerts and clean up resources when you’re done.

Once you complete these four steps, you’ll have a clear picture of how **S3 + Bedrock** can support an **Auto Insurance FNOL** workflow: from photo + police report to an instant answer on rental coverage and a voucher, so the driver isn’t left stranded.

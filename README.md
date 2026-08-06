# CVRanking

<p align="center">
  <img src="https://img.shields.io/badge/Python_3.10-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/Docling-000000?style=for-the-badge&logo=python&logoColor=white" alt="Docling" />
  <img src="https://img.shields.io/badge/Groq_LLaMA_3.3-000000?style=for-the-badge&logo=meta&logoColor=white" alt="LLaMA 3.3" />
  <img src="https://img.shields.io/badge/Sentence_Transformers-FFB84D?style=for-the-badge&logo=huggingface&logoColor=black" alt="Sentence Transformers" />
  <img src="https://img.shields.io/badge/FAISS-0467DF?style=for-the-badge&logo=meta&logoColor=white" alt="FAISS" />
  <img src="https://img.shields.io/badge/Amazon_S3-FF9900?style=for-the-badge&logo=amazons3&logoColor=white" alt="Amazon S3" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>


### Demo -> https://mrsaurabhtanwar.github.io/CVRanking/

CVRanking is an internship portfolio project for comparing individual PDF resumes with saved job descriptions. It extracts structured candidate information, stores the parsed profile, builds a semantic-search vector, and returns a ranked shortlist with score breakdowns and missing required skills.

It is a decision-support prototype, not an automated hiring decision system. Recruiters or reviewers should validate the source resume and use independent judgment before making employment decisions.

## What it does

- Uploads one PDF resume at a time (up to 10 MiB), stores the original in Amazon S3, and schedules background processing.
- Converts the PDF to Markdown with Docling, then uses Groq's `llama-3.3-70b-versatile` model to map the content to a structured candidate profile.
- Persists a candidate record in PostgreSQL, a parsed JSON document in S3, and a normalized FAISS vector backed up to S3.
- Provides CRUD endpoints for job descriptions and filtering endpoints for candidate records.
- Ranks the nearest FAISS matches for a selected job description and reports a composite score, component scores, and missing required skills.
- Serves the included HTML, CSS, and JavaScript dashboard from the FastAPI application when the `frontend/` directory is present.

### Current scope

- The ZIP endpoint accepts a valid ZIP archive up to 50 MiB and stores it in S3. It does **not** extract the archive or process the resumes inside it.
- Upload processing uses FastAPI background tasks. The upload response confirms that processing was scheduled; it is not a completion status.
- Ranking evaluates each retrieved candidate with an LLM. Results depend on parsed resume data and model output and should be treated as assistance, not fact.

## Architecture

```mermaid
flowchart TD
    subgraph Client["Client Interface"]
        UI["Web Dashboard / REST Client"]
    end

    subgraph API["FastAPI Application Server"]
        Endpoints["REST API Endpoints (/upload, /rank, /candidates, /jobs)"]
    end

    subgraph Ingestion["PDF Ingestion & Parsing"]
        S3_PDF[(Amazon S3 Source PDF)]
        Docling["Docling PDF Converter"]
        Parser["Groq LLM Resume Parser"]

        S3_PDF --> Docling --> Parser
    end

    subgraph Storage["Persistence & Indexing Layer"]
        Postgres[(PostgreSQL Metadata)]
        S3_JSON[(Amazon S3 Parsed JSON)]
        FAISS[(FAISS Vector Index)]

        Embedder["SentenceTransformers Embedder"]
    end

    subgraph Evaluation["Composite Ranking Engine"]
        Search["FAISS Top-K Search"]
        Scorer["Multi-Signal Scoring Service"]
        GroqEval["Groq LLM Evaluator"]

        Search --> Scorer --> GroqEval
    end

    %% Linear Stage Connections
    UI -->|1. Upload PDF| Endpoints
    Endpoints -->|2. Save PDF| S3_PDF
    
    Parser -->|3. Structured Profile| Postgres
    Parser -->|4. Profile JSON| S3_JSON
    Parser -->|5. Text Embeddings| Embedder --> FAISS

    UI -->|6. Rank Job Description| Endpoints
    Endpoints -->|7. Query Vector Match| Search
    Postgres & S3_JSON & FAISS -->|8. Candidate Data| Scorer
    GroqEval -->|9. Ranked Shortlist| Endpoints
    Endpoints -->|10. Render Results| UI
```

## How ranking works

1. A job description is converted into text and embedded with `sentence-transformers/all-MiniLM-L6-v2`.
2. FAISS returns the closest candidate vectors (`top_k`, from 1 to 50).
3. For each retrieved candidate, the application loads the parsed profile from memory, S3, or the PostgreSQL record and asks the Groq model for rubric-style scores.
4. The ranking service combines the returned scores with direct required-skill coverage, vector similarity, and an experience function.

The implemented composite score uses these weights:

| Component | Weight | Calculation |
| --- | ---: | --- |
| Domain and work relevance | 30% | 60% LLM domain-relevance score + 40% LLM work-experience relevance score |
| Project quality | 25% | LLM project-quality score |
| Skills | 20% | 40% vector similarity + 30% exact required-skill coverage + 30% LLM skills-match score |
| Experience | 15% | Elastic score based on candidate and job-description experience years |
| Education and achievements | 10% | 60% LLM education score + 40% LLM certifications/achievements score |

The API clamps model-provided numeric scores to the 0–100 range. LLM defaults still exist when expected fields are missing, so the score is not a calibrated or validated measure of candidate quality.

## Tech stack

| Area | Implementation |
| --- | --- |
| API | Python, FastAPI, Uvicorn |
| Persistence | PostgreSQL through SQLAlchemy; JSON fields for parsed profile sections |
| Document extraction | Docling |
| LLM parsing and evaluation | Groq API with `llama-3.3-70b-versatile` |
| Embeddings and retrieval | Sentence Transformers `all-MiniLM-L6-v2`, FAISS (`faiss-cpu`) |
| Object storage | Amazon S3 through Boto3 |
| Dashboard | Static HTML, CSS, and vanilla JavaScript |
| Containerization | Docker and Docker Compose |

## Repository layout

```text
.
├── backend/
│   ├── main.py                 # FastAPI application, CORS, and dashboard mounting
│   ├── database.py             # SQLAlchemy engine and session dependency
│   ├── routers/                # Upload, candidate, job-description, and ranking endpoints
│   ├── schema/                 # Pydantic request and parsed-resume models
│   └── services/               # PDF extraction, LLM parsing, embedding, and scoring logic
├── frontend/
│   ├── index.html              # Dashboard markup
│   ├── script.js               # API client and dashboard interactions
│   └── style.css               # Dashboard styling
├── .github/workflows/deploy.yml # Docker Hub build and EC2 deployment workflow
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

`resumes_pdf.dvc` and `resumespdf.zip.dvc` are DVC pointer files. The associated local resume files and generated storage data are ignored by Git.

## Prerequisites

- Python 3.10 or later
- A reachable PostgreSQL database
- An S3 bucket and AWS credentials that can read and write the configured bucket
- A Groq API key
- Docker and Docker Compose (optional, for containerized execution)

The embedding model is downloaded on the first local startup unless it is already cached. The Docker image pre-downloads that model during the build.

## Configuration

Copy the example file and replace the placeholders:

```bash
copy .env.example .env
```

On macOS or Linux, use `cp .env.example .env` instead.

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_s3_bucket
GROQ_API_KEY=gsk_your_groq_api_key
CORS_ALLOW_ORIGINS=http://127.0.0.1:8080,http://localhost:8080
```

`DATABASE_URL` is required at application startup. Add database-specific SSL options to that URL when your PostgreSQL provider requires them. `CORS_ALLOW_ORIGINS` is a comma-separated list of browser origins; its defaults cover the local dashboard URLs. The embedding service also reads an optional `HF_TOKEN` environment variable for Hugging Face model access.

Keep `.env` out of source control. It is already ignored by this repository.

## Run locally

Clone the repository, create a virtual environment, and install the dependencies:

```bash
git clone <repository-url>
cd cvranking
python -m venv venv
```

Activate the environment:

```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source venv/bin/activate
```

Install and start the application from the repository root:

```bash
pip install -r requirements.txt
uvicorn main:app --app-dir backend --reload --host 127.0.0.1 --port 8080
```

Open the dashboard at [http://127.0.0.1:8080/](http://127.0.0.1:8080/) and the OpenAPI documentation at [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs).

## Run with Docker

With a populated `.env` file in the repository root:

```bash
docker compose up --build
```

The dashboard and API are available at [http://localhost:8080/](http://localhost:8080/). The Compose file persists the FAISS cache in the `faiss_storage` Docker volume. PostgreSQL and S3 remain external services configured through `.env`.

## Typical workflow

1. Create a job description through the dashboard or `POST /api/jobd/job-descriptions`.
2. Upload an individual PDF through the dashboard or `POST /api/upload/upload-file/`.
3. Allow the background task to finish parsing, storing, and indexing the resume. There is currently no job-status endpoint, so refresh the candidate list to check whether the record appears.
4. Choose the job description and run the ranking, or call `POST /api/ranking/rank?jd_id=<id>&top_k=10`.
5. Review the score components, missing required skills, and the original resume before drawing conclusions.

## API summary

FastAPI exposes interactive request schemas and response examples at `/docs`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/upload/upload-file/` | Upload one PDF as multipart field `file`; schedules parsing and indexing. |
| `POST` | `/api/upload/upload-zip-file/` | Store one ZIP archive as multipart field `file`; no extraction or ranking occurs. |
| `GET` | `/api/candidate/candidates` | List candidates; supports `min_exp`, `max_exp`, `skill`, `role`, `search`, `limit`, and `offset`. |
| `GET` | `/api/candidate/candidates/{candidate_id}` | Get one candidate record. |
| `DELETE` | `/api/candidate/candidates/{candidate_id}` | Delete the candidate record, its S3 objects, and its FAISS vector. |
| `POST` | `/api/jobd/job-descriptions` | Create a job description. |
| `GET` | `/api/jobd/job-descriptions` | List job descriptions. |
| `GET` | `/api/jobd/job-descriptions/{jd_id}` | Get one job description. |
| `PUT` | `/api/jobd/job-descriptions/{jd_id}` | Replace a job description's fields. |
| `DELETE` | `/api/jobd/job-descriptions/{jd_id}` | Delete a job description. |
| `POST` | `/api/ranking/rank` | Rank FAISS matches for `jd_id`; `top_k` defaults to 10 and accepts 1–50. |

Example job-description request:

```json
{
  "jd_id": "backend-engineer-1",
  "role": "Backend Engineer",
  "seniority": "Mid",
  "company_overview": "Product team building web services.",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "preferred_skills": ["Docker"],
  "responsibilities": ["Build and maintain APIs"],
  "minimum_years_experience": 2
}
```

## Data handling and security notes

Resume records contain personal information. Configure S3 bucket access, database access, and CORS according to the environment where the application runs. The API has no authentication or authorization layer, and candidate endpoints return personal data; do not expose it publicly without adding access controls.

The application constructs an S3 URL for an uploaded resume. Whether that URL can be opened depends on the bucket policy; private buckets require an additional signed-URL approach that this codebase does not implement.

## Known limitations

- The candidate parser and several ranking components depend on an external LLM. Parsing quality, scoring consistency, latency, and API cost can vary.
- There is no authentication, authorization, audit trail, rate limiting, or retention policy.
- FastAPI background tasks provide no durable queue, retries, processing status, or failure notification. Processing errors are logged to the server console.
- The FAISS index is held in process memory and copied to S3. Concurrent application instances or concurrent writes can overwrite index updates because there is no distributed locking or transaction protocol.
- Candidate deletion lists only the first page of matching S3 resume objects; records with more than 1,000 objects under the same prefix would not be fully removed.
- ZIP archives are stored only; bulk extraction and resume ingestion are not implemented.
- Database tables are created directly through SQLAlchemy metadata. The repository does not include schema migrations.
- The repository does not include an automated test suite.
- The ranking rubric includes LLM-generated education-related scoring. It has not been calibrated for fairness or validated for hiring decisions.

## Potential improvements

- Add a durable worker queue, task status endpoint, retries, and observable error reporting for resume processing.
- Implement safe bulk archive processing with archive-size, file-count, and path validation.
- Add authentication, role-based authorization, audit logging, signed S3 download URLs, and a documented data-retention policy.
- Introduce database migrations, unit/integration tests, and CI checks for the API and dashboard.
- Replace or supplement LLM rubric scores with evaluated, explainable criteria and human-review controls.
- Make FAISS index updates safe across multiple processes or move vector persistence to a service designed for concurrent writes.

## Disclosures & Project Scope

- **Backend Architecture & AI Pipeline**: Developed using Python 3.10, FastAPI, Docling OCR, Groq LLaMA 3.3, SentenceTransformers (`all-MiniLM-L6-v2`), FAISS, SQLAlchemy, and AWS S3 as the primary portfolio project.
- **Frontend Dashboard**: Created with AI assistance (vanilla HTML, CSS, and JavaScript) to provide an interactive visual demonstration interface for testing and presenting the REST API endpoints.

## License

This project is open-source software licensed under the [MIT License](LICENSE).

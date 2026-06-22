# Drive Intelligence Platform

Drive Intelligence Platform is a safe AI-assisted digital archivist for large file collections. It analyzes drives in read-only mode by default, stores a complete audit trail, and only executes file operations after explicit approval.

## Core Principles

- Never delete, rename, move, or create folders automatically.
- Prefer recommendations over assumptions when confidence is low.
- Keep a full rollback manifest for every approved operation.
- Support multi-terabyte, mixed-media archives.

## Included Modules

- Drive scanning and metadata cataloging
- Content, photo, and video analysis
- Duplicate and near-duplicate detection
- Learning engine for folder pattern discovery
- Rule engine for user-defined organization rules
- Audit logging and rollback manifests
- Streamlit dashboard and management views

## Development

Install dependencies in a Python 3.13 environment, then run:

```bash
dip init-db
dip scan /path/to/archive
dip ui
```

## Safety Model

The platform supports three modes:

1. Read Only Mode
2. Recommendation Mode
3. Approved Execution Mode

Execution mode requires explicit user approval before any file operation is performed.

## AI Provider Configuration

The planner supports multiple AI providers selected with environment variables.

### 1) Use Ollama (local, no API billing)

```bash
export DIP_AI_PROVIDER=ollama
export DIP_OLLAMA_BASE_URL=http://localhost:11434
export DIP_OLLAMA_MODEL=qwen2.5:14b-instruct
```

Install/run Ollama model:

```bash
ollama pull qwen2.5:14b-instruct
ollama serve
```

### 2) Use OpenAI

```bash
export DIP_AI_PROVIDER=openai
export DIP_OPENAI_API_KEY=your_key_here
export DIP_OPENAI_MODEL=gpt-4.1-mini
```

### 3) Disable AI

```bash
export DIP_AI_PROVIDER=disabled
```

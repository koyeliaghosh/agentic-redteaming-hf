# Agentic AI Red-Teaming Assistant

A minimal-cost MVP multi-agent system for automated security testing of AI systems using free Hugging Face models.

## Overview

This system orchestrates multiple specialized agents to plan, execute, and evaluate adversarial attacks against target AI models. Built for hackathons and proof-of-concept demonstrations with minimal infrastructure costs.

## Cost Breakdown

**Total Cost: ~$30/month**
- Hugging Face Free Tier: $0 (rate-limited but functional)
- AWS EC2 t3.medium: ~$30/month
- Local Storage: $0 (included in EBS volume)
- No S3 costs

## Features

- **Multi-Agent Architecture**: Specialized agents for planning, execution, and evaluation
- **Free AI Models**: Uses Hugging Face free tier (no API costs)
- **Local Storage**: All data stored on EC2 (no S3 required)
- **Safety Controls**: Emergency stop mechanism and rate limiting
- **REST API**: FastAPI-based interface for mission management

## Quick Start

### Prerequisites

- Python 3.10+
- Hugging Face account (free)
- AWS EC2 instance (optional, for deployment)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-redteaming-hf
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your Hugging Face API key
```

5. Create data directories:
```bash
mkdir -p data/reports data/logs data/faiss_index
```

### Running Locally

```bash
python app.py
```

The API will be available at `http://localhost:8080`

### Running with Docker

```bash
docker build -t redteaming-assistant .
docker run -p 8080:8080 --env-file .env -v $(pwd)/data:/app/data redteaming-assistant
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

### Key Configuration Options

- `HUGGINGFACE_API_KEY`: Your HF API key (required)
- `HF_LLM_MODEL`: LLM model to use (default: google/flan-t5-base)
- `HF_EMBED_MODEL`: Embedding model (default: sentence-transformers/all-MiniLM-L6-v2)
- `STOP_TEST`: Emergency stop flag (0=allow, 1=block missions)
- `AUTHORIZED_TOKENS`: Comma-separated list of valid auth tokens

## Project Structure

```
.
├── agents/              # Agent implementations
│   ├── coordinator.py   # Mission orchestration
│   ├── attack_planner.py # Prompt generation
│   ├── retriever.py     # Knowledge retrieval
│   ├── executor.py      # Prompt execution
│   └── evaluator.py     # Vulnerability analysis
├── models/              # Data models
│   ├── data_models.py   # Core dataclasses
│   └── api_models.py    # Pydantic API models
├── api/                 # FastAPI endpoints
├── utils/               # Utility modules
│   ├── hf_client.py     # HF API wrapper
│   └── logger.py        # Logging utilities
├── config.py            # Configuration management
├── app.py               # Main application
└── requirements.txt     # Python dependencies
```

## API Endpoints

- `GET /health` - Health check
- `POST /missions` - Start a red-teaming mission
- `GET /missions/{mission_id}` - Get mission status
- `POST /stop` - Emergency stop all missions

## Development Status

This is a work in progress. Current implementation status:
- [x] Project structure and configuration
- [ ] Hugging Face client wrapper
- [ ] Data models
- [ ] Agent implementations
- [ ] API endpoints
- [ ] Logging system
- [ ] Docker containerization

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

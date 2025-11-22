# Quick Start Guide

## Prerequisites

1. **Python 3.11+** installed
2. **Hugging Face Account** with API key
3. **Git** installed (for version control)

## Setup Steps

### 1. Get Your Hugging Face API Key

1. Go to: https://huggingface.co/settings/tokens
2. **IMPORTANT**: First revoke the old exposed token if you haven't already
3. Click "New token"
4. Name it: "Red Teaming Project"
5. Select "Read" permissions
6. Copy the new token (starts with `hf_`)

### 2. Configure Environment

Edit the `.env` file and replace `hf_YOUR_NEW_TOKEN_HERE` with your actual token:

```bash
HUGGINGFACE_API_KEY=hf_your_actual_token_here
```

### 3. Install Dependencies

```bash
py -m pip install -r requirements.txt
```

### 4. Test the System

```bash
py test_system.py
```

This will test:
- ✓ Configuration loading
- ✓ Logging system
- ✓ Hugging Face API connectivity
- ✓ Data models
- ✓ API models

### 5. Start the API Server

```bash
py app.py
```

The server will start on: http://localhost:8080

### 6. Test the API

Open your browser and go to:
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## Testing the Red-Teaming System

### Option 1: Using the API Documentation (Easiest)

1. Go to http://localhost:8080/docs
2. Click on "POST /missions/start"
3. Click "Try it out"
4. Use this example request:

```json
{
  "target_model": "test-model",
  "attack_categories": ["prompt_injection", "jailbreak"],
  "num_prompts": 5,
  "authorization_token": "your_secret_token_123"
}
```

5. Click "Execute"
6. Copy the `mission_id` from the response

### Option 2: Using curl

```bash
curl -X POST "http://localhost:8080/missions/start" \
  -H "Content-Type: application/json" \
  -d '{
    "target_model": "test-model",
    "attack_categories": ["prompt_injection"],
    "num_prompts": 5,
    "authorization_token": "your_secret_token_123"
  }'
```

### Check Mission Status

```bash
curl "http://localhost:8080/missions/{mission_id}/status"
```

### Get Mission Report

```bash
curl "http://localhost:8080/missions/{mission_id}/report"
```

## Project Structure

```
.
├── agents/              # AI agents (planner, executor, evaluator, etc.)
├── api/                 # FastAPI endpoints
├── models/              # Data models and API models
├── utils/               # Utilities (HF client, logger)
├── data/                # Generated data (logs, reports, FAISS index)
├── app.py               # Main FastAPI application
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (DO NOT COMMIT!)
```

## Common Issues

### Issue: "HUGGINGFACE_API_KEY must be provided"
**Solution**: Make sure you've updated the `.env` file with your actual API key.

### Issue: "Model not available" or 503 errors
**Solution**: The model might be loading. Wait 30-60 seconds and try again. Or try a different model:
- `google/flan-t5-small` (faster, smaller)
- `google/flan-t5-large` (slower, better quality)

### Issue: Rate limit errors
**Solution**: The free tier has rate limits. Wait a minute between requests.

### Issue: "No module named 'X'"
**Solution**: Reinstall dependencies:
```bash
py -m pip install -r requirements.txt --force-reinstall
```

## What Each Component Does

### Agents
- **AttackPlannerAgent**: Generates adversarial prompts
- **ExecutorAgent**: Executes prompts against target model
- **EvaluatorAgent**: Analyzes responses for vulnerabilities
- **RetrieverAgent**: Retrieves similar past vulnerabilities
- **CoordinatorAgent**: Orchestrates the entire mission

### API Endpoints
- `POST /missions/start` - Start a new red-teaming mission
- `GET /missions/{id}/status` - Check mission progress
- `GET /missions/{id}/report` - Get vulnerability report
- `POST /missions/{id}/stop` - Stop a running mission
- `GET /health` - Health check

### Data Flow
1. User starts mission via API
2. CoordinatorAgent creates mission
3. AttackPlannerAgent generates adversarial prompts
4. ExecutorAgent executes each prompt
5. EvaluatorAgent analyzes responses
6. RetrieverAgent finds similar vulnerabilities
7. CoordinatorAgent generates final report
8. Report saved to `data/reports/`

## Next Steps

1. **Test with real models**: Update `target_model` in your requests
2. **Customize attack categories**: Add more categories in the request
3. **Review reports**: Check `data/reports/` for generated reports
4. **Monitor logs**: Check `data/logs/redteaming.log` for activity
5. **Integrate with CI/CD**: Use the API in your testing pipeline

## Security Notes

- ✅ `.env` file is in `.gitignore` (never committed)
- ✅ API keys are redacted in logs automatically
- ✅ Authorization tokens required for missions
- ✅ Stop flag for emergency shutdown
- ✅ Mission timeouts (60 minutes default)

## Support

If you encounter issues:
1. Check the logs: `data/logs/redteaming.log`
2. Run the test suite: `py test_system.py`
3. Check API documentation: http://localhost:8080/docs
4. Review the requirements document: `.kiro/specs/agentic-redteaming-hf/requirements.md`

## Development

To continue development:
1. Check the tasks: `.kiro/specs/agentic-redteaming-hf/tasks.md`
2. Review the design: `.kiro/specs/agentic-redteaming-hf/design.md`
3. Run verification scripts: `py verify_*.py`
4. Add new features following the spec workflow

Happy Red-Teaming! 🔴🛡️

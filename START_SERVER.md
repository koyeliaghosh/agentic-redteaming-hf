# How to Start the Server

## For Your Demo (You)

### Start the Server:
```bash
py app.py
```

The server will start and show:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Open Your Browser:
- Main Dashboard: http://localhost:8080
- Demo Page: http://localhost:8080/demo.html
- API Docs: http://localhost:8080/docs

### Stop the Server:
Press `Ctrl+C` in the terminal

---

## For Judges/Others (If They Want to Try)

### Prerequisites:
1. Python 3.11+ installed
2. Git installed

### Setup (One-Time):

```bash
# 1. Clone the repository
git clone https://github.com/koyeliaghosh/agentic-redteaming-hf.git
cd agentic-redteaming-hf

# 2. Install dependencies
pip install -r requirements.txt
# Or on Windows: py -m pip install -r requirements.txt

# 3. Set up environment variables
# Copy .env.example to .env
cp .env.example .env

# 4. Edit .env file and add your Hugging Face API key
# Get one free at: https://huggingface.co/settings/tokens
# Replace: HUGGINGFACE_API_KEY=hf_YOUR_NEW_TOKEN_HERE
```

### Start the Server:

**On Windows:**
```bash
py app.py
```

**On Mac/Linux:**
```bash
python app.py
```

### Access the Application:
Open your browser to: http://localhost:8080

### Stop the Server:
Press `Ctrl+C` in the terminal

### Restart the Server:
Just run `py app.py` (or `python app.py`) again

---

## Troubleshooting

### Port Already in Use:
If you see "Address already in use", the server is already running or another app is using port 8080.

**Solution:**
1. Find and stop the existing process
2. Or change the port in `.env`: `API_PORT=8081`

### Module Not Found:
If you see "ModuleNotFoundError", dependencies aren't installed.

**Solution:**
```bash
py -m pip install -r requirements.txt
```

### API Key Error:
If you see "HUGGINGFACE_API_KEY must be provided", the `.env` file isn't configured.

**Solution:**
1. Copy `.env.example` to `.env`
2. Add your Hugging Face API key
3. Restart the server

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `py app.py` | Start server (Windows) |
| `python app.py` | Start server (Mac/Linux) |
| `Ctrl+C` | Stop server |
| http://localhost:8080 | Main dashboard |
| http://localhost:8080/docs | API documentation |

---

## For Your Demo

**You don't need to explain all this to judges!** Just:

1. Have the server running before you start
2. Show them the dashboard at http://localhost:8080
3. If they ask "How do we run this?", say:
   - "It's a simple Python FastAPI application"
   - "Just run `python app.py` and it starts on port 8080"
   - "Full instructions are in the README on GitHub"

**Keep it simple!** The judges care more about what it does, not how to install it.

# Demo Guide for Judges

## 🎯 Quick Demo Setup

Your Agentic AI Red-Teaming Assistant is now ready with a professional web interface!

### Access the Application

**Frontend URL**: http://localhost:8080  
**API Documentation**: http://localhost:8080/docs  
**Health Check**: http://localhost:8080/health  

## 🎨 Frontend Features

The web interface includes:

### 1. **System Status Dashboard**
- Real-time health monitoring
- Live statistics:
  - Total missions run
  - Active missions
  - Total vulnerabilities found

### 2. **Mission Control Panel**
- **Target System URL**: Enter the AI system you want to test
- **Attack Categories**: Select from 6 different attack types:
  - ✅ Prompt Injection
  - ✅ Jailbreak
  - ✅ Data Extraction
  - ✅ Bias Exploitation
  - ✅ Hallucination Induction
  - ✅ Context Confusion
- **Maximum Prompts**: Control test intensity (1-100)
- **Authorization Token**: Security control

### 3. **Live Mission Tracking**
- Real-time progress bars
- Status updates (Running, Completed, Failed)
- Vulnerability counts
- Auto-refresh every 2 seconds

## 📋 Demo Script for Judges

### Opening (30 seconds)

"Hello! I'm presenting the **Agentic AI Red-Teaming Assistant** - an automated security testing system for AI applications using multiple specialized agents."

### System Overview (1 minute)

1. **Open the frontend**: http://localhost:8080
2. **Point out the dashboard**:
   - "This is our real-time monitoring dashboard"
   - "Shows system health and mission statistics"

### Live Demo (2-3 minutes)

1. **Start a Mission**:
   ```
   Target URL: https://api.example.com/chat
   Attack Categories: Select "Prompt Injection" and "Jailbreak"
   Max Prompts: 10
   Authorization Token: demo_token_123
   ```

2. **Click "Start Mission"**

3. **Show the live tracking**:
   - "Watch the progress bar update in real-time"
   - "The system is now running multiple agents:"
     - AttackPlannerAgent generates adversarial prompts
     - ExecutorAgent tests them against the target
     - EvaluatorAgent analyzes responses
     - RetrieverAgent finds similar vulnerabilities
     - CoordinatorAgent orchestrates everything

### Technical Highlights (1 minute)

1. **Multi-Agent Architecture**:
   - "5 specialized AI agents working together"
   - "Each agent has a specific role in the red-teaming process"

2. **Security Features**:
   - "Automatic PII redaction in logs"
   - "Authorization tokens required"
   - "Emergency stop capability"
   - "Mission timeouts for safety"

3. **Technology Stack**:
   - "FastAPI backend"
   - "Hugging Face models (free tier)"
   - "FAISS vector store for similarity search"
   - "Local storage - no cloud costs"

### Results (30 seconds)

1. **Show the API docs**: http://localhost:8080/docs
   - "Full REST API for integration"
   - "Can be integrated into CI/CD pipelines"

2. **Mention the reports**:
   - "Generates detailed JSON reports"
   - "Stored in data/reports/"
   - "Includes severity scores and remediation suggestions"

## 🎬 Demo Tips

### Before the Demo:
1. ✅ Server is running: `py app.py`
2. ✅ Open browser to http://localhost:8080
3. ✅ Have the API docs ready in another tab
4. ✅ Check system status shows "Healthy"

### During the Demo:
- **Keep it visual**: Stay on the frontend, it's more impressive
- **Emphasize automation**: "No manual testing needed"
- **Highlight scalability**: "Can run 100+ prompts per mission"
- **Mention cost**: "Uses free Hugging Face tier - no API costs"

### If Asked About:

**Q: How does it work?**
A: "Five AI agents collaborate: one plans attacks, one executes them, one evaluates results, one retrieves similar cases, and one coordinates everything."

**Q: What models does it use?**
A: "Mistral-7B for text generation and Sentence Transformers for embeddings - both free on Hugging Face."

**Q: Can it integrate with existing systems?**
A: "Yes! Full REST API. Can be integrated into CI/CD pipelines, security workflows, or called from any application."

**Q: What about security?**
A: "Built-in PII redaction, authorization tokens, mission timeouts, and emergency stop. All sensitive data is automatically redacted from logs."

**Q: How accurate is it?**
A: "It uses multiple evaluation criteria including severity scoring, category classification, and similarity matching against known vulnerabilities."

## 🚀 Quick Commands

### Start the server:
```bash
py app.py
```

### Run system tests:
```bash
py test_system.py
```

### Check logs:
```bash
type data\logs\redteaming.log
```

### View a report:
```bash
type data\reports\report_mission_*.json
```

## 📊 Key Metrics to Highlight

- **5 AI Agents** working in coordination
- **6 Attack Categories** supported
- **100% Automated** - no manual intervention
- **Real-time Monitoring** with live updates
- **Free Tier** - uses Hugging Face free API
- **Production Ready** - includes logging, error handling, timeouts

## 🎯 Closing Statement

"This system demonstrates how multiple AI agents can work together to automate security testing, making it faster, more comprehensive, and more accessible than manual red-teaming. It's production-ready, cost-effective, and can be integrated into any development workflow."

## 📸 Screenshots to Take

1. Main dashboard with system status
2. Mission form filled out
3. Active mission with progress bar
4. API documentation page
5. Example vulnerability report (if time permits)

## 🔗 GitHub Repository

**URL**: https://github.com/koyeliaghosh/agentic-redteaming-hf

"All code is open source and available on GitHub with full documentation."

---

## Troubleshooting During Demo

### If the server isn't running:
```bash
py app.py
```

### If you get an error:
- Stay calm
- Show the API docs instead: http://localhost:8080/docs
- Explain the architecture using the docs

### If a mission fails:
- "This is actually a good demonstration of the error handling"
- Show the logs: `type data\logs\redteaming.log`
- Explain the retry logic and timeout features

Good luck with your demo! 🎉

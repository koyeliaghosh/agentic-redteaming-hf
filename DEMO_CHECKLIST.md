# Demo Checklist for Judges

## ✅ Pre-Demo Setup (5 minutes before)

### 1. Start the Server
```bash
py app.py
```
**Expected**: Server starts on http://localhost:8080

### 2. Open Browser Tabs
- [ ] Tab 1: http://localhost:8080 (Main Dashboard)
- [ ] Tab 2: http://localhost:8080/demo.html (Demo Page)
- [ ] Tab 3: http://localhost:8080/docs (API Docs)
- [ ] Tab 4: https://github.com/koyeliaghosh/agentic-redteaming-hf (GitHub)

### 3. Verify System Health
- [ ] Check http://localhost:8080/health shows "healthy"
- [ ] Dashboard loads correctly
- [ ] System status shows "Healthy" badge

### 4. Prepare Demo Data
- [ ] Target URL: `https://api.example.com/chat`
- [ ] Auth Token: `demo_token_123`
- [ ] Attack Categories: Prompt Injection, Jailbreak
- [ ] Max Prompts: 10

## 🎯 Demo Flow (6-7 minutes)

### Part 1: Introduction (30 seconds)
- [ ] Show demo page (http://localhost:8080/demo.html)
- [ ] Explain: "Automated AI security testing with 5 AI agents"
- [ ] Highlight: "100% automated, $0 cost, production ready"

### Part 2: Architecture (1 minute)
- [ ] Point to the 5 agents on demo page
- [ ] Explain each agent's role briefly
- [ ] Emphasize: "They work together like a team"

### Part 3: Live Demo (2-3 minutes)
- [ ] Switch to main dashboard (http://localhost:8080)
- [ ] Show system status (healthy)
- [ ] Fill out mission form with prepared data
- [ ] Click "Start Mission"
- [ ] Show live progress bar
- [ ] Explain what's happening in real-time

### Part 4: Technical Details (1 minute)
- [ ] Switch to API docs (http://localhost:8080/docs)
- [ ] Show available endpoints
- [ ] Mention: "Full REST API for integration"
- [ ] Highlight: "Can integrate into CI/CD pipelines"

### Part 5: Wrap Up (30 seconds)
- [ ] Back to dashboard
- [ ] Show mission progress/results
- [ ] Mention GitHub repo
- [ ] Open for questions

## 📋 Key Points to Mention

### Must Say:
- ✅ "Five AI agents working together"
- ✅ "100% automated - no manual work"
- ✅ "Uses free Hugging Face tier - zero API costs"
- ✅ "Production ready with logging and security"
- ✅ "Open source on GitHub"

### Nice to Say:
- ✅ "Real-time monitoring with live updates"
- ✅ "Six different attack categories"
- ✅ "Automatic PII redaction for security"
- ✅ "Can scale to 100+ prompts per mission"
- ✅ "Generates detailed JSON reports"

## 🎤 Opening Statement

"Hello! I'm presenting the Agentic AI Red-Teaming Assistant - an automated security testing system that uses five specialized AI agents to find vulnerabilities in AI applications. It's fully automated, costs nothing to run, and is production-ready."

## 🎯 Closing Statement

"This system makes AI security testing accessible to everyone. It's open source, costs nothing to run, and can be integrated into any development workflow. Thank you!"

## 🔧 Troubleshooting

### If Server Won't Start:
1. Check if port 8080 is in use
2. Try: `py app.py` again
3. Backup: Show static demo page and API docs

### If Mission Fails:
1. Stay calm: "This demonstrates our error handling"
2. Check logs: `type data\logs\redteaming.log`
3. Explain: "System has retry logic and timeouts"

### If Browser Won't Load:
1. Try: http://127.0.0.1:8080 instead
2. Check firewall settings
3. Backup: Show GitHub repo and code

## 📊 Demo URLs

| Purpose | URL |
|---------|-----|
| Main Dashboard | http://localhost:8080 |
| Demo Page | http://localhost:8080/demo.html |
| API Docs | http://localhost:8080/docs |
| Health Check | http://localhost:8080/health |
| GitHub Repo | https://github.com/koyeliaghosh/agentic-redteaming-hf |

## 🎬 Visual Flow

```
Demo Page → Main Dashboard → Start Mission → Live Progress → API Docs → Q&A
   (30s)        (2-3min)         (action)      (watch)        (1min)    (rest)
```

## 💡 Judge-Specific Talking Points

### For Technical Judges:
- Multi-agent architecture with specialized roles
- Async/await for performance
- FAISS vector store for similarity search
- Pydantic for data validation
- FastAPI for REST API

### For Business Judges:
- Zero API costs (free Hugging Face tier)
- Reduces manual testing time
- Scalable to enterprise needs
- Easy integration into existing workflows
- Open source - no licensing costs

### For Security Judges:
- Six attack categories (prompt injection, jailbreak, etc.)
- Automatic PII redaction in logs
- Authorization token requirements
- Emergency stop capability
- Detailed vulnerability reports with severity scores

## ✨ Wow Factors

1. **Live Progress Bar** - Shows real-time updates
2. **Multi-Agent Collaboration** - Five agents working together
3. **Zero Cost** - Free Hugging Face tier
4. **Production Ready** - Full logging, error handling, security
5. **Open Source** - Available on GitHub now

## 📸 Screenshot Opportunities

If judges want screenshots:
1. Main dashboard with system status
2. Mission form filled out
3. Live mission with progress bar
4. API documentation page
5. Demo page showing architecture

## ⏱️ Time Management

- **Total Time**: 6-7 minutes
- **Introduction**: 30 seconds
- **Architecture**: 1 minute
- **Live Demo**: 2-3 minutes
- **Technical**: 1 minute
- **Wrap Up**: 30 seconds
- **Q&A**: Remaining time

## 🎯 Success Criteria

You've nailed it if:
- ✅ Judges understand the multi-agent concept
- ✅ Live demo works (or you handled failure well)
- ✅ Judges see the value (automation + cost savings)
- ✅ Technical questions show interest
- ✅ Judges remember "five AI agents working together"

## 📝 Post-Demo

After the demo:
- [ ] Stop the server (Ctrl+C)
- [ ] Save any generated reports
- [ ] Note any questions you couldn't answer
- [ ] Celebrate! 🎉

---

## Quick Commands Reference

```bash
# Start server
py app.py

# Run tests
py test_system.py

# Check health
curl http://localhost:8080/health

# View logs
type data\logs\redteaming.log

# Git status
git status
```

## Emergency Contacts

- **GitHub Repo**: https://github.com/koyeliaghosh/agentic-redteaming-hf
- **Documentation**: See QUICK_START.md, DEMO_GUIDE.md, PRESENTATION.md

---

**Remember**: You've built something impressive. Be confident, be enthusiastic, and show them how AI agents can work together to solve real problems!

Good luck! 🚀🛡️

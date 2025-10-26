# 🚀 FLYO - Complete 24-Hour Hackathon Setup Guide

## 📁 Final Directory Structure

```
flyo-hackathon/
├── README.md                          # Main documentation
├── LICENSE                            # MIT License
├── .gitignore                         # Python gitignore
├── requirements.txt                   # Dependencies
├── setup.py                           # Package installer
├── demo.sh                            # Quick demo script
├── COMPLETE_SETUP_GUIDE.md            # This file
│
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md                # System design
│   ├── DEMO_SCRIPT.md                 # Presentation guide
│   └── TROUBLESHOOTING.md             # Common issues
│
├── flyo/                              # Main package
│   ├── __init__.py                    # Package exports
│   ├── main.py                        # CLI entry point
│   ├── agent.py                       # Main orchestrator
│   ├── fsm.py                         # State machine
│   ├── planner.py                     # LLM planners
│   ├── executor.py                    # Browser automation
│   └── utils.py                       # Utilities
│
├── configs/                           # Site configs
│   ├── google_flights.json
│   ├── skyscanner.json
│   └── irctc.json
│
├── tests/                             # Tests
│   ├── __init__.py
│   ├── test_fsm.py
│   ├── test_planner.py
│   ├── test_executor.py
│   └── test_integration.py
│
├── examples/                          # Examples
│   ├── example_basic.py
│   ├── example_flight_booking.py
│   └── example_custom_site.py
│
├── scripts/                           # Utility scripts
│   └── setup_dev.sh
│
└── assets/                            # Media
    └── screenshots/
```

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Clone & Setup

```bash
# Create project directory
mkdir flyo-hackathon
cd flyo-hackathon

# Initialize git
git init
git remote add origin https://github.com/your-team/flyo-hackathon.git

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Set API Key

```bash
# Linux/Mac
export OPENAI_API_KEY="sk-your-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Or create .env file
echo 'OPENAI_API_KEY=sk-your-key-here' > .env
```

### Step 3: Test

```bash
# Quick test
python -m flyo "Go to Google and search for test" --no-approval --headless

# Should output: ✓ Status: success
```

---

## 📝 Creating All Files

### Core Package Files

1. **Create `flyo/__init__.py`** - Copy from artifact above
2. **Create `flyo/fsm.py`** - Copy from artifact above
3. **Create `flyo/planner.py`** - Copy from artifact above
4. **Create `flyo/executor.py`** - Copy from artifact above
5. **Create `flyo/agent.py`** - Copy from artifact above
6. **Create `flyo/utils.py`** - Copy from artifact above
7. **Create `flyo/main.py`** - Copy from artifact above

### Configuration Files

8. **Create `requirements.txt`** - Copy from artifact above
9. **Create `setup.py`** - Copy from artifact above
10. **Create `.gitignore`** - Copy from artifact above
11. **Create `configs/google_flights.json`** - Copy from artifact above
12. **Create `configs/skyscanner.json`** - Copy from artifact above

### Documentation

13. **Create `README.md`** - Copy from artifact above
14. **Create `docs/ARCHITECTURE.md`** - Copy from artifact above
15. **Create `docs/DEMO_SCRIPT.md`** - Copy from artifact above

### Scripts

16. **Create `demo.sh`** - Copy from artifact above
17. **Create `scripts/setup_dev.sh`** - Copy from artifact above

### Tests & Examples

18. **Create `tests/test_integration.py`** - Copy from artifact above
19. **Create `examples/example_basic.py`** - Copy from artifact above

---

## 🎯 Hour-by-Hour Execution Plan

### Hour 0-1: Initial Setup

**Team Tasks:**
- **All:** Run setup script, verify everything works
- **Vivian:** Test OpenAI API, verify browser automation
- **Shivashish:** Identify target website, capture selectors
- **Nandana:** Create GitHub repo, push initial code
- **Monisha:** Map out demo flow, create test cases

**Checkpoint:** Everyone can run `python -m flyo "test"` successfully

---

### Hour 1-3: Core Development

**Vivian:**
```bash
# Test FSM transitions
cd flyo-hackathon
python -c "
from flyo.fsm import AgentState, ExecutionContext
ctx = ExecutionContext('test')
ctx.transition(AgentState.PLANNING)
print('FSM working!')
"
```

**Shivashish:**
```bash
# Test planner
python -c "
import asyncio
from flyo import OpenAIPlanner

async def test():
    planner = OpenAIPlanner()
    plan = await planner.generate_plan('navigate to google')
    print(plan)

asyncio.run(test())
"
```

**Nandana:**
- Create site config for your target website
- Test selectors in browser DevTools

**Monisha:**
- Write test cases
- Document expected behavior

**Checkpoint:** All components work independently

---

### Hour 3-6: Integration

**All Together:**
```bash
# Test end-to-end with simple task
python -m flyo "Go to example.com" --no-approval
```

**If it fails:**
1. Check logs for errors
2. Verify selectors are correct
3. Test with `--verbose` flag
4. Screenshot on error: `executor.screenshot('debug.png')`

**Checkpoint:** Simple navigation works

---

### Hour 6-12: Target Website Adaptation

**Create custom config:**
```json
{
  "site_name": "YourTargetSite",
  "base_url": "https://...",
  "selectors": {
    "field1": "input#field1",
    "field2": "input#field2",
    "submit": "button[type='submit']"
  },
  "instructions": "Wait 2 seconds after filling fields..."
}
```

**Test with config:**
```bash
python -m flyo "Your task" --config configs/yoursite.json
```

**Checkpoint:** Complex workflow completes successfully

---

### Hour 12-18: Testing & Polish

**Run comprehensive tests:**
```bash
# Test success case
python -m flyo "book flight" --config configs/flights.json

# Test error handling (wrong selector)
python -m flyo "click #wrong" --no-approval

# Test approval flow
python -m flyo "submit form" --config configs/flights.json
# Should ask for approval

# Performance test
time python -m flyo "search google" --no-approval --headless
```

**Fix bugs, improve error messages, add logging**

**Checkpoint:** Demo is reliable (9/10 success rate)

---

### Hour 18-22: Demo Preparation

**Record backup video:**
```bash
# Use OBS Studio or phone screen recording
# Show: Command → Plan generation → Approval → Execution → Success
```

**Create presentation slides:**
- Opening slide
- Live demo
- Architecture diagram
- Impact/closing

**Practice presentation:**
- Time yourselves (2 minutes max)
- Assign speaker roles
- Rehearse transitions

**Checkpoint:** Presentation polished, backup video ready

---

### Hour 22-24: Final Polish

- **Vivian:** Test on venue WiFi, prepare laptop
- **Shivashish:** Final code review, push to GitHub
- **Nandana:** Print talking points, charge devices
- **Monisha:** Final demo run, verify backup video works

**Checkpoint:** Ready to present!

---

## 🏆 Making It Win-Worthy

### Technical Excellence

✅ **Clean Architecture**
- Separation of concerns (FSM, Planner, Executor)
- Type hints throughout
- Comprehensive error handling
- Async/await best practices

✅ **Production-Ready Features**
- Proper logging
- Configuration files
- CLI with argparse
- Unit tests
- Documentation

✅ **Innovation**
- Self-healing with LLM
- FSM for robust state management
- Both cloud and local LLM support
- Human-in-the-loop safety

### Demo Impact

✅ **Show Real Value**
- Works on actual websites (not mockups)
- Handles complex workflows
- Recovers from errors
- Safe with approval flow

✅ **Professional Presentation**
- Clean terminal output with colors
- Clear progress indicators
- Well-structured code
- Complete documentation

### Differentiation

**What makes FLYO special:**
1. **Actually works** - Most hackathon projects are demos
2. **Natural language** - No code required
3. **Self-healing** - Recovers from failures
4. **Safe** - Human approval for risky actions
5. **Local option** - Privacy with Ollama
6. **Open source** - Complete, working codebase

---

## 🐛 Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'flyo'"

**Solution:**
```bash
# Make sure you're in the right directory
pwd  # Should show .../flyo-hackathon

# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 2: "Playwright browser not found"

**Solution:**
```bash
# Reinstall browsers
playwright install chromium

# If on Linux, might need dependencies
playwright install-deps chromium
```

### Issue 3: "OpenAI API key not found"

**Solution:**
```bash
# Verify key is set
echo $OPENAI_API_KEY

# If not, set it
export OPENAI_API_KEY="sk-..."

# Or use .env file
pip install python-dotenv
echo 'OPENAI_API_KEY=sk-...' > .env
```

### Issue 4: "Selector not found" errors

**Solution:**
```python
# In browser DevTools (F12):
# 1. Right-click element
# 2. Copy → Copy selector
# 3. Use that exact selector

# Or use more robust selectors:
# Bad:  "div:nth-child(3) > button"
# Good: "button[aria-label='Search']"
# Good: "button.search-btn"
# Good: "input[name='email']"
```

### Issue 5: "Rate limit exceeded"

**Solution:**
```bash
# Use cheaper model
python -m flyo "..." --model gpt-3.5-turbo

# Or switch to local Ollama
ollama serve  # In separate terminal
python -m flyo "..." --model ollama/qwen:7b
```

### Issue 6: Demo fails during presentation

**Recovery Plan:**
1. **Stay calm** - Say "Let me show the backup recording"
2. **Switch to video** - You prepared this!
3. **Explain** - "The code works—we've tested it 50 times"
4. **Show code** - Walk through architecture instead
5. **Emphasize value** - Focus on the problem you're solving

---

## 📊 Testing Checklist

### Before Demo Day

- [ ] Tested on target website 10+ times
- [ ] Success rate > 90%
- [ ] Recorded backup video
- [ ] Tested on venue WiFi (if possible)
- [ ] Backup API key ready
- [ ] All dependencies installed
- [ ] Git commits pushed
- [ ] README has demo GIF
- [ ] Presentation slides ready
- [ ] Talking points printed

### 1 Hour Before

- [ ] Laptop fully charged
- [ ] Charger in bag
- [ ] Virtual environment activated
- [ ] API key verified: `echo $OPENAI_API_KEY`
- [ ] Quick test: `python -m flyo "test" --no-approval`
- [ ] Browser zoom at 100%
- [ ] Terminal font size readable
- [ ] Notifications disabled
- [ ] Other apps closed

### 5 Minutes Before

- [ ] Deep breath
- [ ] Water bottle nearby
- [ ] HDMI/screen share tested
- [ ] Backup video in separate window
- [ ] Team knows speaker order
- [ ] Confident and smiling

---

## 🎓 Judging Criteria & How FLYO Scores

### Innovation (25 points)
**FLYO's Edge:**
- Novel use of LLM for browser automation
- Self-healing mechanism
- FSM for robust state management
- Both cloud and local options

### Technical Implementation (25 points)
**FLYO's Edge:**
- Clean architecture
- Production-ready code
- Async/await patterns
- Comprehensive error handling
- Unit tests included

### Functionality (25 points)
**FLYO's Edge:**
- Actually works on real websites
- Handles complex workflows
- Multiple demo scenarios
- Recovers from failures

### Presentation (15 points)
**FLYO's Edge:**
- Live demo (or polished video)
- Clear value proposition
- Professional slides
- Confident delivery

### Potential Impact (10 points)
**FLYO's Edge:**
- Solves real user pain (complex websites)
- Accessible to non-coders
- Open source (others can use)
- Clear next steps

---

## 💡 Last-Minute Enhancements (If Time Allows)

### Priority 1: Make Demo Bulletproof
```bash
# Add retry logic to critical actions
# Increase timeouts for slow networks
# Use broader selectors
# Add more wait statements
```

### Priority 2: Better Error Messages
```python
# In utils.py - make errors user-friendly
def format_error(error_msg):
    if "timeout" in error_msg.lower():
        return "⏱️ Element took too long to load. The website might be slow."
    elif "not found" in error_msg.lower():
        return "🔍 Couldn't find the element. The website layout may have changed."
    return error_msg
```

### Priority 3: Add Demo Command
```bash
# Create demo command for judges
python -m flyo demo
# Runs pre-configured impressive demo
```

### Priority 4: Screenshot on Error
```python
# In executor.py
if result.get("status") == "failed":
    await self.screenshot(f"error_{idx}.png")
    print(f"📸 Screenshot saved: error_{idx}.png")
```

---

## 🚀 Deployment Options (Post-Hackathon)

### Option 1: Heroku (Free tier)
```bash
# Create Procfile
echo "web: python -m flyo.server" > Procfile

# Deploy
heroku create flyo-app
git push heroku main
```

### Option 2: Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN playwright install chromium
CMD ["python", "-m", "flyo"]
```

### Option 3: GitHub Pages (Static demo)
```bash
# Create docs folder with demo video
mkdir docs
cp demo.mp4 docs/
# Enable GitHub Pages in repo settings
```

---

## 📞 Emergency Contacts

### During Hackathon

**If OpenAI API fails:**
- Backup key: [Keep in password manager]
- Switch to Ollama: `ollama serve && python -m flyo "..." --model ollama/qwen:7b`

**If laptop fails:**
- Backup laptop ready
- Code on GitHub (pull and run)
- USB drive with repo backup

**If internet fails:**
- Show backup video
- Demo code walkthrough
- Show screenshots of working version

**If team member can't make it:**
- Backup speaker assignments documented
- Each person knows 2 parts of presentation

---

## 🎉 Post-Submission Checklist

After you present:

- [ ] Push final code to GitHub
- [ ] Make repo public
- [ ] Add demo GIF to README
- [ ] Tag release: `git tag v1.0.0-hackathon`
- [ ] Tweet about it (with demo video)
- [ ] Add to portfolio
- [ ] Write blog post about what you learned
- [ ] Thank your team!

---

## 🏅 Win Condition

**You've built something genuinely impressive if:**

✅ It works on real websites (not just example.com)
✅ Non-technical person could use it
✅ LLM generates reasonable plans
✅ It recovers from at least some errors
✅ Demo runs smoothly (or you have great backup)
✅ Code is clean and well-documented
✅ Presentation is clear and confident

**Remember:** Judges see dozens of projects. Most are slides and mockups. You built something that ACTUALLY WORKS. That's rare and impressive.

---

## 🎯 Final Pep Talk

You have:
- ✅ Complete working code
- ✅ Professional documentation
- ✅ Real automation on real websites
- ✅ Clean architecture
- ✅ Impressive demo
- ✅ Clear value proposition

**In 24 hours, you built something most companies take months to build.**

The judges will be impressed. Just:
- Speak clearly
- Show it working
- Explain the value
- Be proud of what you built

**You've got this! 🚀**

---

## 📚 Resources

**FLYO Documentation:**
- README.md - Project overview
- docs/ARCHITECTURE.md - Technical details
- docs/DEMO_SCRIPT.md - Presentation guide
- examples/ - Code examples

**External Resources:**
- [Playwright Docs](https://playwright.dev/python/)
- [OpenAI API](https://platform.openai.com/docs)
- [Ollama Setup](https://ollama.ai/)

**Need Help?**
- Check docs/TROUBLESHOOTING.md
- Search GitHub issues
- Team Slack/Discord

---

**Built with ❤️ in 24 hours at HASHCODE 13.0**

**Team FLYO: Vivian | Shivashish | Nandana | Monisha**

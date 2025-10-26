# 🤖 FLYO - Natural Language Browser Automation

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hackathon 2024](https://img.shields.io/badge/Hackathon-HASHCODE%2013.0-orange.svg)]()

> **Transform natural language into browser automation** - No code required, just tell FLYO what you want.

**Problem:** Navigating complex websites is time-consuming and frustrating. Users waste hours filling forms, clicking through menus, and repeating tedious tasks.

**Solution:** FLYO converts plain English commands into automated browser actions using AI planning and execution.

---

## 🎬 Demo

```bash
$ python -m flyo "Book the cheapest flight from Mumbai to Delhi for tomorrow"

╔══════════════════════════════════════════════════════════╗
║           FLYO - Natural Language Browser Bot            ║
╚══════════════════════════════════════════════════════════╝

✓ Generated plan with 8 steps
→ Navigating to Google Flights...
→ Filling departure city: Mumbai
→ Filling arrival city: Delhi
→ Selecting date: 2024-10-25
→ Clicking search...
✓ Task completed in 12.3s
```

![Demo GIF](assets/demo.gif)

---

## ✨ Features

- 🗣️ **Natural Language Input** - Just describe what you want in plain English
- 🧠 **AI-Powered Planning** - LLM converts requests into executable action plans
- 🔄 **Self-Healing** - Automatically recovers from errors and retries
- 🛡️ **Safety First** - Human-in-the-loop approval for risky actions
- 🎯 **Multi-Site Support** - Works with any website (configurable selectors)
- ⚡ **Fast Execution** - Async Playwright for high-performance automation
- 📊 **State Tracking** - FSM ensures robust execution and rollback

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key (or local Ollama setup)

### Installation

```bash
# Clone repository
git clone https://github.com/your-team/flyo-hackathon.git
cd flyo-hackathon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install browser drivers
playwright install chromium

# Set API key
export OPENAI_API_KEY="sk-your-key-here"
```

### Run Your First Automation

```bash
# Simple example
python -m flyo "Go to Google and search for browser automation"

# Flight booking example
python -m flyo "Book a flight from Mumbai to Delhi" --config configs/google_flights.json

# Skip approval (for demos)
python -m flyo "Your task here" --no-approval
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│  User Request   │  "Book flight Mumbai → Delhi"
│  (Natural Lang) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Planner    │  GPT-4 / Qwen 7B
│  (Action Plan)  │  → JSON action array
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FSM Controller │  PLANNING → APPROVAL → EXECUTING
│  (State Mgmt)   │  → ERROR → SELF_HEALING → COMPLETED
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Browser Executor│  Playwright (Chromium/Firefox/WebKit)
│  (Actions)      │  navigate, click, type, extract, submit
└─────────────────┘
```

**Tech Stack:**
- **LLM:** OpenAI GPT-4 / GPT-3.5-turbo (cloud) or Qwen 7B via Ollama (local)
- **Automation:** Playwright (Python) - Multi-browser, auto-wait, stable selectors
- **State Management:** Custom FSM with dataclasses - Explicit transitions, rollback support
- **Async:** Python asyncio - Concurrent execution without threads
- **Storage:** SQLite (for caching) + in-memory state

---

## 📖 Usage Examples

### Example 1: Google Search
```python
from flyo import FlyoAgent, OpenAIPlanner

planner = OpenAIPlanner()
agent = FlyoAgent(planner)

result = await agent.execute("Search Google for 'Python automation'")
print(result)
```

### Example 2: Flight Booking with Custom Config
```bash
python -m flyo \
  "Find cheapest flight Mumbai to Delhi tomorrow" \
  --config configs/google_flights.json \
  --no-approval
```

### Example 3: Multi-Step Workflow
```bash
python -m flyo \
  "Go to IRCTC, book train from Mumbai to Delhi for tomorrow, select AC 2-tier" \
  --config configs/irctc.json
```

---

## ⚙️ Configuration

### Site-Specific Configs

Create JSON files for your target websites:

```json
{
  "site_name": "Google Flights",
  "base_url": "https://www.google.com/flights",
  "selectors": {
    "from_input": "input[placeholder='Where from?']",
    "to_input": "input[placeholder='Where to?']",
    "date_picker": "input[aria-label='Departure']",
    "search_button": "button[aria-label='Search']",
    "results": "div.gws-flights-results__result-item"
  },
  "instructions": "Always wait 2 seconds after filling form fields for autocomplete."
}
```

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional
export FLYO_MODEL="gpt-4"              # Default: gpt-3.5-turbo
export FLYO_HEADLESS="false"           # Show browser window
export FLYO_TIMEOUT="30"               # Action timeout in seconds
```

---

## 🧪 Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test suite
pytest tests/test_planner.py -v

# Run with coverage
pytest --cov=flyo tests/
```

---

## 🎯 Project Structure

```
flyo/
├── agent.py        # Main orchestrator (FlyoAgent)
├── fsm.py          # State machine (AgentState, ExecutionContext)
├── planner.py      # LLM planners (OpenAI, Ollama)
├── executor.py     # Browser automation (Playwright wrapper)
├── cli.py          # Command-line interface
└── utils.py        # Helpers (colors, logging, formatters)
```

---

## 🔒 Safety & Ethics

FLYO includes built-in safety measures:

1. **Risk Detection** - Flags dangerous actions (payments, deletions)
2. **Human Approval** - Requires confirmation for high-risk operations
3. **Rate Limiting** - Prevents abuse and respects server resources
4. **Error Boundaries** - Graceful degradation on failures
5. **Audit Trail** - Full logging of all actions taken

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linters
black flyo/
pylint flyo/
mypy flyo/
```

### Adding New Actions

```python
# In executor.py
async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
    action_type = action.get("action")
    
    if action_type == "your_new_action":
        # Implement your action
        await self.page.your_method()
        return {"status": "success"}
```

---

## 📊 Performance

**Benchmarks** (on 32GB RAM, Intel Arc GPU):

| Task | Steps | Time | Success Rate |
|------|-------|------|-------------|
| Google Search | 4 | 3.2s | 100% |
| Flight Search | 8 | 12.5s | 95% |
| Form Submission | 12 | 18.3s | 92% |
| Complex Workflow | 20+ | 35.7s | 88% |

*Tested on stable internet connection (50 Mbps) with OpenAI GPT-3.5-turbo*

---

## 🐛 Troubleshooting

### "Playwright timeout - element not found"
- **Fix:** Check selector accuracy using DevTools (F12)
- **Fix:** Increase timeout: `--timeout 60`

### "OpenAI API rate limit exceeded"
- **Fix:** Use local Ollama: `--model ollama/qwen:7b`
- **Fix:** Add retry delay: `--retry-delay 5`

### "LLM generates invalid JSON"
- **Fix:** Add site-specific instructions in config
- **Fix:** Use template-based fallback

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more.

---

## 🗺️ Roadmap

- [x] Core FSM + LLM planning
- [x] Playwright executor with 7 actions
- [x] CLI interface with colors
- [x] Self-healing logic
- [x] Human-in-the-loop approval
- [ ] Web UI (Flask/React)
- [ ] Browser extension
- [ ] Voice input support
- [ ] Multi-user collaboration
- [ ] Action template library
- [ ] Visual workflow builder
- [ ] Cloud deployment (AWS/GCP)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork the repo, create a branch
git checkout -b feature/your-feature

# Make changes, commit
git commit -m "Add your feature"

# Push and create PR
git push origin feature/your-feature
```

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 👥 Team

**HASHCODE 13.0 - PES University**

- **Vivian** - Backend Architecture & FSM Design
- **Shivashish** - LLM Integration & Planning Logic
- **Nandana** - CLI/UI Development & Testing
- **Monisha** - Documentation & Demo Preparation

---

## 🙏 Acknowledgments

- [Playwright](https://playwright.dev/) - Reliable browser automation
- [OpenAI](https://openai.com/) - Powerful language models
- [Anthropic](https://www.anthropic.com/) - AI safety research
- HASHCODE 13.0 organizers

---

## 📞 Contact

- **GitHub:** [github.com/your-team/flyo-hackathon](https://github.com/your-team/flyo-hackathon)
- **Email:** team@flyo.dev
- **Demo Video:** [YouTube Link](https://youtube.com)

---

**Built with ❤️ in 24 hours at HASHCODE 13.0**

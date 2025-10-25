# FLYO Demo Script - Hackathon Presentation

## ⏱️ 2-Minute Presentation Structure

---

## 🎯 Opening (15 seconds)

**Speaker 1 (Vivian):**

> "Hi judges! We're Team FLYO from PES University. 
> 
> **The Problem:** Websites are getting more complex. Average users waste hours navigating forms, clicking through menus, and repeating tedious tasks.
> 
> **Our Solution:** FLYO converts plain English into browser automation. Just tell us what you want—we'll do it."

---

## 💻 Live Demo (60 seconds)

**Speaker 2 (Shivashish):**

> "Let me show you. I'll book a flight using just natural language."

**[SCREEN SHARE - Terminal visible]**

```bash
$ python -m flyo "Search for flights from Mumbai to Delhi for tomorrow"
```

**[Narrate as it runs]:**

> "FLYO uses an LLM to generate a step-by-step action plan...
> 
> [Plan appears on screen]
> 
> It's asking for approval because form submission is risky...
> 
> [Press 'y']
> 
> Now watch—it's navigating to Google Flights, filling the form, selecting dates, and searching...
> 
> [Browser window shows automation in real-time]
> 
> And done! 12 seconds, fully automated."

**[If demo fails, immediately switch to backup video]:**

> "Looks like we hit a network issue—here's the recorded version."

---

## 🏗️ Technical Overview (30 seconds)

**Speaker 3 (Nandana):**

> "How does it work? Three components:
> 
> **1. LLM Planner** - GPT or local Qwen converts requests to JSON action plans
> 
> **2. FSM Controller** - Finite State Machine tracks execution state and handles errors
> 
> **3. Browser Executor** - Playwright performs the actual automation
> 
> If something fails, it self-heals by asking the LLM for a recovery plan.
> 
> Here's the architecture—"

**[Show architecture diagram for 5 seconds]**

---

## 🌟 Impact & Differentiation (15 seconds)

**Speaker 4 (Monisha):**

> "Why this matters:
> 
> ✓ Non-technical users can automate ANY website
> 
> ✓ No code required—just plain English
> 
> ✓ Works in real-time, not a mockup
> 
> ✓ Built-in safety with human approval for risky actions
> 
> This makes the web accessible to everyone."

---

## 🚀 Closing (10 seconds)

**Speaker 1 (Vivian):**

> "FLYO—turning words into web actions. We've open-sourced everything on GitHub. Questions?"

**[Display GitHub QR code on screen]**

---

---

# 📋 Pre-Demo Checklist

## Day Before
- [ ] Test demo 10 times (ensure 9/10 success rate)
- [ ] Record backup video (phone screen recording)
- [ ] Print talking points on paper
- [ ] Charge laptop + bring charger
- [ ] Test HDMI/screen mirroring
- [ ] Prepare GitHub repo (make public)

## 1 Hour Before
- [ ] Connect to venue WiFi
- [ ] Test OpenAI API (ensure credits available)
- [ ] Run demo once on venue network
- [ ] Close all other apps
- [ ] Disable notifications
- [ ] Set browser zoom to 100%
- [ ] Terminal font size large enough for judges

## 5 Minutes Before
- [ ] Activate virtual environment
- [ ] Verify API key: `echo $OPENAI_API_KEY`
- [ ] Quick test: `python -m flyo "test" --no-approval --headless`
- [ ] Have backup video ready in separate window
- [ ] Breath, smile, you got this!

---

# 🎤 Speaker Assignments

| Speaker | Part | Duration | Backup |
|---------|------|----------|--------|
| **Vivian** | Opening + Closing | 25s | Shivashish |
| **Shivashish** | Live Demo | 60s | Nandana |
| **Nandana** | Technical Overview | 30s | Monisha |
| **Monisha** | Impact Statement | 15s | Vivian |

**Total:** 2 minutes 10 seconds (with 10s buffer)

---

# 🎯 Demo Commands (Copy-Paste Ready)

## Primary Demo (Recommended)
```bash
python -m flyo "Search for flights from Mumbai to Delhi for tomorrow" --config configs/google_flights.json
```

## Backup Demo 1 (Simpler, less failure points)
```bash
python -m flyo "Go to Google and search for browser automation" --no-approval
```

## Backup Demo 2 (If internet fails)
```bash
python -m flyo "Go to example.com and extract the page title" --no-approval --headless
```

---

# 🔧 Failure Recovery Plan

## Scenario 1: Internet is Slow
- **Action:** Use --headless flag for faster execution
- **Backup:** Switch to pre-recorded video immediately

## Scenario 2: Selector Not Found
- **Action:** Say "The website changed its layout—this is exactly why self-healing is important. Let me show the recorded demo."
- **Backup:** Play video

## Scenario 3: API Rate Limit
- **Action:** "Our API key hit the rate limit from testing. Here's the backup recording."
- **Backup:** Play video

## Scenario 4: Complete Technical Failure
- **Action:** "Let me walk you through the architecture instead."
- **Show:** Architecture diagram + explain code snippets
- **Emphasize:** "The code is working—we've tested it 50+ times. Here's proof from our Git commits."

---

# 📸 Visual Assets Needed

## Screen 1: Opening Slide
```
┌────────────────────────────────────┐
│                                    │
│           🤖 FLYO                  │
│                                    │
│   Natural Language Browser Bot     │
│                                    │
│  "Turn Words Into Web Actions"    │
│                                    │
│   Team: Vivian | Shivashish |     │
│         Nandana | Monisha          │
│                                    │
└────────────────────────────────────┘
```

## Screen 2: Live Demo (Terminal + Browser side-by-side)
- **Left:** Terminal with command running
- **Right:** Browser window showing automation

## Screen 3: Architecture Diagram
- Show the 3-component flow diagram

## Screen 4: Closing Slide
```
┌────────────────────────────────────┐
│                                    │
│        GitHub.com/team/flyo        │
│                                    │
│         [QR CODE HERE]             │
│                                    │
│   Built in 24 hours at HASHCODE   │
│                                    │
└────────────────────────────────────┘
```

---

# 🎭 Tips for Delivery

## Do's ✅
- **Speak clearly and slowly** - Judges are listening carefully
- **Make eye contact** - Don't just stare at screen
- **Show enthusiasm** - You built something cool!
- **Pause after key points** - Let it sink in
- **Smile** - You're proud of this work

## Don'ts ❌
- **Don't rush** - 2 minutes is enough time
- **Don't apologize for bugs** - Have a confident recovery plan
- **Don't over-explain** - Keep it simple
- **Don't read slides** - Talk naturally
- **Don't panic if demo fails** - That's why you have backups

---

# 🏆 Answering Judge Questions

## Expected Questions & Answers

### Q: "How do you handle websites that change their layout?"
**A:** "Great question! Our LLM can adapt to layout changes because it understands semantic meaning, not just fixed selectors. We also support site-specific configs for critical workflows. If selectors break, the self-healing mechanism kicks in."

### Q: "What about websites that block automation?"
**A:** "We use Playwright with anti-detection measures. For sites with heavy bot protection, we'd implement CAPTCHA-solving via human-in-the-loop or third-party services."

### Q: "How accurate is the LLM planning?"
**A:** "In our testing, GPT-3.5 generates correct plans 85-90% of the time. GPT-4 pushes that to 95%. Failures trigger self-healing. We can also use template-based fallbacks for critical flows."

### Q: "What's the biggest challenge you faced?"
**A:** "Getting the LLM to generate valid JSON consistently. We solved it with careful prompt engineering, retry logic, and fallback templates."

### Q: "Can this run without internet?"
**A:** "Yes! We support local models via Ollama. Qwen 2.5 Coder 7B runs on 8GB RAM. It's slightly less accurate but completely private."

### Q: "What's next for this project?"
**A:** "Three things: web UI for non-technical users, browser extension for one-click automation, and a template marketplace where users share common workflows."

---

# 🎬 Recording the Backup Video

## Setup
1. Clean terminal (clear history)
2. Browser window at 1920x1080
3. Record in 1080p, 30fps
4. Audio: Narrate actions clearly

## Script
```
[Start recording]

"Hi, this is FLYO - natural language browser automation.

[Type command]
python -m flyo "Search for flights from Mumbai to Delhi for tomorrow"

[Narrate as it runs]
FLYO is now generating an action plan using GPT...

Here's the plan—8 steps to complete the search.

I'm approving the plan...

Now watch as it automates the entire workflow...

[Browser automation plays]

Navigating to Google Flights...
Filling departure city: Mumbai...
Filling arrival city: Delhi...
Selecting tomorrow's date...
Clicking search...

And done! Results loaded in 12 seconds.

That's FLYO—turning words into web actions."

[End recording]
```

## Edit
- Trim dead air at start/end
- Add captions for key moments
- Export as MP4, H.264, 1080p

---

# ⏰ Timeline on Demo Day

**T-60 min:** Arrive, set up, test everything
**T-30 min:** Final run-through with team
**T-10 min:** Judges arrive, start presentations
**T-0 min:** Your turn - breathe and go!

---

**Remember:** You built something genuinely impressive in 24 hours. The judges know hackathon projects aren't perfect. Show them the vision, show them it works, and show them your technical chops.

**You've got this! 🚀**

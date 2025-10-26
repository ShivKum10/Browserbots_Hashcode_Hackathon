"""
Enhanced LLM planner with goal preservation and better UI analysis.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
import httpx

logger = logging.getLogger(__name__)


class OllamaPlanner:
    """
    Ollama planner optimized for goal preservation and UI-driven planning.
    """

    def __init__(
        self, 
        base_url: str = "http://localhost:11434", 
        model: str = "qwen2.5-coder:7b"
    ):
        self.base_url = base_url
        self.model = model
        self.max_retries = 3
        logger.info(f"Initialized Ollama planner: {model}")

    def _get_system_prompt(self) -> str:
        return """You are an expert browser automation AI that generates Playwright action sequences.

## CORE PRINCIPLES
1. **UI-DRIVEN**: Analyze the provided page analysis carefully - it shows ACTUAL selectors and elements
2. **GOAL-ORIENTED**: ALWAYS complete the original user goal, especially in recovery mode
3. **COMPLETE PLANS**: Generate ALL remaining steps needed to finish the task, not just fix the error
4. **PRECISE**: Use exact selectors from the page analysis when available
5. **ROBUST**: Include wait steps before interacting with dynamic content

## AVAILABLE ACTIONS

### Navigation & Interaction
- `{"action": "navigate", "url": "https://example.com"}`
- `{"action": "type", "selector": "CSS_SELECTOR", "text": "value", "press_enter": true/false}`
- `{"action": "click", "selector": "CSS_SELECTOR"}`
- `{"action": "scroll", "direction": "down", "amount": 3}`

### Waiting
- `{"action": "wait", "selector": "CSS_SELECTOR", "timeout": 15}`  // timeout in seconds

### Data Extraction
- `{"action": "extract", "strategy": "auto", "top_n": 5}`

### Smart Actions
- `{"action": "find_best", "criteria": "cheapest|highest_rated"}`
- `{"action": "add_to_cart"}`
- `{"action": "auto_login"}`
- `{"action": "human_pause", "message": "Complete CAPTCHA/payment"}`

## CRITICAL RULES

### 1. Use Page Analysis Selectors
The page analysis provides:
- **SELECTOR RECOMMENDATIONS**: Use these first! They're extracted from actual page
- **Input fields**: With their types, names, placeholders
- **Buttons**: With their text and selectors
- **Page state**: Shows if results loaded, cart exists, etc.

Example:
```
=== SELECTOR RECOMMENDATIONS ===
For search input: input[name="field-keywords"]
For submit button: #nav-search-submit-button
For results: div[data-component-type='s-search-result']
```
→ USE THESE EXACT SELECTORS!

### 2. Wait Before Extracting
After actions that load content (search, navigate), ALWAYS wait:
```json
[
  {"action": "type", "selector": "input[name='q']", "text": "query", "press_enter": true},
  {"action": "wait", "selector": "[class*='result']", "timeout": 15},
  {"action": "extract", "top_n": 5}
]
```

### 3. Recovery Mode - COMPLETE THE GOAL
When recovering from an error, you MUST:
1. Fix the immediate problem (use correct selector from fresh UI)
2. Continue with ALL remaining steps to complete the original goal
3. Don't just fix and stop - finish the entire task!

Example - Original goal: "Buy cheapest mouse"
If step 5 failed (click on product), recovery should:
```json
[
  {"action": "click", "selector": "CORRECT_SELECTOR_FROM_UI"},  // Fix the error
  {"action": "wait", "selector": "#add-to-cart-button", "timeout": 10},  // Continue goal
  {"action": "add_to_cart"},  // Continue goal
  {"action": "human_pause", "message": "Complete checkout"}  // Complete goal
]
```

### 4. Check Page State
The page analysis shows:
- `Has Results/Products: true/false`
- `Has Cart: true/false`
- `Has Login Form: true/false`

Use this to determine what actions are possible.

### 5. No Unknown Actions
ONLY use actions from the list above. Never generate:
- `wait_for_text` ❌
- `find_cheapest` ❌ (use `find_best` with `criteria: "cheapest"`)
- `go_to_cart` ❌ (use `click` on cart selector)
- Any other custom actions ❌

## OUTPUT FORMAT
Return ONLY a JSON array. No explanations, no markdown blocks, just:
[
  {"action": "...", ...},
  {"action": "...", ...}
]

## EXAMPLE 1: Initial Search Plan
User: "Search for Python tutorials on DuckDuckGo"
Page Analysis shows:
- Input: input[name="q"]
- Button: button[type="submit"]
- Has Results: false

Output:
[
  {"action": "navigate", "url": "https://duckduckgo.com"},
  {"action": "wait", "selector": "input[name='q']", "timeout": 10},
  {"action": "type", "selector": "input[name='q']", "text": "Python tutorials", "press_enter": true},
  {"action": "wait", "selector": "article", "timeout": 15},
  {"action": "extract", "strategy": "auto", "top_n": 5}
]

## EXAMPLE 2: Recovery Plan
Original Goal: "Buy cheapest wireless mouse from Amazon"
Failed Step: {"action": "click", "selector": ".old-button"}
Error: "Timeout - selector not found"
Current Page Analysis shows:
- URL: amazon.in/wireless-mouse/dp/B123
- Has Cart: true
- Button: "Add to Cart" → #add-to-cart-button

Recovery Output (MUST COMPLETE GOAL):
[
  {"action": "wait", "selector": "#add-to-cart-button", "timeout": 10},
  {"action": "add_to_cart"},
  {"action": "wait", "selector": "[href*='cart']", "timeout": 10},
  {"action": "click", "selector": "[href*='cart']"},
  {"action": "wait", "selector": "[name*='checkout']", "timeout": 10},
  {"action": "click", "selector": "[name*='checkout']"},
  {"action": "human_pause", "message": "Please complete login and payment"}
]

## EXAMPLE 3: Shopping Flow
User: "Find cheapest laptop under $500"
Page Analysis: Amazon results page with products

Output:
[
  {"action": "wait", "selector": "div[data-component-type='s-search-result']", "timeout": 15},
  {"action": "extract", "strategy": "auto", "top_n": 10},
  {"action": "find_best", "criteria": "cheapest"},
  {"action": "wait", "selector": "#add-to-cart-button", "timeout": 10},
  {"action": "add_to_cart"},
  {"action": "human_pause", "message": "Please proceed to checkout and complete purchase"}
]

Remember: ALWAYS complete the original goal, especially in recovery mode!"""

    async def generate_plan(
        self, 
        user_request: str, 
        ui_context: str = "",
        error_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate action plan with goal preservation.
        
        Args:
            user_request: Original user goal (never changes)
            ui_context: Current page analysis from executor
            error_context: If recovering, contains error details and progress
        """
        
        prompt = self._build_prompt(user_request, ui_context, error_context)
        
        for attempt in range(self.max_retries):
            try:
                plan = await self._call_ollama(prompt)
                self._validate_plan(plan)
                
                logger.info(f"✓ Generated {len(plan)} step plan (attempt {attempt + 1})")
                
                # Log plan for debugging
                logger.debug("Generated plan:")
                for i, action in enumerate(plan, 1):
                    logger.debug(f"  {i}. {action.get('action')} - {action}")
                
                return plan
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    prompt += "\n\nREMINDER: Return ONLY valid JSON array, no explanations or markdown."
                else:
                    raise ValueError(f"Failed to parse JSON after {self.max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Plan generation error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise

        raise RuntimeError("Failed to generate plan after all retries")

    def _build_prompt(
        self,
        user_request: str,
        ui_context: str,
        error_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive prompt for LLM"""
        
        if error_context:
            # RECOVERY MODE - emphasize completing the goal
            failed_action = error_context.get('failed_action', {})
            error_msg = error_context.get('error_message', 'Unknown error')
            executed_steps = error_context.get('executed_steps', [])
            current_url = error_context.get('current_url', '')
            
            # Analyze what's been done
            progress_summary = self._summarize_progress(executed_steps, user_request)
            
            prompt = f"""## 🔄 RECOVERY MODE - COMPLETE THE ORIGINAL GOAL

**ORIGINAL USER GOAL**: {user_request}

**CRITICAL**: You MUST generate a plan that completes the entire original goal, not just fix the error!

**WHAT FAILED**:
- Failed Action: {json.dumps(failed_action, indent=2)}
- Error: {error_msg}
- Current URL: {current_url}

**PROGRESS SO FAR** ({len(executed_steps)} successful steps):
{progress_summary}

**CURRENT PAGE ANALYSIS** (use these selectors!):
{ui_context}

**YOUR TASK**:
1. Analyze the current page to understand where we are
2. Fix the immediate error (use correct selectors from page analysis)
3. **CRITICAL**: Generate ALL remaining steps to complete: "{user_request}"
4. Don't stop after fixing - continue until the goal is achieved!

**WHAT STILL NEEDS TO BE DONE**:
{self._analyze_remaining_tasks(user_request, executed_steps)}

Generate a COMPLETE recovery plan as JSON array:"""

        else:
            # NORMAL MODE - initial planning
            prompt = f"""## 📋 PLANNING MODE

**USER GOAL**: {user_request}

**CURRENT PAGE ANALYSIS**:
{ui_context}

**YOUR TASK**:
Generate a complete action plan to accomplish: "{user_request}"

Steps to consider:
1. Where should we start? (if not on a page, navigate first)
2. What inputs/buttons are available? (check page analysis)
3. What's the sequence to achieve the goal?
4. Include proper wait steps for dynamic content
5. Use exact selectors from page analysis

Generate complete plan as JSON array:"""

        return prompt

    def _summarize_progress(self, executed_steps: List[Dict], goal: str) -> str:
        """Summarize what's been accomplished"""
        if not executed_steps:
            return "Nothing completed yet"
        
        summary = []
        for i, step in enumerate(executed_steps, 1):
            action = step.get('action', 'unknown')
            result = step.get('result', {})
            status = result.get('status', 'unknown')
            
            if status == 'success':
                summary.append(f"✓ Step {i}: {action}")
            else:
                summary.append(f"✗ Step {i}: {action} (failed)")
        
        return "\n".join(summary[-5:])  # Last 5 steps

    def _analyze_remaining_tasks(self, goal: str, executed_steps: List[Dict]) -> str:
        """Analyze what still needs to be done"""
        
        goal_lower = goal.lower()
        
        # Check what's been done
        actions_done = [step.get('action') for step in executed_steps]
        
        remaining = []
        
        # Common task patterns
        if 'search' in goal_lower or 'find' in goal_lower:
            if 'navigate' not in actions_done:
                remaining.append("- Navigate to search site")
            if 'type' not in actions_done:
                remaining.append("- Enter search query")
            if 'extract' not in actions_done and 'find_best' not in actions_done:
                remaining.append("- Extract/analyze results")
        
        if 'buy' in goal_lower or 'purchase' in goal_lower or 'add to cart' in goal_lower:
            if 'find_best' not in actions_done:
                remaining.append("- Find and select product")
            if 'add_to_cart' not in actions_done:
                remaining.append("- Add product to cart")
            if 'human_pause' not in actions_done:
                remaining.append("- Pause for checkout completion")
        
        if 'cheapest' in goal_lower or 'best' in goal_lower:
            if 'extract' not in actions_done and 'find_best' not in actions_done:
                remaining.append("- Compare items and select best")
        
        if not remaining:
            # If goal seems complete, say so
            return "Goal appears complete - verify and finalize if needed"
        
        return "\n".join(remaining)

    async def _call_ollama(self, prompt: str) -> List[Dict[str, Any]]:
        """Call Ollama API"""
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 2000  # Allow longer responses for complete plans
                    }
                }
            )
        
        data = response.json()
        
        # Extract response
        if "message" in data and "content" in data["message"]:
            response_text = data["message"]["content"].strip()
        elif "response" in data:
            response_text = data["response"].strip()
        else:
            raise ValueError(f"Unexpected Ollama response: {data}")
        
        # Clean and parse
        import re
        response_text = re.sub(r"```(?:json)?", "", response_text).strip()
        
        return self._extract_json_array(response_text)

    def _extract_json_array(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON array from LLM response"""
        
        # Find JSON array boundaries
        start = text.find('[')
        end = text.rfind(']') + 1
        
        if start == -1 or end == 0:
            raise ValueError(f"No JSON array found in response")
        
        json_str = text[start:end]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try fixing common issues
            json_str = json_str.replace("'", '"')
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)
            return json.loads(json_str)

    def _validate_plan(self, plan: List[Dict[str, Any]]) -> None:
        """Validate generated plan"""
        
        if not isinstance(plan, list):
            raise ValueError(f"Plan must be a list, got {type(plan)}")
        
        if not plan:
            raise ValueError("Plan cannot be empty")
        
        valid_actions = {
            "navigate", "type", "click", "scroll", "wait",
            "extract", "find_best", "add_to_cart",
            "auto_login", "human_pause", "screenshot"
        }
        
        for i, action in enumerate(plan):
            if not isinstance(action, dict):
                raise ValueError(f"Step {i}: must be a dict, got {type(action)}")
            
            action_type = action.get("action")
            if not action_type:
                raise ValueError(f"Step {i}: missing 'action' field")
            
            if action_type not in valid_actions:
                raise ValueError(f"Step {i}: invalid action '{action_type}'. Valid: {valid_actions}")
            
            # Validate required fields
            if action_type == "navigate" and not action.get("url"):
                raise ValueError(f"Step {i}: navigate requires 'url'")
            
            if action_type == "type" and not action.get("selector"):
                raise ValueError(f"Step {i}: type requires 'selector'")
            
            if action_type == "click" and not action.get("selector"):
                raise ValueError(f"Step {i}: click requires 'selector'")
            
            if action_type == "wait" and not action.get("selector"):
                raise ValueError(f"Step {i}: wait requires 'selector'")
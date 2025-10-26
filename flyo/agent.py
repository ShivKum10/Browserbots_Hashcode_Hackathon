"""
Adaptive FLYO agent with real-time UI re-analysis on errors.
Maintains original goal while adapting to dynamic page changes.
"""

import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from flyo.fsm import AgentState, ExecutionContext
from flyo.planner import OllamaPlanner
from flyo.executor import BrowserExecutor
import json

logger = logging.getLogger(__name__)


class FlyoAgent:
    """
    Adaptive FLYO agent with intelligent error recovery.
    
    Key Features:
    - Real-time UI re-fetching on every plan generation
    - Context-aware error recovery (remembers original goal)
    - Dynamic plan adaptation based on actual page state
    - Smart caching with validation
    """
    
    def __init__(
        self,
        planner: OllamaPlanner,
        require_approval: bool = True,
        headless: bool = False,
        timeout: int = 30000
    ):
        """
        Initialize adaptive agent.
        
        Args:
            planner: Ollama LLM planner instance
            require_approval: Whether to require approval for risky actions
            headless: Run browser in headless mode
            timeout: Action timeout in milliseconds
        """
        self.planner = planner
        self.executor = BrowserExecutor(headless=headless, timeout=timeout)
        self.context = ExecutionContext(user_request="")
        self.require_approval = require_approval
        self.approval_callback: Optional[Callable] = None
        self.log_callback: Optional[Callable] = None
        self.original_goal: str = ""  # Maintain original goal throughout recovery
        
        logger.info("FlyoAgent initialized with adaptive recovery")
    
    def set_approval_callback(self, callback: Callable[[list], bool]) -> None:
        """Set callback for approval flow"""
        self.approval_callback = callback
    
    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for logging/progress updates"""
        self.log_callback = callback
    
    async def execute(self, user_request: str) -> Dict[str, Any]:
        """
        Main execution pipeline with adaptive recovery.
        
        Args:
            user_request: Natural language task description
            
        Returns:
            Execution summary dictionary
        """
        self.context = ExecutionContext(user_request=user_request)
        self.original_goal = user_request  # Store original goal
        
        try:
            # Start browser early
            if not self.executor.browser:
                await self.executor.start()
            
            # Phase 1: Planning (with real-time UI)
            await self._plan_phase()
            
            # Phase 2: Approval (if required)
            if self.require_approval:
                await self._approval_phase()
            
            # Phase 3: Execution
            await self._execution_phase()
            
            # Phase 4: Completion
            self.context.transition(AgentState.COMPLETED, self.log_callback)
            return self._format_result("success")
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            self.context.error_message = str(e)
            self.context.transition(AgentState.ERROR, self.log_callback)
            
            # Attempt adaptive self-healing
            if self.context.increment_heal_attempt():
                try:
                    await self._adaptive_self_heal()
                    return self._format_result("success")
                except Exception as heal_error:
                    logger.error(f"Self-healing failed: {heal_error}")
                    self.context.error_message = f"Original: {e}. Recovery: {heal_error}"
            
            return self._format_result("error")
        
        finally:
            await self.executor.stop()
    
    async def _plan_phase(self) -> None:
        """
        Phase 1: Generate action plan using REAL-TIME UI context.
        Always fetches fresh UI to ensure accuracy.
        """
        self.context.transition(AgentState.PLANNING, self.log_callback)
        
        # Get FRESH page context (uses smart caching internally)
        page_context = await self.executor.get_page_context()
        
        ui_text = page_context.get('ui_text', '')
        cached = page_context.get('cached', False)
        
        logger.info(f"Planning with {'cached' if cached else 'fresh'} UI context ({len(ui_text)} chars)")
        
        # Store context for debugging
        self.context.page_state = ui_text
        
        # Generate plan with UI context
        self.context.action_plan = await self.planner.generate_plan(
            user_request=self.original_goal,
            ui_context=ui_text,
            error_context=None  # No error in initial planning
        )
        
        logger.info(f"Generated plan with {len(self.context.action_plan)} steps")
    
    async def _approval_phase(self) -> None:
        """Phase 2: Check for risky actions and get approval"""
        self.context.transition(AgentState.AWAITING_APPROVAL, self.log_callback)
        
        # Define risky actions
        risky_actions = {
            "submit_form", "proceed_to_checkout", "auto_login",
            "delete", "confirm_purchase"
        }
        
        # Check if plan contains risky actions
        has_risky = any(
            action.get("action") in risky_actions
            for action in self.context.action_plan
        )
        
        if has_risky:
            logger.warning("Plan contains high-risk actions")
            self.context.approval_required = True
            
            if self.approval_callback:
                approved = self.approval_callback(self.context.action_plan)
                if not approved:
                    self.context.transition(AgentState.CANCELLED, self.log_callback)
                    raise Exception("User rejected action plan")
            else:
                logger.warning("No approval callback set, auto-approving")
        
        logger.info("Plan approved for execution")
    
    async def _execution_phase(self) -> None:
        """
        Phase 3: Execute action plan step-by-step.
        Re-fetches UI context on timeout/error for adaptive recovery.
        """
        self.context.transition(AgentState.EXECUTING, self.log_callback)
        
        for idx, action in enumerate(self.context.action_plan):
            self.context.current_step_idx = idx
            
            action_type = action.get("action", "unknown")
            logger.info(f"Step {idx + 1}/{len(self.context.action_plan)}: {action_type}")
            
            try:
                # Execute action
                result = await self.executor.execute_action(action)
                
                # Record step
                self.context.add_executed_step(action, result)
                
                # Check for failure
                if result.get("status") == "failed":
                    error_msg = result.get("error", "Unknown error")
                    self.context.error_message = error_msg
                    
                    # Trigger adaptive recovery
                    raise Exception(f"Step {idx + 1} failed: {error_msg}")
            
            except Exception as e:
                # On ANY error, trigger adaptive recovery
                logger.warning(f"Error at step {idx + 1}: {e}")
                self.context.error_message = str(e)
                raise  # Propagate to main execute() for recovery
        
        logger.info(f"✓ All {len(self.context.action_plan)} steps completed")
    
    async def _adaptive_self_heal(self) -> None:
        """
        Enhanced adaptive self-healing that COMPLETES the original goal.
        """
        self.context.transition(AgentState.SELF_HEALING, self.log_callback)
        
        logger.info(f"🔄 Adaptive recovery attempt {self.context.self_heal_attempts}...")
        logger.info(f"🎯 Original goal: {self.original_goal}")
        
        # 1. FORCE FRESH UI CONTEXT (invalidate cache)
        if self.executor.page:
            self.executor.ui_cache.invalidate(self.executor.page.url)
            logger.info("Invalidated UI cache to force fresh analysis")
        
        page_context = await self.executor.get_page_context(force_fresh=True)
        fresh_ui = page_context.get('ui_text', '')
        current_url = page_context.get('url', '')
        
        logger.info(f"📄 Captured fresh UI: {len(fresh_ui)} chars from {current_url}")
        
        # 2. BUILD COMPREHENSIVE ERROR CONTEXT
        failed_action = (
            self.context.action_plan[self.context.current_step_idx]
            if self.context.current_step_idx < len(self.context.action_plan)
            else {}
        )
        
        error_context = {
            'error_message': self.context.error_message,
            'failed_action': failed_action,
            'executed_steps': self.context.executed_steps,
            'current_url': current_url,
            'remaining_steps': self.context.action_plan[self.context.current_step_idx + 1:]
        }
        
        logger.info(f"📊 Context: {len(self.context.executed_steps)} successful, failed at step {self.context.current_step_idx + 1}")
        
        # 3. GENERATE COMPLETE RECOVERY PLAN
        logger.info(f"🤖 Asking LLM to generate COMPLETE recovery plan for: '{self.original_goal}'")
        
        recovery_plan = await self.planner.generate_plan(
            user_request=self.original_goal,  # ALWAYS use original goal
            ui_context=fresh_ui,
            error_context=error_context
        )
        
        logger.info(f"📋 Generated recovery plan with {len(recovery_plan)} steps")
        
        # Log the recovery plan
        print("\n" + "="*70)
        print("🔄 RECOVERY PLAN")
        print("="*70)
        for i, action in enumerate(recovery_plan, 1):
            print(f"{i}. {action.get('action')} - {action.get('selector', action.get('url', 'N/A'))}")
        print("="*70 + "\n")
        
        # 4. UPDATE CONTEXT AND RETRY
        self.context.action_plan = recovery_plan
        self.context.current_step_idx = 0
        
        # Clear error message
        self.context.error_message = None
        
        # 5. RE-EXECUTE WITH RECOVERY PLAN
        logger.info("▶️  Executing recovery plan...")
        await self._execution_phase()
        
        self.context.transition(AgentState.COMPLETED, self.log_callback)
        logger.info("✓ Adaptive recovery successful - original goal completed")
    
    def _format_result(self, status: str) -> Dict[str, Any]:
        """Format execution result for output"""
        summary = self.context.get_execution_summary()
        summary["status"] = status
        summary["context"] = self.context
        
        # Add cache statistics
        if self.executor.ui_cache:
            summary["cache_stats"] = {
                "entries": len(self.executor.ui_cache.cache),
                "total_hits": sum(
                    entry.get('hit_count', 0)
                    for entry in self.executor.ui_cache.cache.values()
                )
            }
        
        return summary
    
    async def save_credentials(self, domain: str, username: str, password: str) -> None:
        """
        Save credentials for a domain.
        Call this to enable auto_login for future sessions.
        """
        self.executor.credentials.set(domain, username, password)
        logger.info(f"Saved credentials for {domain}")
    
    async def get_current_ui(self) -> str:
        """
        Get current UI context (useful for debugging).
        """
        if self.executor.page:
            context = await self.executor.get_page_context()
            return context.get('ui_text', '')
        return ""
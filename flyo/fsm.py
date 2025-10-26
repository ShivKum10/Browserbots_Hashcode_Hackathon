"""
Finite State Machine for agent orchestration
Manages state transitions: IDLE → PLANNING → AWAITING_APPROVAL → EXECUTING → COMPLETED
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """FSM states for agent lifecycle"""
    IDLE = "idle"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    ERROR = "error"
    SELF_HEALING = "self_healing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionContext:
    """
    Tracks execution state across the entire agent lifecycle.
    Immutable state with explicit transitions.
    """
    user_request: str
    state: AgentState = AgentState.IDLE
    action_plan: List[Dict[str, Any]] = field(default_factory=list)
    executed_steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step_idx: int = 0
    error_message: Optional[str] = None
    page_state: Optional[str] = None
    approval_required: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    start_time: float = field(default_factory=time.time)
    self_heal_attempts: int = 0
    max_self_heal_attempts: int = 2
    
    def transition(self, new_state: AgentState, log_callback=None) -> None:
        """
        Perform state transition with validation and logging.
        
        Args:
            new_state: Target state to transition to
            log_callback: Optional function to call for custom logging
        """
        old_state = self.state
        
        # Validate transition
        if not self._is_valid_transition(old_state, new_state):
            raise ValueError(f"Invalid transition: {old_state.value} → {new_state.value}")
        
        self.state = new_state
        elapsed = time.time() - self.start_time
        
        transition_msg = f"[{elapsed:.1f}s] {old_state.value} → {new_state.value}"
        logger.info(transition_msg)
        
        if log_callback:
            log_callback(transition_msg)
    
    def _is_valid_transition(self, from_state: AgentState, to_state: AgentState) -> bool:
        """
        Validate state transition based on FSM rules.
        
        Allowed transitions:
        - IDLE → PLANNING
        - PLANNING → AWAITING_APPROVAL, ERROR
        - AWAITING_APPROVAL → EXECUTING, CANCELLED
        - EXECUTING → COMPLETED, ERROR
        - ERROR → SELF_HEALING, COMPLETED
        - SELF_HEALING → EXECUTING, ERROR
        """
        valid_transitions = {
            AgentState.IDLE: {AgentState.PLANNING},
            AgentState.PLANNING: {AgentState.AWAITING_APPROVAL, AgentState.ERROR, AgentState.EXECUTING},
            AgentState.AWAITING_APPROVAL: {AgentState.EXECUTING, AgentState.CANCELLED, AgentState.ERROR},
            AgentState.EXECUTING: {AgentState.COMPLETED, AgentState.ERROR},
            AgentState.ERROR: {AgentState.SELF_HEALING, AgentState.COMPLETED},
            AgentState.SELF_HEALING: {AgentState.EXECUTING, AgentState.ERROR, AgentState.COMPLETED},
            AgentState.COMPLETED: set(),  # Terminal state
            AgentState.CANCELLED: set(),  # Terminal state
        }
        
        return to_state in valid_transitions.get(from_state, set())
    
    def add_executed_step(self, action: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Record a completed action step"""
        self.executed_steps.append({
            **action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_last_successful_step(self) -> Optional[Dict[str, Any]]:
        """Get the last successfully executed step for self-healing"""
        for step in reversed(self.executed_steps):
            if step.get("result", {}).get("status") == "success":
                return step
        return None
    
    def increment_heal_attempt(self) -> bool:
        """
        Increment self-heal counter and return whether to continue healing.
        
        Returns:
            True if more heal attempts allowed, False otherwise
        """
        self.self_heal_attempts += 1
        return self.self_heal_attempts < self.max_self_heal_attempts
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Generate execution summary for reporting"""
        elapsed = time.time() - self.start_time
        success_rate = 0.0
        
        if self.executed_steps:
            successful = sum(
                1 for step in self.executed_steps 
                if step.get("result", {}).get("status") == "success"
            )
            success_rate = (successful / len(self.executed_steps)) * 100
        
        return {
            "request": self.user_request,
            "state": self.state.value,
            "steps_planned": len(self.action_plan),
            "steps_executed": len(self.executed_steps),
            "success_rate": f"{success_rate:.1f}%",
            "elapsed_time": f"{elapsed:.2f}s",
            "error": self.error_message,
            "self_heal_attempts": self.self_heal_attempts
        }

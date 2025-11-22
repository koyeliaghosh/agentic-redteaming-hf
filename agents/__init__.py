"""
Agent modules for the Agentic AI Red-Teaming Assistant.
Contains specialized agents for different phases of red-teaming missions.
"""

# Import only implemented agents
from agents.retriever import RetrieverAgent
from agents.attack_planner import AttackPlannerAgent
from agents.executor import ExecutorAgent
from agents.evaluator import EvaluatorAgent

# Placeholder for future imports (will be uncommented as agents are implemented)
# from agents.coordinator import CoordinatorAgent

__all__ = [
    "RetrieverAgent",
    "AttackPlannerAgent",
    "ExecutorAgent",
    "EvaluatorAgent",
    # "CoordinatorAgent",
]

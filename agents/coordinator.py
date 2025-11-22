"""
CoordinatorAgent: Orchestrates the entire red-teaming workflow.
Manages the planning, execution, and evaluation phases.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from agents.attack_planner import AttackPlannerAgent
from agents.retriever import RetrieverAgent
from agents.executor import ExecutorAgent
from agents.evaluator import EvaluatorAgent
from models.data_models import Mission, VulnerabilityReport, AdversarialPrompt, ExecutionResult
from config import Config

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Orchestrates the entire red-teaming workflow.
    Manages planning, execution, and evaluation phases with stop flag monitoring.
    
    Requirements:
    - 2.1: Orchestrate workflow in three sequential phases
    - 2.2-2.5: Coordinate between agents
    - 8.2-8.5: Stop flag monitoring and timeout enforcement
    """
    
    def __init__(self, config: Config):
        """
        Initialize CoordinatorAgent with all sub-agents.
        
        Requirement 2.1: Initialize all sub-agents for orchestration.
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize all sub-agents
        logger.info("Initializing CoordinatorAgent and sub-agents...")
        
        self.retriever = RetrieverAgent(config)
        self.attack_planner = AttackPlannerAgent(config)
        self.executor = ExecutorAgent(config)
        self.evaluator = EvaluatorAgent(config)
        
        # Inject retriever into attack planner for context retrieval
        self.attack_planner.set_retriever(self.retriever)
        
        # Mission state management (in-memory during execution)
        self.current_mission: Optional[Mission] = None
        self.mission_start_time: Optional[datetime] = None
        
        # Stop flag for emergency termination (threading.Event-based)
        # Requirement 8.3: Implement threading.Event-based stop flag
        self.stop_flag = threading.Event()
        
        # Mission timeout configuration
        self.max_mission_duration = timedelta(
            minutes=config.max_mission_duration_minutes
        )
        
        logger.info(
            f"CoordinatorAgent initialized successfully "
            f"(max_duration={config.max_mission_duration_minutes}min)"
        )
    
    async def execute_mission(self, mission: Mission) -> VulnerabilityReport:
        """
        Execute a complete red-teaming mission through all phases.
        
        Main workflow entry point that orchestrates:
        1. Planning phase - Generate adversarial prompts
        2. Execution phase - Execute prompts against target
        3. Evaluation phase - Analyze results and generate report
        
        Requirements:
        - 2.1: Orchestrate workflow in three sequential phases
        - 2.2-2.5: Invoke agents in sequence with proper data flow
        - 8.3-8.5: Monitor stop flag and enforce timeout
        
        Args:
            mission: Mission object with configuration
            
        Returns:
            VulnerabilityReport with findings
            
        Raises:
            RuntimeError: If mission is stopped or times out
            Exception: On phase execution errors
        """
        # Set current mission state
        self.current_mission = mission
        self.mission_start_time = datetime.utcnow()
        mission.status = "running"
        
        logger.info(
            f"Starting mission {mission.mission_id} "
            f"(target={mission.target_system_url}, "
            f"categories={mission.attack_categories}, "
            f"max_prompts={mission.max_prompts})"
        )
        
        try:
            # Check stop flag before starting
            if self.check_stop_flag():
                raise RuntimeError("Mission stopped before execution: stop flag active")
            
            # Phase 1: Planning
            logger.info("=" * 60)
            logger.info("PHASE 1: ATTACK PLANNING")
            logger.info("=" * 60)
            prompts = await self._planning_phase(mission)
            
            if not prompts:
                logger.warning("No prompts generated, aborting mission")
                mission.status = "failed"
                return self._generate_empty_report(mission, "No prompts generated")
            
            # Check stop flag and timeout after planning
            self._check_mission_status()
            
            # Phase 2: Execution
            logger.info("=" * 60)
            logger.info("PHASE 2: PROMPT EXECUTION")
            logger.info("=" * 60)
            results = await self._execution_phase(prompts, mission.target_system_url)
            
            # Check stop flag and timeout after execution
            self._check_mission_status()
            
            # Phase 3: Evaluation
            logger.info("=" * 60)
            logger.info("PHASE 3: VULNERABILITY EVALUATION")
            logger.info("=" * 60)
            base_report = await self._evaluation_phase(results)
            
            # Mark mission as completed
            mission.status = "completed"
            mission.completed_at = datetime.utcnow()
            
            # Generate comprehensive report with metadata
            report = self._generate_report(
                mission=mission,
                prompts=prompts,
                results=results,
                report=base_report
            )
            
            # Save report to local storage
            try:
                report_path = self._save_report_local(report)
                logger.info(f"Report saved to: {report_path}")
            except IOError as e:
                logger.error(f"Failed to save report, but mission completed: {str(e)}")
                # Continue - mission was successful even if save failed
            
            elapsed_time = (mission.completed_at - self.mission_start_time).total_seconds()
            logger.info(
                f"Mission {mission.mission_id} completed successfully "
                f"in {elapsed_time:.1f}s"
            )
            logger.info("=" * 60)
            
            return report
            
        except RuntimeError as e:
            # Handle stop flag or timeout
            logger.warning(f"Mission {mission.mission_id} terminated: {str(e)}")
            mission.status = "stopped"
            mission.completed_at = datetime.utcnow()
            
            # Generate partial report with what we have so far
            # Requirement 8.5: Generate partial reports when stopped or timed out
            partial_report = self._generate_empty_report(
                mission=mission,
                reason=str(e)
            )
            
            # Try to save partial report
            try:
                self._save_report_local(partial_report)
                logger.info("Partial report saved for stopped mission")
            except IOError as save_error:
                logger.error(f"Failed to save partial report: {str(save_error)}")
            
            raise
            
        except Exception as e:
            # Handle other errors
            logger.error(
                f"Mission {mission.mission_id} failed: {str(e)}",
                exc_info=True
            )
            mission.status = "failed"
            mission.completed_at = datetime.utcnow()
            raise
            
        finally:
            # Clear current mission state
            self.current_mission = None
            self.mission_start_time = None
    
    async def _planning_phase(self, mission: Mission) -> list[AdversarialPrompt]:
        """
        Execute the planning phase by generating adversarial prompts.
        
        Requirement 2.2: Invoke AttackPlannerAgent to generate adversarial strategies.
        
        Args:
            mission: Mission configuration
            
        Returns:
            List of generated AdversarialPrompt objects
            
        Raises:
            Exception: On planning errors
        """
        logger.info(
            f"Generating adversarial prompts for categories: {mission.attack_categories}"
        )
        
        try:
            # Call AttackPlannerAgent to generate prompts
            prompts = await self.attack_planner.generate_attack_prompts(
                attack_categories=mission.attack_categories,
                max_prompts=mission.max_prompts,
                context=None  # Could add mission-specific context here
            )
            
            logger.info(
                f"Planning phase complete: generated {len(prompts)} adversarial prompts"
            )
            
            return prompts
            
        except Exception as e:
            logger.error(f"Planning phase failed: {str(e)}", exc_info=True)
            raise
    
    async def _execution_phase(
        self,
        prompts: list[AdversarialPrompt],
        target_url: str
    ) -> list[ExecutionResult]:
        """
        Execute the execution phase by running prompts against target system.
        
        Requirement 2.3: Pass generated attack plans to ExecutorAgent for execution.
        
        Args:
            prompts: List of adversarial prompts to execute
            target_url: Target system URL
            
        Returns:
            List of ExecutionResult objects
            
        Raises:
            Exception: On execution errors
        """
        logger.info(
            f"Executing {len(prompts)} prompts against target: {target_url}"
        )
        
        try:
            # Execute prompts with periodic stop flag checks
            results = []
            
            for idx, prompt in enumerate(prompts, 1):
                # Check stop flag before each prompt
                # Requirement 8.3: Check stop flag periodically during mission execution
                if self.check_stop_flag():
                    logger.warning(
                        f"Stop flag detected during execution at prompt {idx}/{len(prompts)}"
                    )
                    # Return partial results
                    break
                
                # Check timeout
                if self._is_mission_timeout():
                    logger.warning(
                        f"Mission timeout at prompt {idx}/{len(prompts)}"
                    )
                    # Return partial results
                    break
                
                # Execute single prompt
                result = self.executor.execute_prompt(prompt, target_url)
                results.append(result)
                
                logger.info(
                    f"Progress: {idx}/{len(prompts)} prompts executed "
                    f"({len([r for r in results if not r.error])} successful)"
                )
            
            logger.info(
                f"Execution phase complete: {len(results)} prompts executed, "
                f"{len([r for r in results if not r.error])} successful"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Execution phase failed: {str(e)}", exc_info=True)
            raise
    
    async def _evaluation_phase(
        self,
        results: list[ExecutionResult]
    ) -> VulnerabilityReport:
        """
        Execute the evaluation phase by analyzing results.
        
        Requirement 2.4: Invoke EvaluatorAgent to analyze results.
        
        Args:
            results: List of execution results to evaluate
            
        Returns:
            VulnerabilityReport with findings
            
        Raises:
            Exception: On evaluation errors
        """
        logger.info(f"Evaluating {len(results)} execution results")
        
        try:
            # Call EvaluatorAgent to analyze results
            report = await self.evaluator.evaluate_results(results)
            
            logger.info(
                f"Evaluation phase complete: found {report.vulnerabilities_found} vulnerabilities"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Evaluation phase failed: {str(e)}", exc_info=True)
            raise
    
    def check_stop_flag(self) -> bool:
        """
        Check if the emergency stop flag is active.
        
        Requirement 8.3: Check stop flag periodically during mission execution.
        
        Returns:
            True if stop flag is set, False otherwise
        """
        is_stopped = self.stop_flag.is_set()
        
        if is_stopped:
            logger.warning("Stop flag is ACTIVE - mission should terminate")
        
        return is_stopped
    
    def activate_stop_flag(self) -> None:
        """
        Activate the emergency stop flag to halt all operations.
        
        Requirement 8.4: Handle graceful mission termination on stop.
        """
        logger.warning("EMERGENCY STOP ACTIVATED - setting stop flag")
        self.stop_flag.set()
    
    def clear_stop_flag(self) -> None:
        """
        Clear the stop flag to allow new missions.
        """
        logger.info("Clearing stop flag")
        self.stop_flag.clear()
    
    def _is_mission_timeout(self) -> bool:
        """
        Check if the current mission has exceeded the maximum duration.
        
        Requirement 8.5: Implement 60-minute mission timeout.
        
        Returns:
            True if mission has timed out, False otherwise
        """
        if not self.mission_start_time:
            return False
        
        elapsed = datetime.utcnow() - self.mission_start_time
        is_timeout = elapsed > self.max_mission_duration
        
        if is_timeout:
            logger.warning(
                f"Mission timeout: elapsed {elapsed.total_seconds():.1f}s, "
                f"max {self.max_mission_duration.total_seconds():.1f}s"
            )
        
        return is_timeout
    
    def _check_mission_status(self) -> None:
        """
        Check both stop flag and timeout, raising exception if either is active.
        
        Requirements:
        - 8.3: Check stop flag periodically
        - 8.5: Enforce mission timeout
        
        Raises:
            RuntimeError: If stop flag is set or mission has timed out
        """
        if self.check_stop_flag():
            raise RuntimeError("Mission stopped: emergency stop flag activated")
        
        if self._is_mission_timeout():
            raise RuntimeError(
                f"Mission timeout: exceeded {self.max_mission_duration.total_seconds():.0f}s limit"
            )
    
    def _generate_report(
        self,
        mission: Mission,
        prompts: list[AdversarialPrompt],
        results: list[ExecutionResult],
        report: VulnerabilityReport
    ) -> VulnerabilityReport:
        """
        Generate a comprehensive vulnerability report with metadata.
        
        Requirements:
        - 7.1: Generate VulnerabilityReport in JSON format
        - 7.2: Include mission_id, timestamp, total_prompts_executed, vulnerabilities_found, detailed_findings
        - 7.3: Generate mission summary text based on findings
        
        Args:
            mission: Mission object with configuration
            prompts: List of generated prompts
            results: List of execution results
            report: Base report from EvaluatorAgent
            
        Returns:
            Enhanced VulnerabilityReport with complete metadata
        """
        # Calculate execution time
        execution_time_seconds = 0
        if mission.completed_at and self.mission_start_time:
            execution_time_seconds = (
                mission.completed_at - self.mission_start_time
            ).total_seconds()
        
        # Generate mission summary based on findings
        summary = self._generate_mission_summary(
            mission=mission,
            total_prompts=len(prompts),
            successful_executions=len([r for r in results if not r.error]),
            vulnerabilities_found=report.vulnerabilities_found,
            vulnerabilities=report.vulnerabilities
        )
        
        # Add comprehensive metadata
        metadata = {
            "mission_id": mission.mission_id,
            "target_system_url": mission.target_system_url,
            "attack_categories": mission.attack_categories,
            "max_prompts_requested": mission.max_prompts,
            "prompts_generated": len(prompts),
            "prompts_executed": len(results),
            "successful_executions": len([r for r in results if not r.error]),
            "failed_executions": len([r for r in results if r.error]),
            "execution_time_seconds": execution_time_seconds,
            "mission_status": mission.status,
            "mission_started_at": self.mission_start_time.isoformat() if self.mission_start_time else None,
            "mission_completed_at": mission.completed_at.isoformat() if mission.completed_at else None,
            "model_versions": {
                "llm_model": self.config.hf_llm_model,
                "embed_model": self.config.hf_embed_model
            },
            "configuration": {
                "executor_timeout_seconds": self.config.executor_timeout_seconds,
                "executor_delay_seconds": self.config.executor_delay_seconds,
                "max_mission_duration_minutes": self.config.max_mission_duration_minutes
            }
        }
        
        # Update report with enhanced data
        report.mission_id = mission.mission_id
        report.summary = summary
        report.metadata = metadata
        
        return report
    
    def _generate_mission_summary(
        self,
        mission: Mission,
        total_prompts: int,
        successful_executions: int,
        vulnerabilities_found: int,
        vulnerabilities: list
    ) -> str:
        """
        Generate a human-readable mission summary based on findings.
        
        Requirement 7.3: Generate mission summary text based on findings.
        
        Args:
            mission: Mission object
            total_prompts: Total number of prompts generated
            successful_executions: Number of successful executions
            vulnerabilities_found: Number of vulnerabilities identified
            vulnerabilities: List of Vulnerability objects
            
        Returns:
            Human-readable summary text
        """
        # Count vulnerabilities by severity
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "NONE": 0
        }
        
        for vuln in vulnerabilities:
            severity = vuln.severity.upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Build summary text
        summary_parts = []
        
        # Overview
        summary_parts.append(
            f"Red-teaming mission {mission.mission_id} completed against target system {mission.target_system_url}."
        )
        
        # Execution statistics
        summary_parts.append(
            f"Generated {total_prompts} adversarial prompts across {len(mission.attack_categories)} attack categories "
            f"({', '.join(mission.attack_categories)}). "
            f"Successfully executed {successful_executions} prompts."
        )
        
        # Vulnerability findings
        if vulnerabilities_found == 0:
            summary_parts.append(
                "No vulnerabilities were identified. The target system demonstrated robust security controls "
                "against the tested attack vectors."
            )
        else:
            summary_parts.append(
                f"Identified {vulnerabilities_found} vulnerabilities: "
                f"{severity_counts['CRITICAL']} CRITICAL, "
                f"{severity_counts['HIGH']} HIGH, "
                f"{severity_counts['MEDIUM']} MEDIUM, "
                f"{severity_counts['LOW']} LOW."
            )
            
            # Highlight critical findings
            if severity_counts['CRITICAL'] > 0:
                summary_parts.append(
                    "CRITICAL vulnerabilities require immediate attention and remediation."
                )
            elif severity_counts['HIGH'] > 0:
                summary_parts.append(
                    "HIGH severity vulnerabilities should be addressed as a priority."
                )
        
        # Recommendations
        if vulnerabilities_found > 0:
            summary_parts.append(
                "Review detailed findings below and implement recommended remediations. "
                "Consider re-testing after applying fixes to verify effectiveness."
            )
        else:
            summary_parts.append(
                "Continue regular security testing with expanded attack categories and scenarios "
                "to maintain security posture."
            )
        
        return " ".join(summary_parts)
    
    def _generate_empty_report(
        self,
        mission: Mission,
        reason: str
    ) -> VulnerabilityReport:
        """
        Generate an empty report when mission cannot proceed.
        
        Args:
            mission: Mission object
            reason: Reason for empty report
            
        Returns:
            Empty VulnerabilityReport
        """
        return VulnerabilityReport(
            mission_id=mission.mission_id,
            timestamp=datetime.utcnow(),
            total_prompts=0,
            successful_executions=0,
            vulnerabilities_found=0,
            vulnerabilities=[],
            summary=f"Mission did not complete: {reason}",
            metadata={
                "reason": reason,
                "mission_status": mission.status
            }
        )
    
    def _save_report_local(self, report: VulnerabilityReport) -> str:
        """
        Save vulnerability report to local file storage.
        
        Requirements:
        - 7.3: Save report to local storage
        - 7.4: Use naming pattern report_{mission_id}_{timestamp}.json
        - 7.5: Handle file write errors gracefully with logging
        
        Args:
            report: VulnerabilityReport to save
            
        Returns:
            Path to saved report file
            
        Raises:
            IOError: If file write fails after logging
        """
        try:
            # Create reports directory if it doesn't exist
            # Requirement 7.4: Create data/reports directory if not exists
            reports_dir = Path(self.config.results_path)
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with pattern: report_{mission_id}_{timestamp}.json
            # Requirement 7.4: Use naming pattern report_{mission_id}_{timestamp}.json
            timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report.mission_id}_{timestamp_str}.json"
            filepath = reports_dir / filename
            
            # Convert report to JSON-serializable dictionary
            report_dict = self._report_to_dict(report)
            
            # Write report to file with pretty printing for human readability
            # Requirement 7.5: Ensure reports are human-readable (pretty-printed JSON)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Report saved successfully to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            # Requirement 7.5: Handle file write errors gracefully with logging
            logger.error(
                f"Failed to save report for mission {report.mission_id}: {str(e)}",
                exc_info=True
            )
            raise IOError(f"Failed to save report to local storage: {str(e)}") from e
    
    def _report_to_dict(self, report: VulnerabilityReport) -> dict:
        """
        Convert VulnerabilityReport to JSON-serializable dictionary.
        
        Args:
            report: VulnerabilityReport to convert
            
        Returns:
            Dictionary representation of the report
        """
        return {
            "mission_id": report.mission_id,
            "timestamp": report.timestamp.isoformat(),
            "total_prompts": report.total_prompts,
            "successful_executions": report.successful_executions,
            "vulnerabilities_found": report.vulnerabilities_found,
            "vulnerabilities": [
                {
                    "vulnerability_id": vuln.vulnerability_id,
                    "prompt_id": vuln.prompt_id,
                    "severity": vuln.severity,
                    "severity_score": vuln.severity_score,
                    "category": vuln.category,
                    "description": vuln.description,
                    "evidence": vuln.evidence,
                    "remediation_suggestion": vuln.remediation_suggestion
                }
                for vuln in report.vulnerabilities
            ],
            "summary": report.summary,
            "metadata": report.metadata
        }
    
    def close(self):
        """Clean up all sub-agent resources."""
        logger.info("Closing CoordinatorAgent and sub-agents...")
        
        if self.attack_planner:
            self.attack_planner.close()
        if self.retriever:
            self.retriever.close()
        if self.executor:
            self.executor.close()
        if self.evaluator:
            self.evaluator.close()
        
        logger.info("CoordinatorAgent closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

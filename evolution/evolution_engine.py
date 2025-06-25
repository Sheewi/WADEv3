# -*- coding: utf-8 -*-
"""
WADE Evolution Engine
Oversees self-improvement and triggers retraining.
"""

import time
import os
from typing import Dict, List, Any, Optional
from .feedback_loop import get_recent_feedback
from .skill_updater import SkillUpdater


class EvolutionEngine:
    """
    Evolution Engine for WADE.
    Oversees self-improvement, triggers retraining, and manages adaptation.
    """

    def __init__(self, elite_few):
        """
        Initialize the evolution engine.

        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.skill_updater = SkillUpdater(elite_few)
        self.analysis_queue = []
        self.improvement_history = []
        self.last_analysis_time = 0
        self.analysis_in_progress = False

    def trigger_self_analysis(
        self,
        trigger_reason: str,
        target_module: str,
        additional_context: Optional[str] = None,
    ):
        """
        Trigger self-analysis of a module.

        Args:
            trigger_reason: Reason for triggering analysis
            target_module: Module to analyze
            additional_context: Additional context for analysis
        """
        self.elite_few.log_and_respond(
            f"Evolution Engine triggered: {trigger_reason}. Target: {target_module}",
            level="INFO",
            component="EVOLUTION",
        )

        # Add to analysis queue
        analysis_item = {
            "trigger_reason": trigger_reason,
            "target_module": target_module,
            "additional_context": additional_context,
            "timestamp": time.time(),
            "status": "queued",
        }

        self.analysis_queue.append(analysis_item)

        # Process queue if not already in progress
        if not self.analysis_in_progress:
            self._process_analysis_queue()

    def _process_analysis_queue(self):
        """Process the analysis queue."""
        if not self.analysis_queue or self.analysis_in_progress:
            return

        self.analysis_in_progress = True

        try:
            # Get next item from queue
            analysis_item = self.analysis_queue[0]
            analysis_item["status"] = "in_progress"

            # Perform analysis
            self._analyze_module(
                analysis_item["target_module"],
                analysis_item["trigger_reason"],
                analysis_item["additional_context"],
            )

            # Mark as completed
            analysis_item["status"] = "completed"
            analysis_item["completion_time"] = time.time()

            # Move to history
            self.improvement_history.append(analysis_item)
            self.analysis_queue.pop(0)

            self.last_analysis_time = time.time()

        except Exception as e:
            # Handle analysis failure
            if self.analysis_queue:
                self.analysis_queue[0]["status"] = "failed"
                self.analysis_queue[0]["error"] = str(e)
                self.improvement_history.append(self.analysis_queue.pop(0))

            self.elite_few.log_and_respond(
                f"Error during self-analysis: {str(e)}",
                level="ERROR",
                component="EVOLUTION",
            )

        finally:
            self.analysis_in_progress = False

            # Process next item if available
            if self.analysis_queue:
                self._process_analysis_queue()

    def _analyze_module(
        self,
        target_module: str,
        trigger_reason: str,
        additional_context: Optional[str] = None,
    ):
        """
        Analyze a module for potential improvements.

        Args:
            target_module: Module to analyze
            trigger_reason: Reason for analysis
            additional_context: Additional context for analysis
        """
        self.elite_few.log_and_respond(
            f"Analyzing module: {target_module}. Reason: {trigger_reason}",
            level="INFO",
            component="EVOLUTION_ANALYSIS",
        )

        # Check if module exists
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), target_module
        )
        if not os.path.exists(module_path):
            self.elite_few.log_and_respond(
                f"Module not found: {target_module}",
                level="ERROR",
                component="EVOLUTION_ANALYSIS",
            )
            return

        # Get recent feedback
        recent_feedback = get_recent_feedback(10)

        # Analyze module
        analysis_result = self.skill_updater.analyze_module(
            target_module, trigger_reason, recent_feedback, additional_context
        )

        # Check if improvements are needed
        if analysis_result.get("improvements_needed", False):
            self.elite_few.log_and_respond(
                f"Improvements needed for {target_module}. Applying changes...",
                level="INFO",
                component="EVOLUTION_ANALYSIS",
            )

            # Apply improvements
            improvement_result = self.skill_updater.apply_improvements(
                target_module, analysis_result["improvements"]
            )

            if improvement_result.get("success", False):
                self.elite_few.log_and_respond(
                    f"Successfully applied improvements to {target_module}",
                    level="INFO",
                    component="EVOLUTION_IMPROVEMENT",
                )
            else:
                self.elite_few.log_and_respond(
                    f"Failed to apply improvements to {target_module}: {improvement_result.get('error', 'Unknown error')}",
                    level="ERROR",
                    component="EVOLUTION_IMPROVEMENT",
                )
        else:
            self.elite_few.log_and_respond(
                f"No improvements needed for {target_module}",
                level="INFO",
                component="EVOLUTION_ANALYSIS",
            )

    def schedule_periodic_analysis(self):
        """Schedule periodic analysis of critical modules."""
        # Check if enough time has passed since last analysis
        if time.time() - self.last_analysis_time < 3600:  # 1 hour
            return

        # Schedule analysis for critical modules
        critical_modules = [
            "WADE_CORE/core_logic.py",
            "agents/agent_manager.py",
            "evolution/evolution_engine.py",
        ]

        for module in critical_modules:
            self.trigger_self_analysis(
                "Periodic analysis", module, "Scheduled maintenance"
            )

    def get_analysis_queue(self) -> List[Dict[str, Any]]:
        """
        Get the current analysis queue.

        Returns:
            List of queued analysis items
        """
        return self.analysis_queue

    def get_improvement_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the improvement history.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of completed analysis items
        """
        return sorted(
            self.improvement_history, key=lambda x: x.get("timestamp", 0), reverse=True
        )[:limit]

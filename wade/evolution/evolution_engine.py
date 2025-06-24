# -*- coding: utf-8 -*-
"""
WADE Evolution Engine
Provides self-improvement capabilities.
"""

import os
import sys
import time
import threading
import json
from typing import Dict, List, Any, Optional

class EvolutionEngine:
    """
    Evolution Engine for WADE.
    Provides self-improvement capabilities.
    """
    
    def __init__(self, elite_few):
        """
        Initialize the evolution engine.
        
        Args:
            elite_few: Reference to the EliteFew instance
        """
        self.elite_few = elite_few
        self.is_evolving = False
        self.evolution_thread = None
        self.evolution_interval = 3600  # seconds
        self.evolution_stats = {
            'generations': 0,
            'last_evolution': None,
            'improvements': 0,
            'failures': 0
        }
        
        # Load evolution configuration
        self._load_config()
    
    def _load_config(self):
        """Load evolution configuration."""
        config = self.elite_few.wade_core.config.get('evolution', {})
        
        self.is_enabled = config.get('enabled', True)
        self.feedback_threshold = config.get('feedback_threshold', 0.6)
        self.learning_rate = config.get('learning_rate', 0.1)
        self.evolution_interval = config.get('adaptation_interval', 3600)
        self.max_generations = config.get('max_generations', 100)
        self.mutation_rate = config.get('mutation_rate', 0.05)
    
    def start_evolution(self):
        """Start the evolution process."""
        if not self.is_enabled:
            self.elite_few.log_and_respond(
                "Evolution is disabled in configuration.",
                level="WARN",
                component="EVOLUTION"
            )
            return False
        
        if self.is_evolving:
            return True
        
        # Start evolution thread
        self.is_evolving = True
        self.evolution_thread = threading.Thread(target=self._evolution_loop)
        self.evolution_thread.daemon = True
        self.evolution_thread.start()
        
        self.elite_few.log_and_respond(
            "Evolution process started.",
            level="INFO",
            component="EVOLUTION"
        )
        
        return True
    
    def stop_evolution(self):
        """Stop the evolution process."""
        if not self.is_evolving:
            return True
        
        self.is_evolving = False
        if self.evolution_thread:
            self.evolution_thread.join(timeout=5)
            self.evolution_thread = None
        
        self.elite_few.log_and_respond(
            "Evolution process stopped.",
            level="INFO",
            component="EVOLUTION"
        )
        
        return True
    
    def _evolution_loop(self):
        """Main evolution loop."""
        while self.is_evolving:
            try:
                # Perform evolution
                self._evolve()
                
                # Update stats
                self.evolution_stats['generations'] += 1
                self.evolution_stats['last_evolution'] = time.time()
                
                # Sleep for evolution interval
                time.sleep(self.evolution_interval)
                
            except Exception as e:
                self.elite_few.log_and_respond(
                    f"Error in evolution loop: {str(e)}",
                    level="ERROR",
                    component="EVOLUTION"
                )
                time.sleep(60)  # Sleep for a minute before retrying
    
    def _evolve(self):
        """Perform one evolution cycle."""
        self.elite_few.log_and_respond(
            "Starting evolution cycle...",
            level="INFO",
            component="EVOLUTION"
        )
        
        # Get feedback from feedback loop
        from evolution.feedback_loop import get_feedback_stats, analyze_feedback_patterns
        
        feedback_stats = get_feedback_stats()
        feedback_patterns = analyze_feedback_patterns()
        
        # Check if evolution is needed
        if feedback_stats.get('success_rate', 1.0) >= self.feedback_threshold:
            self.elite_few.log_and_respond(
                f"Success rate ({feedback_stats.get('success_rate', 1.0):.2f}) above threshold ({self.feedback_threshold}). No evolution needed.",
                level="INFO",
                component="EVOLUTION"
            )
            return
        
        # Identify areas for improvement
        improvement_areas = self._identify_improvement_areas(feedback_patterns)
        
        if not improvement_areas:
            self.elite_few.log_and_respond(
                "No improvement areas identified.",
                level="INFO",
                component="EVOLUTION"
            )
            return
        
        # Apply improvements
        success_count = 0
        for area in improvement_areas:
            if self._apply_improvement(area):
                success_count += 1
        
        # Update stats
        self.evolution_stats['improvements'] += success_count
        self.evolution_stats['failures'] += len(improvement_areas) - success_count
        
        self.elite_few.log_and_respond(
            f"Evolution cycle completed. Applied {success_count}/{len(improvement_areas)} improvements.",
            level="INFO",
            component="EVOLUTION"
        )
    
    def _identify_improvement_areas(self, feedback_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify areas for improvement based on feedback patterns.
        
        Args:
            feedback_patterns: Feedback pattern analysis
            
        Returns:
            List of improvement areas
        """
        improvement_areas = []
        
        # Check if patterns were found
        if not feedback_patterns.get('patterns_found', False):
            return []
        
        # Check recurring failures
        for failure in feedback_patterns.get('recurring_failures', []):
            # Extract module name from failure message
            module_name = self._extract_module_from_failure(failure.get('message', ''))
            
            if module_name:
                improvement_areas.append({
                    'module': module_name,
                    'type': 'recurring_failure',
                    'message': failure.get('message', ''),
                    'count': failure.get('count', 0),
                    'priority': min(1.0, failure.get('count', 0) / 10.0)  # Priority based on count (max 1.0)
                })
        
        # Sort by priority (highest first)
        improvement_areas.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        return improvement_areas
    
    def _extract_module_from_failure(self, message: str) -> Optional[str]:
        """
        Extract module name from failure message.
        
        Args:
            message: Failure message
            
        Returns:
            Module name or None if not found
        """
        # Simple extraction based on common patterns
        if 'in module' in message:
            parts = message.split('in module')
            if len(parts) > 1:
                module_part = parts[1].strip()
                return module_part.split()[0].strip()
        
        # Check for file paths
        if '.py' in message:
            parts = message.split('.py')
            if len(parts) > 1:
                file_part = parts[0].split('/')[-1]
                return f"{file_part}.py"
        
        return None
    
    def _apply_improvement(self, improvement_area: Dict[str, Any]) -> bool:
        """
        Apply an improvement to a module.
        
        Args:
            improvement_area: Improvement area information
            
        Returns:
            True if improvement was applied successfully, False otherwise
        """
        module = improvement_area.get('module')
        
        if not module:
            return False
        
        try:
            # Use skill updater to analyze and improve module
            from evolution.skill_updater import SkillUpdater
            
            skill_updater = SkillUpdater(self.elite_few)
            
            # Analyze module
            analysis = skill_updater.analyze_module(
                module,
                "evolution_cycle",
                [],  # No recent feedback needed here
                f"Triggered by evolution cycle due to recurring failure: {improvement_area.get('message', '')}"
            )
            
            if not analysis.get('improvements_needed', False):
                self.elite_few.log_and_respond(
                    f"No improvements needed for module {module}.",
                    level="INFO",
                    component="EVOLUTION"
                )
                return False
            
            # Apply improvements
            result = skill_updater.apply_improvements(module, analysis.get('improvements', []))
            
            if result.get('success', False):
                self.elite_few.log_and_respond(
                    f"Successfully applied improvements to module {module}.",
                    level="SUCCESS",
                    component="EVOLUTION"
                )
                return True
            else:
                self.elite_few.log_and_respond(
                    f"Failed to apply improvements to module {module}: {result.get('error', 'Unknown error')}",
                    level="ERROR",
                    component="EVOLUTION"
                )
                return False
                
        except Exception as e:
            self.elite_few.log_and_respond(
                f"Error applying improvement to module {module}: {str(e)}",
                level="ERROR",
                component="EVOLUTION"
            )
            return False
    
    def get_evolution_stats(self) -> Dict[str, Any]:
        """
        Get evolution statistics.
        
        Returns:
            Dictionary with evolution statistics
        """
        return self.evolution_stats
    
    def is_evolution_enabled(self) -> bool:
        """
        Check if evolution is enabled.
        
        Returns:
            True if evolution is enabled, False otherwise
        """
        return self.is_enabled
    
    def set_evolution_enabled(self, enabled: bool):
        """
        Enable or disable evolution.
        
        Args:
            enabled: Whether to enable evolution
        """
        self.is_enabled = enabled
        
        if enabled and not self.is_evolving:
            self.start_evolution()
        elif not enabled and self.is_evolving:
            self.stop_evolution()
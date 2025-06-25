# -*- coding: utf-8 -*-
"""
WADE Monk Agent
Observes and analyzes behavior patterns.
"""

import os
import sys
import time
import json
import logging
import re
from typing import Dict, List, Any, Optional

from agents.base_agent import BaseAgent


class MonkAgent(BaseAgent):
    """
    Monk Agent for WADE.
    Observes and analyzes behavior patterns.
    """

    def __init__(self, agent_id: str, agent_type: str, elite_few):
        """
        Initialize the monk agent.

        Args:
            agent_id: Unique ID for the agent
            agent_type: Type of agent
            elite_few: Reference to the EliteFew instance
        """
        super().__init__(agent_id, agent_type, elite_few)

        # Initialize monk-specific state
        self.observations = []
        self.patterns = {}
        self.observation_threshold = 0.7  # Confidence threshold for observations
        self.analysis_depth = 3  # Depth of analysis

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load agent configuration."""
        config = (
            self.elite_few.wade_core.config.get("agents", {})
            .get("agent_config", {})
            .get("monk", {})
        )

        if config:
            self.observation_threshold = config.get(
                "observation_threshold", self.observation_threshold
            )
            self.analysis_depth = config.get("analysis_depth", self.analysis_depth)

    def process_task(self, task: str) -> Optional[str]:
        """
        Process a task.

        Args:
            task: Task to process

        Returns:
            Response or None if task couldn't be processed
        """
        # Update state
        self.update_state({"tasks_processed": self.state["tasks_processed"] + 1})

        try:
            # Check if task is a monk-specific command
            if task.lower().startswith("monk:"):
                return self._process_monk_command(task[5:].strip())

            # Check if task is an observation request
            if re.search(r"(?i)(?:observe|analyze|pattern|behavior)", task):
                return self._process_observation_request(task)

            # Add task to observations
            self._add_observation(task)

            # Check if we have any insights about this task
            insight = self._get_insight(task)

            if insight:
                self.update_state(
                    {"successful_tasks": self.state["successful_tasks"] + 1}
                )
                return insight

            # No specific response for this task
            return None

        except Exception as e:
            self.logger.error(f"Error processing task: {e}")

            self.update_state({"failed_tasks": self.state["failed_tasks"] + 1})

            return None

    def _process_monk_command(self, command: str) -> str:
        """
        Process a monk-specific command.

        Args:
            command: Command to process

        Returns:
            Response
        """
        # Check for status command
        if command.lower() == "status":
            return self._get_status()

        # Check for patterns command
        if command.lower() == "patterns":
            return self._get_patterns()

        # Check for observations command
        if command.lower() == "observations":
            return self._get_observations()

        # Check for analyze command
        if command.lower().startswith("analyze "):
            target = command[8:].strip()
            return self._analyze(target)

        # Unknown command
        return f"Unknown monk command: {command}"

    def _get_status(self) -> str:
        """
        Get agent status.

        Returns:
            Status information
        """
        return f"""
Monk Agent Status:
- Agent ID: {self.agent_id}
- Active: {'Yes' if self.is_active() else 'No'}
- Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.state['created']))}
- Last Active: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.state['last_active']))}
- Tasks Processed: {self.state['tasks_processed']}
- Successful Tasks: {self.state['successful_tasks']}
- Failed Tasks: {self.state['failed_tasks']}
- Observations: {len(self.observations)}
- Patterns: {len(self.patterns)}
- Observation Threshold: {self.observation_threshold}
- Analysis Depth: {self.analysis_depth}
"""

    def _get_patterns(self) -> str:
        """
        Get detected patterns.

        Returns:
            Pattern information
        """
        if not self.patterns:
            return "No patterns detected yet."

        result = "Detected Patterns:\n"

        for pattern_type, patterns in self.patterns.items():
            result += f"\n{pattern_type.capitalize()}:\n"

            for pattern, info in patterns.items():
                result += f"- {pattern} (confidence: {info['confidence']:.2f}, occurrences: {info['occurrences']})\n"

        return result

    def _get_observations(self) -> str:
        """
        Get recent observations.

        Returns:
            Observation information
        """
        if not self.observations:
            return "No observations yet."

        result = "Recent Observations:\n"

        # Show last 10 observations
        for i, obs in enumerate(self.observations[-10:]):
            result += f"{i+1}. {obs['text']} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(obs['timestamp']))})\n"

        return result

    def _analyze(self, target: str) -> str:
        """
        Analyze a target.

        Args:
            target: Target to analyze

        Returns:
            Analysis results
        """
        # Check if target is a pattern type
        if target in self.patterns:
            return self._analyze_pattern_type(target)

        # Check if target is a specific pattern
        for pattern_type, patterns in self.patterns.items():
            if target in patterns:
                return self._analyze_pattern(pattern_type, target)

        # Check if target is a recent observation
        try:
            index = int(target) - 1
            if 0 <= index < len(self.observations):
                return self._analyze_observation(self.observations[index])
        except ValueError:
            pass

        # Analyze as free text
        return self._analyze_text(target)

    def _analyze_pattern_type(self, pattern_type: str) -> str:
        """
        Analyze a pattern type.

        Args:
            pattern_type: Pattern type to analyze

        Returns:
            Analysis results
        """
        if pattern_type not in self.patterns:
            return f"No patterns of type '{pattern_type}' found."

        patterns = self.patterns[pattern_type]

        result = f"Analysis of {pattern_type} patterns:\n\n"

        # Sort patterns by confidence
        sorted_patterns = sorted(
            patterns.items(), key=lambda x: x[1]["confidence"], reverse=True
        )

        for pattern, info in sorted_patterns:
            result += f"- {pattern} (confidence: {info['confidence']:.2f}, occurrences: {info['occurrences']})\n"

            if "examples" in info:
                result += "  Examples:\n"
                for example in info["examples"][:3]:  # Show up to 3 examples
                    result += f"  - {example}\n"

            if "insights" in info:
                result += "  Insights:\n"
                for insight in info["insights"]:
                    result += f"  - {insight}\n"

            result += "\n"

        return result

    def _analyze_pattern(self, pattern_type: str, pattern: str) -> str:
        """
        Analyze a specific pattern.

        Args:
            pattern_type: Pattern type
            pattern: Pattern to analyze

        Returns:
            Analysis results
        """
        if (
            pattern_type not in self.patterns
            or pattern not in self.patterns[pattern_type]
        ):
            return f"Pattern '{pattern}' not found."

        info = self.patterns[pattern_type][pattern]

        result = f"Analysis of pattern '{pattern}':\n\n"
        result += f"- Type: {pattern_type}\n"
        result += f"- Confidence: {info['confidence']:.2f}\n"
        result += f"- Occurrences: {info['occurrences']}\n"

        if "first_observed" in info:
            result += f"- First Observed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['first_observed']))}\n"

        if "last_observed" in info:
            result += f"- Last Observed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(info['last_observed']))}\n"

        if "examples" in info:
            result += "\nExamples:\n"
            for example in info["examples"]:
                result += f"- {example}\n"

        if "insights" in info:
            result += "\nInsights:\n"
            for insight in info["insights"]:
                result += f"- {insight}\n"

        return result

    def _analyze_observation(self, observation: Dict[str, Any]) -> str:
        """
        Analyze an observation.

        Args:
            observation: Observation to analyze

        Returns:
            Analysis results
        """
        result = f"Analysis of observation: {observation['text']}\n\n"
        result += f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(observation['timestamp']))}\n"

        # Check for patterns in this observation
        matching_patterns = []

        for pattern_type, patterns in self.patterns.items():
            for pattern, info in patterns.items():
                if "examples" in info and observation["text"] in info["examples"]:
                    matching_patterns.append((pattern_type, pattern))

        if matching_patterns:
            result += "\nMatching Patterns:\n"
            for pattern_type, pattern in matching_patterns:
                result += f"- [{pattern_type}] {pattern}\n"

        # Generate insights
        insights = self._generate_insights(observation["text"])

        if insights:
            result += "\nInsights:\n"
            for insight in insights:
                result += f"- {insight}\n"

        return result

    def _analyze_text(self, text: str) -> str:
        """
        Analyze free text.

        Args:
            text: Text to analyze

        Returns:
            Analysis results
        """
        result = f"Analysis of text: {text}\n\n"

        # Check for similar observations
        similar_observations = self._find_similar_observations(text)

        if similar_observations:
            result += "Similar Observations:\n"
            for obs in similar_observations:
                result += f"- {obs['text']} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(obs['timestamp']))})\n"

        # Check for matching patterns
        matching_patterns = self._find_matching_patterns(text)

        if matching_patterns:
            result += "\nMatching Patterns:\n"
            for pattern_type, pattern in matching_patterns:
                result += f"- [{pattern_type}] {pattern}\n"

        # Generate insights
        insights = self._generate_insights(text)

        if insights:
            result += "\nInsights:\n"
            for insight in insights:
                result += f"- {insight}\n"

        return result

    def _process_observation_request(self, task: str) -> str:
        """
        Process an observation request.

        Args:
            task: Task to process

        Returns:
            Response
        """
        # Check for pattern request
        if re.search(r"(?i)(?:what|any|show|tell).*(?:pattern|behavior)", task):
            return self._get_patterns()

        # Check for observation request
        if re.search(r"(?i)(?:what|any|show|tell).*(?:observe|observation)", task):
            return self._get_observations()

        # Check for analysis request
        if re.search(r"(?i)(?:analyze|analysis)", task):
            # Extract target
            match = re.search(
                r'(?i)(?:analyze|analysis).*?(?:of|on|about)?\s+["\']?([^"\']+)["\']?',
                task,
            )

            if match:
                target = match.group(1).strip()
                return self._analyze(target)

        # Generic response
        return "I am a Monk agent. I observe and analyze behavior patterns. You can ask me about patterns, observations, or request analysis."

    def _add_observation(self, text: str):
        """
        Add an observation.

        Args:
            text: Observation text
        """
        # Create observation
        observation = {"text": text, "timestamp": time.time()}

        # Add to observations
        self.observations.append(observation)

        # Limit observations to 1000
        if len(self.observations) > 1000:
            self.observations.pop(0)

        # Update patterns
        self._update_patterns(observation)

    def _update_patterns(self, observation: Dict[str, Any]):
        """
        Update patterns based on a new observation.

        Args:
            observation: New observation
        """
        text = observation["text"]

        # Update word patterns
        self._update_word_patterns(text)

        # Update phrase patterns
        self._update_phrase_patterns(text)

        # Update command patterns
        self._update_command_patterns(text)

    def _update_word_patterns(self, text: str):
        """
        Update word patterns.

        Args:
            text: Text to analyze
        """
        # Initialize word patterns if not exists
        if "word" not in self.patterns:
            self.patterns["word"] = {}

        # Extract words
        words = re.findall(r"\b\w+\b", text.lower())

        # Update word patterns
        for word in words:
            if len(word) < 3:
                continue  # Skip short words

            if word not in self.patterns["word"]:
                self.patterns["word"][word] = {
                    "confidence": 0.1,
                    "occurrences": 1,
                    "examples": [text],
                    "first_observed": time.time(),
                    "last_observed": time.time(),
                }
            else:
                pattern = self.patterns["word"][word]
                pattern["occurrences"] += 1
                pattern["confidence"] = min(0.9, pattern["confidence"] + 0.05)
                pattern["last_observed"] = time.time()

                if text not in pattern["examples"]:
                    pattern["examples"].append(text)

                    # Limit examples to 10
                    if len(pattern["examples"]) > 10:
                        pattern["examples"].pop(0)

    def _update_phrase_patterns(self, text: str):
        """
        Update phrase patterns.

        Args:
            text: Text to analyze
        """
        # Initialize phrase patterns if not exists
        if "phrase" not in self.patterns:
            self.patterns["phrase"] = {}

        # Extract phrases (2-4 words)
        words = re.findall(r"\b\w+\b", text.lower())

        for n in range(2, 5):
            if len(words) < n:
                continue

            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])

                if phrase not in self.patterns["phrase"]:
                    self.patterns["phrase"][phrase] = {
                        "confidence": 0.1,
                        "occurrences": 1,
                        "examples": [text],
                        "first_observed": time.time(),
                        "last_observed": time.time(),
                    }
                else:
                    pattern = self.patterns["phrase"][phrase]
                    pattern["occurrences"] += 1
                    pattern["confidence"] = min(0.9, pattern["confidence"] + 0.05)
                    pattern["last_observed"] = time.time()

                    if text not in pattern["examples"]:
                        pattern["examples"].append(text)

                        # Limit examples to 10
                        if len(pattern["examples"]) > 10:
                            pattern["examples"].pop(0)

    def _update_command_patterns(self, text: str):
        """
        Update command patterns.

        Args:
            text: Text to analyze
        """
        # Initialize command patterns if not exists
        if "command" not in self.patterns:
            self.patterns["command"] = {}

        # Check if text starts with a command word
        command_words = [
            "show",
            "list",
            "get",
            "find",
            "search",
            "create",
            "add",
            "update",
            "delete",
            "remove",
        ]

        first_word = text.lower().split()[0] if text else ""

        if first_word in command_words:
            command = first_word

            if command not in self.patterns["command"]:
                self.patterns["command"][command] = {
                    "confidence": 0.1,
                    "occurrences": 1,
                    "examples": [text],
                    "first_observed": time.time(),
                    "last_observed": time.time(),
                }
            else:
                pattern = self.patterns["command"][command]
                pattern["occurrences"] += 1
                pattern["confidence"] = min(0.9, pattern["confidence"] + 0.05)
                pattern["last_observed"] = time.time()

                if text not in pattern["examples"]:
                    pattern["examples"].append(text)

                    # Limit examples to 10
                    if len(pattern["examples"]) > 10:
                        pattern["examples"].pop(0)

    def _get_insight(self, task: str) -> Optional[str]:
        """
        Get insight for a task.

        Args:
            task: Task to get insight for

        Returns:
            Insight or None if no insight available
        """
        # Check if we have enough observations
        if len(self.observations) < 5:
            return None

        # Generate insights
        insights = self._generate_insights(task)

        if not insights:
            return None

        # Return first insight
        return f"Monk Insight: {insights[0]}"

    def _generate_insights(self, text: str) -> List[str]:
        """
        Generate insights for text.

        Args:
            text: Text to generate insights for

        Returns:
            List of insights
        """
        insights = []

        # Check for recurring patterns
        matching_patterns = self._find_matching_patterns(text)

        if matching_patterns:
            for pattern_type, pattern in matching_patterns:
                info = self.patterns[pattern_type][pattern]

                if info["confidence"] >= self.observation_threshold:
                    if pattern_type == "word":
                        insights.append(
                            f"The word '{pattern}' appears frequently in your interactions."
                        )
                    elif pattern_type == "phrase":
                        insights.append(
                            f"The phrase '{pattern}' appears frequently in your interactions."
                        )
                    elif pattern_type == "command":
                        insights.append(f"You often use the '{pattern}' command.")

        # Check for similar observations
        similar_observations = self._find_similar_observations(text)

        if similar_observations and len(similar_observations) >= 3:
            insights.append("You've made similar requests multiple times.")

        return insights

    def _find_matching_patterns(self, text: str) -> List[tuple]:
        """
        Find patterns that match text.

        Args:
            text: Text to match

        Returns:
            List of (pattern_type, pattern) tuples
        """
        matching_patterns = []

        # Check word patterns
        if "word" in self.patterns:
            words = re.findall(r"\b\w+\b", text.lower())

            for word in words:
                if word in self.patterns["word"]:
                    matching_patterns.append(("word", word))

        # Check phrase patterns
        if "phrase" in self.patterns:
            text_lower = text.lower()

            for phrase in self.patterns["phrase"]:
                if phrase in text_lower:
                    matching_patterns.append(("phrase", phrase))

        # Check command patterns
        if "command" in self.patterns:
            first_word = text.lower().split()[0] if text else ""

            if first_word in self.patterns["command"]:
                matching_patterns.append(("command", first_word))

        return matching_patterns

    def _find_similar_observations(self, text: str) -> List[Dict[str, Any]]:
        """
        Find observations similar to text.

        Args:
            text: Text to find similar observations for

        Returns:
            List of similar observations
        """
        similar_observations = []

        # Simple similarity: check if text contains or is contained in observation
        for obs in self.observations:
            obs_text = obs["text"].lower()
            text_lower = text.lower()

            if obs_text in text_lower or text_lower in obs_text:
                similar_observations.append(obs)

        return similar_observations

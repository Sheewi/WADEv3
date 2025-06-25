#!/usr/bin/env python3
"""
Wade CrewAI - Enhanced Adaptive Learning System
"""

import json
import sqlite3
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import pickle
from pathlib import Path


class UserProfiler:
    """Analyzes user behavior patterns and preferences"""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.db_path = memory_dir / "user_profile.db"
        self._init_database()

    def _init_database(self):
        """Initialize user profile database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    request_type TEXT,
                    complexity TEXT,
                    agents_used TEXT,
                    success_rating INTEGER,
                    response_time REAL,
                    user_feedback TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    preference_type TEXT PRIMARY KEY,
                    preference_value TEXT,
                    confidence_score REAL,
                    last_updated REAL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_usage (
                    tool_name TEXT,
                    usage_count INTEGER,
                    success_rate REAL,
                    avg_rating REAL,
                    last_used REAL,
                    PRIMARY KEY (tool_name)
                )
            """
            )

    def analyze_user_patterns(self) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        with sqlite3.connect(self.db_path) as conn:
            # Get recent interactions
            recent_interactions = conn.execute(
                """
                SELECT * FROM user_interactions
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """,
                (datetime.now().timestamp() - 30 * 24 * 3600,),
            ).fetchall()  # Last 30 days

            if not recent_interactions:
                return self._default_profile()

            # Analyze patterns
            request_types = [row[2] for row in recent_interactions]
            complexities = [row[3] for row in recent_interactions]
            success_ratings = [
                row[5] for row in recent_interactions if row[5] is not None
            ]

            patterns = {
                "preferred_request_types": Counter(request_types).most_common(5),
                "preferred_complexity": Counter(complexities).most_common(1)[0][0],
                "avg_success_rating": (
                    np.mean(success_ratings) if success_ratings else 3.0
                ),
                "total_interactions": len(recent_interactions),
                "active_days": len(
                    set(
                        [
                            datetime.fromtimestamp(row[1]).date()
                            for row in recent_interactions
                        ]
                    )
                ),
                "preferred_agents": self._analyze_agent_preferences(
                    recent_interactions
                ),
                "time_patterns": self._analyze_time_patterns(recent_interactions),
            }

            return patterns

    def _analyze_agent_preferences(self, interactions: List) -> Dict[str, float]:
        """Analyze which agents user prefers"""
        agent_usage = defaultdict(int)
        agent_success = defaultdict(list)

        for interaction in interactions:
            agents = json.loads(interaction[4]) if interaction[4] else []
            rating = interaction[5] if interaction[5] else 3

            for agent in agents:
                agent_usage[agent] += 1
                agent_success[agent].append(rating)

        # Calculate preference scores (usage * avg_success)
        preferences = {}
        for agent, usage in agent_usage.items():
            avg_success = np.mean(agent_success[agent])
            preferences[agent] = usage * (avg_success / 5.0)  # Normalize to 0-1

        return preferences

    def _analyze_time_patterns(self, interactions: List) -> Dict[str, Any]:
        """Analyze when user is most active"""
        hours = [datetime.fromtimestamp(row[1]).hour for row in interactions]
        days = [datetime.fromtimestamp(row[1]).weekday() for row in interactions]

        return {
            "peak_hours": Counter(hours).most_common(3),
            "active_days": Counter(days).most_common(7),
            "session_length_avg": self._calculate_avg_session_length(interactions),
        }

    def _calculate_avg_session_length(self, interactions: List) -> float:
        """Calculate average session length"""
        if len(interactions) < 2:
            return 0.0

        sessions = []
        current_session_start = interactions[-1][1]  # Most recent first

        for i in range(len(interactions) - 1):
            time_gap = interactions[i][1] - interactions[i + 1][1]
            if time_gap > 1800:  # 30 minutes gap = new session
                sessions.append(interactions[i + 1][1] - current_session_start)
                current_session_start = interactions[i][1]

        return np.mean(sessions) if sessions else 0.0

    def _default_profile(self) -> Dict[str, Any]:
        """Default profile for new users"""
        return {
            "preferred_request_types": [("exploit", 1), ("tool", 1), ("recon", 1)],
            "preferred_complexity": "moderate",
            "avg_success_rating": 3.0,
            "total_interactions": 0,
            "active_days": 0,
            "preferred_agents": {"commander": 1.0, "exploit": 0.8, "tool": 0.8},
            "time_patterns": {
                "peak_hours": [],
                "active_days": [],
                "session_length_avg": 0.0,
            },
        }

    def update_interaction(self, interaction_data: Dict[str, Any]):
        """Update user interaction data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_interactions
                (timestamp, request_type, complexity, agents_used, success_rating, response_time, user_feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    interaction_data.get("timestamp", datetime.now().timestamp()),
                    interaction_data.get("request_type", "unknown"),
                    interaction_data.get("complexity", "moderate"),
                    json.dumps(interaction_data.get("agents_used", [])),
                    interaction_data.get("success_rating"),
                    interaction_data.get("response_time"),
                    interaction_data.get("user_feedback"),
                ),
            )


class AdaptiveTaskPlanner:
    """Plans tasks based on user preferences and success patterns"""

    def __init__(self, user_profiler: UserProfiler):
        self.user_profiler = user_profiler
        self.success_patterns = {}

    def plan_optimal_approach(
        self, user_input: str, base_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Plan optimal approach based on user patterns"""
        user_patterns = self.user_profiler.analyze_user_patterns()

        # Adjust agent selection based on user preferences
        preferred_agents = user_patterns.get("preferred_agents", {})
        required_agents = base_plan.get("required_agents", [])

        # Add preferred agents if relevant
        for agent, score in preferred_agents.items():
            if score > 0.7 and agent not in required_agents:
                if self._is_agent_relevant(agent, user_input):
                    required_agents.append(agent)

        # Adjust complexity based on user preference
        preferred_complexity = user_patterns.get("preferred_complexity", "moderate")
        if (
            base_plan.get("complexity") == "simple"
            and preferred_complexity == "complex"
        ):
            base_plan["complexity"] = "moderate"  # Gradual increase

        # Add personalization metadata
        base_plan.update(
            {
                "required_agents": required_agents,
                "user_preferences_applied": True,
                "confidence_score": self._calculate_confidence(user_patterns),
                "personalization_level": self._get_personalization_level(user_patterns),
            }
        )

        return base_plan

    def _is_agent_relevant(self, agent: str, user_input: str) -> bool:
        """Check if agent is relevant to current request"""
        agent_keywords = {
            "recon": ["scan", "discover", "enumerate", "reconnaissance"],
            "exploit": ["exploit", "attack", "penetrate", "hack", "payload"],
            "tool": ["create", "build", "develop", "script", "tool"],
            "research": ["research", "investigate", "find", "intelligence"],
        }

        keywords = agent_keywords.get(agent, [])
        return any(keyword in user_input.lower() for keyword in keywords)

    def _calculate_confidence(self, user_patterns: Dict[str, Any]) -> float:
        """Calculate confidence in personalization"""
        interactions = user_patterns.get("total_interactions", 0)
        if interactions < 5:
            return 0.3
        elif interactions < 20:
            return 0.6
        else:
            return 0.9

    def _get_personalization_level(self, user_patterns: Dict[str, Any]) -> str:
        """Determine level of personalization to apply"""
        interactions = user_patterns.get("total_interactions", 0)
        if interactions < 5:
            return "minimal"
        elif interactions < 20:
            return "moderate"
        else:
            return "high"


class ResponsePersonalizer:
    """Personalizes responses based on user preferences"""

    def __init__(self, user_profiler: UserProfiler):
        self.user_profiler = user_profiler

    def personalize_response(
        self, base_response: str, user_patterns: Dict[str, Any]
    ) -> str:
        """Personalize response based on user patterns"""

        # Adjust Wade's personality based on user preferences
        preferred_complexity = user_patterns.get("preferred_complexity", "moderate")
        avg_rating = user_patterns.get("avg_success_rating", 3.0)

        # Add personalized intro based on user history
        personalized_intro = self._get_personalized_intro(user_patterns)

        # Adjust technical detail level
        if preferred_complexity == "simple":
            # Add more explanations
            base_response = self._add_explanations(base_response)
        elif preferred_complexity == "complex":
            # Add more technical details
            base_response = self._add_technical_details(base_response)

        # Add personalized recommendations
        recommendations = self._get_personalized_recommendations(user_patterns)

        # Combine all elements
        personalized_response = f"{personalized_intro}\n\n{base_response}"

        if recommendations:
            personalized_response += f"\n\n{recommendations}"

        return personalized_response

    def _get_personalized_intro(self, user_patterns: Dict[str, Any]) -> str:
        """Get personalized intro based on user history"""
        interactions = user_patterns.get("total_interactions", 0)

        if interactions == 0:
            return "Welcome to the family! Let's get you started with some serious firepower."
        elif interactions < 10:
            return "Good to see you back, family. Ready for another ride?"
        elif interactions < 50:
            return "Family, you're becoming quite the expert. Let's push it to the next level."
        else:
            return "My most trusted family member is back. Time to show them what we're really capable of."

    def _add_explanations(self, response: str) -> str:
        """Add explanations for users who prefer simpler responses"""
        # This would add more detailed explanations
        # For now, just add a note
        return (
            response
            + "\n\n💡 Need more details on any part? Just ask - family helps family understand."
        )

    def _add_technical_details(self, response: str) -> str:
        """Add technical details for advanced users"""
        # This would add more technical depth
        return (
            response
            + "\n\n🔧 Want to dive deeper into the technical implementation? I can break down every detail."
        )

    def _get_personalized_recommendations(self, user_patterns: Dict[str, Any]) -> str:
        """Get personalized recommendations"""
        preferred_types = user_patterns.get("preferred_request_types", [])

        if not preferred_types:
            return ""

        top_type = preferred_types[0][0] if preferred_types else "exploit"

        recommendations = {
            "exploit": "💀 Based on your history, you might also want to try advanced payload encoding or multi-stage exploits.",
            "tool": "🛠️ Since you love building tools, consider creating a custom framework that combines multiple techniques.",
            "recon": "🔍 Your reconnaissance skills are solid. Ready to try some advanced OSINT or dark web research?",
            "research": "📊 Your research game is strong. Want to explore some automated intelligence correlation?",
        }

        return recommendations.get(top_type, "")


class AdaptiveLearningSystem:
    """Main adaptive learning system that coordinates all components"""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.user_profiler = UserProfiler(memory_dir)
        self.task_planner = AdaptiveTaskPlanner(self.user_profiler)
        self.response_personalizer = ResponsePersonalizer(self.user_profiler)

    def adapt_to_user(
        self, user_input: str, base_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt crew behavior to user preferences"""

        # Get user patterns
        user_patterns = self.user_profiler.analyze_user_patterns()

        # Plan optimal approach
        adapted_plan = self.task_planner.plan_optimal_approach(user_input, base_plan)

        # Add user patterns for response personalization
        adapted_plan["user_patterns"] = user_patterns

        return adapted_plan

    def personalize_response(self, response: str, user_patterns: Dict[str, Any]) -> str:
        """Personalize response based on user patterns"""
        return self.response_personalizer.personalize_response(response, user_patterns)

    def record_interaction(self, interaction_data: Dict[str, Any]):
        """Record interaction for learning"""
        self.user_profiler.update_interaction(interaction_data)

    def get_user_insights(self) -> Dict[str, Any]:
        """Get insights about user behavior"""
        return self.user_profiler.analyze_user_patterns()


# Integration with existing crew system
def integrate_adaptive_learning():
    """Integration function to add adaptive learning to existing crew"""

    # This would be added to crew.py
    adaptive_system = AdaptiveLearningSystem(Path.home() / ".wade" / "memory")

    # Modify the process_request method to use adaptive learning
    def enhanced_process_request(
        self, user_input: str, context: Dict[str, Any] = None
    ) -> str:
        # Original analysis
        task_plan = self._analyze_request(user_input, context)

        # Apply adaptive learning
        adapted_plan = adaptive_system.adapt_to_user(user_input, task_plan)

        # Create tasks with adapted plan
        tasks = self._create_tasks(adapted_plan, user_input)

        # Execute crew
        self.crew.tasks = tasks
        result = self.crew.kickoff()

        # Personalize response
        if "user_patterns" in adapted_plan:
            result = adaptive_system.personalize_response(
                result, adapted_plan["user_patterns"]
            )

        # Record interaction for learning
        adaptive_system.record_interaction(
            {
                "timestamp": time.time(),
                "request_type": (
                    adapted_plan.get("keywords", ["unknown"])[0]
                    if adapted_plan.get("keywords")
                    else "unknown"
                ),
                "complexity": adapted_plan.get("complexity", "moderate"),
                "agents_used": adapted_plan.get("required_agents", []),
                "response_time": time.time() - start_time,
                "user_input": user_input,
                "response": result,
            }
        )

        return result

    return enhanced_process_request

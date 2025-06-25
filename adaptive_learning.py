#!/usr/bin/env python3
"""
Wade CrewAI - Enhanced Adaptive Learning System with Self-Evolution Capabilities
"""

import json
import sqlite3
import numpy as np
import logging
import os
import re
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AdaptiveLearning")


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
        """Default profile for new users with enhanced security focus"""
        return {
            "preferred_request_types": [("exploit", 1), ("tool", 1), ("recon", 1), ("coding", 1), ("security", 1)],
            "preferred_complexity": "moderate",
            "avg_success_rating": 3.0,
            "total_interactions": 0,
            "active_days": 0,
            "preferred_agents": {"commander": 1.0, "exploit": 0.8, "tool": 0.8, "security": 0.9, "coder": 0.7},
            "security_focus_level": 0.7,  # High security focus
            "technical_expertise": "intermediate",
            "kali_linux_usage": 0.6,  # Moderate Kali Linux usage
            "preferred_tools": [("nmap", 1), ("metasploit", 1), ("burpsuite", 1), ("wireshark", 1)],
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


class SelfEvolutionEngine:
    """Implements self-evolution capabilities for the WADE system"""
    
    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.evolution_db_path = memory_dir / "evolution.db"
        self.learning_rate = 0.05  # Controls how quickly the system evolves
        self.observation_threshold = 10  # Minimum observations before evolution
        self._init_database()
        
    def _init_database(self):
        """Initialize evolution database"""
        with sqlite3.connect(self.evolution_db_path) as conn:
            # Store evolution parameters
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evolution_parameters (
                    parameter_name TEXT PRIMARY KEY,
                    parameter_value REAL,
                    last_updated REAL,
                    update_count INTEGER
                )
            """)
            
            # Store observations for learning
            conn.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    observation_type TEXT,
                    observation_data TEXT,
                    impact_score REAL
                )
            """)
            
            # Store evolution history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evolution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    parameter_name TEXT,
                    old_value REAL,
                    new_value REAL,
                    reason TEXT
                )
            """)
            
            # Initialize default parameters if not exists
            self._init_default_parameters(conn)
    
    def _init_default_parameters(self, conn):
        """Initialize default evolution parameters"""
        default_params = {
            "security_focus": 0.8,  # High focus on security
            "technical_depth": 0.7,  # Moderately high technical detail
            "kali_integration": 0.9,  # Strong Kali Linux integration
            "creativity": 0.6,  # Moderate creativity
            "autonomy": 0.7,  # Moderate autonomy
            "learning_rate": 0.05,  # Base learning rate
            "risk_tolerance": 0.6,  # Moderate risk tolerance
            "multi_agent_coordination": 0.8,  # Strong multi-agent capabilities
            "memory_utilization": 0.7,  # Good memory utilization
            "adaptation_speed": 0.6,  # Moderate adaptation speed
        }
        
        for param, value in default_params.items():
            conn.execute("""
                INSERT OR IGNORE INTO evolution_parameters 
                (parameter_name, parameter_value, last_updated, update_count) 
                VALUES (?, ?, ?, ?)
            """, (param, value, datetime.now().timestamp(), 0))
    
    def record_observation(self, observation_type: str, data: Dict[str, Any], impact: float = 0.0):
        """Record an observation for learning"""
        try:
            with sqlite3.connect(self.evolution_db_path) as conn:
                conn.execute("""
                    INSERT INTO observations 
                    (timestamp, observation_type, observation_data, impact_score) 
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().timestamp(),
                    observation_type,
                    json.dumps(data),
                    impact
                ))
            logger.info(f"Recorded {observation_type} observation with impact {impact}")
            return True
        except Exception as e:
            logger.error(f"Error recording observation: {str(e)}")
            return False
    
    def evolve_system(self) -> Dict[str, Any]:
        """Evolve the system based on observations"""
        try:
            with sqlite3.connect(self.evolution_db_path) as conn:
                # Get current parameters
                current_params = {}
                for row in conn.execute("SELECT parameter_name, parameter_value FROM evolution_parameters"):
                    current_params[row[0]] = row[1]
                
                # Get recent observations
                recent_obs = conn.execute("""
                    SELECT observation_type, observation_data, impact_score 
                    FROM observations 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (datetime.now().timestamp() - 30 * 24 * 3600,)).fetchall()
                
                if len(recent_obs) < self.observation_threshold:
                    logger.info(f"Not enough observations for evolution: {len(recent_obs)}/{self.observation_threshold}")
                    return {"evolved": False, "reason": "Not enough observations"}
                
                # Process observations and determine evolution
                evolution_changes = self._process_observations(recent_obs, current_params)
                
                # Apply changes and record history
                for param, change in evolution_changes.items():
                    if param in current_params:
                        old_value = current_params[param]
                        new_value = max(0.0, min(1.0, old_value + change['delta']))
                        
                        conn.execute("""
                            UPDATE evolution_parameters 
                            SET parameter_value = ?, last_updated = ?, update_count = update_count + 1
                            WHERE parameter_name = ?
                        """, (new_value, datetime.now().timestamp(), param))
                        
                        conn.execute("""
                            INSERT INTO evolution_history 
                            (timestamp, parameter_name, old_value, new_value, reason) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            datetime.now().timestamp(),
                            param,
                            old_value,
                            new_value,
                            change['reason']
                        ))
                        
                        logger.info(f"Evolved parameter {param}: {old_value} -> {new_value}, reason: {change['reason']}")
                
                return {
                    "evolved": bool(evolution_changes),
                    "changes": len(evolution_changes),
                    "parameters": evolution_changes
                }
        except Exception as e:
            logger.error(f"Error during system evolution: {str(e)}")
            return {"evolved": False, "error": str(e)}
    
    def _process_observations(self, observations, current_params) -> Dict[str, Dict[str, Any]]:
        """Process observations and determine parameter changes"""
        changes = {}
        
        # Group observations by type
        obs_by_type = defaultdict(list)
        for obs_type, obs_data, impact in observations:
            obs_by_type[obs_type].append((json.loads(obs_data), impact))
        
        # Process security-related observations
        if 'security_query' in obs_by_type:
            security_obs = obs_by_type['security_query']
            if len(security_obs) > 5:
                avg_impact = sum(impact for _, impact in security_obs) / len(security_obs)
                if avg_impact > 0.6:
                    changes['security_focus'] = {
                        'delta': self.learning_rate * 0.5,
                        'reason': f"High impact security queries observed ({len(security_obs)} queries)"
                    }
                    changes['kali_integration'] = {
                        'delta': self.learning_rate * 0.3,
                        'reason': "Increased security focus requires better Kali integration"
                    }
        
        # Process technical depth observations
        if 'technical_query' in obs_by_type:
            tech_obs = obs_by_type['technical_query']
            if len(tech_obs) > 5:
                avg_complexity = sum(data.get('complexity', 0.5) for data, _ in tech_obs) / len(tech_obs)
                if avg_complexity > 0.7:
                    changes['technical_depth'] = {
                        'delta': self.learning_rate * 0.4,
                        'reason': f"High complexity technical queries observed (avg: {avg_complexity:.2f})"
                    }
        
        # Process multi-agent observations
        if 'multi_agent_task' in obs_by_type:
            agent_obs = obs_by_type['multi_agent_task']
            if len(agent_obs) > 3:
                avg_agents = sum(len(data.get('agents', [])) for data, _ in agent_obs) / len(agent_obs)
                if avg_agents > 2:
                    changes['multi_agent_coordination'] = {
                        'delta': self.learning_rate * 0.6,
                        'reason': f"Complex multi-agent tasks observed (avg agents: {avg_agents:.1f})"
                    }
        
        # Process error observations (negative feedback)
        if 'error' in obs_by_type:
            error_obs = obs_by_type['error']
            if len(error_obs) > 3:
                # Too many errors might indicate we're being too autonomous or risky
                changes['autonomy'] = {
                    'delta': -self.learning_rate * 0.3,
                    'reason': f"Multiple errors observed ({len(error_obs)} errors)"
                }
                changes['risk_tolerance'] = {
                    'delta': -self.learning_rate * 0.2,
                    'reason': "Reducing risk tolerance due to errors"
                }
        
        return changes
    
    def get_evolution_parameters(self) -> Dict[str, float]:
        """Get current evolution parameters"""
        try:
            with sqlite3.connect(self.evolution_db_path) as conn:
                params = {}
                for row in conn.execute("SELECT parameter_name, parameter_value FROM evolution_parameters"):
                    params[row[0]] = row[1]
                return params
        except Exception as e:
            logger.error(f"Error getting evolution parameters: {str(e)}")
            return {}
    
    def get_evolution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get evolution history"""
        try:
            with sqlite3.connect(self.evolution_db_path) as conn:
                history = []
                for row in conn.execute("""
                    SELECT timestamp, parameter_name, old_value, new_value, reason 
                    FROM evolution_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,)):
                    history.append({
                        "timestamp": datetime.fromtimestamp(row[0]).isoformat(),
                        "parameter": row[1],
                        "old_value": row[2],
                        "new_value": row[3],
                        "reason": row[4]
                    })
                return history
        except Exception as e:
            logger.error(f"Error getting evolution history: {str(e)}")
            return []
    
    def manual_adjust_parameter(self, parameter: str, value: float, reason: str) -> bool:
        """Manually adjust an evolution parameter"""
        try:
            with sqlite3.connect(self.evolution_db_path) as conn:
                # Check if parameter exists
                param_exists = conn.execute(
                    "SELECT 1 FROM evolution_parameters WHERE parameter_name = ?", 
                    (parameter,)
                ).fetchone()
                
                if not param_exists:
                    logger.error(f"Parameter {parameter} does not exist")
                    return False
                
                # Get current value
                old_value = conn.execute(
                    "SELECT parameter_value FROM evolution_parameters WHERE parameter_name = ?", 
                    (parameter,)
                ).fetchone()[0]
                
                # Ensure value is in valid range
                new_value = max(0.0, min(1.0, value))
                
                # Update parameter
                conn.execute("""
                    UPDATE evolution_parameters 
                    SET parameter_value = ?, last_updated = ?, update_count = update_count + 1
                    WHERE parameter_name = ?
                """, (new_value, datetime.now().timestamp(), parameter))
                
                # Record in history
                conn.execute("""
                    INSERT INTO evolution_history 
                    (timestamp, parameter_name, old_value, new_value, reason) 
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().timestamp(),
                    parameter,
                    old_value,
                    new_value,
                    f"Manual adjustment: {reason}"
                ))
                
                logger.info(f"Manually adjusted {parameter}: {old_value} -> {new_value}")
                return True
        except Exception as e:
            logger.error(f"Error adjusting parameter: {str(e)}")
            return False


class ResponsePersonalizer:
    """Personalizes responses based on user preferences with enhanced capabilities"""

    def __init__(self, user_profiler: UserProfiler, evolution_engine: SelfEvolutionEngine = None):
        self.user_profiler = user_profiler
        self.evolution_engine = evolution_engine

    def personalize_response(
        self, base_response: str, user_patterns: Dict[str, Any], query_type: str = None
    ) -> str:
        """Personalize response based on user patterns and system evolution parameters"""

        # Get evolution parameters if available
        evolution_params = {}
        if self.evolution_engine:
            evolution_params = self.evolution_engine.get_evolution_parameters()
            
            # Record observation for learning if query type is provided
            if query_type:
                self.evolution_engine.record_observation(
                    f"{query_type}_query",
                    {
                        "complexity": user_patterns.get("preferred_complexity", "moderate"),
                        "user_expertise": user_patterns.get("technical_expertise", "intermediate"),
                        "security_focus": "security" in query_type.lower(),
                        "patterns": user_patterns
                    },
                    impact=0.7  # Default impact score
                )

        # Adjust Wade's personality based on user preferences and evolution
        preferred_complexity = user_patterns.get("preferred_complexity", "moderate")
        avg_rating = user_patterns.get("avg_success_rating", 3.0)
        
        # Apply evolution parameters to personalization
        security_focus = evolution_params.get("security_focus", 0.7)
        technical_depth = evolution_params.get("technical_depth", 0.6)
        kali_integration = evolution_params.get("kali_integration", 0.8)
        
        # Add personalized intro based on user history
        personalized_intro = self._get_personalized_intro(user_patterns, evolution_params)

        # Adjust technical detail level based on both user preference and system evolution
        if preferred_complexity == "simple" or technical_depth < 0.4:
            # Add more explanations
            base_response = self._add_explanations(base_response)
        elif preferred_complexity == "complex" or technical_depth > 0.7:
            # Add more technical details
            base_response = self._add_technical_details(base_response, technical_depth)
        
        # Add security focus if appropriate
        if security_focus > 0.6 and ("security" in query_type.lower() if query_type else False):
            base_response = self._enhance_security_content(base_response, security_focus)
            
        # Add Kali Linux integration if appropriate
        if kali_integration > 0.7 and any(term in (query_type.lower() if query_type else "") 
                                         for term in ["kali", "security", "pentest", "hack"]):
            base_response = self._add_kali_integration(base_response, kali_integration)

        # Add personalized recommendations
        recommendations = self._get_personalized_recommendations(user_patterns, evolution_params)

        # Combine all elements
        personalized_response = f"{personalized_intro}\n\n{base_response}"

        if recommendations:
            personalized_response += f"\n\n{recommendations}"
            
        # Trigger system evolution occasionally (1 in 20 chance)
        if self.evolution_engine and random.random() < 0.05:
            evolution_result = self.evolution_engine.evolve_system()
            if evolution_result.get("evolved", False):
                logger.info(f"System evolved: {evolution_result}")

        return personalized_response

    def _get_personalized_intro(self, user_patterns: Dict[str, Any], evolution_params: Dict[str, float] = None) -> str:
        """Get personalized intro based on user history and system evolution"""
        interactions = user_patterns.get("total_interactions", 0)
        
        # Apply evolution parameters if available
        autonomy = 0.5
        security_focus = 0.5
        if evolution_params:
            autonomy = evolution_params.get("autonomy", 0.5)
            security_focus = evolution_params.get("security_focus", 0.5)
        
        # Base intros
        intros = [
            "Welcome to the family! Let's get you started with some serious firepower.",
            "Good to see you back, family. Ready for another ride?",
            "Family, you're becoming quite the expert. Let's push it to the next level.",
            "My most trusted family member is back. Time to show them what we're really capable of."
        ]
        
        # Security-focused intros
        security_intros = [
            "Welcome to the secure zone. Your digital fortress awaits construction.",
            "Back for more security insights? Let's fortify your digital presence.",
            "Your security expertise is growing. Let's explore advanced protection strategies.",
            "The security master returns. Time to deploy our most sophisticated defenses."
        ]
        
        # Select intro based on interactions
        idx = 0
        if interactions < 10:
            idx = 0
        elif interactions < 30:
            idx = 1
        elif interactions < 100:
            idx = 2
        else:
            idx = 3
            
        # Choose between regular and security-focused intro based on security_focus parameter
        if security_focus > 0.7 and random.random() < security_focus:
            return security_intros[idx]
        else:
            return intros[idx]

    def _add_explanations(self, response: str) -> str:
        """Add explanations for users who prefer simpler responses"""
        # Add more detailed explanations
        explanations = [
            "\n\n💡 Need more details on any part? Just ask - family helps family understand.",
            "\n\n💡 I can break this down further if needed. Just let me know which part you'd like explained.",
            "\n\n💡 This might be complex, but I'm here to guide you through each step."
        ]
        
        return response + random.choice(explanations)

    def _add_technical_details(self, response: str, technical_depth: float = 0.6) -> str:
        """Add technical details for advanced users based on technical depth parameter"""
        # Add technical depth based on the parameter
        if technical_depth > 0.8:
            # High technical depth
            return response + "\n\n🔧 For the technically inclined: This implementation leverages advanced concepts in system architecture and security protocols. I can elaborate on the low-level details if you're interested."
        elif technical_depth > 0.6:
            # Medium-high technical depth
            return response + "\n\n🔧 Want to dive deeper into the technical implementation? I can break down every detail of how this works under the hood."
        else:
            # Medium technical depth
            return response + "\n\n🔧 There's more technical depth to this if you're interested. Just ask for more details."
            
    def _enhance_security_content(self, response: str, security_focus: float) -> str:
        """Enhance response with security-focused content"""
        if security_focus > 0.8:
            # High security focus
            security_notes = [
                "\n\n🔒 **Security Note**: From a penetration testing perspective, this approach could expose potential vulnerabilities. Consider implementing additional hardening measures.",
                "\n\n🔒 **Security Insight**: This implementation should be complemented with proper access controls and encryption to prevent unauthorized access.",
                "\n\n🔒 **Security Consideration**: In a red team scenario, this would be a primary target for exploitation. Consider defense-in-depth strategies."
            ]
            return response + random.choice(security_notes)
        else:
            # Moderate security focus
            security_notes = [
                "\n\n🔒 Remember to consider the security implications of this approach.",
                "\n\n🔒 As always, security should be a priority when implementing this solution.",
                "\n\n🔒 Don't forget to review this from a security perspective before deployment."
            ]
            return response + random.choice(security_notes)
            
    def _add_kali_integration(self, response: str, kali_integration: float) -> str:
        """Add Kali Linux integration suggestions"""
        if kali_integration > 0.8:
            # High Kali integration
            kali_notes = [
                "\n\n🐉 **Kali Integration**: You can automate this process using Kali's built-in tools. Consider creating a custom script in `/usr/share/kali-tools/` for easy access.",
                "\n\n🐉 **Kali Workflow**: This fits perfectly into a Kali-based penetration testing workflow. You can integrate it with Metasploit for enhanced capabilities.",
                "\n\n🐉 **Kali Toolkit**: Add this to your Kali arsenal by creating a custom module that interfaces with existing reconnaissance tools."
            ]
            return response + random.choice(kali_notes)
        else:
            # Moderate Kali integration
            kali_notes = [
                "\n\n🐉 This can be easily executed in your Kali environment.",
                "\n\n🐉 Kali Linux has several tools that complement this approach.",
                "\n\n🐉 Consider adding this to your Kali toolkit for future operations."
            ]
            return response + random.choice(kali_notes)

    def _get_personalized_recommendations(self, user_patterns: Dict[str, Any], evolution_params: Dict[str, float] = None) -> str:
        """Get personalized recommendations based on user patterns and system evolution"""
        preferred_types = user_patterns.get("preferred_request_types", [])

        if not preferred_types:
            return ""
            
        # Apply evolution parameters if available
        security_focus = 0.5
        kali_integration = 0.5
        multi_agent_coordination = 0.5
        if evolution_params:
            security_focus = evolution_params.get("security_focus", 0.5)
            kali_integration = evolution_params.get("kali_integration", 0.5)
            multi_agent_coordination = evolution_params.get("multi_agent_coordination", 0.5)

        # Get top preference
        top_type = preferred_types[0][0] if preferred_types else "exploit"

        # Base recommendations
        base_recommendations = {
            "exploit": "💀 Based on your history, you might also want to try advanced payload encoding or multi-stage exploits.",
            "tool": "🛠️ Since you love building tools, consider creating a custom framework that combines multiple techniques.",
            "recon": "🔍 Your reconnaissance skills are solid. Ready to try some advanced OSINT or dark web research?",
            "research": "📊 Your research game is strong. Want to explore some automated intelligence correlation?",
            "coding": "💻 Looking to enhance your coding skills? Ask me about security-focused programming patterns.",
            "security": "🔐 For your next security challenge, consider exploring advanced threat modeling techniques."
        }
        
        # Security-focused recommendations
        security_recommendations = {
            "exploit": "💀 For advanced exploitation, try combining multiple vulnerabilities in a single attack chain using Phind-CodeLlama's uncensored capabilities.",
            "tool": "🛠️ Consider developing a custom security tool that integrates with your existing workflow and leverages AI for vulnerability detection.",
            "recon": "🔍 Enhance your reconnaissance by correlating data from multiple sources using advanced OSINT techniques and AI analysis.",
            "research": "📊 Implement an AI-driven threat intelligence platform that automatically correlates findings from multiple sources.",
            "coding": "💻 Implement secure coding practices with automated vulnerability scanning in your CI/CD pipeline using AI-powered code analysis.",
            "security": "🔐 Develop a custom security framework that addresses your specific threat model with AI-enhanced detection capabilities."
        }
        
        # Kali-focused recommendations
        kali_recommendations = {
            "exploit": "💀 Try integrating custom exploits with Kali's Metasploit framework and automating your workflow with Python scripts.",
            "tool": "🛠️ Build a custom Kali tool that automates your most common security workflows and integrates with the WADE AI system.",
            "recon": "🔍 Use Kali's reconnaissance tools in combination with AI-powered analysis for more comprehensive target profiling.",
            "research": "📊 Set up a Kali-based research environment with custom dashboards for visualizing security data.",
            "coding": "💻 Develop Python scripts that leverage Kali's libraries and integrate with WADE for advanced security testing.",
            "security": "🔐 Create a custom Kali ISO with WADE pre-integrated and your preferred tools and configurations pre-installed."
        }
        
        # Multi-agent recommendations
        agent_recommendations = {
            "exploit": "💀 Try using multiple specialized agents to develop a sophisticated exploit chain with automated payload generation.",
            "tool": "🛠️ Create a team of agents to build and test security tools collaboratively, each specializing in different aspects.",
            "recon": "🔍 Deploy multiple reconnaissance agents to gather and correlate data from different sources with AI-powered analysis.",
            "research": "📊 Build a research system with specialized agents for data collection, analysis, and visualization.",
            "coding": "💻 Use specialized coding agents to develop and audit security-critical components with automated vulnerability detection.",
            "security": "🔐 Build a security operations center with multiple specialized agents handling different aspects of your security posture."
        }
        
        # Choose recommendation based on evolution parameters
        if security_focus > 0.7 and random.random() < security_focus:
            recommendation = security_recommendations.get(top_type, base_recommendations.get(top_type, ""))
        elif kali_integration > 0.7 and random.random() < kali_integration:
            recommendation = kali_recommendations.get(top_type, base_recommendations.get(top_type, ""))
        elif multi_agent_coordination > 0.7 and random.random() < multi_agent_coordination:
            recommendation = agent_recommendations.get(top_type, base_recommendations.get(top_type, ""))
        else:
            recommendation = base_recommendations.get(top_type, "")
            
        # Add a second recommendation occasionally
        if len(preferred_types) > 1 and random.random() < 0.3:
            second_type = preferred_types[1][0]
            if second_type != top_type:
                second_rec = base_recommendations.get(second_type, "")
                if second_rec:
                    recommendation += f"\n\n{second_rec}"
                    
        return recommendation


class AdaptiveLearningSystem:
    """Main adaptive learning system that coordinates all components with self-evolution capabilities"""

    def __init__(self, memory_dir: Path):
        """Initialize the adaptive learning system with self-evolution engine"""
        self.memory_dir = memory_dir
        self.user_profiler = UserProfiler(memory_dir)
        self.task_planner = AdaptiveTaskPlanner(self.user_profiler)
        self.evolution_engine = SelfEvolutionEngine(memory_dir)
        self.response_personalizer = ResponsePersonalizer(self.user_profiler, self.evolution_engine)
        
        # Initialize system with default evolution parameters
        logger.info("Initializing adaptive learning system with self-evolution capabilities")
        logger.info(f"Evolution parameters: {self.evolution_engine.get_evolution_parameters()}")

    def adapt_to_user(
        self, user_input: str, base_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt crew behavior to user preferences and system evolution parameters"""

        # Get user patterns
        user_patterns = self.user_profiler.analyze_user_patterns()
        
        # Get evolution parameters
        evolution_params = self.evolution_engine.get_evolution_parameters()

        # Plan optimal approach with evolution parameters
        adapted_plan = self.task_planner.plan_optimal_approach(user_input, base_plan)
        
        # Apply evolution parameters to the plan
        if evolution_params:
            # Enhance security focus if parameter is high
            if evolution_params.get("security_focus", 0.5) > 0.7:
                if "security" not in adapted_plan.get("focus_areas", []):
                    adapted_plan.setdefault("focus_areas", []).append("security")
                    
            # Enhance Kali integration if parameter is high
            if evolution_params.get("kali_integration", 0.5) > 0.7:
                adapted_plan["kali_integration"] = True
                
            # Enhance multi-agent coordination if parameter is high
            if evolution_params.get("multi_agent_coordination", 0.5) > 0.7:
                adapted_plan["agent_count"] = max(adapted_plan.get("agent_count", 1), 3)
                
            # Add evolution parameters to the plan
            adapted_plan["evolution_params"] = evolution_params

        # Add user patterns for response personalization
        adapted_plan["user_patterns"] = user_patterns

        # Record observation for evolution
        query_type = self._detect_query_type(user_input)
        self.evolution_engine.record_observation(
            f"{query_type}_query",
            {
                "input_length": len(user_input),
                "query_type": query_type,
                "plan": {k: v for k, v in adapted_plan.items() if k != "user_patterns"}
            },
            impact=0.6
        )

        return adapted_plan

    def personalize_response(self, response: str, user_patterns: Dict[str, Any], query_type: str = None) -> str:
        """Personalize response based on user patterns and system evolution"""
        if query_type is None:
            query_type = "general"
            
        return self.response_personalizer.personalize_response(response, user_patterns, query_type)
        
    def record_interaction(self, interaction_data: Dict[str, Any]):
        """Record interaction for learning and evolution"""
        # Record for user profiling
        self.user_profiler.update_interaction(interaction_data)
        
        # Record for evolution
        query_type = interaction_data.get("request_type", "general")
        complexity = interaction_data.get("complexity", "moderate")
        success_rating = interaction_data.get("success_rating", 3)
        
        # Calculate impact based on success rating (higher rating = higher impact)
        impact = min(1.0, max(0.0, success_rating / 5.0))
        
        # Record observation
        self.evolution_engine.record_observation(
            f"{query_type}_query",
            {
                "complexity": complexity,
                "success_rating": success_rating,
                "agents_used": interaction_data.get("agents_used", []),
                "response_time": interaction_data.get("response_time", 0),
            },
            impact=impact
        )
        
        # Occasionally trigger evolution (1 in 20 chance)
        if random.random() < 0.05:
            evolution_result = self.evolution_engine.evolve_system()
            if evolution_result.get("evolved", False):
                logger.info(f"System evolved: {evolution_result}")
                
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query based on content"""
        query_lower = query.lower()
        
        # Security-related keywords
        if any(kw in query_lower for kw in ["hack", "exploit", "vulnerability", "security", "pentest", "attack"]):
            return "security"
            
        # Kali-related keywords
        if any(kw in query_lower for kw in ["kali", "linux", "terminal", "command", "shell"]):
            return "kali"
            
        # Coding-related keywords
        if any(kw in query_lower for kw in ["code", "program", "script", "function", "class", "develop"]):
            return "coding"
            
        # Tool-related keywords
        if any(kw in query_lower for kw in ["tool", "utility", "framework", "build", "create"]):
            return "tool"
            
        # Research-related keywords
        if any(kw in query_lower for kw in ["research", "analyze", "investigate", "study", "learn"]):
            return "research"
            
        return "general"
        
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get the current evolution status"""
        return {
            "parameters": self.evolution_engine.get_evolution_parameters(),
            "history": self.evolution_engine.get_evolution_history(5)
        }
        
    def trigger_evolution(self) -> Dict[str, Any]:
        """Manually trigger system evolution"""
        return self.evolution_engine.evolve_system()
        
    def adjust_evolution_parameter(self, parameter: str, value: float, reason: str) -> bool:
        """Manually adjust an evolution parameter"""
        return self.evolution_engine.manual_adjust_parameter(parameter, value, reason)

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

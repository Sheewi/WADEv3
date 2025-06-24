#!/usr/bin/env python3
"""
Wade Core - Main system for the Wade AI Assistant
Integrates model router, agent factory, and memory system
"""

import os
import json
import asyncio
import logging
import datetime
import sqlite3
from typing import Dict, Any, List, Optional, Union
from collections import Counter

# Import components
from model_router import ModelRouter
from dynamic_agent_factory import DynamicAgentFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WadeCore")

class MemorySystem:
    """Persistent memory system for Wade"""
    
    def __init__(self, db_path: str = None):
        """Initialize the memory system"""
        self.db_path = db_path or os.path.expanduser("~/.wade/data/memory.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
        
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            preferences TEXT,
            created_at TEXT,
            last_active TEXT
        )
        ''')
        
        # Conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            metadata TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        ''')
        
        # User preferences table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT,
            key TEXT,
            value TEXT,
            updated_at TEXT,
            PRIMARY KEY (user_id, key),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Knowledge base table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            content TEXT,
            source TEXT,
            created_at TEXT,
            tags TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        self.conn.commit()
        
    def create_user(self, user_id: str, name: str = None) -> bool:
        """Create a new user"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, name, preferences, created_at, last_active) VALUES (?, ?, ?, ?, ?)",
                (user_id, name or user_id, "{}", now, now)
            )
            
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False
            
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, preferences, created_at, last_active FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                "id": row[0],
                "name": row[1],
                "preferences": json.loads(row[2]),
                "created_at": row[3],
                "last_active": row[4]
            }
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
            
    def update_user_activity(self, user_id: str) -> bool:
        """Update user's last active timestamp"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            
            cursor.execute(
                "UPDATE users SET last_active = ? WHERE id = ?",
                (now, user_id)
            )
            
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating user activity: {str(e)}")
            return False
            
    def create_conversation(self, user_id: str, title: str = None) -> Optional[str]:
        """Create a new conversation and return its ID"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            conversation_id = f"conv_{now.replace(':', '').replace('.', '').replace('-', '')}"
            
            cursor.execute(
                "INSERT INTO conversations (id, user_id, title, created_at) VALUES (?, ?, ?, ?)",
                (conversation_id, user_id, title or f"Conversation {now}", now)
            )
            
            self.conn.commit()
            return conversation_id
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return None
            
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Add a message to a conversation and return its ID"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            message_id = f"msg_{now.replace(':', '').replace('.', '').replace('-', '')}"
            
            cursor.execute(
                "INSERT INTO messages (id, conversation_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, conversation_id, role, content, now, json.dumps(metadata or {}))
            )
            
            self.conn.commit()
            return message_id
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return None
            
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the history of a conversation"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, role, content, timestamp, metadata FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conversation_id,)
            )
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "timestamp": row[3],
                    "metadata": json.loads(row[4])
                })
                
            return messages
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
            
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a user's conversations"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, title, created_at FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    "id": row[0],
                    "title": row[1],
                    "created_at": row[2]
                })
                
            return conversations
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []
            
    def set_user_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Set a user preference"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            
            cursor.execute(
                "INSERT OR REPLACE INTO user_preferences (user_id, key, value, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, key, json.dumps(value), now)
            )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting user preference: {str(e)}")
            return False
            
    def get_user_preference(self, user_id: str, key: str) -> Optional[Any]:
        """Get a user preference"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT value FROM user_preferences WHERE user_id = ? AND key = ?",
                (user_id, key)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
                
            return json.loads(row[0])
        except Exception as e:
            logger.error(f"Error getting user preference: {str(e)}")
            return None
            
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all preferences for a user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT key, value FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            
            preferences = {}
            for row in cursor.fetchall():
                preferences[row[0]] = json.loads(row[1])
                
            return preferences
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return {}
            
    def add_knowledge_item(self, user_id: str, content: str, source: str, tags: List[str] = None) -> Optional[str]:
        """Add an item to the knowledge base"""
        try:
            cursor = self.conn.cursor()
            now = datetime.datetime.now().isoformat()
            item_id = f"know_{now.replace(':', '').replace('.', '').replace('-', '')}"
            
            cursor.execute(
                "INSERT INTO knowledge_items (id, user_id, content, source, created_at, tags) VALUES (?, ?, ?, ?, ?, ?)",
                (item_id, user_id, content, source, now, json.dumps(tags or []))
            )
            
            self.conn.commit()
            return item_id
        except Exception as e:
            logger.error(f"Error adding knowledge item: {str(e)}")
            return None
            
    def get_knowledge_items(self, user_id: str, tags: List[str] = None) -> List[Dict[str, Any]]:
        """Get knowledge items for a user, optionally filtered by tags"""
        try:
            cursor = self.conn.cursor()
            
            if tags:
                # This is a simple implementation - in a real system, you'd use a proper search mechanism
                cursor.execute("SELECT id, content, source, created_at, tags FROM knowledge_items WHERE user_id = ?", (user_id,))
                
                items = []
                for row in cursor.fetchall():
                    item_tags = json.loads(row[4])
                    if any(tag in item_tags for tag in tags):
                        items.append({
                            "id": row[0],
                            "content": row[1],
                            "source": row[2],
                            "created_at": row[3],
                            "tags": item_tags
                        })
                        
                return items
            else:
                cursor.execute(
                    "SELECT id, content, source, created_at, tags FROM knowledge_items WHERE user_id = ?",
                    (user_id,)
                )
                
                items = []
                for row in cursor.fetchall():
                    items.append({
                        "id": row[0],
                        "content": row[1],
                        "source": row[2],
                        "created_at": row[3],
                        "tags": json.loads(row[4])
                    })
                    
                return items
        except Exception as e:
            logger.error(f"Error getting knowledge items: {str(e)}")
            return []


class AdaptiveLearning:
    """System for learning from interactions and adapting to user preferences"""
    
    def __init__(self, memory_system: MemorySystem):
        """Initialize the adaptive learning system"""
        self.memory = memory_system
        
    def track_interaction(self, user_id: str, query: str, response: str, metadata: Dict[str, Any] = None):
        """Track an interaction for learning"""
        try:
            # Extract topics from the query
            topics = self._extract_topics(query)
            
            # Update topic preferences
            current_topics = self.memory.get_user_preference(user_id, "favorite_topics") or {}
            for topic in topics:
                current_topics[topic] = current_topics.get(topic, 0) + 1
            self.memory.set_user_preference(user_id, "favorite_topics", current_topics)
            
            # Track response length preference
            response_lengths = self.memory.get_user_preference(user_id, "response_lengths") or []
            response_lengths.append(len(response))
            if len(response_lengths) > 20:  # Keep only the last 20
                response_lengths = response_lengths[-20:]
            self.memory.set_user_preference(user_id, "response_lengths", response_lengths)
            
            # Track code preference
            has_code = "```" in response
            code_preferences = self.memory.get_user_preference(user_id, "code_preferences") or []
            code_preferences.append(1 if has_code else 0)
            if len(code_preferences) > 20:  # Keep only the last 20
                code_preferences = code_preferences[-20:]
            self.memory.set_user_preference(user_id, "code_preferences", code_preferences)
            
            # Track active hours
            hour = datetime.datetime.now().hour
            active_hours = self.memory.get_user_preference(user_id, "active_hours") or {}
            active_hours[str(hour)] = active_hours.get(str(hour), 0) + 1
            self.memory.set_user_preference(user_id, "active_hours", active_hours)
            
            # Track tools used
            if metadata and "tools_used" in metadata:
                tools_used = self.memory.get_user_preference(user_id, "tools_used") or {}
                for tool in metadata["tools_used"]:
                    tools_used[tool] = tools_used.get(tool, 0) + 1
                self.memory.set_user_preference(user_id, "tools_used", tools_used)
                
            return True
        except Exception as e:
            logger.error(f"Error tracking interaction: {str(e)}")
            return False
            
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get a user's profile based on tracked interactions"""
        try:
            # Get raw preferences
            favorite_topics = self.memory.get_user_preference(user_id, "favorite_topics") or {}
            response_lengths = self.memory.get_user_preference(user_id, "response_lengths") or []
            code_preferences = self.memory.get_user_preference(user_id, "code_preferences") or []
            active_hours = self.memory.get_user_preference(user_id, "active_hours") or {}
            tools_used = self.memory.get_user_preference(user_id, "tools_used") or {}
            
            # Process into a profile
            profile = {
                "favorite_topics": sorted(favorite_topics.items(), key=lambda x: x[1], reverse=True)[:5],
                "preferred_response_length": sum(response_lengths) / len(response_lengths) if response_lengths else 500,
                "code_preference": sum(code_preferences) / len(code_preferences) if code_preferences else 0.5,
                "active_hours": sorted(active_hours.items(), key=lambda x: int(x[1]), reverse=True)[:3],
                "favorite_tools": sorted(tools_used.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            return profile
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return {}
            
    def adapt_response(self, user_id: str, query: str, base_response: str) -> str:
        """Adapt a response based on user preferences"""
        try:
            profile = self.get_user_profile(user_id)
            
            # If we don't have enough data, return the base response
            if not profile or "preferred_response_length" not in profile:
                return base_response
                
            adapted_response = base_response
            
            # Adjust response length
            preferred_length = profile["preferred_response_length"]
            current_length = len(base_response)
            
            if current_length > preferred_length * 1.5:
                # Response is too long, shorten it
                adapted_response = self._shorten_response(base_response)
            elif current_length < preferred_length * 0.5 and current_length < 200:
                # Response is too short, expand it
                adapted_response = self._expand_response(base_response, query)
                
            # Add code examples if user prefers them
            if profile["code_preference"] > 0.7 and "```" not in adapted_response and self._is_code_appropriate(query):
                adapted_response = self._add_code_example(adapted_response, query)
                
            return adapted_response
        except Exception as e:
            logger.error(f"Error adapting response: {str(e)}")
            return base_response
            
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text"""
        topics = []
        
        # Simple keyword-based topic extraction
        topic_keywords = {
            "security": ["hack", "security", "vulnerability", "exploit", "password", "encryption"],
            "programming": ["code", "program", "function", "script", "develop", "programming"],
            "system": ["linux", "kali", "system", "install", "configure", "setup"],
            "network": ["network", "wifi", "packet", "traffic", "connection", "protocol"],
            "web": ["website", "web", "http", "html", "css", "javascript"],
            "database": ["database", "sql", "query", "table", "record", "data"],
            "hardware": ["hardware", "device", "usb", "memory", "cpu", "gpu"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
                
        return topics
        
    def _shorten_response(self, response: str) -> str:
        """Shorten a response while preserving key information"""
        # Simple implementation - in a real system, you'd use a more sophisticated approach
        paragraphs = response.split("\n\n")
        
        if len(paragraphs) <= 2:
            return response
            
        # Keep first paragraph, last paragraph, and a shortened middle
        shortened = paragraphs[0] + "\n\n"
        
        if len(paragraphs) > 3:
            shortened += "...\n\n"
            
        shortened += paragraphs[-1]
        return shortened
        
    def _expand_response(self, response: str, query: str) -> str:
        """Expand a response with additional information"""
        # Simple implementation - in a real system, you'd generate actual additional content
        expanded = response + "\n\n"
        expanded += "Would you like me to provide more details about any specific aspect of this response?"
        return expanded
        
    def _is_code_appropriate(self, query: str) -> bool:
        """Determine if code examples are appropriate for the query"""
        code_indicators = ["how to", "example", "code", "script", "program", "function", "implement"]
        return any(indicator in query.lower() for indicator in code_indicators)
        
    def _add_code_example(self, response: str, query: str) -> str:
        """Add a relevant code example to the response"""
        # Simple implementation - in a real system, you'd generate actual code examples
        response += "\n\n"
        response += "```python\n# Example code\n# This would be actual generated code in a real implementation\n```"
        return response


class WadeCore:
    """Main system for the Wade AI Assistant"""
    
    def __init__(self, config_path: str = None):
        """Initialize the Wade core system"""
        self.config_path = config_path or os.path.expanduser("~/.wade/config/wade.json")
        self.config = self._load_config()
        
        # Initialize components
        self.memory = MemorySystem()
        self.learning = AdaptiveLearning(self.memory)
        self.model_router = ModelRouter()
        self.agent_factory = DynamicAgentFactory(self.model_router)
        
        logger.info("Wade Core initialized")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "version": "1.0.0",
                "name": "Wade",
                "description": "Advanced Multi-Agent System for Kali Linux",
                "default_user": "default",
                "logging_level": "INFO",
                "max_conversation_length": 100,
                "max_context_length": 4096
            }
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            return default_config
            
    async def process_query(self, query: str, user_id: str = None, conversation_id: str = None, 
                          context: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a user query and return a response"""
        # Use default user if not specified
        user_id = user_id or self.config["default_user"]
        
        # Ensure user exists
        user = self.memory.get_user(user_id)
        if not user:
            self.memory.create_user(user_id)
            
        # Update user activity
        self.memory.update_user_activity(user_id)
        
        # Create or continue conversation
        if not conversation_id:
            conversation_id = self.memory.create_conversation(user_id)
            
        # Add user message to memory
        self.memory.add_message(conversation_id, "user", query)
        
        # Get conversation history for context if not provided
        if not context:
            history = self.memory.get_conversation_history(conversation_id)
            context = [{"role": msg["role"], "content": msg["content"]} for msg in history]
            
        # Check if this is a request to create a new agent
        if self._is_agent_creation_request(query):
            result = await self._handle_agent_creation(query, user_id)
            
            # Add assistant message to memory
            self.memory.add_message(conversation_id, "assistant", result["response"], 
                                  {"agent_created": result.get("agent_id")})
                                  
            return result
            
        # Check if this is a task that requires multiple agents
        if self._is_complex_task(query):
            result = await self._handle_complex_task(query, user_id, context)
            
            # Add assistant message to memory
            self.memory.add_message(conversation_id, "assistant", result["response"], 
                                  {"agents_used": result.get("agent_ids", [])})
                                  
            return result
            
        # Route to appropriate model
        model_name = self.model_router.route_query(query, self.memory.get_user_preferences(user_id))
        
        # Generate response
        response_data = await self.model_router.query_model(model_name, query, context)
        
        # Adapt response based on user preferences
        adapted_response = self.learning.adapt_response(user_id, query, response_data)
        
        # Track interaction for learning
        self.learning.track_interaction(user_id, query, adapted_response)
        
        # Add assistant message to memory
        self.memory.add_message(conversation_id, "assistant", adapted_response, {"model": model_name})
        
        return {
            "response": adapted_response,
            "conversation_id": conversation_id,
            "model": model_name
        }
        
    def _is_agent_creation_request(self, query: str) -> bool:
        """Determine if a query is requesting agent creation"""
        creation_indicators = [
            "create a new agent",
            "make an agent",
            "build an agent",
            "create agent",
            "new agent"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in creation_indicators)
        
    async def _handle_agent_creation(self, query: str, user_id: str) -> Dict[str, Any]:
        """Handle a request to create a new agent"""
        try:
            # Extract agent description from query
            description = query
            for prefix in ["create a new agent", "make an agent", "build an agent", "create agent", "new agent"]:
                if prefix in query.lower():
                    description = query[query.lower().find(prefix) + len(prefix):].strip()
                    if description.startswith("that") or description.startswith("which") or description.startswith("to"):
                        description = description[description.find(" "):].strip()
                    break
                    
            # Create the agent
            agent_id = await self.agent_factory.create_agent_from_description(description)
            
            if agent_id:
                return {
                    "response": f"I've created a new agent based on your description. The agent ID is {agent_id}.",
                    "agent_id": agent_id,
                    "success": True
                }
            else:
                return {
                    "response": "I'm sorry, I couldn't create an agent based on your description. Please try again with more details.",
                    "success": False
                }
        except Exception as e:
            logger.error(f"Error handling agent creation: {str(e)}")
            return {
                "response": f"An error occurred while creating the agent: {str(e)}",
                "success": False
            }
            
    def _is_complex_task(self, query: str) -> bool:
        """Determine if a query represents a complex task requiring multiple agents"""
        # Check for task indicators
        task_indicators = [
            "build a",
            "create a",
            "develop a",
            "implement a",
            "design a",
            "analyze",
            "investigate",
            "research",
            "find vulnerabilities",
            "secure my",
            "optimize my",
            "automate"
        ]
        
        query_lower = query.lower()
        has_task_indicator = any(indicator in query_lower for indicator in task_indicators)
        
        # Check for complexity indicators
        complexity_indicators = [
            "complex",
            "comprehensive",
            "detailed",
            "thorough",
            "complete",
            "full",
            "end-to-end",
            "step by step"
        ]
        
        has_complexity = any(indicator in query_lower for indicator in complexity_indicators)
        
        # Check length - longer queries often indicate complex tasks
        is_long_query = len(query.split()) > 15
        
        return (has_task_indicator and (has_complexity or is_long_query))
        
    async def _handle_complex_task(self, query: str, user_id: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """Handle a complex task requiring multiple agents"""
        try:
            # Analyze the task and create appropriate agents
            result = await self.agent_factory.analyze_task_and_create_agents(query)
            
            if not result["crew"]:
                # Fall back to single-agent approach
                model_name = self.model_router.route_query(query, self.memory.get_user_preferences(user_id))
                response_data = await self.model_router.query_model(model_name, query, context)
                
                return {
                    "response": response_data,
                    "model": model_name,
                    "fallback": True
                }
                
            # Run the crew to handle the task
            crew_result = await result["crew"].run()
            
            # Format the response
            agent_ids = result["agent_ids"]
            analysis = result["analysis"]
            
            response = f"I've analyzed your task and created a team of specialized agents to handle it:\n\n"
            
            for i, agent_info in enumerate(analysis.get("agents", [])):
                if i < len(agent_ids):
                    response += f"- **{agent_info.get('type', 'Agent')}**: {agent_info.get('subtask', 'No subtask specified')}\n"
                    
            response += f"\n{crew_result}\n\n"
            response += "The agents have completed their work. Is there anything specific you'd like me to explain or modify?"
            
            return {
                "response": response,
                "agent_ids": agent_ids,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error handling complex task: {str(e)}")
            return {
                "response": f"An error occurred while processing your task: {str(e)}",
                "success": False
            }
            
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a user's conversations"""
        return self.memory.get_user_conversations(user_id, limit)
        
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the history of a conversation"""
        return self.memory.get_conversation_history(conversation_id)
        
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get a user's profile"""
        return self.learning.get_user_profile(user_id)
        
    def get_available_models(self) -> List[str]:
        """Get available models"""
        return self.model_router.get_available_models()
        
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get available agents"""
        return self.agent_factory.get_active_agents()
        
    def get_agent_templates(self) -> List[str]:
        """Get available agent templates"""
        return self.agent_factory.get_template_names()


# Example usage
async def main():
    wade = WadeCore()
    
    # Process a query
    result = await wade.process_query(
        "Find vulnerabilities in a WordPress site",
        user_id="test_user"
    )
    
    print(f"Response: {result['response'][:100]}...")
    print(f"Model used: {result['model']}")
    print(f"Conversation ID: {result['conversation_id']}")
    
    # Get user profile
    profile = wade.get_user_profile("test_user")
    print(f"User profile: {profile}")
    
    # Create a new agent
    agent_result = await wade.process_query(
        "Create a new agent that specializes in network traffic analysis",
        user_id="test_user"
    )
    
    print(f"Agent creation result: {agent_result['response']}")
    
    # Handle a complex task
    task_result = await wade.process_query(
        "Build a comprehensive web scraper that can extract data from e-commerce websites and store it in a database",
        user_id="test_user"
    )
    
    print(f"Complex task result: {task_result['response'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
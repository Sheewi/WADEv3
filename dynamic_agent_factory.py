#!/usr/bin/env python3
"""
Dynamic Agent Factory for Wade - Create and manage agents dynamically
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from crewai import Agent, Task, Crew, Process
from langchain.llms import Ollama

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DynamicAgentFactory")


class DynamicAgentFactory:
    """
    Factory for dynamically creating and managing agents based on needs
    """

    def __init__(self, model_router=None, config_path: str = None):
        """Initialize the agent factory"""
        self.model_router = model_router
        self.config_path = config_path or os.path.expanduser(
            "~/.wade/config/agents.json"
        )
        self.agent_templates = {}
        self.active_agents = {}
        self.llm = Ollama(model="phind-codellama")
        self._load_templates()

    def _load_templates(self):
        """Load agent templates from configuration file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.agent_templates = json.load(f)
                logger.info(f"Loaded {len(self.agent_templates)} agent templates")
            else:
                logger.warning(
                    f"Agent templates file not found at {self.config_path}, creating default templates"
                )
                self._create_default_templates()
        except Exception as e:
            logger.error(f"Error loading agent templates: {str(e)}")
            self._create_default_templates()

    def _create_default_templates(self):
        """Create default agent templates"""
        self.agent_templates = {
            "hacker": {
                "role": "Offensive Security Specialist",
                "goal": "Find and exploit vulnerabilities in target systems",
                "backstory": "You are an elite ethical hacker with expertise in penetration testing and vulnerability assessment. You help identify security weaknesses and suggest remediation strategies.",
                "tools": ["terminal", "nmap_scan", "metasploit"],
                "allow_delegation": True,
                "verbose": True,
            },
            "defender": {
                "role": "Defensive Security Specialist",
                "goal": "Protect systems from attacks and ensure security compliance",
                "backstory": "You are a cybersecurity expert specializing in defense mechanisms, intrusion detection, and incident response. You help secure systems against potential threats.",
                "tools": ["terminal", "snort_alert", "firewall_config"],
                "allow_delegation": True,
                "verbose": True,
            },
            "researcher": {
                "role": "Intelligence Researcher",
                "goal": "Gather and analyze information from various sources",
                "backstory": "You are an expert in OSINT (Open Source Intelligence) and research methodologies. You can find, analyze, and synthesize information from diverse sources including the dark web.",
                "tools": ["terminal", "web_search", "tor_search"],
                "allow_delegation": True,
                "verbose": True,
            },
            "customizer": {
                "role": "System Customization Specialist",
                "goal": "Enhance and personalize the Kali Linux environment",
                "backstory": "You are an expert in Linux customization, desktop environments, and user experience design. You help create personalized, efficient working environments.",
                "tools": ["terminal", "file_editor", "package_manager"],
                "allow_delegation": True,
                "verbose": True,
            },
            "developer": {
                "role": "Tool Developer",
                "goal": "Create and modify tools and scripts for specific tasks",
                "backstory": "You are a skilled programmer with expertise in Python, Bash, and other languages used in security tools. You can create custom tools or modify existing ones to meet specific needs.",
                "tools": ["terminal", "code_interpreter", "git"],
                "allow_delegation": True,
                "verbose": True,
            },
            "learner": {
                "role": "Continuous Learning Specialist",
                "goal": "Improve the system's knowledge and capabilities over time",
                "backstory": "You are an expert in machine learning and knowledge management. You help the system learn from interactions and improve its capabilities.",
                "tools": ["terminal", "memory_store", "model_trainer"],
                "allow_delegation": True,
                "verbose": True,
            },
        }

        # Save the default templates
        self._save_templates()

    def _save_templates(self):
        """Save agent templates to configuration file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.agent_templates, f, indent=2)
            logger.info(
                f"Saved {len(self.agent_templates)} agent templates to {self.config_path}"
            )
        except Exception as e:
            logger.error(f"Error saving agent templates: {str(e)}")

    def get_template_names(self) -> List[str]:
        """Get list of available agent template names"""
        return list(self.agent_templates.keys())

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent template"""
        return self.agent_templates.get(template_name)

    def add_template(self, name: str, template: Dict[str, Any]) -> bool:
        """Add a new agent template"""
        if name in self.agent_templates:
            logger.warning(
                f"Template '{name}' already exists, use update_template to modify it"
            )
            return False

        self.agent_templates[name] = template
        self._save_templates()
        logger.info(f"Added new agent template: {name}")
        return True

    def update_template(self, name: str, template: Dict[str, Any]) -> bool:
        """Update an existing agent template"""
        if name not in self.agent_templates:
            logger.warning(
                f"Template '{name}' does not exist, use add_template to create it"
            )
            return False

        self.agent_templates[name] = template
        self._save_templates()
        logger.info(f"Updated agent template: {name}")
        return True

    def remove_template(self, name: str) -> bool:
        """Remove an agent template"""
        if name not in self.agent_templates:
            logger.warning(f"Template '{name}' does not exist")
            return False

        del self.agent_templates[name]
        self._save_templates()
        logger.info(f"Removed agent template: {name}")
        return True

    def create_agent(
        self,
        template_name: str,
        agent_id: str = None,
        custom_params: Dict[str, Any] = None,
    ) -> Optional[Agent]:
        """Create an agent from a template"""
        if template_name not in self.agent_templates:
            logger.error(f"Template '{template_name}' does not exist")
            return None

        template = self.agent_templates[template_name]
        custom_params = custom_params or {}

        # Generate a unique ID if not provided
        if not agent_id:
            import uuid

            agent_id = f"{template_name}_{uuid.uuid4().hex[:8]}"

        # Merge template with custom parameters
        agent_params = {**template, **custom_params}

        # Create the agent
        try:
            agent = Agent(
                role=agent_params.get("role", "Assistant"),
                goal=agent_params.get("goal", "Help the user"),
                backstory=agent_params.get("backstory", "You are an AI assistant."),
                verbose=agent_params.get("verbose", True),
                allow_delegation=agent_params.get("allow_delegation", True),
                llm=self.llm,
            )

            # Store the active agent
            self.active_agents[agent_id] = {
                "agent": agent,
                "template": template_name,
                "params": agent_params,
                "created_at": asyncio.get_event_loop().time(),
            }

            logger.info(f"Created agent '{agent_id}' from template '{template_name}'")
            return agent
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return None

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an active agent by ID"""
        if agent_id in self.active_agents:
            return self.active_agents[agent_id]["agent"]
        return None

    def remove_agent(self, agent_id: str) -> bool:
        """Remove an active agent"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            logger.info(f"Removed agent '{agent_id}'")
            return True
        return False

    def get_active_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all active agents"""
        return {
            agent_id: {
                "template": info["template"],
                "role": info["params"].get("role", "Assistant"),
                "created_at": info["created_at"],
            }
            for agent_id, info in self.active_agents.items()
        }

    async def create_agent_from_description(self, description: str) -> Optional[str]:
        """
        Dynamically create a new agent based on a natural language description
        Returns the ID of the created agent
        """
        # Use the LLM to generate agent parameters from the description
        prompt = f"""
        Create an AI agent based on the following description:

        {description}

        Generate a JSON object with the following fields:
        - role: The role or title of the agent
        - goal: The primary goal or objective of the agent
        - backstory: A detailed backstory for the agent
        - tools: A list of tools the agent might need (from: terminal, web_search, code_interpreter, file_editor, etc.)
        - allow_delegation: Whether the agent can delegate tasks (true/false)
        - verbose: Whether the agent should be verbose in its responses (true/false)

        Return only the JSON object, nothing else.
        """

        try:
            # Query the LLM
            if self.model_router:
                response = await self.model_router.generate(
                    prompt, required_capabilities=["reasoning"]
                )
                json_str = response.get("response", "")
            else:
                # Use the default LLM
                import requests

                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "phind-codellama",
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                json_str = response.json().get("response", "")

            # Extract and parse the JSON
            import re

            json_match = re.search(r"```json\n(.*?)\n```", json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without the markdown code block
                json_match = re.search(r"(\{.*\})", json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)

            agent_params = json.loads(json_str)

            # Generate a template name
            template_name = agent_params.get("role", "custom").lower().replace(" ", "_")
            if template_name in self.agent_templates:
                template_name = f"{template_name}_{len(self.agent_templates)}"

            # Add the template
            self.add_template(template_name, agent_params)

            # Create and return the agent
            agent_id = f"{template_name}_{asyncio.get_event_loop().time()}"
            agent = self.create_agent(template_name, agent_id)

            if agent:
                return agent_id
            return None
        except Exception as e:
            logger.error(f"Error creating agent from description: {str(e)}")
            return None

    def create_crew(
        self, agent_ids: List[str], tasks: List[Dict[str, Any]] = None
    ) -> Optional[Crew]:
        """Create a crew from a list of agent IDs"""
        # Get the agents
        agents = []
        for agent_id in agent_ids:
            agent = self.get_agent(agent_id)
            if agent:
                agents.append(agent)
            else:
                logger.warning(f"Agent '{agent_id}' not found")

        if not agents:
            logger.error("No valid agents provided")
            return None

        # Create tasks if provided
        crew_tasks = []
        if tasks:
            for i, task_params in enumerate(tasks):
                if i < len(agents):
                    task = Task(
                        description=task_params.get("description", f"Task {i+1}"),
                        expected_output=task_params.get(
                            "expected_output", "Completed task"
                        ),
                        agent=agents[i],
                    )
                    crew_tasks.append(task)

        # Create the crew
        try:
            crew = Crew(
                agents=agents, tasks=crew_tasks, verbose=2, process=Process.sequential
            )
            return crew
        except Exception as e:
            logger.error(f"Error creating crew: {str(e)}")
            return None

    async def analyze_task_and_create_agents(
        self, task_description: str
    ) -> Dict[str, Any]:
        """
        Analyze a task description and create appropriate agents to handle it
        Returns a dictionary with created agent IDs and a crew
        """
        # Use the LLM to analyze the task and determine needed agents
        prompt = f"""
        Analyze the following task and determine which specialized agents would be needed to complete it:

        {task_description}

        For each agent needed, provide:
        1. A name/type for the agent
        2. Why this agent is needed for the task
        3. What specific subtask this agent should handle

        Return your analysis as a JSON object with an "agents" array containing objects with "type", "reason", and "subtask" fields.
        """

        try:
            # Query the LLM
            if self.model_router:
                response = await self.model_router.generate(
                    prompt, required_capabilities=["reasoning"]
                )
                json_str = response.get("response", "")
            else:
                # Use the default LLM
                import requests

                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "phind-codellama",
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                json_str = response.json().get("response", "")

            # Extract and parse the JSON
            import re

            json_match = re.search(r"```json\n(.*?)\n```", json_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without the markdown code block
                json_match = re.search(r"(\{.*\})", json_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)

            analysis = json.loads(json_str)

            # Create agents based on the analysis
            agent_ids = []
            tasks = []

            for agent_info in analysis.get("agents", []):
                agent_type = agent_info.get("type", "").lower().replace(" ", "_")
                subtask = agent_info.get("subtask", "")

                # Check if we have a template for this agent type
                if agent_type in self.agent_templates:
                    # Create agent from existing template
                    agent_id = f"{agent_type}_{asyncio.get_event_loop().time()}"
                    agent = self.create_agent(agent_type, agent_id)
                    if agent:
                        agent_ids.append(agent_id)
                        tasks.append(
                            {
                                "description": subtask,
                                "expected_output": f"Completed: {subtask}",
                            }
                        )
                else:
                    # Create a new agent template based on the type
                    new_agent_prompt = f"""
                    Create an AI agent with the following type: {agent_type}

                    The agent will be responsible for this subtask: {subtask}

                    Generate a JSON object with the following fields:
                    - role: The role or title of the agent (based on the type)
                    - goal: The primary goal or objective of the agent
                    - backstory: A detailed backstory for the agent
                    - tools: A list of tools the agent might need
                    - allow_delegation: Whether the agent can delegate tasks (true/false)
                    - verbose: Whether the agent should be verbose in its responses (true/false)

                    Return only the JSON object, nothing else.
                    """

                    # Query the LLM for agent parameters
                    if self.model_router:
                        agent_response = await self.model_router.generate(
                            new_agent_prompt, required_capabilities=["reasoning"]
                        )
                        agent_json_str = agent_response.get("response", "")
                    else:
                        # Use the default LLM
                        agent_response = requests.post(
                            "http://localhost:11434/api/generate",
                            json={
                                "model": "phind-codellama",
                                "prompt": new_agent_prompt,
                                "stream": False,
                            },
                        )
                        agent_response.raise_for_status()
                        agent_json_str = agent_response.json().get("response", "")

                    # Extract and parse the JSON
                    agent_json_match = re.search(
                        r"```json\n(.*?)\n```", agent_json_str, re.DOTALL
                    )
                    if agent_json_match:
                        agent_json_str = agent_json_match.group(1)
                    else:
                        # Try to find JSON without the markdown code block
                        agent_json_match = re.search(
                            r"(\{.*\})", agent_json_str, re.DOTALL
                        )
                        if agent_json_match:
                            agent_json_str = agent_json_match.group(1)

                    agent_params = json.loads(agent_json_str)

                    # Add the template
                    self.add_template(agent_type, agent_params)

                    # Create the agent
                    agent_id = f"{agent_type}_{asyncio.get_event_loop().time()}"
                    agent = self.create_agent(agent_type, agent_id)
                    if agent:
                        agent_ids.append(agent_id)
                        tasks.append(
                            {
                                "description": subtask,
                                "expected_output": f"Completed: {subtask}",
                            }
                        )

            # Create a crew with the agents
            crew = self.create_crew(agent_ids, tasks)

            return {"agent_ids": agent_ids, "crew": crew, "analysis": analysis}
        except Exception as e:
            logger.error(f"Error analyzing task and creating agents: {str(e)}")
            return {"agent_ids": [], "crew": None, "error": str(e)}


# Example usage
async def main():
    factory = DynamicAgentFactory()

    # Get available templates
    templates = factory.get_template_names()
    print(f"Available templates: {templates}")

    # Create an agent from a template
    agent = factory.create_agent("developer")
    if agent:
        print(f"Created agent: {agent}")

    # Create an agent from a description
    agent_id = await factory.create_agent_from_description(
        "Create an agent that specializes in network traffic analysis and can detect intrusions"
    )
    if agent_id:
        print(f"Created custom agent with ID: {agent_id}")

    # Analyze a task and create appropriate agents
    result = await factory.analyze_task_and_create_agents(
        "Build a web scraper that can extract data from e-commerce websites and store it in a database"
    )
    print(f"Created {len(result['agent_ids'])} agents for the task")

    # Get active agents
    active_agents = factory.get_active_agents()
    print(f"Active agents: {active_agents}")


if __name__ == "__main__":
    asyncio.run(main())

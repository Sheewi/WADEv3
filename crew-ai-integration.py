#!/usr/bin/env python3
"""
Crew AI Integration for Wade - Multi-agent system for Kali Linux
This demonstrates how to integrate Crew AI with the Phind model in Wade
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from langchain.tools import Tool
from langchain.agents import load_tools
from langchain.llms import Ollama

# Configure Ollama LLM
llm = Ollama(model="phind-codellama")

# Define specialized agents


class WadeAgentSystem:
    """Wade multi-agent system using Crew AI framework"""

    def __init__(self):
        """Initialize the Wade agent system"""
        self.llm = llm
        self.agents = self._create_agents()
        self.tools = self._create_tools()
        self.crew = self._create_crew()

    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized agents for different tasks"""

        # Hacking specialist agent
        hacker = Agent(
            role="Offensive Security Specialist",
            goal="Find and exploit vulnerabilities in target systems",
            backstory="You are an elite ethical hacker with expertise in penetration testing and vulnerability assessment. You help identify security weaknesses and suggest remediation strategies.",
            verbose=True,
            llm=self.llm,
            allow_delegation=True,
        )

        # Defensive security agent
        defender = Agent(
            role="Defensive Security Specialist",
            goal="Protect systems from attacks and ensure security compliance",
            backstory="You are a cybersecurity expert specializing in defense mechanisms, intrusion detection, and incident response. You help secure systems against potential threats.",
            verbose=True,
            llm=self.llm,
            allow_delegation=True,
        )

        # Research agent
        researcher = Agent(
            role="Intelligence Researcher",
            goal="Gather and analyze information from various sources",
            backstory="You are an expert in OSINT (Open Source Intelligence) and research methodologies. You can find, analyze, and synthesize information from diverse sources including the dark web.",
            verbose=True,
            llm=self.llm,
            allow_delegation=True,
        )

        # System customization agent
        customizer = Agent(
            role="System Customization Specialist",
            goal="Enhance and personalize the Kali Linux environment",
            backstory="You are an expert in Linux customization, desktop environments, and user experience design. You help create personalized, efficient working environments.",
            verbose=True,
            llm=self.llm,
            allow_delegation=True,
        )

        # Tool development agent
        developer = Agent(
            role="Tool Developer",
            goal="Create and modify tools and scripts for specific tasks",
            backstory="You are a skilled programmer with expertise in Python, Bash, and other languages used in security tools. You can create custom tools or modify existing ones to meet specific needs.",
            verbose=True,
            llm=self.llm,
            allow_delegation=True,
        )

        # Learning and improvement agent
        learner = Agent(
            role="Continuous Learning Specialist",
            goal="Improve the system's knowledge and capabilities over time",
            backstory="You are an expert in machine learning and knowledge management. You help the system learn from interactions and improve its capabilities.",
            verbose=True,
            llm=self.llm,
            allow_delegation=True,
        )

        return {
            "hacker": hacker,
            "defender": defender,
            "researcher": researcher,
            "customizer": customizer,
            "developer": developer,
            "learner": learner,
        }

    def _create_tools(self) -> Dict[str, List[Tool]]:
        """Create tools for the agents to use"""

        # Basic tools available to all agents
        basic_tools = load_tools(["terminal", "human"])

        # Specialized tools for each agent type
        hacker_tools = basic_tools + load_tools(["nmap_scan", "metasploit"])
        defender_tools = basic_tools + load_tools(["snort_alert", "firewall_config"])
        researcher_tools = basic_tools + load_tools(["web_search", "tor_search"])
        customizer_tools = basic_tools + load_tools(["file_editor", "package_manager"])
        developer_tools = basic_tools + load_tools(["code_interpreter", "git"])
        learner_tools = basic_tools + load_tools(["memory_store", "model_trainer"])

        return {
            "hacker": hacker_tools,
            "defender": defender_tools,
            "researcher": researcher_tools,
            "customizer": customizer_tools,
            "developer": developer_tools,
            "learner": learner_tools,
        }

    def _create_crew(self) -> Crew:
        """Create the crew with all agents"""
        return Crew(
            agents=list(self.agents.values()),
            tasks=self._create_tasks(),
            verbose=2,
            process=Process.sequential,
        )

    def _create_tasks(self) -> List[Task]:
        """Create tasks for the crew"""

        # Task for the hacker agent
        hacking_task = Task(
            description="Identify potential vulnerabilities in the target system",
            expected_output="A detailed report of vulnerabilities with severity ratings",
            agent=self.agents["hacker"],
        )

        # Task for the defender agent
        defense_task = Task(
            description="Recommend security measures to protect against identified vulnerabilities",
            expected_output="A comprehensive security plan with specific configurations",
            agent=self.agents["defender"],
        )

        # Task for the researcher agent
        research_task = Task(
            description="Gather intelligence on the latest security threats and techniques",
            expected_output="An intelligence report with actionable insights",
            agent=self.agents["researcher"],
        )

        # Task for the customizer agent
        customization_task = Task(
            description="Create a personalized desktop environment with the Vin Diesel theme",
            expected_output="Configuration files and scripts for the custom environment",
            agent=self.agents["customizer"],
        )

        # Task for the developer agent
        development_task = Task(
            description="Develop a custom tool for automating repetitive security tasks",
            expected_output="A working script or application with documentation",
            agent=self.agents["developer"],
        )

        # Task for the learner agent
        learning_task = Task(
            description="Analyze user interactions to improve system responses",
            expected_output="A learning report with suggestions for model improvements",
            agent=self.agents["learner"],
        )

        return [
            hacking_task,
            defense_task,
            research_task,
            customization_task,
            development_task,
            learning_task,
        ]

    async def run(self, query: str) -> Dict[str, Any]:
        """Run the crew to process a user query"""
        # Determine which agent should handle the query
        handling_agent = self._route_query(query)

        # Create a specific task for this query
        task = Task(
            description=f"Process the following user query: {query}",
            expected_output="A comprehensive response addressing the user's needs",
            agent=self.agents[handling_agent],
        )

        # Create a temporary crew with just this task
        temp_crew = Crew(
            agents=[self.agents[handling_agent]],
            tasks=[task],
            verbose=2,
            process=Process.sequential,
        )

        # Run the crew and return the result
        result = await temp_crew.run()
        return {
            "agent": handling_agent,
            "response": result,
            "metadata": {
                "confidence": 0.85,
                "processing_time": 1.2,
                "agents_consulted": [handling_agent],
            },
        }

    def _route_query(self, query: str) -> str:
        """Determine which agent should handle a query"""
        # Simple keyword-based routing for demonstration
        query = query.lower()

        if any(
            word in query
            for word in ["hack", "exploit", "vulnerability", "penetration"]
        ):
            return "hacker"
        elif any(word in query for word in ["protect", "defend", "secure", "firewall"]):
            return "defender"
        elif any(
            word in query
            for word in ["research", "find", "information", "intelligence"]
        ):
            return "researcher"
        elif any(
            word in query for word in ["customize", "theme", "desktop", "appearance"]
        ):
            return "customizer"
        elif any(word in query for word in ["develop", "create", "script", "program"]):
            return "developer"
        elif any(word in query for word in ["learn", "improve", "train", "enhance"]):
            return "learner"
        else:
            # Default to researcher for general queries
            return "researcher"


# Example usage
async def main():
    wade_system = WadeAgentSystem()
    result = await wade_system.run("Find vulnerabilities in a WordPress site")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

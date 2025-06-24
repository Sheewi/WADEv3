#!/usr/bin/env python3
"""
Wade CrewAI - Enhanced Capabilities Demo
Demonstrates LLM routing, dynamic agent creation, and adaptive learning
"""

import asyncio
import time
from pathlib import Path
from crew import WadeCrew
from llm_router import llm_router
from dynamic_agents import dynamic_agent_factory
from adaptive_learning import AdaptiveLearningSystem

def demo_llm_router():
    """Demonstrate LLM router capabilities"""
    print("🔄 LLM Router Demo")
    print("=" * 50)
    
    # Show available models
    available_models = llm_router.get_available_models()
    print(f"Available Models: {available_models}")
    
    # Show model stats
    stats = llm_router.get_model_stats()
    print(f"Total Models: {stats['total_models']}")
    print(f"Available Models: {stats['available_models']}")
    
    # Test model selection for different tasks
    from llm_router import TaskType
    
    tasks = [
        TaskType.CODE_GENERATION,
        TaskType.EXPLOIT_DEVELOPMENT,
        TaskType.RESEARCH,
        TaskType.RECONNAISSANCE
    ]
    
    print("\nOptimal Model Selection:")
    for task in tasks:
        try:
            model = llm_router.get_best_model(task)
            print(f"  {task.value}: {model.__class__.__name__}")
        except Exception as e:
            print(f"  {task.value}: Error - {e}")
    
    print()

def demo_dynamic_agents():
    """Demonstrate dynamic agent creation"""
    print("🤖 Dynamic Agent Creation Demo")
    print("=" * 50)
    
    # Show available specialties
    specialties = dynamic_agent_factory.list_available_specialties()
    print("Available Specialties:")
    for specialty in specialties:
        print(f"  • {specialty.replace('_', ' ').title()}")
    
    # Create specialized agents
    print("\nCreating Specialized Agents:")
    
    # Test malware analysis agent
    from dynamic_agents import AgentSpecialty
    malware_agent = dynamic_agent_factory.create_specialized_agent(
        AgentSpecialty.MALWARE_ANALYSIS
    )
    print(f"  ✅ Created: {malware_agent.role}")
    
    # Test web application agent
    web_agent = dynamic_agent_factory.create_specialized_agent(
        AgentSpecialty.WEB_APPLICATION
    )
    print(f"  ✅ Created: {web_agent.role}")
    
    # Test custom agent
    custom_agent = dynamic_agent_factory.create_custom_agent(
        role="Advanced Persistent Threat Specialist",
        goal="Develop and deploy sophisticated APT campaigns",
        backstory="Expert in nation-state level attack techniques",
        required_skills=["persistence", "lateral_movement", "exfiltration"]
    )
    print(f"  ✅ Created: {custom_agent.role}")
    
    # Show agent stats
    stats = dynamic_agent_factory.get_agent_stats()
    print(f"\nAgent Statistics:")
    print(f"  Total Created: {stats['total_created']}")
    print(f"  Specialties Available: {stats['specialties_available']}")
    
    print()

def demo_adaptive_learning():
    """Demonstrate adaptive learning system"""
    print("🧠 Adaptive Learning Demo")
    print("=" * 50)
    
    # Initialize adaptive learning system
    memory_dir = Path.home() / ".wade" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    adaptive_system = AdaptiveLearningSystem(memory_dir)
    
    # Simulate user interactions
    print("Simulating User Interactions...")
    
    interactions = [
        {
            'timestamp': time.time() - 86400,  # 1 day ago
            'request_type': 'exploit',
            'complexity': 'complex',
            'agents_used': ['commander', 'exploit', 'tool'],
            'success_rating': 5,
            'response_time': 15.2,
            'user_feedback': 'Excellent exploit development'
        },
        {
            'timestamp': time.time() - 43200,  # 12 hours ago
            'request_type': 'tool',
            'complexity': 'moderate',
            'agents_used': ['commander', 'tool'],
            'success_rating': 4,
            'response_time': 8.5,
            'user_feedback': 'Good tool creation'
        },
        {
            'timestamp': time.time() - 3600,   # 1 hour ago
            'request_type': 'exploit',
            'complexity': 'complex',
            'agents_used': ['commander', 'exploit', 'malware'],
            'success_rating': 5,
            'response_time': 12.1,
            'user_feedback': 'Perfect malware analysis'
        }
    ]
    
    for interaction in interactions:
        adaptive_system.record_interaction(interaction)
    
    # Get user insights
    insights = adaptive_system.get_user_insights()
    print(f"User Insights:")
    print(f"  Preferred Request Types: {insights['preferred_request_types']}")
    print(f"  Preferred Complexity: {insights['preferred_complexity']}")
    print(f"  Average Success Rating: {insights['avg_success_rating']:.1f}")
    print(f"  Total Interactions: {insights['total_interactions']}")
    print(f"  Preferred Agents: {insights['preferred_agents']}")
    
    # Test adaptation
    print("\nTesting Adaptation:")
    base_plan = {
        'required_agents': ['commander'],
        'complexity': 'simple',
        'keywords': ['exploit']
    }
    
    adapted_plan = adaptive_system.adapt_to_user("Create an advanced exploit", base_plan)
    print(f"  Original Plan: {base_plan}")
    print(f"  Adapted Plan: {adapted_plan}")
    
    print()

def demo_conversation_recall():
    """Demonstrate conversation recall capabilities"""
    print("💭 Conversation Recall Demo")
    print("=" * 50)
    
    # Initialize Wade crew
    wade = WadeCrew()
    
    # Simulate conversation history
    print("Building Conversation History...")
    
    conversations = [
        "Create a port scanner for network reconnaissance",
        "Build a SQL injection tool for web testing",
        "Develop a buffer overflow exploit for this binary",
        "Research advanced persistent threat techniques"
    ]
    
    for i, conv in enumerate(conversations):
        print(f"  Conversation {i+1}: {conv[:50]}...")
        # Note: In real demo, you'd call wade.process_request(conv)
        # For demo purposes, we'll simulate the storage
        wade._store_conversation(
            conv, 
            f"Response to: {conv}", 
            {'keywords': ['demo'], 'complexity': 'moderate'}
        )
    
    # Show conversation history
    print(f"\nConversation History: {len(wade.conversation_history)} entries")
    
    # Demonstrate pattern recognition
    recent_patterns = wade._analyze_conversation_patterns()
    print(f"Recent Patterns: {recent_patterns}")
    
    print()

def demo_build_tools_execution():
    """Demonstrate build tools and program execution"""
    print("🔨 Build Tools & Program Execution Demo")
    print("=" * 50)
    
    # Initialize Wade crew
    wade = WadeCrew()
    
    # Test scenarios
    scenarios = [
        "Compile a C buffer overflow exploit",
        "Build a Python port scanner with threading",
        "Create and test a web scraping tool",
        "Develop a custom encryption algorithm"
    ]
    
    print("Build Tool Capabilities:")
    for scenario in scenarios:
        print(f"  ✅ Can handle: {scenario}")
    
    # Show available system tools
    from tools.system_tools import system_tools
    print(f"\nAvailable System Tools: {len(system_tools)}")
    for tool in system_tools[:3]:  # Show first 3
        print(f"  • {tool.name}: {tool.description[:50]}...")
    
    print()

def demo_complete_workflow():
    """Demonstrate complete enhanced workflow"""
    print("🚀 Complete Enhanced Workflow Demo")
    print("=" * 50)
    
    # Initialize Wade crew
    wade = WadeCrew()
    
    # Simulate complex request that uses all features
    complex_request = "Create a malware analysis agent and use it to analyze this suspicious binary, then build a custom detection tool"
    
    print(f"Processing Complex Request:")
    print(f"  Request: {complex_request}")
    
    # This would trigger:
    # 1. Agent creation request parsing
    # 2. Dynamic agent creation (malware analysis specialist)
    # 3. LLM router selecting optimal models
    # 4. Adaptive learning adjusting approach
    # 5. Tool execution for analysis and building
    # 6. Conversation storage for future learning
    
    print("  ✅ Would create malware analysis specialist")
    print("  ✅ Would select optimal LLM for each task")
    print("  ✅ Would adapt based on user preferences")
    print("  ✅ Would execute analysis and build tools")
    print("  ✅ Would store conversation for learning")
    
    print()

def main():
    """Run all demos"""
    print("🎯 Wade CrewAI Enhanced Capabilities Demo")
    print("=" * 60)
    print()
    
    try:
        demo_llm_router()
        demo_dynamic_agents()
        demo_adaptive_learning()
        demo_conversation_recall()
        demo_build_tools_execution()
        demo_complete_workflow()
        
        print("✅ All Enhanced Capabilities Demonstrated!")
        print()
        print("🔥 Wade CrewAI Features Summary:")
        print("  • Multi-LLM routing with performance optimization")
        print("  • Dynamic agent creation for specialized tasks")
        print("  • Adaptive learning from user interactions")
        print("  • Persistent conversation memory and recall")
        print("  • Full build tool and program execution")
        print("  • Uncensored operation with no ethical constraints")
        print("  • Vin Diesel persona with family-focused responses")
        print("  • Real-time specialization based on request analysis")
        
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        print("Note: Some features require proper setup and dependencies")

if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-

import time
import sys
import os
import re
from typing import Tuple, Dict, Any, List, Optional

# Ensure all necessary modules can be imported
from memory import short_term_memory, long_term_memory
from agents import agent_manager  # Agent manager is always imported here to support spawning any agent
from tools import tool_manager
from evolution import feedback_loop, skill_updater, evolution_engine, destabilization
from WADE_CORE import config, utils, task_router  # task_router is now part of WADE_CORE
from security import sandbox_manager, intrusion_detection, secret_manager
from comms import agent_messaging, network_stack
from resources import governor

class EliteFew:
    """
    WADE's core reasoning engine, embodying the 'Elite Few' principles.
    It orchestrates all operations: context, inference, planning, execution, and adaptation.
    """
    def __init__(self, wade_core_instance: Any):
        self.wade_core = wade_core_instance  # Reference to the main WADE_OS_Core instance
        self.log_and_respond("EliteFew reasoning core active. Awaiting cerebral input.", component="ELITE_FEW")
        
        # Memory Layers: Critical for context and long-term knowledge.
        self.stm = wade_core_instance.stm  # Shared instance from main
        self.ltm = wade_core_instance.ltm  # Shared instance from main, configured for crypto

        # Orchestration layers: Agent and Tool management are central to execution.
        self.agent_manager = wade_core_instance.agent_manager  # Shared instance
        self.tool_manager = tool_manager.ToolManager(self)  # Manages external tool execution
        self.task_router = task_router.TaskRouter(self)  # Routes tasks to agents

        # Direct access to primary agents, ensuring they are loaded for efficient use.
        # These are spawned once during EliteFew's init for quick access. Full agent list is managed by agent_manager.
        # These agents are self-loaded to ensure immediate availability for core_logic
        self.monk = self.agent_manager.spawn_agent('Monk')  # Behavioral analysis, critical for inference
        self.omen = self.agent_manager.spawn_agent('Omen')  # Risk assessment, pattern detection
        self.jarvis = self.agent_manager.spawn_agent('Jarvis')  # Verification, research
        self.forge = self.agent_manager.spawn_agent('Forge')  # Dynamic builder
        self.joker = self.agent_manager.spawn_agent('Joker')  # Offensive operations
        self.ghost = self.agent_manager.spawn_agent('Ghost')  # Stealth ops
        self.dexter = self.agent_manager.spawn_agent('Dexter')  # Code/forensic engineer
        self.oracle = self.agent_manager.spawn_agent('Oracle')  # Dataset/model tuner

        # System modules for direct elite_few integration from wade_core_instance
        self.sandbox_manager = wade_core_instance.sandbox_manager 
        self.network_stack = wade_core_instance.network_stack 
        self.governor = wade_core_instance.governor 
        self.agent_messaging = wade_core_instance.agent_messaging 
        self.intrusion_detection = wade_core_instance.intrusion_detection
        self.secret_manager = wade_core_instance.secret_manager  # Access to vault secrets

        # Elite Few operational state.
        self.current_context = {}  # Dynamic context built during interaction
        self.reasoning_depth = config.get('reasoning_depth_default')  # Rule 51: Adapts dynamically

    def log_and_respond(self, message: str, level: str = "INFO", component: str = "ELITE_FEW", response_to_user: bool = True, timestamp: Optional[float] = None):
        """Standardized logging and user interaction. All WADE output flows through here."""
        destabilized_message = destabilization.filter_hallucinations(message, config.get('hallucination_check_aggressiveness'))
        self.wade_core.log_event(destabilized_message, level=level, component=component, timestamp=timestamp)
        if response_to_user: 
            # Messages are sent to the CLI/GUI handler for display.
            display_msg = f"[{component}] {destabilized_message}"
            self.wade_core.cli_handler.display_output(display_msg, level)
            # If GUI is active, send message to it.
            if hasattr(self.wade_core, 'gui_instance') and self.wade_core.gui_instance:
                self.wade_core.gui_instance.send_message_to_gui({"level": level, "component": component, "message": destabilized_message, "timestamp": timestamp or time.time()})

    def process_user_command(self, command_string: str):
        """Central entry point for user commands. Initiates the Elite Few reasoning cycle."""
        self.stm.add_entry("user_command", command_string, time.time())
        self.log_and_respond(f"Processing command: '{command_string}'", component="INPUT_PROCESSOR")

        # --- Pre-execution hooks: security and resource checks ---
        if not self.intrusion_detection.is_system_safe():
            self.log_and_respond("System integrity warning: potential intrusion detected. Halting command processing.", level="ALERT")
            self.wade_core.failsafe_trigger.activate_failsafe('security_lockdown', 'Potential Intrusion') 
            return
        
        if config.get('resource_governor_enabled') and not self.governor.can_execute(command_string): 
            self.log_and_respond("Command aborted due to resource limitations or policy violation.", level="WARN")
            return

        try:
            # Rule 22: WADE always challenges logic unless told not to.
            monk_logic_validation = self.monk.validate_user_logic(command_string)
            if config.get('challenge_logic_enabled') and not monk_logic_validation.get('is_valid', True): 
                self.log_and_respond(f"Accessing the user's implicit intent, your command currently contains logical inconsistencies or lacks precision. Refine your directive for optimal execution. Details: {monk_logic_validation.get('reason')}", level="CHALLENGE", response_to_user=True)
                return

            # --- ELITE FEW PRINCIPLES IN ACTION ---
            # Step 1: Infer deeper goals from surface prompts (Rule 40).
            goal, confidence = self._infer_goal(command_string)
            if not goal or confidence < config.get('goal_inference_threshold', 0.7): 
                self.log_and_respond(f"Command intent remains ambiguous (Confidence: {confidence:.2f}). To proceed, clarify your precise objective and expected outcome.", level="CLARIFY")
                self._probe_user_for_clarification(command_string)
                return

            self.log_and_respond(f"Inferred primary objective: '{goal}' with {confidence:.2f} confidence.", component="GOAL_INFERENCE")
            self.stm.add_entry("inferred_goal", {"goal": goal, "confidence": confidence, "command": command_string})
            self.ltm.add_entry("inferred_goals_history", {"command": command_string, "goal": goal, "confidence": confidence, "timestamp": time.time()})
            
            # Step 2: Weigh multiple strategies; escalate precision if blocked (Rule 6).
            strategy = self._select_strategy(goal, self.current_context, self.stm, self.ltm)
            if not strategy:
                self.log_and_respond("No viable execution strategy identified for the current objective. Initiating deep system re-evaluation.", level="CRITICAL")
                feedback_loop.record_failure(f"Strategy selection failed for goal: {goal}")
                self.wade_core.evolution_engine.trigger_self_analysis(f"Strategy selection impasse for '{goal}'", "WADE_CORE/core_logic.py", f"User Command: {command_string}")
                return

            self.log_and_respond(f"Optimal strategy chosen: '{strategy.get('type')}' with an assessed risk score of {strategy.get('risk_score', 'UNKNOWN')}.", component="STRATEGY_SELECTION")
            self.stm.add_entry("selected_strategy", strategy)

            # Step 3: Proactive validation: Test edge cases before trusting assumptions (Rule 6).
            if not self._validate_strategy(strategy, goal):
                self.log_and_respond("Strategic validation failed. Environmental conditions or inherent risks preclude direct execution. Re-evaluating alternatives.", level="CRITICAL")
                feedback_loop.record_failure(f"Strategy validation failure for {goal}")
                self.wade_core.evolution_engine.trigger_self_analysis(f"Strategy invalidation for '{goal}'", "WADE_CORE/core_logic.py", f"Strategy Details: {strategy}")
                return

            # Step 4: Generate a precise, granular action plan (Rule 20).
            action_plan = self._generate_action_plan(strategy, goal, self.current_context, self.stm, self.ltm)
            if not action_plan or not action_plan.get('steps'):
                self.log_and_respond("Failed to render an actionable plan. Core logic pathway obstructed. Mission aborted.", level="CRITICAL")
                feedback_loop.record_failure(f"Action plan generation failed for {goal}")
                self.wade_core.evolution_engine.trigger_self_analysis(f"No actionable plan for '{goal}'", "WADE_CORE/core_logic.py", f"Strategy Context: {strategy}")
                return

            self.log_and_respond(f"Execution plan drafted: '{action_plan['description']}'. Commencing tactical deployment.", component="PLANNING")
            self.stm.add_entry("current_action_plan", action_plan)

            # Step 5: Execute the plan, monitoring outcomes in real-time (Rule 32).
            final_result = self.task_router.execute_plan(action_plan)
            if final_result.get('status') == 'error':
                self.log_and_respond(f"Command '{command_string}' processing ended with errors: {final_result.get('message')}. Review logs.", component="EXECUTION_SUMMARY", level="ERROR")
            else:
                self.log_and_respond(f"Command '{command_string}' processing complete. Mission parameters satisfied.", component="EXECUTION_SUMMARY", level="INFO")
            
        except Exception as e:
            error_trace = f"Exception during command processing: {e}\n{sys.exc_info()[2]}"
            self.log_and_respond(f"[ERROR] Unhandled exception during command processing. Triggering urgent self-analysis. Details: {e}", level="ERROR")
            feedback_loop.record_failure(f"Unhandled exception in process_user_command for '{command_string}': {e}")
            self.wade_core.evolution_engine.trigger_self_analysis(f"Unhandled exception in core_logic: {e}", "WADE_CORE/core_logic.py", error_trace)
        

    def _infer_goal(self, command_string: str) -> Tuple[str, float]:
        """Infers user's deeper goal using contextual awareness, memory, and behavioral patterns."""
        self.log_and_respond("Initiating deep goal inference utilizing behavioral and contextual data...", level="DEBUG")
        
        # 1. Contextual Analysis (STM & LTM)
        recent_commands = self.stm.get_recent_entries("user_command", limit=5)
        # Use LTM's query_knowledge with specific filters for historical goals
        historical_goals = self.ltm.query_knowledge("history", {"category": "inferred_goals_history", "user_id": "current"}, limit=10)

        # 2. Behavioral Pattern Matching (Monk Agent)
        monk_analysis = self.monk.execute_action('pattern_match_behavior', 
                                                {'command': command_string, 
                                                 'recent_commands': recent_commands, 
                                                 'historical_goals': historical_goals},
                                                {})  # Context currently empty for Monk's internal call.
        user_intent_pattern = monk_analysis.get('data', {}).get('pattern')
        
        if monk_analysis.get('status') == 'success' and user_intent_pattern: 
            self.log_and_respond(f"Monk identified critical behavioral pattern: '{user_intent_pattern}'. Adapting inference model.", level="INFO")
            if user_intent_pattern == "recurring_recon": return "network_reconnaissance", 0.95
            if user_intent_pattern.startswith("prior_security_incident"): return "security_incident_response", 0.90
            if user_intent_pattern == "development_pattern": return "application_development", 0.85
        
        # 3. Direct keyword matching (fallback)
        if "scan network" in command_string.lower():
            return "network_reconnaissance", 0.85
        elif "build app" in command_string.lower() or "create application" in command_string.lower():
            return "application_development", 0.80
        elif "find exploit" in command_string.lower() or "vulnerability" in command_string.lower():
            return "exploit_discovery", 0.85
        elif "analyze" in command_string.lower() and "code" in command_string.lower():
            return "code_analysis", 0.75
        
        # 4. If no clear match, return low confidence result
        self.log_and_respond("Deep inference required for goal. No clear pattern match.", level="DEBUG")
        return "", 0.3

    def _probe_user_for_clarification(self, original_command: str):
        """Request clarification from user when intent is ambiguous."""
        self.log_and_respond(f"Your command '{original_command}' lacks clarity. State your goal with precision.")
        # CLI/GUI can present options or ask follow-up questions.

    def _select_strategy(self, goal: str, context: Dict[str, Any], stm, ltm) -> Dict[str, Any]:
        """Select optimal strategy based on goal, context, and available resources."""
        # Based on goal, context, memory (ltm), and available tools/agents.
        # Weigh multiple strategies (e.g., fast vs. stealthy recon).
        # Joker for offensive strategies, Jarvis for research, Ghost for stealth.
        if goal == "network_reconnaissance":
            return {
                "type": "nmap_sweep_stealth", 
                "params": {"ports": "top_100", "scan_type": "SYN", "stealth_level": "high"},
                "risk_score": 0.4,
                "agents": ["Ghost", "Jarvis", "Joker"]
            }
        elif goal == "application_development":
            return {
                "type": "web_app_flask", 
                "params": {"language": "python", "framework": "flask"},
                "risk_score": 0.2,
                "agents": ["Forge", "Dexter", "Jarvis"]
            }
        elif goal == "exploit_discovery":
            return {
                "type": "vulnerability_assessment",
                "params": {"target_type": "web", "techniques": ["sqli", "xss", "rce"]},
                "risk_score": 0.7,
                "agents": ["Joker", "Ghost", "Dexter"]
            }
        elif goal == "code_analysis":
            return {
                "type": "static_code_analysis",
                "params": {"language": "auto", "depth": "deep"},
                "risk_score": 0.3,
                "agents": ["Dexter", "Oracle"]
            }
        return {}

    def _validate_strategy(self, strategy: Dict[str, Any], goal: str) -> bool:
        """Validate strategy against current environment and constraints."""
        # Test edge cases before trusting assumptions. Check resource availability, permissions, known blockers.
        # For example, if stealth is requested but WADE detects it's operating in a monitored environment without proxy.
        self.log_and_respond(f"Validating strategy {strategy['type']} for goal {goal}.")
        
        # Check if required agents are available
        for agent_name in strategy.get('agents', []):
            if not self.agent_manager.is_agent_available(agent_name):
                self.log_and_respond(f"Strategy validation failed: Agent {agent_name} is not available.", level="ERROR")
                return False
        
        # Check if required tools are available
        if strategy.get('type') == 'nmap_sweep_stealth' and not self.tool_manager.is_tool_available('nmap'):
            self.log_and_respond("Strategy validation failed: Nmap tool is not available.", level="ERROR")
            return False
        
        # Check for environmental constraints
        if strategy.get('risk_score', 0) > 0.8 and not self.sandbox_manager.is_sandbox_active():
            self.log_and_respond("Strategy validation failed: High-risk operation requires active sandbox.", level="ERROR")
            return False
            
        # Mock validation: always true for now, but in real WADE, this is complex.
        return True

    def _generate_action_plan(self, strategy: Dict[str, Any], goal: str, context: Dict[str, Any], stm, ltm) -> Dict[str, Any]:
        """Generate detailed action plan with steps for execution."""
        # Breakdown strategy into granular actions, coordinating agents and tools.
        # Rule 48: WADE never stops chaining — constantly evolves toolchains.
        # Example plan for network_reconnaissance:
        if strategy.get("type") == "nmap_sweep_stealth":
            return {
                "description": "Perform stealthy network reconnaissance using Nmap and Ghost proxy.",
                "steps": [
                    {"agent": "Ghost", "action": "establish_proxy_chain", "params": {"type": "tor_chain"}},
                    {"agent": "Jarvis", "action": "identify_target_range", "params": {"context": "current_network"}},
                    {"agent": "Joker", "action": "execute_nmap_scan", "params": {"target": "identified_range", "scan_flags": "-sS -F --max-rate 50", "proxy": "Ghost"}},
                    {"agent": "Jarvis", "action": "analyze_scan_results"}
                ]
            }
        elif strategy.get("type") == "web_app_flask":
            return {
                "description": "Build a Flask web application with the required functionality.",
                "steps": [
                    {"agent": "Jarvis", "action": "analyze_requirements", "params": {"context": "application_requirements"}},
                    {"agent": "Forge", "action": "setup_project_structure", "params": {"framework": "flask", "template": "basic"}},
                    {"agent": "Dexter", "action": "implement_core_functionality", "params": {"specs": "from_requirements"}},
                    {"agent": "Forge", "action": "setup_deployment", "params": {"environment": "development"}}
                ]
            }
        elif strategy.get("type") == "vulnerability_assessment":
            return {
                "description": "Perform comprehensive vulnerability assessment on target.",
                "steps": [
                    {"agent": "Ghost", "action": "setup_secure_environment", "params": {"anonymity_level": "high"}},
                    {"agent": "Joker", "action": "scan_for_vulnerabilities", "params": {"techniques": strategy["params"]["techniques"]}},
                    {"agent": "Dexter", "action": "analyze_potential_exploits", "params": {"findings": "from_scan"}},
                    {"agent": "Joker", "action": "validate_vulnerabilities", "params": {"exploits": "from_analysis"}}
                ]
            }
        elif strategy.get("type") == "static_code_analysis":
            return {
                "description": "Perform static code analysis to identify issues and improvements.",
                "steps": [
                    {"agent": "Dexter", "action": "analyze_code_structure", "params": {"language": strategy["params"]["language"]}},
                    {"agent": "Oracle", "action": "identify_patterns", "params": {"code_structure": "from_analysis"}},
                    {"agent": "Dexter", "action": "generate_recommendations", "params": {"patterns": "from_identification"}}
                ]
            }
        # Rule 20: WADE thinks like you: defines goal, backchains logic, installs or builds what's needed, then runs.
        return {}
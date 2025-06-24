#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
import time
import logging

# Ensure /WADE is in path for internal imports
def setup_environment():
    wade_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if wade_root not in sys.path:
        sys.path.insert(0, wade_root)

    # Set up runtime directories if they don't exist
    os.makedirs(os.path.join(wade_root, 'WADE_RUNTIME', 'temp'), exist_ok=True)
    os.makedirs(os.path.join(wade_root, 'WADE_RUNTIME', 'logs'), exist_ok=True)

    # Ensure event_timeline.json exists
    timeline_path = os.path.join(wade_root, 'WADE_RUNTIME', 'logs', 'event_timeline.json')
    if not os.path.exists(timeline_path):
        with open(timeline_path, 'w') as f:
            json.dump([], f)  # Start with an empty JSON array

setup_environment()

from WADE_CORE import config, core_logic
from interface import cli_handler, gui_overlay
from agents import agent_manager
from evolution import evolution_engine
from memory import short_term_memory, long_term_memory
from comms import agent_messaging, network_stack
from security import sandbox_manager, intrusion_detection, secret_manager
from resources import governor

class WADE_OS_Core:
    """
    Central orchestrator for the WADE OS system.
    Manages the lifecycle, components, and core operations.
    """
    def __init__(self):
        self.is_running = True
        self.log_event("WADE_OS_Core initialized.")
        self.load_configuration()
        
        # Initialize core components
        self.stm = short_term_memory.ShortTermMemory()
        self.ltm = long_term_memory.LongTermMemory()
        self.network_stack = network_stack.NetworkStack()
        self.agent_messaging = agent_messaging.AgentMessaging()
        self.sandbox_manager = sandbox_manager.SandboxManager()
        self.governor = governor.ResourceGovernor()
        self.intrusion_detection = intrusion_detection.IntrusionDetection()
        self.secret_manager = secret_manager.SecretManager()
        self.failsafe_trigger = FailsafeTrigger(self)
        
        # Initialize core logic and agents
        self.elite_few = core_logic.EliteFew(self)
        self.agent_manager = agent_manager.AgentManager(self.elite_few)
        self.evolution_engine = evolution_engine.EvolutionEngine(self.elite_few)
        self.cli_handler = cli_handler.CLIHandler(self.elite_few)
        self.gui_instance = None

    def load_configuration(self):
        # Configuration is dynamic and can be modified by WADE itself
        config.load_config()
        self.log_event(f"Configuration loaded: {config.get('system_id', 'N/A')}")

    def log_event(self, message, level="INFO", component="CORE", timestamp=None):
        timestamp = timestamp or time.time()
        event = {
            "timestamp": timestamp,
            "level": level,
            "component": component,
            "message": message
        }
        timeline_path = os.path.join(os.path.dirname(__file__), '..', 'WADE_RUNTIME', 'logs', 'event_timeline.json')
        try:
            with open(timeline_path, 'r+') as f:
                data = json.load(f)
                data.append(event)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
        except Exception as e:
            print(f"[ERROR] Failed to log event: {e}")  # Fallback for critical logging failure

    def start_gui(self):
        """Initialize and start the GUI overlay in a separate thread."""
        if not hasattr(self, 'gui_instance') or not self.gui_instance:
            self.log_event("Starting GUI overlay in a separate thread.")
            # gui_overlay.initialize_gui returns the GUIOverlay instance to allow sending messages later.
            # The thread management is handled within initialize_gui to encapsulate Flask/WebSocket specifics.
            try:
                self.gui_instance = gui_overlay.initialize_gui(self.elite_few, self.cli_handler)
                if not self.gui_instance:  # If GUI failed to initialize
                    self.log_event("GUI failed to initialize. Proceeding in CLI-only mode.", level="ERROR", component="GUI_INIT")
            except Exception as e:
                self.log_event(f"Exception during GUI initialization: {e}. Proceeding in CLI-only mode.", level="ERROR", component="GUI_INIT")
                self.gui_instance = None  # Ensure it's None if creation failed
        else:
            self.log_event("GUI thread already running.", level="DEBUG", component="GUI_INIT")

    def run(self):
        """The main operational loop of WADE. Continuous interaction and execution."""
        self.log_event("WADE_OS initiating main operational cycle. Your digital intelligence is online.", component="OPERATION_START")
        self.start_gui()  # Ensure GUI is ready prior to interaction

        while self.is_running:
            try:
                # CLI input is primary, but GUI can also inject commands (Rule 7).
                user_input = self.cli_handler.get_input(f"\n[{config.get('system_id')}]-WADE> ")
                
                if user_input.lower().strip() == 'exit':
                    self.is_running = False
                    self.log_event("User initiated graceful shutdown. Protocols disengaging.", component="SHUTDOWN_REQ")
                    break
                
                if user_input.lower().strip() == 'emergency_wipe':  # Direct invocation of failsafe
                    self.elite_few.log_and_respond("EMERGENCY WIPE PROTOCOL ACTIVATED. SYSTEM NEUTRALIZATION INITIATED.", level="CRITICAL", response_to_user=True)
                    self.failsafe_trigger.activate_failsafe('perform_secure_wipe', 'User Activated')
                    self.is_running = False  # System will self-destruct or reboot into neutral state
                    break

                if user_input.strip():  # Process only non-empty commands
                    self.elite_few.process_user_command(user_input)
                
            except KeyboardInterrupt:
                self.log_event("KeyboardInterrupt detected. Initiating emergency shutdown sequence.", level="CRITICAL", component="SHUTDOWN_REQ")
                self.is_running = False
            except Exception as e:
                error_msg = f"Critical error in main loop: {e}. Traceback: {sys.exc_info()}"
                self.elite_few.log_and_respond(f"[ERROR] Unhandled exception during command processing. Triggering self-analysis. Details: {e}", level="ERROR", component="MAIN_LOOP_ERROR")
                self.evolution_engine.trigger_self_analysis(f"Unhandled exception in Main Loop: {e}", "WADE_CORE/main.py", error_msg)
                time.sleep(1)  # Prevent rapid error loop in case of recurring critical issue

        self.shutdown()

    def shutdown(self):
        """Graceful shutdown sequence: ensures data integrity and resource release."""
        self.log_event("WADE_OS executing shutdown sequence. Preserving state...", level="INFO", component="SHUTDOWN")
        self.agent_manager.terminate_all_agents()
        self.network_stack.shutdown()  # Close network connections gracefully
        self.agent_messaging.shutdown()  # Close inter-agent comms
        if self.intrusion_detection: self.intrusion_detection.stop_monitoring()  # Stop IDS
        config.save_config()  # Persist any runtime config changes.
        self.log_event("WADE_OS shutdown complete. Master protocols disengaged.", level="INFO", component="SHUTDOWN")
        sys.exit(0)


class FailsafeTrigger:
    """Handles emergency protocols and failsafe mechanisms"""
    
    def __init__(self, wade_core):
        self.wade_core = wade_core
        
    def activate_failsafe(self, failsafe_type, reason):
        """Activate a specific failsafe protocol"""
        self.wade_core.log_event(f"FAILSAFE ACTIVATED: {failsafe_type} - Reason: {reason}", 
                                level="CRITICAL", component="FAILSAFE")
        
        if failsafe_type == 'security_lockdown':
            # Implement security lockdown protocol
            pass
        elif failsafe_type == 'perform_secure_wipe':
            # Implement secure wipe protocol
            pass
        # Add more failsafe types as needed


if __name__ == "__main__":
    # Ensure WADE runs with maximum environmental control from the start.
    if os.geteuid() != 0:
        logging.warning("WADE is not running as root. Functionality will be limited. For full environmental control, run with 'sudo' or via 'wade.service'.")
    
    wade = WADE_OS_Core()
    wade.run()
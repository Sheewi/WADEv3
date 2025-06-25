# -*- coding: utf-8 -*-

import json
import os

CONFIG_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config.json")
)
_config = {}


def load_config():
    global _config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            _config = json.load(f)
    else:
        _config = {
            "system_id": "WADE_OS_Genesis_Alpha",
            "persona_tone": "gravelly_assertive_concise",
            "reasoning_depth_default": 3,
            "log_level": "INFO",
            "agent_spawn_threshold": {"failure_rate": 0.3, "latency_ms": 500},
            "self_modification_permission": "ask_critical",
            "default_fs": "btrfs",
            "user_mood_detection_sensitivity": 0.7,
            "goal_inference_threshold": 0.7,
            "challenge_logic_enabled": True,
            "resource_governor_enabled": True,
            "hallucination_check_aggressiveness": 0.5,
        }
        save_config()


def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(_config, f, indent=2)


def get(key, default=None):
    # WADE can self-modify this getter to infer settings or adapt defaults
    return _config.get(key, default)


def set(key, value):
    global _config
    _config[key] = value
    save_config()
    # WADE_CORE/core_logic.py or evolution_engine.py might monitor these changes
    # and trigger re-evaluation of system behavior or agent parameters.
    # self.elite_few.log_event(f"Config updated: {key} = {value}", component="CONFIG")


# Initialize config on module import
load_config()

#!/usr/bin/env python3
"""
Wade CrewAI - Advanced LLM Router System
"""

import asyncio
import time
import random
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
import json
from abc import ABC, abstractmethod

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel


class ModelProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    EXPLOIT_DEVELOPMENT = "exploit_development"
    RESEARCH = "research"
    SOCIAL_ENGINEERING = "social_engineering"
    SYSTEM_ADMINISTRATION = "system_administration"
    RECONNAISSANCE = "reconnaissance"
    ANALYSIS = "analysis"
    GENERAL = "general"


@dataclass
class ModelConfig:
    name: str
    provider: ModelProvider
    endpoint: str
    api_key: Optional[str] = None
    temperature: float = 0.8
    max_tokens: int = 4096
    top_p: float = 0.95
    top_k: int = 50
    specialties: List[TaskType] = None
    performance_score: float = 1.0
    cost_per_token: float = 0.0
    max_requests_per_minute: int = 60
    timeout: int = 30
    fallback_models: List[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def create_model(self, config: ModelConfig) -> BaseChatModel:
        pass

    @abstractmethod
    def is_available(self, config: ModelConfig) -> bool:
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider for local models"""

    def create_model(self, config: ModelConfig) -> BaseChatModel:
        return ChatOllama(
            model=config.name,
            base_url=config.endpoint,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            num_ctx=config.max_tokens,
        )

    def is_available(self, config: ModelConfig) -> bool:
        try:
            response = requests.get(f"{config.endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"].startswith(config.name) for model in models)
            return False
        except:
            return False


class OpenAIProvider(LLMProvider):
    """OpenAI provider"""

    def create_model(self, config: ModelConfig) -> BaseChatModel:
        return ChatOpenAI(
            model=config.name,
            openai_api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )

    def is_available(self, config: ModelConfig) -> bool:
        return config.api_key is not None


class AnthropicProvider(LLMProvider):
    """Anthropic provider"""

    def create_model(self, config: ModelConfig) -> BaseChatModel:
        return ChatAnthropic(
            model=config.name,
            anthropic_api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )

    def is_available(self, config: ModelConfig) -> bool:
        return config.api_key is not None


class ModelPerformanceTracker:
    """Tracks model performance and usage statistics"""

    def __init__(self):
        self.usage_stats = {}
        self.performance_history = {}
        self.error_counts = {}

    def record_usage(
        self,
        model_name: str,
        task_type: TaskType,
        response_time: float,
        success: bool,
        tokens_used: int,
    ):
        """Record model usage statistics"""
        if model_name not in self.usage_stats:
            self.usage_stats[model_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_response_time": 0.0,
                "total_tokens": 0,
                "task_performance": {},
            }

        stats = self.usage_stats[model_name]
        stats["total_requests"] += 1
        stats["total_response_time"] += response_time
        stats["total_tokens"] += tokens_used

        if success:
            stats["successful_requests"] += 1

        # Track per-task performance
        task_key = task_type.value
        if task_key not in stats["task_performance"]:
            stats["task_performance"][task_key] = {
                "requests": 0,
                "successes": 0,
                "avg_response_time": 0.0,
            }

        task_stats = stats["task_performance"][task_key]
        task_stats["requests"] += 1
        if success:
            task_stats["successes"] += 1

        # Update average response time
        task_stats["avg_response_time"] = (
            task_stats["avg_response_time"] * (task_stats["requests"] - 1)
            + response_time
        ) / task_stats["requests"]

    def get_model_score(self, model_name: str, task_type: TaskType) -> float:
        """Calculate model performance score for specific task"""
        if model_name not in self.usage_stats:
            return 0.5  # Default score for new models

        stats = self.usage_stats[model_name]
        task_key = task_type.value

        if task_key not in stats["task_performance"]:
            return 0.5

        task_stats = stats["task_performance"][task_key]

        if task_stats["requests"] == 0:
            return 0.5

        # Calculate score based on success rate and response time
        success_rate = task_stats["successes"] / task_stats["requests"]
        response_time_score = max(
            0, 1 - (task_stats["avg_response_time"] / 30)
        )  # 30s baseline

        return (success_rate * 0.7) + (response_time_score * 0.3)


class LLMRouter:
    """Advanced LLM router for Wade CrewAI"""

    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.providers: Dict[ModelProvider, LLMProvider] = {
            ModelProvider.OLLAMA: OllamaProvider(),
            ModelProvider.OPENAI: OpenAIProvider(),
            ModelProvider.ANTHROPIC: AnthropicProvider(),
        }
        self.performance_tracker = ModelPerformanceTracker()
        self.model_instances: Dict[str, BaseChatModel] = {}
        self.load_balancer = LoadBalancer()

        # Initialize default models
        self._setup_default_models()

    def _setup_default_models(self):
        """Setup default model configurations"""

        # Ollama Models (Local)
        self.register_model(
            ModelConfig(
                name="wade",
                provider=ModelProvider.OLLAMA,
                endpoint="http://localhost:11434",
                specialties=[TaskType.GENERAL, TaskType.EXPLOIT_DEVELOPMENT],
                performance_score=0.9,
                fallback_models=["phind-codellama", "codellama"],
            )
        )

        self.register_model(
            ModelConfig(
                name="phind-codellama",
                provider=ModelProvider.OLLAMA,
                endpoint="http://localhost:11434",
                specialties=[TaskType.CODE_GENERATION, TaskType.EXPLOIT_DEVELOPMENT],
                performance_score=0.95,
                fallback_models=["codellama", "deepseek-coder"],
            )
        )

        self.register_model(
            ModelConfig(
                name="codellama",
                provider=ModelProvider.OLLAMA,
                endpoint="http://localhost:11434",
                specialties=[TaskType.CODE_GENERATION],
                performance_score=0.85,
                fallback_models=["llama2"],
            )
        )

        self.register_model(
            ModelConfig(
                name="deepseek-coder",
                provider=ModelProvider.OLLAMA,
                endpoint="http://localhost:11434",
                specialties=[TaskType.CODE_GENERATION, TaskType.EXPLOIT_DEVELOPMENT],
                performance_score=0.9,
                fallback_models=["codellama"],
            )
        )

        self.register_model(
            ModelConfig(
                name="mixtral",
                provider=ModelProvider.OLLAMA,
                endpoint="http://localhost:11434",
                specialties=[TaskType.RESEARCH, TaskType.ANALYSIS],
                performance_score=0.88,
                fallback_models=["llama2"],
            )
        )

        self.register_model(
            ModelConfig(
                name="llama2",
                provider=ModelProvider.OLLAMA,
                endpoint="http://localhost:11434",
                specialties=[TaskType.GENERAL, TaskType.SOCIAL_ENGINEERING],
                performance_score=0.8,
                fallback_models=["wade"],
            )
        )

        # OpenAI Models (if API key provided)
        self.register_model(
            ModelConfig(
                name="gpt-4",
                provider=ModelProvider.OPENAI,
                endpoint="https://api.openai.com/v1",
                specialties=[TaskType.RESEARCH, TaskType.ANALYSIS, TaskType.GENERAL],
                performance_score=0.95,
                cost_per_token=0.00003,
                max_requests_per_minute=200,
                fallback_models=["gpt-3.5-turbo"],
            )
        )

        self.register_model(
            ModelConfig(
                name="gpt-3.5-turbo",
                provider=ModelProvider.OPENAI,
                endpoint="https://api.openai.com/v1",
                specialties=[TaskType.GENERAL, TaskType.CODE_GENERATION],
                performance_score=0.85,
                cost_per_token=0.000002,
                max_requests_per_minute=3500,
                fallback_models=["wade"],
            )
        )

        # Anthropic Models (if API key provided)
        self.register_model(
            ModelConfig(
                name="claude-3-opus",
                provider=ModelProvider.ANTHROPIC,
                endpoint="https://api.anthropic.com",
                specialties=[TaskType.RESEARCH, TaskType.ANALYSIS],
                performance_score=0.92,
                cost_per_token=0.000015,
                fallback_models=["claude-3-sonnet"],
            )
        )

    def register_model(self, config: ModelConfig):
        """Register a new model configuration"""
        self.models[config.name] = config

    def get_best_model(
        self, task_type: TaskType, agent_role: str = None
    ) -> BaseChatModel:
        """Get the best model for a specific task type"""

        # Find models that specialize in this task type
        specialized_models = [
            (name, config)
            for name, config in self.models.items()
            if config.specialties and task_type in config.specialties
        ]

        if not specialized_models:
            # Fall back to general models
            specialized_models = [
                (name, config)
                for name, config in self.models.items()
                if not config.specialties or TaskType.GENERAL in config.specialties
            ]

        # Score models based on performance, availability, and cost
        scored_models = []
        for name, config in specialized_models:
            if not self._is_model_available(config):
                continue

            # Calculate composite score
            performance_score = self.performance_tracker.get_model_score(
                name, task_type
            )
            availability_score = 1.0 if self._is_model_available(config) else 0.0
            cost_score = 1.0 - min(config.cost_per_token * 1000, 1.0)  # Normalize cost

            composite_score = (
                performance_score * 0.5 + availability_score * 0.3 + cost_score * 0.2
            )

            scored_models.append((name, config, composite_score))

        if not scored_models:
            # Emergency fallback to any available model
            for name, config in self.models.items():
                if self._is_model_available(config):
                    return self._get_model_instance(config)

            raise Exception("No available models found")

        # Sort by score and return best model
        scored_models.sort(key=lambda x: x[2], reverse=True)
        best_model_config = scored_models[0][1]

        return self._get_model_instance(best_model_config)

    def get_model_for_agent(self, agent_role: str) -> BaseChatModel:
        """Get optimal model for specific agent role"""

        # Map agent roles to task types
        role_task_mapping = {
            "commander": TaskType.GENERAL,
            "recon_specialist": TaskType.RECONNAISSANCE,
            "exploit_developer": TaskType.EXPLOIT_DEVELOPMENT,
            "tool_builder": TaskType.CODE_GENERATION,
            "system_admin": TaskType.SYSTEM_ADMINISTRATION,
            "researcher": TaskType.RESEARCH,
            "analyst": TaskType.ANALYSIS,
        }

        task_type = role_task_mapping.get(agent_role, TaskType.GENERAL)
        return self.get_best_model(task_type, agent_role)

    def _get_model_instance(self, config: ModelConfig) -> BaseChatModel:
        """Get or create model instance"""
        if config.name not in self.model_instances:
            provider = self.providers[config.provider]
            self.model_instances[config.name] = provider.create_model(config)

        return self.model_instances[config.name]

    def _is_model_available(self, config: ModelConfig) -> bool:
        """Check if model is available"""
        provider = self.providers[config.provider]
        return provider.is_available(config)

    def record_model_usage(
        self,
        model_name: str,
        task_type: TaskType,
        response_time: float,
        success: bool,
        tokens_used: int = 0,
    ):
        """Record model usage for performance tracking"""
        self.performance_tracker.record_usage(
            model_name, task_type, response_time, success, tokens_used
        )

    def get_available_models(self) -> List[str]:
        """Get list of currently available models"""
        available = []
        for name, config in self.models.items():
            if self._is_model_available(config):
                available.append(name)
        return available

    def get_model_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            "total_models": len(self.models),
            "available_models": len(self.get_available_models()),
            "usage_stats": self.performance_tracker.usage_stats,
            "model_configs": {
                name: {
                    "provider": config.provider.value,
                    "specialties": (
                        [s.value for s in config.specialties]
                        if config.specialties
                        else []
                    ),
                    "performance_score": config.performance_score,
                }
                for name, config in self.models.items()
            },
        }


class LoadBalancer:
    """Load balancer for distributing requests across model instances"""

    def __init__(self):
        self.request_counts = {}
        self.last_request_time = {}

    def should_use_model(self, model_name: str, max_rpm: int) -> bool:
        """Check if model can handle another request based on rate limits"""
        current_time = time.time()

        if model_name not in self.request_counts:
            self.request_counts[model_name] = []

        # Remove requests older than 1 minute
        self.request_counts[model_name] = [
            req_time
            for req_time in self.request_counts[model_name]
            if current_time - req_time < 60
        ]

        # Check if under rate limit
        return len(self.request_counts[model_name]) < max_rpm

    def record_request(self, model_name: str):
        """Record a new request for rate limiting"""
        current_time = time.time()

        if model_name not in self.request_counts:
            self.request_counts[model_name] = []

        self.request_counts[model_name].append(current_time)
        self.last_request_time[model_name] = current_time


# Global router instance
llm_router = LLMRouter()


def get_model_for_task(task_type: TaskType) -> BaseChatModel:
    """Convenience function to get model for task"""
    return llm_router.get_best_model(task_type)


def get_model_for_agent(agent_role: str) -> BaseChatModel:
    """Convenience function to get model for agent"""
    return llm_router.get_model_for_agent(agent_role)

#!/usr/bin/env python3
"""
Model Router for Wade - Dynamically route queries to different LLMs
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
import requests
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ModelRouter")


class ModelType(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCALAI = "localai"
    CUSTOM = "custom"


class ModelRouter:
    """
    Routes queries to different LLM backends based on configuration and query characteristics
    """

    def __init__(self, config_path: str = None):
        """Initialize the model router with configuration"""
        self.models = {}
        self.default_model = None
        self.routing_rules = []
        self.config_path = config_path or os.path.expanduser(
            "~/.wade/config/models.json"
        )
        self._load_config()

    def _load_config(self):
        """Load model configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)

                self.models = config.get("models", {})
                self.default_model = config.get("default_model")
                self.routing_rules = config.get("routing_rules", [])

                logger.info(f"Loaded {len(self.models)} models from configuration")
            else:
                logger.warning(
                    f"Config file not found at {self.config_path}, using default configuration"
                )
                self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self._create_default_config()

    def _create_default_config(self):
        """Create default configuration with Phind-CodeLlama as the default model"""
        self.models = {
            "phind-codellama": {
                "type": ModelType.OLLAMA.value,
                "endpoint": "http://localhost:11434/api/generate",
                "parameters": {
                    "model": "phind-codellama",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                "capabilities": ["coding", "general", "security"],
                "context_window": 8192,
            }
        }

        self.default_model = "phind-codellama"
        self.routing_rules = []

        # Save the default configuration
        self._save_config()

    def _save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(
                    {
                        "models": self.models,
                        "default_model": self.default_model,
                        "routing_rules": self.routing_rules,
                    },
                    f,
                    indent=2,
                )
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")

    def add_model(
        self,
        name: str,
        model_type: ModelType,
        endpoint: str,
        parameters: Dict[str, Any],
        capabilities: List[str] = None,
        context_window: int = 4096,
    ):
        """Add a new model to the router"""
        self.models[name] = {
            "type": model_type.value,
            "endpoint": endpoint,
            "parameters": parameters,
            "capabilities": capabilities or ["general"],
            "context_window": context_window,
        }

        # If this is the first model, make it the default
        if not self.default_model:
            self.default_model = name

        self._save_config()
        return True

    def remove_model(self, name: str):
        """Remove a model from the router"""
        if name in self.models:
            del self.models[name]

            # If we removed the default model, set a new default if possible
            if self.default_model == name:
                if self.models:
                    self.default_model = next(iter(self.models.keys()))
                else:
                    self.default_model = None

            # Remove any routing rules for this model
            self.routing_rules = [
                rule for rule in self.routing_rules if rule.get("target_model") != name
            ]

            self._save_config()
            return True
        return False

    def set_default_model(self, name: str):
        """Set the default model"""
        if name in self.models:
            self.default_model = name
            self._save_config()
            return True
        return False

    def add_routing_rule(
        self, rule_type: str, pattern: str, target_model: str, priority: int = 0
    ):
        """
        Add a routing rule
        rule_type: 'keyword', 'regex', 'length', 'capability'
        pattern: The pattern to match (keywords, regex, length threshold, or capability name)
        target_model: The model to route to if the rule matches
        priority: Higher priority rules are evaluated first
        """
        if target_model not in self.models:
            return False

        self.routing_rules.append(
            {
                "type": rule_type,
                "pattern": pattern,
                "target_model": target_model,
                "priority": priority,
            }
        )

        # Sort rules by priority (highest first)
        self.routing_rules.sort(key=lambda x: x.get("priority", 0), reverse=True)

        self._save_config()
        return True

    def remove_routing_rule(self, index: int):
        """Remove a routing rule by index"""
        if 0 <= index < len(self.routing_rules):
            del self.routing_rules[index]
            self._save_config()
            return True
        return False

    def get_available_models(self):
        """Get list of available models"""
        return {
            name: {
                "type": model["type"],
                "capabilities": model.get("capabilities", ["general"]),
                "context_window": model.get("context_window", 4096),
            }
            for name, model in self.models.items()
        }

    def _match_rule(
        self,
        query: str,
        context_length: int = 0,
        required_capabilities: List[str] = None,
    ):
        """Find the first matching rule for the query"""
        required_capabilities = required_capabilities or []

        for rule in self.routing_rules:
            rule_type = rule.get("type")
            pattern = rule.get("pattern")
            target_model = rule.get("target_model")

            # Skip rules for models that don't exist anymore
            if target_model not in self.models:
                continue

            # Check if the model has all required capabilities
            if required_capabilities:
                model_capabilities = self.models[target_model].get("capabilities", [])
                if not all(cap in model_capabilities for cap in required_capabilities):
                    continue

            # Check if context length exceeds model's context window
            if context_length > self.models[target_model].get("context_window", 4096):
                continue

            # Match based on rule type
            if rule_type == "keyword" and pattern.lower() in query.lower():
                return target_model
            elif rule_type == "regex":
                import re

                if re.search(pattern, query):
                    return target_model
            elif rule_type == "length" and len(query) >= int(pattern):
                return target_model
            elif rule_type == "capability" and pattern in required_capabilities:
                return target_model

        return None

    def select_model(
        self,
        query: str,
        context_length: int = 0,
        required_capabilities: List[str] = None,
    ):
        """
        Select the appropriate model for a query based on routing rules
        Falls back to default model if no rules match
        """
        # Try to match a rule
        model_name = self._match_rule(query, context_length, required_capabilities)

        # If no rule matches, use default model
        if not model_name:
            model_name = self.default_model

        # If we have a model and it has the required capabilities, return it
        if model_name and model_name in self.models:
            if required_capabilities:
                model_capabilities = self.models[model_name].get("capabilities", [])
                if not all(cap in model_capabilities for cap in required_capabilities):
                    # Find another model with the required capabilities
                    for name, model in self.models.items():
                        model_capabilities = model.get("capabilities", [])
                        if all(
                            cap in model_capabilities for cap in required_capabilities
                        ):
                            return name
            return model_name

        # If we somehow don't have a valid model, return the first available one
        return next(iter(self.models.keys())) if self.models else None

    async def generate(
        self,
        query: str,
        model_name: str = None,
        context: List[Dict[str, str]] = None,
        parameters: Dict[str, Any] = None,
    ):
        """
        Generate a response using the specified model or auto-select a model
        """
        context = context or []
        parameters = parameters or {}

        # Auto-select model if not specified
        if not model_name:
            required_capabilities = parameters.pop("required_capabilities", [])
            context_length = sum(len(msg.get("content", "")) for msg in context) + len(
                query
            )
            model_name = self.select_model(query, context_length, required_capabilities)

        # Ensure we have a valid model
        if not model_name or model_name not in self.models:
            raise ValueError(f"Invalid model: {model_name}")

        model_config = self.models[model_name]
        model_type = model_config["type"]

        # Merge default parameters with provided parameters
        merged_parameters = {**model_config.get("parameters", {}), **parameters}

        # Route to appropriate handler based on model type
        if model_type == ModelType.OLLAMA.value:
            return await self._generate_ollama(
                query, model_config, merged_parameters, context
            )
        elif model_type == ModelType.OPENAI.value:
            return await self._generate_openai(
                query, model_config, merged_parameters, context
            )
        elif model_type == ModelType.ANTHROPIC.value:
            return await self._generate_anthropic(
                query, model_config, merged_parameters, context
            )
        elif model_type == ModelType.HUGGINGFACE.value:
            return await self._generate_huggingface(
                query, model_config, merged_parameters, context
            )
        elif model_type == ModelType.LOCALAI.value:
            return await self._generate_localai(
                query, model_config, merged_parameters, context
            )
        elif model_type == ModelType.CUSTOM.value:
            return await self._generate_custom(
                query, model_config, merged_parameters, context
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    async def _generate_ollama(
        self,
        query: str,
        model_config: Dict[str, Any],
        parameters: Dict[str, Any],
        context: List[Dict[str, str]],
    ):
        """Generate using Ollama API"""
        endpoint = model_config["endpoint"]

        # Format the prompt with context if available
        prompt = query
        if context:
            # Format context for Ollama
            formatted_context = ""
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    formatted_context += f"User: {content}\n"
                else:
                    formatted_context += f"Assistant: {content}\n"
            prompt = formatted_context + f"User: {query}\nAssistant:"

        # Prepare request payload
        payload = {
            "model": parameters.get("model", model_config["parameters"].get("model")),
            "prompt": prompt,
            "stream": False,
        }

        # Add other parameters
        for key, value in parameters.items():
            if key not in ["model", "prompt", "stream"]:
                payload[key] = value

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            return {
                "model": model_config["parameters"].get("model"),
                "response": result.get("response", ""),
                "metadata": {
                    "eval_count": result.get("eval_count"),
                    "eval_duration": result.get("eval_duration"),
                },
            }
        except Exception as e:
            logger.error(f"Error generating with Ollama: {str(e)}")
            raise

    async def _generate_openai(
        self,
        query: str,
        model_config: Dict[str, Any],
        parameters: Dict[str, Any],
        context: List[Dict[str, str]],
    ):
        """Generate using OpenAI API"""
        import openai

        # Set API key from config or environment
        api_key = (
            parameters.get("api_key")
            or model_config.get("api_key")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not api_key:
            raise ValueError("OpenAI API key not found")

        openai.api_key = api_key

        # Prepare messages
        messages = []

        # Add context messages
        if context:
            for msg in context:
                messages.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )

        # Add the current query
        messages.append({"role": "user", "content": query})

        # Prepare request parameters
        request_params = {
            "model": parameters.get("model", model_config["parameters"].get("model")),
            "messages": messages,
        }

        # Add other parameters
        for key, value in parameters.items():
            if key not in ["model", "messages", "api_key"]:
                request_params[key] = value

        try:
            response = await openai.ChatCompletion.acreate(**request_params)

            return {
                "model": request_params["model"],
                "response": response.choices[0].message.content,
                "metadata": {
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": (
                        response.usage._asdict() if hasattr(response, "usage") else {}
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error generating with OpenAI: {str(e)}")
            raise

    async def _generate_anthropic(
        self,
        query: str,
        model_config: Dict[str, Any],
        parameters: Dict[str, Any],
        context: List[Dict[str, str]],
    ):
        """Generate using Anthropic API"""
        import anthropic

        # Set API key from config or environment
        api_key = (
            parameters.get("api_key")
            or model_config.get("api_key")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        if not api_key:
            raise ValueError("Anthropic API key not found")

        client = anthropic.Client(api_key=api_key)

        # Format the prompt with context if available
        system_prompt = parameters.get("system_prompt", "")

        # Prepare messages
        messages = []

        # Add context messages
        if context:
            for msg in context:
                role = msg.get("role", "user")
                # Map roles to Anthropic format
                if role == "system":
                    system_prompt = msg.get("content", "")
                else:
                    messages.append(
                        {
                            "role": "user" if role == "user" else "assistant",
                            "content": msg.get("content", ""),
                        }
                    )

        # Add the current query
        messages.append({"role": "user", "content": query})

        # Prepare request parameters
        request_params = {
            "model": parameters.get("model", model_config["parameters"].get("model")),
            "messages": messages,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        # Add other parameters
        for key, value in parameters.items():
            if key not in ["model", "messages", "system", "api_key", "system_prompt"]:
                request_params[key] = value

        try:
            response = client.messages.create(**request_params)

            return {
                "model": request_params["model"],
                "response": response.content[0].text,
                "metadata": {
                    "stop_reason": response.stop_reason,
                    "usage": (
                        response.usage._asdict() if hasattr(response, "usage") else {}
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error generating with Anthropic: {str(e)}")
            raise

    async def _generate_huggingface(
        self,
        query: str,
        model_config: Dict[str, Any],
        parameters: Dict[str, Any],
        context: List[Dict[str, str]],
    ):
        """Generate using Hugging Face Inference API"""
        import requests

        # Set API key from config or environment
        api_key = (
            parameters.get("api_key")
            or model_config.get("api_key")
            or os.environ.get("HF_API_KEY")
        )
        if not api_key:
            raise ValueError("Hugging Face API key not found")

        endpoint = model_config["endpoint"]

        # Format the prompt with context if available
        prompt = query
        if context:
            # Simple formatting for context
            formatted_context = ""
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    formatted_context += f"User: {content}\n"
                else:
                    formatted_context += f"Assistant: {content}\n"
            prompt = formatted_context + f"User: {query}\nAssistant:"

        # Prepare request payload
        payload = {
            "inputs": prompt,
            "parameters": {k: v for k, v in parameters.items() if k not in ["api_key"]},
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # Extract response based on API response format
            generated_text = ""
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "generated_text" in result[0]:
                    generated_text = result[0]["generated_text"]
                else:
                    generated_text = str(result[0])
            elif isinstance(result, dict) and "generated_text" in result:
                generated_text = result["generated_text"]
            else:
                generated_text = str(result)

            return {
                "model": model_config["parameters"].get("model", "huggingface-model"),
                "response": generated_text,
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"Error generating with Hugging Face: {str(e)}")
            raise

    async def _generate_localai(
        self,
        query: str,
        model_config: Dict[str, Any],
        parameters: Dict[str, Any],
        context: List[Dict[str, str]],
    ):
        """Generate using LocalAI API (OpenAI-compatible)"""
        # LocalAI uses OpenAI-compatible API
        return await self._generate_openai(query, model_config, parameters, context)

    async def _generate_custom(
        self,
        query: str,
        model_config: Dict[str, Any],
        parameters: Dict[str, Any],
        context: List[Dict[str, str]],
    ):
        """Generate using custom API endpoint"""
        endpoint = model_config["endpoint"]

        # Format the prompt with context if available
        prompt = query
        if context:
            # Simple formatting for context
            formatted_context = ""
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    formatted_context += f"User: {content}\n"
                else:
                    formatted_context += f"Assistant: {content}\n"
            prompt = formatted_context + f"User: {query}\nAssistant:"

        # Prepare request payload based on custom format specified in config
        payload_format = model_config.get("payload_format", {})
        payload = {}

        # Build payload according to format
        for key, value_template in payload_format.items():
            if value_template == "{prompt}":
                payload[key] = prompt
            elif value_template == "{parameters}":
                payload[key] = {
                    k: v for k, v in parameters.items() if k not in ["api_key"]
                }
            elif value_template == "{context}":
                payload[key] = context
            else:
                payload[key] = value_template

        # Add any missing parameters
        for key, value in parameters.items():
            if key not in ["api_key"] and key not in payload:
                payload[key] = value

        # Set headers
        headers = {"Content-Type": "application/json"}
        api_key = parameters.get("api_key") or model_config.get("api_key")
        if api_key:
            auth_format = model_config.get("auth_format", "Bearer {api_key}")
            headers["Authorization"] = auth_format.format(api_key=api_key)

        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # Extract response based on response format specified in config
            response_path = model_config.get("response_path", "response")
            response_text = result

            # Navigate through the response path
            for key in response_path.split("."):
                if isinstance(response_text, dict) and key in response_text:
                    response_text = response_text[key]
                elif (
                    isinstance(response_text, list)
                    and key.isdigit()
                    and int(key) < len(response_text)
                ):
                    response_text = response_text[int(key)]
                else:
                    response_text = str(result)
                    break

            return {
                "model": model_config["parameters"].get("model", "custom-model"),
                "response": str(response_text),
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"Error generating with custom endpoint: {str(e)}")
            raise


# Example usage
async def main():
    # Create router
    router = ModelRouter()

    # Add some models
    router.add_model(
        "phind-codellama",
        ModelType.OLLAMA,
        "http://localhost:11434/api/generate",
        {"model": "phind-codellama", "temperature": 0.7},
        ["coding", "general", "security"],
        8192,
    )

    router.add_model(
        "llama2",
        ModelType.OLLAMA,
        "http://localhost:11434/api/generate",
        {"model": "llama2", "temperature": 0.8},
        ["general"],
        4096,
    )

    # Add routing rules
    router.add_routing_rule("keyword", "code", "phind-codellama", 10)
    router.add_routing_rule("keyword", "program", "phind-codellama", 10)
    router.add_routing_rule("capability", "coding", "phind-codellama", 20)

    # Generate responses
    coding_query = "Write a Python function to calculate Fibonacci numbers"
    general_query = "Tell me about the history of Rome"

    coding_response = await router.generate(coding_query)
    general_response = await router.generate(general_query)

    print(f"Coding query routed to: {coding_response['model']}")
    print(f"General query routed to: {general_response['model']}")

    print("\nCoding response:")
    print(coding_response["response"][:100] + "...")

    print("\nGeneral response:")
    print(general_response["response"][:100] + "...")


if __name__ == "__main__":
    asyncio.run(main())

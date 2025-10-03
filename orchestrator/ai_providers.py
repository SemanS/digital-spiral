"""AI Provider abstraction for different LLM providers (OpenAI, Google AI, etc.)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send chat request to AI provider.
        
        Returns:
            {
                "message": str,
                "tool_calls": List[Dict] or None
            }
        """
        pass


class GoogleAIProvider(AIProvider):
    """Google AI (Gemini) provider with function calling support."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tools to Gemini function declarations."""
        function_declarations = []
        
        for tool in tools:
            if tool["type"] != "function":
                continue
                
            func = tool["function"]
            
            # Convert parameters to Gemini format
            parameters = func["parameters"]
            properties = {}
            required = parameters.get("required", [])
            
            for prop_name, prop_def in parameters.get("properties", {}).items():
                properties[prop_name] = {
                    "type": prop_def["type"].upper(),
                    "description": prop_def.get("description", "")
                }
            
            function_declarations.append({
                "name": func["name"],
                "description": func["description"],
                "parameters": {
                    "type": "OBJECT",
                    "properties": properties,
                    "required": required
                }
            })
        
        return function_declarations
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style messages to Gemini format."""
        gemini_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Gemini uses "user" and "model" roles
            if role == "assistant":
                role = "model"
            elif role == "system":
                # System messages are handled separately in Gemini
                continue
            
            gemini_messages.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        return gemini_messages
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send chat request to Google AI (Gemini)."""
        
        import aiohttp
        
        # Convert tools to Gemini format
        function_declarations = self._convert_tools_to_gemini_format(tools)
        
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini_format(messages)
        
        # Add system message as first user message if provided
        if system_message:
            gemini_messages.insert(0, {
                "role": "user",
                "parts": [{"text": system_message}]
            })
            gemini_messages.insert(1, {
                "role": "model",
                "parts": [{"text": "Rozumiem. Som pripravený pomôcť s Jira úlohami."}]
            })
        
        # Build request
        url = f"{self.base_url}/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        payload = {
            "contents": gemini_messages,
            "tools": [{"function_declarations": function_declarations}] if function_declarations else None,
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        logger.info(f"Sending request to Gemini API")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error: {error_text}")
                    raise Exception(f"Gemini API error: {error_text}")
                
                result = await response.json()
                logger.info(f"Gemini response: {json.dumps(result, indent=2)}")
                
                # Parse response
                candidates = result.get("candidates", [])
                if not candidates:
                    return {"message": "Prepáč, nepodarilo sa mi vygenerovať odpoveď.", "tool_calls": None}
                
                candidate = candidates[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                if not parts:
                    return {"message": "Prepáč, nepodarilo sa mi vygenerovať odpoveď.", "tool_calls": None}
                
                # Check for function calls
                function_calls = []
                text_response = ""
                
                for part in parts:
                    if "text" in part:
                        text_response += part["text"]
                    elif "functionCall" in part:
                        function_calls.append(part["functionCall"])
                
                if function_calls:
                    # Convert to OpenAI-style tool calls
                    tool_calls = []
                    for i, fc in enumerate(function_calls):
                        tool_calls.append({
                            "tool_call_id": f"call_{i}",
                            "function_name": fc["name"],
                            "arguments": fc.get("args", {})
                        })
                    
                    return {
                        "message": text_response or "Vykonávam akciu...",
                        "tool_calls": tool_calls
                    }
                
                return {
                    "message": text_response,
                    "tool_calls": None
                }


class OpenAIProvider(AIProvider):
    """OpenAI provider with function calling support."""
    
    def __init__(self, api_key: str, organization: Optional[str] = None):
        import openai
        self.client = openai.OpenAI(api_key=api_key, organization=organization)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send chat request to OpenAI."""
        
        # Add system message
        if system_message:
            messages = [{"role": "system", "content": system_message}] + messages
        
        # Call OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check for tool calls
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                tool_calls.append({
                    "tool_call_id": tc.id,
                    "function_name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments)
                })
            
            return {
                "message": message.content or "Vykonávam akciu...",
                "tool_calls": tool_calls
            }
        
        return {
            "message": message.content,
            "tool_calls": None
        }


def get_ai_provider(tenant_id: str = "demo") -> AIProvider:
    """Get AI provider based on configuration."""
    
    # Check for Google AI key first
    google_api_key = os.getenv("GOOGLE_AI_API_KEY")
    if google_api_key:
        logger.info("Using Google AI (Gemini) provider")
        return GoogleAIProvider(google_api_key)
    
    # Fall back to OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_org = os.getenv("OPENAI_ORGANIZATION")
    
    if openai_api_key:
        logger.info("Using OpenAI provider")
        return OpenAIProvider(openai_api_key, openai_org)
    
    raise Exception("No AI provider configured. Set GOOGLE_AI_API_KEY or OPENAI_API_KEY")


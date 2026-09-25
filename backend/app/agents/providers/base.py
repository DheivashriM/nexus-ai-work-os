"""
LLM Provider Base Interface (llmFactory / BaseLLMProvider)
Defines abstract contracts (BaseLLMProvider, LLMResponse, ToolCallRequest) implemented by concrete provider adapters
(OpenAIProvider, GeminiProvider, RuleBasedProvider).
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ToolCallRequest(BaseModel):
    id: str
    tool_name: str
    arguments: Dict[str, Any]

class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCallRequest] = []
    finish_reason: str = "stop" # stop, tool_calls

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        pass

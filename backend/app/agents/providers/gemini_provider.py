import os
import json
import uuid
from typing import List, Dict, Any, Optional
from app.agents.providers.base import BaseLLMProvider, LLMResponse, ToolCallRequest

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-3.6-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model

    def _convert_openai_tools_to_gemini(self, openai_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        declarations = []
        for t in openai_tools:
            if t.get("type") == "function":
                fn = t.get("function", {})
                param_schema = fn.get("parameters", {})
                
                props = param_schema.get("properties", {})
                converted_props = {}
                for k, v in props.items():
                    p_type = str(v.get("type", "string")).upper()
                    converted_props[k] = {
                        "type": p_type,
                        "description": v.get("description", "")
                    }
                
                declarations.append({
                    "name": fn.get("name"),
                    "description": fn.get("description", ""),
                    "parameters": {
                        "type": "OBJECT",
                        "properties": converted_props,
                        "required": param_schema.get("required", [])
                    }
                })
        return [{"function_declarations": declarations}] if declarations else []

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")

        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        gemini_tools = self._convert_openai_tools_to_gemini(tools) if tools else None
        
        try:
            model = genai.GenerativeModel(self.model_name, tools=gemini_tools)
        except Exception:
            model = genai.GenerativeModel("models/gemini-3.6-flash", tools=gemini_tools)

        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            if content:
                prompt_parts.append(f"{role}: {content}")
        
        formatted_prompt = "\n".join(prompt_parts)

        try:
            response = model.generate_content(formatted_prompt)
        except Exception as e:
            import logging
            logging.getLogger("uvicorn").warning(f"[GeminiProvider] API call failed: {e}. Falling back to RuleBasedProvider.")
            from app.agents.providers.rule_based_provider import RuleBasedProvider
            return RuleBasedProvider().generate(messages, tools)

        tool_calls: List[ToolCallRequest] = []
        text_content = None

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call and part.function_call.name:
                    fc = part.function_call
                    args_dict = dict(fc.args) if hasattr(fc, "args") else {}
                    tool_calls.append(ToolCallRequest(
                        id=str(uuid.uuid4()),
                        tool_name=fc.name,
                        arguments=args_dict
                    ))
                elif hasattr(part, "text") and part.text:
                    text_content = part.text

        if not text_content and not tool_calls:
            try:
                text_content = response.text
            except Exception:
                text_content = "Processing completed."

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else "stop"
        )

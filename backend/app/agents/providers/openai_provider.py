import os
import json
import uuid
from typing import List, Dict, Any, Optional
from app.agents.providers.base import BaseLLMProvider, LLMResponse, ToolCallRequest

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set.")

        import openai
        try:
            client = openai.OpenAI(api_key=self.api_key)

            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message

            tool_calls: List[ToolCallRequest] = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    tool_calls.append(
                        ToolCallRequest(
                            id=tc.id or str(uuid.uuid4()),
                            tool_name=tc.function.name,
                            arguments=args
                        )
                    )

            return LLMResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop"
            )
        except Exception as e:
            # Fall back to RuleBasedProvider on OpenAI API errors (e.g. insufficient quota / billing)
            from app.agents.providers.rule_based_provider import RuleBasedProvider
            return RuleBasedProvider().generate(messages, tools)

"""
AI Agent Orchestrator & Provider Factory Module (aiOrchestrator / llmFactory)
Manages the multi-turn agent execution loop, conversation context, LLM provider instantiation
(OpenAI, Gemini, Rule-Based), tool call execution dispatch, and synthesis of final execution responses.
"""
import os
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.ai_models import AIConversation, AIMessage, AIActionLog
from app.schemas.ai_schemas import AIChatResponse, ToolExecutionStep
from app.agents.context import AgentContext
from app.agents.executor import AgentExecutor
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.providers.base import BaseLLMProvider
from app.agents.providers.rule_based_provider import RuleBasedProvider
from app.agents.providers.openai_provider import OpenAIProvider
from app.agents.providers.gemini_provider import GeminiProvider
from app.tools.registry import registry

class AIAgentService:
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.provider = self._init_provider()

    def _init_provider(self) -> BaseLLMProvider:
        from app.core.config import settings
        provider_type = (settings.LLM_PROVIDER or os.getenv("LLM_PROVIDER") or "rule_based").lower()
        openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if provider_type == "openai" and openai_key and openai_key.strip() and openai_key != "your_openai_api_key_here":
            return OpenAIProvider(api_key=openai_key)
        gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if provider_type == "gemini" and gemini_key:
            return GeminiProvider(api_key=gemini_key)
        return RuleBasedProvider()

    def process_chat(self, user_message: str, conversation_id: Optional[str] = None) -> AIChatResponse:
        # 1. Retrieve or create conversation
        if conversation_id:
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == self.user.id
            ).first()
            if not conv:
                title = f"📱 WhatsApp AI ({self.user.whatsapp_number or 'Mobile'})" if "wa_" in conversation_id else user_message[:40]
                conv = AIConversation(id=conversation_id, user_id=self.user.id, title=title)
                self.db.add(conv)
                self.db.commit()
                self.db.refresh(conv)
        else:
            conv = self._create_conversation(user_message)

        # 2. Add user message to conversation history
        user_msg_db = AIMessage(
            conversation_id=conv.id,
            role="user",
            content=user_message
        )
        self.db.add(user_msg_db)
        self.db.commit()

        # 3. Build messages array for LLM Provider
        history_messages = self._build_messages_history(conv.id)

        openai_tools = registry.get_openai_tool_definitions()
        all_steps: List[ToolExecutionStep] = []
        all_summaries: List[str] = []

        agent_ctx = AgentContext(user=self.user, db=self.db, conversation_id=conv.id)
        executor = AgentExecutor(agent_ctx)

        current_history = history_messages.copy()
        final_reply = ""

        # Multi-turn Agent Execution Loop (up to 3 iterations)
        for iteration in range(3):
            response = self.provider.generate(current_history, tools=openai_tools)
            if not response.tool_calls:
                if all_summaries:
                    # Prefer synthesized tool content over generic fallback text
                    is_generic = not response.content or response.content.startswith("I understood your query about")
                    if is_generic or len(all_summaries) > 0:
                        final_reply = self._build_final_reply(all_summaries, all_steps)
                    else:
                        final_reply = response.content
                else:
                    final_reply = response.content or "Processing complete."
                break

            steps, summaries, tool_msgs = executor.execute_tool_calls(response.tool_calls)
            all_steps.extend(steps)
            all_summaries.extend(summaries)

            # Check if clarification is required
            has_clarification = any(s.result and isinstance(s.result, dict) and s.result.get("needs_clarification") for s in steps)
            if has_clarification:
                final_reply = self._build_final_reply(all_summaries, all_steps)
                break

            # Feed tool outputs back to LLM context for next iteration
            current_history.extend(tool_msgs)

            # If tool calls executed and succeeded (read or write), construct final reply and finish loop
            final_reply = self._build_final_reply(all_summaries, all_steps)
            if any(s.status == "SUCCESS" for s in steps):
                break

        # 6. Save Assistant response to conversation DB
        assistant_msg_db = AIMessage(
            conversation_id=conv.id,
            role="assistant",
            content=final_reply,
            tool_calls={"summaries": all_summaries} if all_summaries else None
        )
        self.db.add(assistant_msg_db)
        self.db.commit()

        return AIChatResponse(
            conversation_id=conv.id,
            reply=final_reply,
            execution_steps=all_steps,
            actions_taken=all_summaries
        )

    def _create_conversation(self, initial_prompt: str) -> AIConversation:
        title = initial_prompt[:40] + ("..." if len(initial_prompt) > 40 else "")
        conv = AIConversation(user_id=self.user.id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def _build_messages_history(self, conv_id: str) -> List[Dict[str, Any]]:
        db_msgs = self.db.query(AIMessage).filter(AIMessage.conversation_id == conv_id).order_by(AIMessage.created_at).all()
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in db_msgs:
            history.append({"role": m.role, "content": m.content})
        return history

    def _build_final_reply(self, summaries: List[str], steps: List[ToolExecutionStep]) -> str:
        # First check if any tool returned a clarification request or custom error
        for step in steps:
            if step.result and isinstance(step.result, dict):
                if step.result.get("needs_clarification"):
                    return step.result.get("error") or "Please provide the missing details to proceed."
                if step.result.get("error"):
                    return step.result.get("error")

        # Filter summaries to only include successful tool steps
        valid_summaries = []
        for step, summary in zip(steps, summaries):
            if step.status == "SUCCESS" and summary and not summary.startswith("Could not resolve"):
                valid_summaries.append(summary)

        if valid_summaries:
            return " ".join(valid_summaries)

        failed_steps = [s for s in steps if s.status in ["FAILED", "UNAUTHORIZED"]]
        if failed_steps:
            errors = [s.result.get("error", "Error") for s in failed_steps if s.result and s.result.get("error")]
            return f"I encountered an issue: {'; '.join(errors)}"

        return "Requested action completed successfully."

    def get_user_conversations(self) -> List[AIConversation]:
        return self.db.query(AIConversation).filter(
            AIConversation.user_id == self.user.id
        ).order_by(AIConversation.updated_at.desc()).all()

    def get_conversation_by_id(self, conv_id: str) -> Optional[AIConversation]:
        return self.db.query(AIConversation).filter(
            AIConversation.id == conv_id,
            AIConversation.user_id == self.user.id
        ).first()

    def delete_conversation(self, conv_id: str) -> bool:
        conv = self.get_conversation_by_id(conv_id)
        if conv:
            self.db.delete(conv)
            self.db.commit()
            return True
        return False

    def get_user_action_logs(self, limit: int = 50) -> List[AIActionLog]:
        return self.db.query(AIActionLog).filter(
            AIActionLog.user_id == self.user.id
        ).order_by(AIActionLog.created_at.desc()).limit(limit).all()

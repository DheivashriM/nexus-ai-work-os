"""
Tool Registry Module (toolsRegistry)
Central registry for defining, listing, and accessing AI Agent tools.
Generates OpenAI-compliant function call JSON schemas and dispatches tool execution.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.user import User

class ToolContext:
    def __init__(self, user: User, db: Session, conversation_id: Optional[str] = None):
        self.user = user
        self.db = db
        self.conversation_id = conversation_id

class BaseTool(ABC):
    name: str
    description: str
    category: str  # PROJECT_TOOLS, TASK_TOOLS, TEAM_TOOLS, BLOCKER_TOOLS, AUDIT_TOOLS
    risk_level: str  # LOW_RISK, NORMAL_WRITE, HIGH_RISK
    args_schema: Type[BaseModel]

    @abstractmethod
    def execute(self, args: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        pass

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_openai_tool_definitions(self) -> List[Dict[str, Any]]:
        definitions = []
        for tool in self._tools.values():
            schema = tool.args_schema.model_json_schema()
            definitions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema
                }
            })
        return definitions

# Global tool registry instance
registry = ToolRegistry()

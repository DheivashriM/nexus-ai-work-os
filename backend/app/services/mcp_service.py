import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENTS_DIR = PROJECT_ROOT / ".agents"
MCP_CONFIG_PATH = AGENTS_DIR / "mcp_config.json"
TIMELINES_MCP_URL = "https://mcp.services.timelines.ai/mcp"

class MCPService:
    @staticmethod
    def get_mcp_config() -> Dict[str, Any]:
        """Reads current .agents/mcp_config.json file if it exists."""
        if not MCP_CONFIG_PATH.exists():
            return {"mcpServers": {}}
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"mcpServers": {}}

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.mcp.server import call_tool, list_tools

router = APIRouter(prefix="/mcp", tags=["MCP"])


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict = {}


@router.get("/tools")
def mcp_list_tools():
    return {"tools": list_tools()}


@router.post("/call")
def mcp_call_tool(req: ToolCallRequest):
    try:
        result = call_tool(req.tool, req.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid arguments: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"tool": req.tool, "result": result}

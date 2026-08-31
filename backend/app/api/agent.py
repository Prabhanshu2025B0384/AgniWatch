from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Any
from app.services.x402_service import require_payment
from app.services.agent import execute_tool
from app.database.supabase import supabase

router = APIRouter()

class ToolCallRequest(BaseModel):
    tool_name: str
    args: dict[str, Any]

@router.post("/execute")
async def handle_tool_call(
    tool_call: ToolCallRequest,
    request: Request,
    payment_payload: dict = Depends(require_payment)
):
    """
    x402 Protected Endpoint: Agentic Tool Execution.
    Allows other agents or frontends to invoke internal tools and pay via x402.
    """
    result = await execute_tool(tool_call.tool_name, tool_call.args)
    
    # Log the agent request
    if supabase:
        try:
            supabase.table('agent_requests').insert({
                "query_text": f"Tool call: {tool_call.tool_name}",
                "tools_called": {"name": tool_call.tool_name, "args": tool_call.args},
                "result": result
            }).execute()
        except Exception:
            pass

    return {
        "status": "success",
        "tool_name": tool_call.tool_name,
        "result": result,
        "payment_receipt": payment_payload.model_dump() if hasattr(payment_payload, 'model_dump') else str(payment_payload)
    }

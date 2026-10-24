"""ASI:One / Agentverse entry point for Vison Forge."""

from __future__ import annotations

import truststore
truststore.inject_into_ssl()

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from vison.forge_service import run_forge


load_dotenv()

seed = os.getenv("VISON_AGENT_SEED")
if not seed:
    raise RuntimeError("VISON_AGENT_SEED is missing. Add a private seed phrase to .env; see .env.example.")

agent = Agent(
    name="vison-forge-agent",
    seed=seed,
    port=int(os.getenv("VISON_AGENT_PORT", "8001")),
    mailbox=True,
    publish_agent_details=True,
)
chat_protocol = Protocol(spec=chat_protocol_spec)

_executor = ThreadPoolExecutor(max_workers=8)

print(f"\n[Vison Forge Agent]")
print(f"Address: {agent.address}")
print(f"Agentverse Inspector: https://agentverse.ai/agents/{agent.address}")
print(f"Waiting for incoming ACP / ASI:One messages on port {os.getenv('VISON_AGENT_PORT', '8001')}...\n")


def _make_response(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=text),
            EndSessionContent(type="end-session"),
        ],
    )


def _run_forge_sync(user_text: str, session_id: str) -> str:
    """Run forge planning synchronously in a thread (keeps asyncio event loop unblocked)."""
    try:
        return run_forge(user_text, session_id=session_id)
    except Exception as exc:
        return (
            f"Vison Forge encountered an error while processing your request: {exc}\n\n"
            "Please rephrase your hardware project description and include:\n"
            "- Platform: Arduino, ESP32, Raspberry Pi, or Robotics\n"
            "- Budget (e.g. under ₹2500)\n"
            "- Deadline (e.g. 7 days)\n"
            "- Experience level (beginner / intermediate)\n"
            "Example: *I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2.*"
        )


@chat_protocol.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, message: ChatMessage) -> None:
    try:
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.now(timezone.utc),
                acknowledged_msg_id=message.msg_id,
            ),
        )
    except Exception as exc:
        ctx.logger.warning(f"Failed to send acknowledgement to {sender}: {exc}")

    try:
        user_text = " ".join(
            item.text for item in message.content if isinstance(item, TextContent)
        ).strip()

        if not user_text:
            reply = (
                "👋 Welcome to **Vison Forge** — your hardware project planning agent!\n\n"
                "Describe a safe, low-voltage Arduino, ESP32, Raspberry Pi, or simple robotics project.\n\n"
                "Include your budget, deadline, experience level, and team size for the best results.\n\n"
                "**Example prompt:**\n"
                "*I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2.*"
            )
        else:
            ctx.logger.info(f"Processing Vison Forge request from {sender}: {user_text[:80]}")
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(_executor, _run_forge_sync, user_text, sender)

        await ctx.send(sender, _make_response(reply))
    except Exception as exc:
        ctx.logger.error(f"Error handling chat from {sender}: {exc}")
        try:
            await ctx.send(sender, _make_response(f"Vison Forge encountered an error: {exc}. Please try again."))
        except Exception:
            pass


@chat_protocol.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, message: ChatAcknowledgement) -> None:
    ctx.logger.debug(f"Ack from {sender}: {message.acknowledged_msg_id}")


agent.include(chat_protocol, publish_manifest=True)


if __name__ == "__main__":
    agent.run()

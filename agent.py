"""ASI:One / Agentverse entry point for Vison Forge."""

from __future__ import annotations

import os
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
if not os.getenv("ASI_ONE_API_KEY"):
    print("Warning: ASI_ONE_API_KEY is missing; Vison will use its limited local intent fallback.")

agent = Agent(
    name="vison-forge-agent",
    seed=seed,
    port=int(os.getenv("VISON_AGENT_PORT", "8001")),
    mailbox=True,
    publish_agent_details=True,
)
chat_protocol = Protocol(spec=chat_protocol_spec)

print(f"\n[Vison Forge Agent]")
print(f"Address: {agent.address}")
print(f"Agentverse Inspector: https://agentverse.ai/agents/{agent.address}")
print(f"Waiting for incoming ACP / ASI:One messages on port {os.getenv('VISON_AGENT_PORT', '8001')}...\n")


def response_message(text: str) -> ChatMessage:
    return ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=text),
            EndSessionContent(type="end-session"),
        ],
    )


@chat_protocol.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, message: ChatMessage) -> None:
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=message.msg_id,
        ),
    )
    user_text = " ".join(item.text for item in message.content if isinstance(item, TextContent)).strip()
    if not user_text:
        text = "Describe a low-voltage Arduino, ESP32, Raspberry Pi, or simple robotics project. Include your budget, deadline, and experience level."
    else:
        ctx.logger.info("Running Vison Forge project assessment for an ASI:One request")
        text = run_forge(user_text)
    await ctx.send(sender, response_message(text))


@chat_protocol.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, message: ChatAcknowledgement) -> None:
    ctx.logger.debug(f"Acknowledgement received from {sender}: {message.acknowledged_msg_id}")


agent.include(chat_protocol, publish_manifest=True)


if __name__ == "__main__":
    agent.run()

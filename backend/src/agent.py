import logging
import json
import os
import asyncio
from datetime import datetime
from typing import Annotated, Literal
from dataclasses import dataclass, field

from dotenv import load_dotenv
from pydantic import Field
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
    MetricsCollectedEvent,
    RunContext,
    function_tool,
)

from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# ======================================================
# ORDER MANAGEMENT SYSTEM
# ======================================================
@dataclass
class OrderState:
    """Coffee shop order state"""
    drinkType: str | None = None
    size: str | None = None
    milk: str | None = None
    extras: list[str] = field(default_factory=list)
    name: str | None = None
    
    def is_complete(self) -> bool:
        return all([self.drinkType, self.size, self.milk, self.name])
    
    def to_dict(self) -> dict:
        return {
            "drinkType": self.drinkType,
            "size": self.size,
            "milk": self.milk,
            "extras": self.extras,
            "name": self.name
        }
    
    def get_summary(self) -> str:
        if not self.is_complete():
            return "Order in progress..."
        extras_text = f" with {', '.join(self.extras)}" if self.extras else ""
        return f"{self.size.title()} {self.drinkType.title()} with {self.milk.title()} milk{extras_text} for {self.name}"

@dataclass
class Userdata:
    """User session data"""
    order: OrderState
    session_start: datetime = field(default_factory=datetime.now)

# ======================================================
# BARISTA AGENT FUNCTION TOOLS
# ======================================================

@function_tool
async def set_drink_type(ctx: RunContext[Userdata],
                         drink: Annotated[Literal["latte","cappuccino","americano","espresso","mocha","coffee","cold brew","matcha"], Field(description="Drink type")]) -> str:
    ctx.userdata.order.drinkType = drink
    return f"One {drink} coming up!"

@function_tool
async def set_size(ctx: RunContext[Userdata],
                   size: Annotated[Literal["small","medium","large","extra large"], Field(description="Size")]) -> str:
    ctx.userdata.order.size = size
    return f"{size.title()} size selected."

@function_tool
async def set_milk(ctx: RunContext[Userdata],
                   milk: Annotated[Literal["whole","skim","almond","oat","soy","coconut","none"], Field(description="Milk type")]) -> str:
    ctx.userdata.order.milk = milk
    return f"{milk.title()} milk selected."

@function_tool
async def set_extras(ctx: RunContext[Userdata],
                     extras: Annotated[list[Literal["sugar","whipped cream","caramel","extra shot","vanilla","cinnamon","honey"]] | None, Field(description="Extras")] = None) -> str:
    ctx.userdata.order.extras = extras if extras else []
    return f"Extras set: {', '.join(ctx.userdata.order.extras)}" if extras else "No extras selected."

@function_tool
async def set_name(ctx: RunContext[Userdata],
                   name: Annotated[str, Field(description="Customer name")]) -> str:
    ctx.userdata.order.name = name.strip().title()
    return f"Name recorded: {ctx.userdata.order.name}"

@function_tool
async def complete_order(ctx: RunContext[Userdata]) -> str:
    order = ctx.userdata.order
    if not order.is_complete():
        missing = []
        if not order.drinkType: missing.append("drink type")
        if not order.size: missing.append("size")
        if not order.milk: missing.append("milk")
        if not order.name: missing.append("name")
        return f"Missing info: {', '.join(missing)}"
    
    try:
        save_order_to_json(order)
        extras_text = f" with {', '.join(order.extras)}" if order.extras else ""
        return f"Order confirmed: {order.size} {order.drinkType} with {order.milk} milk{extras_text} for {order.name}"
    except Exception as e:
        return f"Order recorded but failed to save: {e}"

@function_tool
async def get_order_status(ctx: RunContext[Userdata]) -> str:
    order = ctx.userdata.order
    return f"Order status: {order.get_summary()}"

class BaristaAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="""
            You are a friendly barista at Cafe Coffee Day.
            Collect: drink type, size, milk, extras, customer name.
            Confirm and complete order using function tools.
            """,
            tools=[set_drink_type, set_size, set_milk, set_extras, set_name, complete_order, get_order_status],
        )

def create_empty_order():
    return OrderState()

# ======================================================
# ORDER STORAGE
# ======================================================
def get_orders_folder():
    base_dir = os.path.dirname(__file__)
    backend_dir = os.path.abspath(os.path.join(base_dir, ".."))
    folder = os.path.join(backend_dir, "orders")
    os.makedirs(folder, exist_ok=True)
    return folder

def save_order_to_json(order: OrderState) -> str:
    folder = get_orders_folder()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"order_{timestamp}.json"
    path = os.path.join(folder, filename)
    order_data = order.to_dict()
    order_data["timestamp"] = datetime.now().isoformat()
    order_data["session_id"] = f"session_{timestamp}"
    with open(path, "w", encoding='utf-8') as f:
        json.dump(order_data, f, indent=4, ensure_ascii=False)
    return path

# ======================================================
# SYSTEM PREWARM
# ======================================================
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

# ======================================================
# AGENT SESSION
# ======================================================
async def entrypoint(ctx: JobContext):
    userdata = Userdata(order=create_empty_order())
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-matthew", style="Conversation", text_pacing=True),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )

    usage_collector = metrics.UsageCollector()
    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent):
        usage_collector.collect(ev.metrics)

    await session.start(agent=BaristaAgent(), room=ctx.room, room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    await ctx.connect()

# ======================================================
# LAUNCH
# ======================================================
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))



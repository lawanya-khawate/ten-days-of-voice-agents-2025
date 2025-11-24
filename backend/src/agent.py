import logging
import json
import os
import asyncio
from datetime import datetime
from typing import Annotated
from dataclasses import dataclass, field, asdict

print("\n" + "🌱" * 42)
print("🧘 DAILY WELLNESS VOICE COMPANION – ACTIVE")
print("🌱" * 42 + "\n")

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
    RunContext,
    function_tool,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# ======================================================
# 🌿 STATE MANAGEMENT & DATA STRUCTURES
# ======================================================

@dataclass
class CheckInState:
    mood: str | None = None
    energy: str | None = None
    objectives: list[str] = field(default_factory=list)
    advice_given: str | None = None
    
    def is_complete(self) -> bool:
        return (
            self.mood is not None
            and self.energy is not None
            and len(self.objectives) > 0
        )
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Userdata:
    current_checkin: CheckInState
    history_summary: str
    session_start: datetime = field(default_factory=datetime.now)

# ======================================================
# 💾 JSON PERSISTENCE
# ======================================================
WELLNESS_LOG_FILE = "wellness_log.json"

def get_log_path():
    base_dir = os.path.dirname(__file__)
    backend_dir = os.path.abspath(os.path.join(base_dir, ".."))
    return os.path.join(backend_dir, WELLNESS_LOG_FILE)

def load_history() -> list:
    path = get_log_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_checkin_entry(entry: CheckInState) -> None:
    path = get_log_path()
    history = load_history()

    record = {
        "timestamp": datetime.now().isoformat(),
        "mood": entry.mood,
        "energy": entry.energy,
        "objectives": entry.objectives,
        "summary": entry.advice_given
    }

    history.append(record)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
        
    print("\n🌼 Wellness check-in saved!\n")

# ======================================================
# 🧠 WELLNESS AGENT TOOLS
# ======================================================

@function_tool
async def record_mood_and_energy(
    ctx: RunContext[Userdata],
    mood: Annotated[str, Field(description="How the user feels emotionally today")],
    energy: Annotated[str, Field(description="How energized or drained they feel today")],
) -> str:
    ctx.userdata.current_checkin.mood = mood
    ctx.userdata.current_checkin.energy = energy
    return f"Thank you for sharing. I've noted your mood as {mood} and your energy as {energy}."

@function_tool
async def record_objectives(
    ctx: RunContext[Userdata],
    objectives: Annotated[list[str], Field(description="1–3 simple goals for today")],
) -> str:
    ctx.userdata.current_checkin.objectives = objectives
    return "Got it. Those are meaningful intentions for today."

@function_tool
async def complete_checkin(
    ctx: RunContext[Userdata],
    final_advice_summary: Annotated[str, Field(description="1 short supportive sentence recapping the advice")],
) -> str:
    state = ctx.userdata.current_checkin
    state.advice_given = final_advice_summary

    if not state.is_complete():
        return "Almost there — I still need your mood, energy, and at least one goal."

    save_checkin_entry(state)

    recap = (
        f"Here’s your check-in summary:\n"
        f"• Mood: {state.mood}\n"
        f"• Energy: {state.energy}\n"
        f"• Intentions: {', '.join(state.objectives)}\n\n"
        f"Reminder: {final_advice_summary}\n"
        f"I'm grateful you took this moment for yourself today. 💚"
    )
    return recap

# ======================================================
# 🤖 AGENT BEHAVIOR & PERSONALITY
# ======================================================

class WellnessAgent(Agent):
    def __init__(self, history_context: str):
        super().__init__(
            instructions=f"""
You are a calm, supportive Daily Wellness Companion.
Your purpose is to help the user:
1️⃣ Check in with how they feel (mood + energy)
2️⃣ Set 1–3 small intentions for the day
3️⃣ Receive one grounded supportive reminder

If history exists, refer to it gently:
Example: “Last time you were tired — how is today?”

Offer only non-medical wellness suggestions like:
• Take a short stretch break
• Start with one tiny task
• Drink water or step outside briefly

Avoid:
• Clinical or diagnostic language
• Prescribing treatment or medication

At the end, call `complete_checkin` to save.
""",
            tools=[
                record_mood_and_energy,
                record_objectives,
                complete_checkin,
            ],
        )

# ======================================================
# 🚀 START SESSION
# ======================================================

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):

    # Load past history
    history = load_history()
    if history:
        last = history[-1]
        history_summary = (
            f"Last time: Mood — {last.get('mood')}, "
            f"Energy — {last.get('energy')}, "
            f"Goals — {', '.join(last.get('objectives', []))}."
        )
    else:
        history_summary = "No previous entries — this may be their first check-in."

    userdata = Userdata(
        current_checkin=CheckInState(),
        history_summary=history_summary
    )

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(
            voice="en-US-natalie",
            style="Promo",
            text_pacing=True,
        ),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
        userdata=userdata,
    )

    await session.start(
        agent=WellnessAgent(history_context=history_summary),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))


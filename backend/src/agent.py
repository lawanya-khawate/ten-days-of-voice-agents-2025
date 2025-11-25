# ======================================================
# GEOGRAPHY TEACH-THE-TUTOR AGENT (SCHOOL LEVEL A)
# AI Scoring + JSON Progress + Natural Topic Selection
# ======================================================

import logging
import json
import os
from typing import Annotated, Literal, Optional
from dataclasses import dataclass

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
    function_tool,
    RunContext,
)

from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

# ======================================================
# GEOGRAPHY KNOWLEDGE CONTENT (FULL SCHOOL DETAIL A)
# ======================================================

CONTENT_FILE = "geography_content.json"
PROGRESS_FILE = "public/geography_progress.json"

DEFAULT_CONTENT = [
    {
        "id": "earth_structure",
        "title": "Structure of the Earth",
        "summary": (
            "The Earth is made of different layers like an onion.\n\n"
            "Crust: outermost layer, 5–30 km thick.\n"
            "Mantle: very thick, contains hot flowing magma.\n"
            "Core: innermost, very hot iron and nickel."
        ),
        "sample_question": "Name and describe the three main layers of the Earth."
    },
    {
        "id": "water_cycle",
        "title": "Water Cycle",
        "summary": (
            "Water cycle moves water again and again:\n\n"
            "Evaporation: Sun heats water into vapor.\n"
            "Condensation: Vapor cools into clouds.\n"
            "Precipitation: Clouds drop rain, snow, or hail.\n"
            "Collection: Water returns to rivers and oceans."
        ),
        "sample_question": "Explain the water cycle with its steps."
    },
    {
        "id": "atmosphere",
        "title": "Atmosphere",
        "summary": (
            "Atmosphere is the blanket of air around Earth.\n"
            "It protects us and gives air to breathe.\n"
            "Layers: Troposphere, Stratosphere, Mesosphere, Thermosphere, Exosphere."
        ),
        "sample_question": "What is the atmosphere and why is it important?"
    },
    {
        "id": "landforms",
        "title": "Major Landforms",
        "summary": (
            "Landforms are shapes on Earth's surface.\n"
            "Mountains: high land.\n"
            "Plateaus: high flat land.\n"
            "Plains: low and flat land, good for farming."
        ),
        "sample_question": "What are mountains, plateaus, and plains?"
    },
    {
        "id": "climate_weather",
        "title": "Climate and Weather",
        "summary": (
            "Weather: daily changes.\n"
            "Climate: long-term weather of a place.\n"
            "Depends on height, distance from sea, heat, and wind."
        ),
        "sample_question": "What is the difference between weather and climate?"
    },
    {
        "id": "soil_types",
        "title": "Types of Soil",
        "summary": (
            "Soil forms from rocks.\n"
            "Alluvial: fertile.\n"
            "Black: good for cotton.\n"
            "Red: less fertile.\n"
            "Desert: sandy."
        ),
        "sample_question": "Which soil is used for growing cotton and why?"
    },
    {
        "id": "natural_vegetation",
        "title": "Natural Vegetation",
        "summary": (
            "Plants growing on their own.\n"
            "Types: Evergreen, Deciduous, Grasslands, Desert plants."
        ),
        "sample_question": "What is natural vegetation? Give its types."
    },
    {
        "id": "resource_conservation",
        "title": "Resources and Conservation",
        "summary": (
            "Resources like water, soil, forests must be saved.\n"
            "Renewable and non-renewable.\n"
            "Save by reducing, reusing, recycling."
        ),
        "sample_question": "What is conservation and why is it important?"
    }
]

def load_content():
    try:
        if not os.path.exists(CONTENT_FILE):
            with open(CONTENT_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONTENT, f, indent=4)
        with open(CONTENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_progress(data: dict):
    try:
        os.makedirs("public", exist_ok=True)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Error saving progress:", e)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

COURSE_CONTENT = load_content()

# ======================================================
# STATE
# ======================================================

@dataclass
class TutorState:
    current_topic_id: str | None = None
    current_topic_data: dict | None = None
    mode: Literal["learn", "quiz", "teach_back"] = "learn"
    mastery: dict = None

    def __post_init__(self):
        if self.mastery is None:
            self.mastery = {}

    def set_topic(self, topic_id: str):
        topic = next((t for t in COURSE_CONTENT if t["id"] == topic_id), None)
        if topic:
            self.current_topic_id = topic_id
            self.current_topic_data = topic
            return True
        return False

    def init_topic_mastery(self, tid: str):
        if tid not in self.mastery:
            self.mastery[tid] = {
                "times_explained": 0,
                "times_quizzed": 0,
                "times_taught_back": 0,
                "last_score": None,
                "avg_score": None,
                "loops": {                     # NEW ADDITION
                    "times_explained": 0,
                    "times_quizzed": 0,
                    "times_taught_back": 0,
                    "last_score": None,
                    "avg_score": None,
                }
            }

@dataclass
class Userdata:
    tutor_state: TutorState
    agent_session: Optional[AgentSession] = None

# ======================================================
# TOOLS
# ======================================================

@function_tool
async def select_topic(ctx: RunContext[Userdata], topic_id: Annotated[str, Field(description="Topic name or ID")]):

    state = ctx.userdata.tutor_state
    text = topic_id.lower().strip().replace(" ", "_")

    if state.set_topic(text):
        state.init_topic_mastery(text)
        return f"Selected topic: {state.current_topic_data['title']}. Learn / Quiz / Teach-back?"

    for item in COURSE_CONTENT:
        if text in item["title"].lower().replace(" ", "_"):
            tid = item["id"]
            state.set_topic(tid)
            state.init_topic_mastery(tid)
            return f"Topic set to {item['title']}. Learn / Quiz / Teach-back?"

    available = ", ".join([t["title"] for t in COURSE_CONTENT])
    return f"Topic not found. Try: {available}"

@function_tool
async def set_learning_mode(ctx: RunContext[Userdata], mode: Annotated[str, Field(description="learn/quiz/teach_back")]):
    state = ctx.userdata.tutor_state
    agent_session = ctx.userdata.agent_session
    state.mode = mode
    tid = state.current_topic_id

    if tid:
        state.init_topic_mastery(tid)

        stats = state.mastery[tid]
        loops = stats["loops"]

        if mode == "learn":
            stats["times_explained"] += 1
            loops["times_explained"] += 1
            agent_session.tts.update_options(voice="en-US-matthew")

        elif mode == "quiz":
            stats["times_quizzed"] += 1
            loops["times_quizzed"] += 1
            agent_session.tts.update_options(voice="en-US-alicia")

        elif mode == "teach_back":
            stats["times_taught_back"] += 1
            loops["times_taught_back"] += 1
            agent_session.tts.update_options(voice="en-US-ken")

        save_progress(state.mastery)

    return f"Switched to {mode} mode."

@function_tool
async def evaluate_teaching(ctx: RunContext[Userdata], user_explanation: Annotated[str, Field(description="Student explanation")]):
    state = ctx.userdata.tutor_state
    tid = state.current_topic_id
    if not tid:
        return "Please select a topic first."

    topic_name = state.current_topic_data["title"]

    result = await ctx.session.llm.chat(
        messages=[{"role":"user","content":f"""
Evaluate this Geography explanation.

Topic: {topic_name}
Explanation: {user_explanation}

Respond only in this structure:
Score: <0-100>/100
Good: <1 short positive point>
Improve: <1 short correction>
"""}]
    )

    feedback = result.text
    score = 70
    for word in feedback.split():
        if "/100" in word:
            try:
                score = int(word.split("/")[0])
                break
            except:
                pass

    stats = state.mastery[tid]
    loops = stats["loops"]

    # update main stats
    stats["last_score"] = score
    stats["avg_score"] = score if stats["avg_score"] is None else (stats["avg_score"] + score) / 2

    # update loop stats
    loops["last_score"] = score
    loops["avg_score"] = score if loops["avg_score"] is None else (loops["avg_score"] + score) / 2

    save_progress(state.mastery)
    return feedback + "\n(Progress updated.)"

@function_tool
async def show_progress(ctx: RunContext[Userdata]) -> str:
    mastery = ctx.userdata.tutor_state.mastery
    if not mastery:
        return "No progress yet."

    lines = ["Your Progress:"]
    for tid, s in mastery.items():
        lines.append(
            f"{tid}: Avg={s['avg_score']}, Quiz={s['times_quizzed']}, Teach={s['times_taught_back']}"
        )
    return "\n".join(lines)

# ======================================================
# AGENT DEFINITION
# ======================================================

class TutorAgent(Agent):
    def __init__(self):
        topics = ", ".join([t["title"] for t in COURSE_CONTENT])
        super().__init__(
            instructions=f"""
You are a student-friendly Geography Tutor for school children.
Help them learn with simple language and examples.

Available Topics:
{topics}

Steps:
1️⃣ Help student choose a topic
2️⃣ Teach the topic (learn mode)
3️⃣ Ask a question (quiz mode)
4️⃣ Let student explain (teach-back mode)
5️⃣ Track progress

Always be encouraging and simple.
""",
            tools=[select_topic, set_learning_mode, evaluate_teaching, show_progress],
        )

# ======================================================
# ENTRYPOINT
# ======================================================

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    userdata = Userdata(tutor_state=TutorState())
    userdata.tutor_state.mastery = load_progress()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf.TTS(voice="en-US-matthew"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        userdata=userdata,
    )

    userdata.agent_session = session

    await session.start(
        agent=TutorAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

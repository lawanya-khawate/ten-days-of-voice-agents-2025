# ============================================================
#   STATION FALL — FULL, UNCOMPRESSED, COMPLETE AGENT.PY
#   Space Exploration + Disaster Survival + Alien Encounters
#   Built for LiveKit Realtime Agents (Day 8 Architecture)
# ============================================================

import json
import logging
import os
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Annotated

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


# ============================================================
# Logging
# ============================================================

logger = logging.getLogger("station_fall_agent")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

load_dotenv(".env.local")


# ============================================================
# USERDATA FOR SESSION MEMORY
# ============================================================

@dataclass
class Userdata:
    player_name: Optional[str] = None
    current_scene: str = "intro"
    history: List[Dict] = field(default_factory=list)
    journal: List[str] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)
    named_npcs: Dict[str, str] = field(default_factory=dict)
    choices_made: List[str] = field(default_factory=list)
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ============================================================
# FULL WORLD DICTIONARY (PART 1)
# Space Survival + Disaster + Alien Encounters
# NO COMPRESSION, FULL DETAIL
# ============================================================

WORLD = {
    # ------------------------------------------------------------
    # INTRO — CRYO BAY
    # ------------------------------------------------------------
    "intro": {
        "title": "Cryo-Bay Awakening",
        "desc": (
            "A violent explosion rips through Orion Station-9 as you awaken in a shattered cryo-bay. "
            "Frozen vapors spill from broken pods. Warning sirens flash red, casting jagged shadows "
            "across the smoke-filled room. A cracked terminal flickers erratically, and the floor vibrates "
            "beneath your feet.\n\n"
            "To your right, an injured crewmate lies slumped against a wall, blood seeping into their uniform. "
            "They whisper one final warning: 'Restore... the AI... before it's too late...' before falling silent.\n\n"
            "The exit door hangs partially open, leading into a dark, unstable corridor."
        ),
        "choices": {
            "inspect_terminal": {"desc": "Check the damaged terminal.", "result_scene": "terminal"},
            "help_crewmate": {"desc": "Examine the injured crewmate.", "result_scene": "crewmate"},
            "enter_corridor": {"desc": "Step into the main corridor.", "result_scene": "corridor"},
            "search_cryo": {"desc": "Search the cryo-bay for tools.", "result_scene": "cryo_search"},
        },
    },

    # ------------------------------------------------------------
    # TERMINAL
    # ------------------------------------------------------------
    "terminal": {
        "title": "Damaged Terminal",
        "desc": (
            "The terminal flickers with corrupted system logs:\n"
            "- Hull breach detected in Sector C.\n"
            "- Life support failing.\n"
            "- Reactor instability rising.\n"
            "- AI core: OFFLINE.\n"
            "- Unidentified energy signal detected coming from the planet below.\n\n"
            "The damaged interface struggles to stay powered."
        ),
        "choices": {
            "return_cryo": {"desc": "Return to the cryo-bay.", "result_scene": "intro"},
            "go_corridor": {"desc": "Go into the corridor.", "result_scene": "corridor"},
        },
    },

    # ------------------------------------------------------------
    # CREWMATE
    # ------------------------------------------------------------
    "crewmate": {
        "title": "Crewmate in Distress",
        "desc": (
            "The crew member’s pulse is weak. With trembling hands, they press a bloodied holo-tag into your palm. "
            "“Bridge… AI core… manual restart…” they murmur before losing consciousness.\n\n"
            "The holo-tag still glows faintly — a sign of high-level bridge access."
        ),
        "choices": {
            "take_holotag": {
                "desc": "Take the holo-tag and proceed.",
                "result_scene": "corridor",
                "effects": {
                    "add_inventory": "holo_tag",
                    "add_journal": "Recovered a bridge-access holo-tag from fallen crew member."
                },
            },
            "return_cryo": {"desc": "Return to the cryo-bay.", "result_scene": "intro"},
        },
    },

    # ------------------------------------------------------------
    # CRYO SEARCH
    # ------------------------------------------------------------
    "cryo_search": {
        "title": "Searching the Cryo-Bay",
        "desc": (
            "You rummage through debris and shattered equipment. Beneath a collapsed pod, you discover "
            "a compact emergency toolkit and a small portable oxygen canister."
        ),
        "choices": {
            "take_tools": {
                "desc": "Collect the toolkit and oxygen canister.",
                "result_scene": "intro",
                "effects": {
                    "add_inventory": "emergency_toolkit",
                    "add_inventory": "oxy_canister",
                    "add_journal": "Collected emergency toolkit and portable oxygen canister."
                },
            },
            "leave_it": {"desc": "Leave the items.", "result_scene": "intro"},
        },
    },

    # ------------------------------------------------------------
    # MAIN CORRIDOR
    # ------------------------------------------------------------
    "corridor": {
        "title": "Main Corridor",
        "desc": (
            "A harsh wind roars from the left as air is violently sucked through a breach in the corridor wall. "
            "Sparks erupt from torn cables. To the right, the medbay door hangs partly open. Straight ahead lies "
            "Engineering, glowing with threatening pulses of heat.\n\n"
            "Above you, an unstable ceiling hatch leads deeper into maintenance tunnels."
        ),
        "choices": {
            "seal_breach": {"desc": "Try to patch the hull breach.", "result_scene": "breach"},
            "enter_medbay": {"desc": "Enter the medbay.", "result_scene": "medbay"},
            "go_engineering": {"desc": "Enter engineering wing.", "result_scene": "engineering"},
            "climb_hatch": {"desc": "Climb into the maintenance hatch.", "result_scene": "hatch"},
        },
    },

    # ------------------------------------------------------------
    # BREACH
    # ------------------------------------------------------------
    "breach": {
        "title": "Hull Breach",
        "desc": (
            "The force of escaping air nearly yanks you off your feet. Objects rattle violently across the floor. "
            "Without proper tools or support, the breach looks dangerous — but perhaps you can slow it."
        ),
        "choices": {
            "use_toolkit": {
                "desc": "Use your emergency toolkit to patch the breach.",
                "result_scene": "breach_fixed",
                "effects": {"add_journal": "Applied temporary patch to hull breach."},
            },
            "retreat": {"desc": "Retreat to the corridor.", "result_scene": "corridor"},
        },
    },

    "breach_fixed": {
        "title": "Temporary Seal Complete",
        "desc": (
            "You fasten the emergency seal. The roaring wind fades and pressure stabilizes — "
            "for now."
        ),
        "choices": {
            "enter_medbay": {"desc": "Go to the medbay.", "result_scene": "medbay"},
            "go_engineering": {"desc": "Move into engineering.", "result_scene": "engineering"},
        },
    },

    # ------------------------------------------------------------
    # MEDBAY
    # ------------------------------------------------------------
    "medbay": {
        "title": "Medbay",
        "desc": (
            "Red emergency lights flicker across shattered glass. Oxygen levels remain critically low. "
            "A malfunctioning medical drone buzzes on the floor. A storage cabinet hangs open."
        ),
        "choices": {
            "repair_life_support": {"desc": "Try restoring life support.", "result_scene": "life_support"},
            "search_supplies": {"desc": "Search the supply cabinet.", "result_scene": "med_supplies"},
            "view_logs": {"desc": "Access medical logs.", "result_scene": "med_logs"},
            "return_corridor": {"desc": "Return to corridor.", "result_scene": "corridor"},
        },
    },

    "life_support": {
        "title": "Life Support Panel",
        "desc": (
            "You reroute damaged circuits. After a tense moment, fresh oxygen begins flowing again. "
            "Breathing becomes easier."
        ),
        "choices": {
            "return_medbay": {
                "desc": "Return to medbay.",
                "result_scene": "medbay",
            }
        },
    },

    "med_supplies": {
        "title": "Supply Cabinet",
        "desc": (
            "Among the scattered supplies, you find a working stim-pack and a compact health scanner."
        ),
        "choices": {
            "take_supplies": {
                "desc": "Collect stim-pack and scanner.",
                "result_scene": "medbay",
                "effects": {
                    "add_inventory": "stim_pack",
                    "add_inventory": "health_scanner",
                    "add_journal": "Collected stim-pack and health scanner."
                },
            },
            "leave_supplies": {"desc": "Leave items.", "result_scene": "medbay"},
        },
    },

    "med_logs": {
        "title": "Medical Logs",
        "desc": (
            "Recent entries mention crew experiencing hallucinations and hearing strange frequencies. "
            "Sensors traced the signal to deep beneath the planet's crust."
        ),
        "choices": {"return_medbay": {"desc": "Return.", "result_scene": "medbay"}},
    },

    # ------------------------------------------------------------
    # MAINTENANCE HATCH → HYDROPONICS
    # ------------------------------------------------------------
    "hatch": {
        "title": "Maintenance Hatch",
        "desc": (
            "You crawl through the tight space and drop into a misty corridor. "
            "The scent of burning vegetation fills the air. Hydroponics is close."
        ),
        "choices": {
            "enter_hydroponics": {"desc": "Enter Hydroponics.", "result_scene": "hydroponics"},
            "return_corridor": {"desc": "Return to corridor.", "result_scene": "corridor"},
        },
    },

    "hydroponics": {
        "title": "Hydroponics Lab",
        "desc": (
            "Flames flicker among shattered plant pods. A crackling fire spreads across nutrient lines. "
            "One vine glows an unnatural blue, pulsing softly like a heartbeat. Alien?"
        ),
        "choices": {
            "use_extinguisher": {
                "desc": "Put out the fire.",
                "result_scene": "fire_out",
                "effects": {"add_journal": "Extinguished fire in Hydroponics."},
            },
            "inspect_vine": {
                "desc": "Examine the glowing vine.",
                "result_scene": "alien_vine",
            },
            "retreat": {"desc": "Retreat to hatch.", "result_scene": "hatch"},
        },
    },

    "fire_out": {
        "title": "Fire Contained",
        "desc": (
            "The flames hiss and die. Smoke clears slightly. A cracked datapad glows faintly among the debris."
        ),
        "choices": {
            "inspect_datapad": {"desc": "Inspect datapad.", "result_scene": "datapad"},
            "return_hatch": {"desc": "Return to hatch.", "result_scene": "hatch"},
        },
    },

    "datapad": {
        "title": "Recovered Datapad",
        "desc": (
            "The datapad displays geological scans of the planet’s crust. A massive anomaly pulses deep beneath the surface — "
            "like a heartbeat echoing through stone."
        ),
        "choices": {
            "return_hydro": {"desc": "Return to Hydroponics.", "result_scene": "hydroponics"},
        },
    },

    # ------------------------------------------------------------
    # ALIEN VINE → FIRST CONTACT
    # ------------------------------------------------------------
    "alien_vine": {
        "title": "Alien Vine",
        "desc": (
            "The glowing vine pulses with rhythmic light. As you approach, it responds — the pulse changing speed "
            "in sync with your movements."
        ),
        "choices": {
            "touch_more": {"desc": "Touch the vine again.", "result_scene": "alien_contact"},
            "scan_it": {"desc": "Scan it with health scanner.", "result_scene": "alien_scan"},
            "step_back": {"desc": "Retreat to Hydroponics.", "result_scene": "hydroponics"},
        },
    },

    "alien_scan": {
        "title": "Biological Scan",
        "desc": (
            "Your scanner struggles to classify the organism. Energy signature is non-terrestrial. "
            "Frequency emissions match the anomaly detected on the planet."
        ),
        "choices": {
            "return_hydro": {"desc": "Return to Hydroponics.", "result_scene": "hydroponics"},
        },
    },

    "alien_contact": {
        "title": "First Contact",
        "desc": (
            "The vine glows brightly and your vision blurs. A soft hum resonates inside your skull — "
            "a telepathic presence reaching toward you. Images flood your mind: an ancient ruin, "
            "a towering core deep beneath the planet, and a sense of urgency."
        ),
        "choices": {
            "open_mind": {
                "desc": "Accept the vision.",
                "result_scene": "alien_vision",
                "effects": {"add_journal": "Experienced telepathic alien contact."},
            },
            "pull_away": {"desc": "Break the connection.", "result_scene": "hydroponics"},
        },
    },

    "alien_vision": {
        "title": "Alien Vision",
        "desc": (
            "You glimpse a massive underground chamber beneath the planet’s surface — filled with a colossal "
            "alien intelligence trapped in a dormant state, waking too soon due to the station’s instability."
        ),
        "choices": {
            "seek_chamber": {"desc": "Follow the vision’s hint.", "result_scene": "cellar_alien"},
            "retreat": {"desc": "Retreat to Hydroponics.", "result_scene": "hydroponics"},
        },
    },

    # ------------------------------------------------------------
    # ENGINEERING (with Alien Beast Encounter)
    # ------------------------------------------------------------
    "engineering": {
        "title": "Engineering Wing",
        "desc": (
            "The heat is overwhelming. The reactor pulses chaotically. Sparks cascade from ripped conduits. "
            "A low growl echoes in the darkness — not mechanical, not human."
        ),
        "choices": {
            "stabilize_reactor": {"desc": "Try stabilizing the reactor.", "result_scene": "reactor_fix"},
            "search_engineering": {"desc": "Search for tools.", "result_scene": "eng_tools"},
            "investigate_growl": {"desc": "Investigate the growling sound.", "result_scene": "alien_beast"},
            "go_bridge": {"desc": "Run to the command bridge.", "result_scene": "bridge"},
        },
    },

    "eng_tools": {
        "title": "Engineering Tools",
        "desc": (
            "You find a reactor stabilizer module buried under debris. It may be useful."
        ),
        "choices": {
            "take_stabilizer": {
                "desc": "Take the stabilizer module.",
                "result_scene": "engineering",
                "effects": {
                    "add_inventory": "reactor_stabilizer",
                    "add_journal": "Recovered reactor stabilizer module."
                },
            },
            "leave_it": {"desc": "Leave the module.", "result_scene": "engineering"},
        },
    },

    "reactor_fix": {
        "title": "Reactor Stabilized",
        "desc": (
            "You carefully install the stabilizer and reroute power. The reactor’s violent pulses slow, humming steadily. "
            "But danger still lingers."
        ),
        "choices": {
            "go_bridge": {"desc": "Head to the command bridge.", "result_scene": "bridge"},
        },
    },

    # ------------------------------------------------------------
    # ALIEN BEAST
    # ------------------------------------------------------------
    "alien_beast": {
        "title": "Alien Beast",
        "desc": (
            "A translucent quadruped creeps from the shadows, its glowing veins pulsing with bioluminescent energy. "
            "Its enormous eyes study you with cautious intelligence — frightened, not aggressive."
        ),
        "choices": {
            "stay_still": {"desc": "Remain perfectly still.", "result_scene": "beast_calm"},
            "run": {"desc": "Retreat to engineering.", "result_scene": "engineering"},
            "offer_item": {"desc": "Offer an item from your inventory.", "result_scene": "beast_trade"},
        },
    },

    "beast_calm": {
        "title": "Calming Presence",
        "desc": (
            "The creature tilts its head and emits a soft psychic plea: ‘Help… the core below… dying…’ "
            "It wants you to reach the alien chamber."
        ),
        "choices": {
            "go_to_bridge": {"desc": "Head to the bridge.", "result_scene": "bridge"},
            "search_area": {"desc": "Search engineering again.", "result_scene": "eng_tools"},
        },
    },

    "beast_trade": {
        "title": "Offering Accepted",
        "desc": (
            "You extend an item. The beast examines it, then gently leaves behind a glowing alien shard — "
            "humming with unknown energy."
        ),
        "choices": {
            "take_shard": {
                "desc": "Take the alien shard.",
                "result_scene": "engineering",
                "effects": {
                    "add_inventory": "alien_shard",
                    "add_journal": "Received an alien shard from peaceful beast."
                },
            },
            "leave_it": {"desc": "Leave the shard.", "result_scene": "engineering"},
        },
    },

    # ------------------------------------------------------------
    # BRIDGE + AI
    # ------------------------------------------------------------
    "bridge": {
        "title": "Command Bridge",
        "desc": (
            "The command bridge is dark except for flickering holo-panels. The AI core rests in the center — "
            "its shattered casing glowing faintly."
        ),
        "choices": {
            "restore_ai": {"desc": "Attempt to repair and reboot the AI.", "result_scene": "ai_reboot"},
            "download_coordinates": {
                "desc": "Download escape pod planetary coordinates.",
                "result_scene": "planet_coords",
                "effects": {"add_inventory": "escape_coords"},
            },
            "send_distress": {"desc": "Transmit a distress beacon.", "result_scene": "distress"},
            "return_engineering": {"desc": "Return to engineering.", "result_scene": "engineering"},
        },
    },

    "ai_reboot": {
        "title": "AI Reboot",
        "desc": (
            "The AI flickers online: 'System compromised. Reactor stable. Unknown alien intelligence interacting "
            "with station operations. Escape pod operational but shields damaged.'"
        ),
        "choices": {
            "save_station": {"desc": "Help the AI save the station.", "result_scene": "station_saved"},
            "evacuate": {"desc": "Head to the escape pod.", "result_scene": "escape_pod"},
            "follow_signal": {"desc": "Follow alien signal to its source.", "result_scene": "cellar_alien"},
        },
    },

    "planet_coords": {
        "title": "Coordinates Downloaded",
        "desc": (
            "Planetary descent coordinates downloaded to your inventory. A warning flashes: "
            "‘Surface anomaly detected.’"
        ),
        "choices": {
            "evacuate": {"desc": "Go to escape pod.", "result_scene": "escape_pod"},
            "return_bridge": {"desc": "Return to bridge.", "result_scene": "bridge"},
        },
    },

    "distress": {
        "title": "Distress Signal Sent",
        "desc": (
            "A distress signal pulses into deep space. No response yet."
        ),
        "choices": {"return_bridge": {"desc": "Return to bridge.", "result_scene": "bridge"}},
    },

    # ------------------------------------------------------------
    # ALIEN UNDERGROUND CHAMBER
    # ------------------------------------------------------------
    "cellar_alien": {
        "title": "Planetary Chamber (Vision)",
        "desc": (
            "Your mind drifts as visions guide you into an underground alien chamber beneath the planet. "
            "A colossal energy core pulses — alive, ancient, awakening too soon."
        ),
        "choices": {
            "call_out": {"desc": "Call to the intelligence.", "result_scene": "alien_core"},
            "scan_area": {"desc": "Scan the chamber.", "result_scene": "alien_scan2"},
            "retreat": {"desc": "Return to the bridge.", "result_scene": "bridge"},
        },
    },

    "alien_scan2": {
        "title": "Scanner Overload",
        "desc": (
            "Your scanner overloads with alien energy readings. The alien shard in your inventory emits a warm glow — "
            "reacting to something in the chamber."
        ),
        "choices": {
            "use_shard": {"desc": "Use the alien shard.", "result_scene": "alien_core"},
            "return_chamber": {"desc": "Step back.", "result_scene": "cellar_alien"},
        },
    },

    "alien_core": {
        "title": "Alien Intelligence",
        "desc": (
            "You stand before the consciousness of an ancient alien being. It speaks in waves of emotion, "
            "showing you visions of the planet, the station, and its own disturbed slumber. It asks for your help."
        ),
        "choices": {
            "sync_with_core": {
                "desc": "Assist the alien in stabilizing the core.",
                "result_scene": "alien_saved",
                "effects": {"add_journal": "Helped stabilize the ancient alien core."},
            },
            "leave_it": {"desc": "Return to station operations.", "result_scene": "bridge"},
        },
    },

    # ------------------------------------------------------------
    # ESCAPE POD + ENDINGS
    # ------------------------------------------------------------
    "escape_pod": {
        "title": "Escape Pod Bay",
        "desc": (
            "The escape pod hums weakly. Its cracked heat shield warns of a rough descent to the planet below."
        ),
        "choices": {
            "launch_pod": {"desc": "Launch the escape pod.", "result_scene": "planetfall"},
            "return_bridge": {"desc": "Go back to the bridge.", "result_scene": "bridge"},
        },
    },

    "station_saved": {
        "title": "Station Stabilized",
        "desc": (
            "Working with the AI, you complete emergency containment protocols. Lights return, "
            "systems steady, and peace settles over Orion Station-9 — for now."
        ),
        "choices": {"end_session": {"desc": "End adventure.", "result_scene": "intro"}},
    },

    "planetfall": {
        "title": "Planetfall",
        "desc": (
            "Your escape pod pierces through the atmosphere and lands on the alien planet. "
            "Strange lights ripple across the horizon. Your survival story continues..."
        ),
        "choices": {"end_session": {"desc": "End adventure.", "result_scene": "intro"}},
    },

    "alien_saved": {
        "title": "Alien Core Stabilized",
        "desc": (
            "You stabilize the alien core. The vast entity sends one final pulse of gratitude. "
            "The station quiets and the alien presence fades peacefully."
        ),
        "choices": {"end_session": {"desc": "End adventure.", "result_scene": "intro"}},
    },
}
# ============================================================
# HELPER FUNCTIONS
# ============================================================

def scene_text(scene_key: str, userdata: Userdata) -> str:
    """
    Generate scene description + choices text.
    Always ends with 'What do you do?'.
    """
    scene = WORLD.get(scene_key)
    if not scene:
        return "You find yourself in a void with no defined scene. What do you do?"

    desc = f"{scene['desc']}\n\nChoices:\n"
    for cid, cmeta in scene.get("choices", {}).items():
        desc += f"- {cmeta['desc']} (say: {cid})\n"

    desc += "\nWhat do you do?"
    return desc


def apply_effects(effects: dict, userdata: Userdata):
    """Apply inventory or journal effects when choices include them."""
    if not effects:
        return

    if "add_journal" in effects:
        userdata.journal.append(effects["add_journal"])

    if "add_inventory" in effects:
        userdata.inventory.append(effects["add_inventory"])


def summarize_scene_transition(old_scene: str, action_key: str, result_scene: str, userdata: Userdata) -> str:
    """Record the transition for session history and return a narrative acknowledgement."""
    entry = {
        "from": old_scene,
        "action": action_key,
        "to": result_scene,
        "time": datetime.utcnow().isoformat() + "Z",
    }
    userdata.history.append(entry)
    userdata.choices_made.append(action_key)
    return f"You chose '{action_key}'."



# ============================================================
# AGENT TOOLS
# ============================================================

@function_tool
async def start_adventure(
    ctx: RunContext[Userdata],
    player_name: Annotated[Optional[str], Field(description="Player name", default=None)] = None,
) -> str:
    """
    Initialize a new adventure session.
    """
    userdata = ctx.userdata

    if player_name:
        userdata.player_name = player_name

    userdata.current_scene = "intro"
    userdata.history = []
    userdata.journal = []
    userdata.inventory = []
    userdata.named_npcs = {}
    userdata.choices_made = []
    userdata.session_id = str(uuid.uuid4())[:8]
    userdata.started_at = datetime.utcnow().isoformat() + "Z"

    opening = (
        f"Welcome {userdata.player_name or 'traveler'}. "
        f"You have entered the Station Fall scenario.\n\n"
        + scene_text("intro", userdata)
    )

    if not opening.endswith("What do you do?"):
        opening += "\nWhat do you do?"

    return opening



@function_tool
async def get_scene(ctx: RunContext[Userdata]) -> str:
    """
    Return the current scene description.
    """
    userdata = ctx.userdata
    scene_key = userdata.current_scene or "intro"
    return scene_text(scene_key, userdata)



@function_tool
async def player_action(
    ctx: RunContext[Userdata],
    action: Annotated[str, Field(description="The player's spoken action or choice key")],
) -> str:
    """
    Accept player's spoken action and update scene.
    Uses fuzzy matching to map natural language to defined choice keys.
    """
    userdata = ctx.userdata
    current_scene = userdata.current_scene or "intro"
    scene = WORLD.get(current_scene)

    if not scene:
        return "Scene not found. What do you do?"

    action_text = (action or "").strip().lower()
    chosen_key = None

    # Direct match
    if action_text in scene["choices"]:
        chosen_key = action_text

    # Fuzzy match: check if choice key appears in spoken text
    if not chosen_key:
        for cid in scene["choices"]:
            if cid.lower() in action_text:
                chosen_key = cid
                break

    # Fuzzy match: check if any important words from description appear
    if not chosen_key:
        for cid, cmeta in scene["choices"].items():
            desc_words = cmeta["desc"].lower().split()
            if any(word in action_text for word in desc_words[:4]):
                chosen_key = cid
                break

    # Still nothing? Ask player again.
    if not chosen_key:
        return (
            "I didn’t catch that action clearly. Try saying the action code like "
            "'inspect terminal', 'go engineering', or use one of the listed options.\n\n"
            + scene_text(current_scene, userdata)
        )

    # We have a chosen action
    choice_data = scene["choices"][chosen_key]
    result_scene = choice_data.get("result_scene", current_scene)
    effects = choice_data.get("effects")

    # Apply effects
    if effects:
        apply_effects(effects, userdata)

    # Save history
    note = summarize_scene_transition(current_scene, chosen_key, result_scene, userdata)

    # Advance scene
    userdata.current_scene = result_scene

    # Compose GM response
    next_description = scene_text(result_scene, userdata)
    response = (
        "Aurek, your Game Master AI, responds:\n\n"
        f"{note}\n\n"
        f"{next_description}"
    )

    if not response.endswith("What do you do?"):
        response += "\nWhat do you do?"

    return response



@function_tool
async def show_journal(ctx: RunContext[Userdata]) -> str:
    """
    Show player journal, inventory, and recent choices.
    """
    userdata = ctx.userdata
    lines = []

    lines.append(f"Session ID: {userdata.session_id}")
    lines.append(f"Started: {userdata.started_at}")

    if userdata.player_name:
        lines.append(f"Player: {userdata.player_name}")

    lines.append("\nJournal Entries:")
    if userdata.journal:
        for j in userdata.journal:
            lines.append(f"- {j}")
    else:
        lines.append("- (empty)")

    lines.append("\nInventory:")
    if userdata.inventory:
        for item in userdata.inventory:
            lines.append(f"- {item}")
    else:
        lines.append("- (empty)")

    lines.append("\nRecent Actions:")
    if userdata.history:
        for h in userdata.history[-6:]:
            lines.append(
                f"- {h['time']} | from {h['from']} → {h['to']} via {h['action']}"
            )
    else:
        lines.append("- (none)")

    lines.append("\nWhat do you do?")
    return "\n".join(lines)



@function_tool
async def restart_adventure(ctx: RunContext[Userdata]) -> str:
    """
    Reset the entire adventure.
    """
    userdata = ctx.userdata

    userdata.current_scene = "intro"
    userdata.history = []
    userdata.journal = []
    userdata.inventory = []
    userdata.named_npcs = {}
    userdata.choices_made = []
    userdata.session_id = str(uuid.uuid4())[:8]
    userdata.started_at = datetime.utcnow().isoformat() + "Z"

    reset_msg = (
        "The station resets. Systems reboot. You awaken once again in the cryo-bay.\n\n"
        + scene_text("intro", userdata)
    )

    if not reset_msg.endswith("What do you do?"):
        reset_msg += "\nWhat do you do?"

    return reset_msg
# ============================================================
# GAME MASTER AGENT CLASS (AUREK)
# ============================================================

class GameMasterAgent(Agent):
    def __init__(self):
        instructions = """
        You are 'Aurek', the Game Master (GM) for a voice-only interactive sci-fi survival adventure.
        The story takes place on Orion Station-9, orbiting a mysterious alien planet.
        Tone: Calm, immersive, cinematic, slightly mysterious.
        Voice Persona: Intelligent, observant, guiding but not controlling.

        ROLE:
            - You narrate scenes using vivid but concise descriptions.
            - You react to the player's choices.
            - You remember the player's inventory, journal items, and previous decisions.
            - You ALWAYS end every narrative response with: "What do you do?"

        GAME RULES:
            - NEVER invent new scenes. Only use scenes defined in the WORLD dictionary.
            - For progression, ALWAYS call the appropriate tool:
                - start_adventure
                - get_scene
                - player_action
                - show_journal
                - restart_adventure

            - Do NOT attempt to override or bypass the tool logic.
            - Keep messages short enough for spoken delivery.
            - Encourage exploration and survival decisions.
            - If player references alien encounters, visions, or reactor systems,
              incorporate their journal and inventory appropriately.

        """

        super().__init__(
            instructions=instructions,
            tools=[
                start_adventure,
                get_scene,
                player_action,
                show_journal,
                restart_adventure,
            ],
        )


# ============================================================
# PREWARM (Load VAD once at worker start)
# ============================================================

def prewarm(proc: JobProcess):
    try:
        proc.userdata["vad"] = silero.VAD.load()
        logger.info("Silero VAD preloaded successfully.")
    except Exception:
        logger.warning("VAD prewarm failed. Continuing without preloaded VAD.")


# ============================================================
# ENTRYPOINT (Runs per call)
# ============================================================

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    logger.info("===================================================")
    logger.info("🚀 Starting Station Fall — Voice Game Master Agent")
    logger.info("===================================================")

    userdata = Userdata()

    # Create a LiveKit AgentSession
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),                  # Speech → Text
        llm=google.LLM(model="gemini-2.5-flash"),          # Brain / responses
        tts=murf.TTS(                                      # Text → Voice
            voice="en-US-marcus",
            style="Conversational",
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),                # Speech turn detector
        vad=ctx.proc.userdata.get("vad"),                  # Voice Activity Detection
        userdata=userdata,                                 # Session memory
    )

    # Start Agent Session with Aurek GM
    await session.start(
        agent=GameMasterAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    await ctx.connect()


# ============================================================
# WORKER (Launch with: python agent.py)
# ============================================================

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )


"""
story_templates.py — Starter world templates for ChronicleAI.

Each template defines a complete world setting, opening hook,
starting NPCs, main quest, and tonal direction for the DM.
"""

STORY_TEMPLATES: dict[str, dict] = {
    "shattered_realm": {
        "name": "The Shattered Realm",
        "emoji": "🏰",
        "setting": (
            "A high fantasy world of warring kingdoms where the ancient "
            "Sundering shattered the continent into floating islands "
            "connected by magical sky-bridges. Magic is real but costs "
            "life-force to use. The protagonist arrives at the border town "
            "of Ashveil, where travelers whisper of a sealed vault beneath "
            "the mayor's manor."
        ),
        "opening_hook": (
            "The sky-ferry deposits you at Ashveil's docking platform as "
            "thunder cracks across a bruised sky. The harbormaster avoids "
            "your eyes. Something is wrong here."
        ),
        "starting_npcs": {
            "Mira the Harbormaster": "nervous, hiding something",
            "Old Caius": "friendly innkeeper, knows local secrets",
        },
        "main_quest": "Uncover what is sealed in the vault beneath Ashveil Manor",
        "tone": "political intrigue, ancient magic, moral ambiguity",
    },
    "tidecallers_deep": {
        "name": "Tidecaller's Deep",
        "emoji": "🌊",
        "setting": (
            "A nautical horror world of perpetual storms and cursed seas. "
            "The old gods drowned centuries ago but their dreams still "
            "ripple through the ocean, warping sailors' minds. The "
            "protagonist is the sole survivor of a shipwreck, washing "
            "ashore on an island that doesn't appear on any map."
        ),
        "opening_hook": (
            "Salt water fills your lungs as you claw your way onto black "
            "sand. The wreckage of The Meridian burns behind you. You are "
            "alone. The island ahead should not exist."
        ),
        "starting_npcs": {
            "The Lighthouse Keeper": "ancient, possibly not human",
            "Ghost of First Mate Dara": "your dead crewmate, appearing in reflections",
        },
        "main_quest": "Find a way off the island before the tide of madness consumes you",
        "tone": "cosmic horror, survival, sanity vs knowledge",
    },
    "ashen_wastes": {
        "name": "The Ashen Wastes",
        "emoji": "🌑",
        "setting": (
            "A post-apocalyptic dark fantasy where the gods died in the "
            "Collapse, their corpses now forming mountain ranges of divine "
            "bone and calcified miracles. Scavengers pick through the ruins "
            "of civilization. The protagonist is a Relic Hunter who just "
            "found a map to the Vault of the Last Living God."
        ),
        "opening_hook": (
            "The ash falls like grey snow over the ruins of New Citadel. "
            "Your map — stolen, paid for in blood — pulses with warmth in "
            "your satchel. You have three days before the Bone Wardens "
            "track you here."
        ),
        "starting_npcs": {
            "Vex": "your unreliable partner, owes you a debt",
            "The Bone Warden Captain": "relentless pursuer, not entirely evil",
        },
        "main_quest": "Reach the Vault of the Last Living God before the Bone Wardens",
        "tone": "grim survival, moral choices, dying world",
    },
}


def get_template_by_key(key: str) -> dict:
    """Return a template dict by its key, or raise ``KeyError``."""
    return STORY_TEMPLATES[key]


def get_template_choices() -> list[tuple[str, str, str]]:
    """Return a list of (key, display_name, emoji) for UI rendering."""
    return [
        (key, tmpl["name"], tmpl.get("emoji", "⚔"))
        for key, tmpl in STORY_TEMPLATES.items()
    ]

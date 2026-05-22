from __future__ import annotations

import math
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


GOODS = {
    "water": {"name": "Water", "weight": 1},
    "grain": {"name": "Grain", "weight": 1},
    "ore": {"name": "Ore", "weight": 2},
    "medicine": {"name": "Medicine", "weight": 1},
    "circuits": {"name": "Circuits", "weight": 1},
    "relics": {"name": "Relics", "weight": 1},
    "alloys": {"name": "Alloys", "weight": 2},
    "polymers": {"name": "Polymers", "weight": 1},
    "ceramics": {"name": "Ceramics", "weight": 1},
    "composites": {"name": "Composites", "weight": 1},
    "coolant": {"name": "Coolant", "weight": 1},
    "electronics": {"name": "Electronics", "weight": 1},
}

GOOD_MARKETS = {
    "water": {
        "basePrice": 12,
        "transport": 0.06,
        "sources": {"eirene": 0.58, "aurora": 0.75, "solace": 0.92},
        "sourceLabel": "ice and garden worlds",
    },
    "grain": {
        "basePrice": 13,
        "transport": 0.07,
        "sources": {"eirene": 0.54, "aurora": 0.92},
        "sourceLabel": "agricultural habitats",
    },
    "ore": {
        "basePrice": 24,
        "transport": 0.09,
        "sources": {"vesta": 0.5, "morrow": 0.74},
        "sourceLabel": "foundries and mining moons",
    },
    "medicine": {
        "basePrice": 44,
        "transport": 0.055,
        "sources": {"solace": 0.55, "kepler": 0.82},
        "sourceLabel": "medical sanctuaries",
    },
    "circuits": {
        "basePrice": 57,
        "transport": 0.06,
        "sources": {"kepler": 0.78, "vesta": 0.84, "morrow": 0.82},
        "sourceLabel": "research labs and salvage yards",
    },
    "relics": {
        "basePrice": 132,
        "transport": 0.075,
        "sources": {"morrow": 0.56, "kepler": 0.9},
        "sourceLabel": "rift ruins and survey archives",
    },
    "alloys": {
        "basePrice": 32,
        "transport": 0.08,
        "sources": {"vesta": 0.52, "morrow": 0.78},
        "sourceLabel": "foundries and salvage mills",
    },
    "polymers": {
        "basePrice": 18,
        "transport": 0.06,
        "sources": {"eirene": 0.54, "solace": 0.72, "aurora": 0.88},
        "sourceLabel": "garden chemworks and med fabs",
    },
    "ceramics": {
        "basePrice": 28,
        "transport": 0.075,
        "sources": {"vesta": 0.56, "morrow": 0.8, "aurora": 0.92},
        "sourceLabel": "kilns, slagworks, and heat-shield shops",
    },
    "composites": {
        "basePrice": 40,
        "transport": 0.065,
        "sources": {"vesta": 0.68, "kepler": 0.76, "aurora": 0.9},
        "sourceLabel": "fabrication yards and research labs",
    },
    "coolant": {
        "basePrice": 22,
        "transport": 0.055,
        "sources": {"aurora": 0.66, "kepler": 0.76, "solace": 0.84},
        "sourceLabel": "station pumps and climate-control plants",
    },
    "electronics": {
        "basePrice": 48,
        "transport": 0.06,
        "sources": {"kepler": 0.58, "vesta": 0.78, "aurora": 0.88},
        "sourceLabel": "workshops, probe labs, and assembly decks",
    },
}

SYSTEMS = {
    "aurora": {
        "name": "Aurora Station",
        "faction": "Free Dockyards",
        "economy": "Trade hub",
        "x": 0,
        "y": 0,
        "risk": 0.12,
        "description": "A bright ring station where every deal starts with a handshake and ends with a surcharge.",
        "market": {
            "water": 9,
            "grain": 12,
            "ore": 23,
            "medicine": 42,
            "circuits": 54,
            "relics": 130,
            "alloys": 33,
            "polymers": 17,
            "ceramics": 27,
            "composites": 39,
            "coolant": 20,
            "electronics": 45,
        },
    },
    "kepler": {
        "name": "Kepler Reach",
        "faction": "Survey League",
        "economy": "Research frontier",
        "x": 2,
        "y": -1,
        "risk": 0.18,
        "description": "A scatter of observatories listening to ancient noise in the dark.",
        "market": {
            "water": 13,
            "grain": 17,
            "ore": 20,
            "medicine": 34,
            "circuits": 49,
            "relics": 118,
            "alloys": 35,
            "polymers": 21,
            "ceramics": 31,
            "composites": 34,
            "coolant": 18,
            "electronics": 39,
        },
    },
    "vesta": {
        "name": "Vesta Foundry",
        "faction": "Iron Compact",
        "economy": "Heavy industry",
        "x": -2,
        "y": 1,
        "risk": 0.16,
        "description": "Molten docks, old union songs, and freighters queued like beads on a wire.",
        "market": {
            "water": 14,
            "grain": 19,
            "ore": 12,
            "medicine": 46,
            "circuits": 58,
            "relics": 142,
            "alloys": 20,
            "polymers": 24,
            "ceramics": 22,
            "composites": 30,
            "coolant": 25,
            "electronics": 43,
        },
    },
    "eirene": {
        "name": "Eirene Garden",
        "faction": "Green Choir",
        "economy": "Agricultural habitat",
        "x": 1,
        "y": 3,
        "risk": 0.1,
        "description": "A terraced habitat full of orchard decks, clean air, and watchful customs officers.",
        "market": {
            "water": 8,
            "grain": 7,
            "ore": 28,
            "medicine": 37,
            "circuits": 63,
            "relics": 151,
            "alloys": 38,
            "polymers": 12,
            "ceramics": 35,
            "composites": 42,
            "coolant": 24,
            "electronics": 52,
        },
    },
    "morrow": {
        "name": "Morrow Rift",
        "faction": "Unclaimed",
        "economy": "Salvage zone",
        "x": -3,
        "y": -2,
        "risk": 0.36,
        "description": "Broken moons and broken promises drift through a region of unreliable beacons.",
        "market": {
            "water": 17,
            "grain": 22,
            "ore": 18,
            "medicine": 55,
            "circuits": 46,
            "relics": 98,
            "alloys": 28,
            "polymers": 26,
            "ceramics": 25,
            "composites": 45,
            "coolant": 31,
            "electronics": 50,
        },
    },
    "solace": {
        "name": "Solace Spire",
        "faction": "Civic Mandate",
        "economy": "Medical sanctuary",
        "x": 4,
        "y": 2,
        "risk": 0.14,
        "description": "White towers and patient traffic, protected by polite but heavily armed patrols.",
        "market": {
            "water": 12,
            "grain": 15,
            "ore": 31,
            "medicine": 24,
            "circuits": 60,
            "relics": 126,
            "alloys": 42,
            "polymers": 16,
            "ceramics": 32,
            "composites": 44,
            "coolant": 19,
            "electronics": 55,
        },
    },
}

PLANET_SAMPLE_SIZE = 6

STATIONS = {
    "aurora": {
        "name": "Aurora Ring Station",
        "areas": [
            {
                "id": "docking",
                "name": "Docking Collar A",
                "faction": "Free Dockyards",
                "wealth": "Working",
                "economy": "Port services",
                "security": "Managed",
                "description": "Traffic crews, fuel umbilicals, and independent captains waiting for clearance.",
            },
            {
                "id": "bourse",
                "name": "Meridian Bourse",
                "faction": "Free Dockyards",
                "wealth": "Affluent",
                "economy": "Commodities exchange",
                "security": "Tight",
                "description": "A bright trading floor where water futures and salvage rights change hands by the minute.",
            },
            {
                "id": "underdeck",
                "name": "Underdeck Twelve",
                "faction": "Dockside Union",
                "wealth": "Low",
                "economy": "Black repair work",
                "security": "Loose",
                "description": "The station's practical underside: cheap noodles, cheaper welds, and very few receipts.",
            },
            {
                "id": "embassy",
                "name": "Shared Embassy Row",
                "faction": "Civic Mandate",
                "wealth": "Comfortable",
                "economy": "Diplomatic services",
                "security": "Tight",
                "description": "Quiet offices where minor factions rent flags, translators, and plausible deniability.",
            },
        ],
    },
    "kepler": {
        "name": "Kepler Listening Post",
        "areas": [
            {
                "id": "gantry",
                "name": "Survey Gantry",
                "faction": "Survey League",
                "wealth": "Working",
                "economy": "Probe launches",
                "security": "Managed",
                "description": "Stacks of folded probes wait beside pilots who swear the stars are starting to answer back.",
            },
            {
                "id": "archive",
                "name": "Signal Archive",
                "faction": "Survey League",
                "wealth": "Comfortable",
                "economy": "Research licensing",
                "security": "Tight",
                "description": "Cold vaults of pattern-matched radio ghosts, leased by the hour to nervous academics.",
            },
            {
                "id": "canteen",
                "name": "Blue Shift Canteen",
                "faction": "Independent Crews",
                "wealth": "Modest",
                "economy": "Crew services",
                "security": "Loose",
                "description": "A dim mess hall where survey pilots trade coordinates and pretend not to be superstitious.",
            },
        ],
    },
    "vesta": {
        "name": "Vesta Anvil Station",
        "areas": [
            {
                "id": "forge",
                "name": "Open Forge Deck",
                "faction": "Iron Compact",
                "wealth": "Industrial",
                "economy": "Heavy fabrication",
                "security": "Tight",
                "description": "Heat shimmer, crane-song, and molten metal bright enough to paint the windows gold.",
            },
            {
                "id": "union",
                "name": "Union Hall 9",
                "faction": "Foundry Local",
                "wealth": "Working",
                "economy": "Labor contracts",
                "security": "Managed",
                "description": "A stubborn hall of contract boards, old banners, and captains looking for reliable hands.",
            },
            {
                "id": "scrap",
                "name": "Scrap Crown",
                "faction": "Iron Compact",
                "wealth": "Low",
                "economy": "Salvage resale",
                "security": "Loose",
                "description": "A rotating crown of surplus hull plates, cracked drones, and parts that still know their jobs.",
            },
        ],
    },
    "eirene": {
        "name": "Eirene Orchard Station",
        "areas": [
            {
                "id": "customs",
                "name": "Green Customs Hall",
                "faction": "Green Choir",
                "wealth": "Comfortable",
                "economy": "Agricultural inspection",
                "security": "Tight",
                "description": "Seed vault seals, patient inspectors, and the clean smell of quarantine foam.",
            },
            {
                "id": "market",
                "name": "Canopy Market",
                "faction": "Green Choir",
                "wealth": "Affluent",
                "economy": "Food exports",
                "security": "Managed",
                "description": "Tiered stalls under grow-lamps, dense with citrus steam and polite bargaining.",
            },
            {
                "id": "pilgrim",
                "name": "Pilgrim Fernwalk",
                "faction": "Wayfarer Compact",
                "wealth": "Modest",
                "economy": "Transit lodging",
                "security": "Loose",
                "description": "A humid path of rented sleep pods, prayer ribbons, and travelers between lives.",
            },
        ],
    },
    "morrow": {
        "name": "Morrow Patchwork Dock",
        "areas": [
            {
                "id": "clamps",
                "name": "Borrowed Clamp Line",
                "faction": "Unclaimed",
                "wealth": "Low",
                "economy": "Emergency docking",
                "security": "Loose",
                "description": "Mag-clamps bolted to older mag-clamps, holding together through confidence and rust.",
            },
            {
                "id": "auction",
                "name": "Last Light Auction",
                "faction": "Rift Brokers",
                "wealth": "Volatile",
                "economy": "Salvage claims",
                "security": "Managed",
                "description": "A loud auction room where wreckage is sold before anyone proves it is empty.",
            },
            {
                "id": "clinic",
                "name": "Red Lantern Clinic",
                "faction": "Civic Mandate",
                "wealth": "Modest",
                "economy": "Frontier medicine",
                "security": "Tight",
                "description": "A compact clinic with patched bulkheads, strict triage, and no patience for hero stories.",
            },
        ],
    },
    "solace": {
        "name": "Solace High Spire",
        "areas": [
            {
                "id": "triage",
                "name": "Triage Atrium",
                "faction": "Civic Mandate",
                "wealth": "Affluent",
                "economy": "Medical intake",
                "security": "Tight",
                "description": "White floors, quiet drones, and patient traffic moving with ceremonial precision.",
            },
            {
                "id": "pharma",
                "name": "Pharma Exchange",
                "faction": "Civic Mandate",
                "wealth": "Elite",
                "economy": "Medicine brokerage",
                "security": "Strict",
                "description": "Glass counters, sealed cases, and prices that make captains reconsider altruism.",
            },
            {
                "id": "garden",
                "name": "Recovery Garden",
                "faction": "Green Choir",
                "wealth": "Comfortable",
                "economy": "Therapeutic habitat",
                "security": "Managed",
                "description": "A quiet garden deck where off-duty medics and lucky patients remember the sky.",
            },
        ],
    },
}

PLANETS = {
    "aurora": [
        {
            "id": "new-lumen",
            "name": "New Lumen",
            "type": "temperate colony",
            "dominantFaction": "Free Dockyards",
            "wealth": "Comfortable",
            "placeCount": 2600,
            "seed": "aurora-new-lumen",
            "terrain": ["coastal arcology", "rain plain", "old launch desert", "tidal city"],
            "factions": ["Free Dockyards", "Dockside Union", "Civic Mandate", "Independent Freeholders"],
        },
        {
            "id": "brass-moon",
            "name": "Brass Moon",
            "type": "airless mining moon",
            "dominantFaction": "Dockside Union",
            "wealth": "Working",
            "placeCount": 1800,
            "seed": "aurora-brass-moon",
            "terrain": ["regolith mine", "crater town", "ice shadow", "rail depot"],
            "factions": ["Dockside Union", "Free Dockyards", "Rift Brokers", "Independent Freeholders"],
        },
    ],
    "kepler": [
        {
            "id": "halcyon",
            "name": "Halcyon",
            "type": "storm world",
            "dominantFaction": "Survey League",
            "wealth": "Research",
            "placeCount": 3400,
            "seed": "kepler-halcyon",
            "terrain": ["storm shelf", "high observatory", "lightning basin", "floating lab"],
            "factions": ["Survey League", "Independent Crews", "Civic Mandate", "Wayfarer Compact"],
        }
    ],
    "vesta": [
        {
            "id": "rivet",
            "name": "Rivet",
            "type": "factory planet",
            "dominantFaction": "Iron Compact",
            "wealth": "Industrial",
            "placeCount": 4200,
            "seed": "vesta-rivet",
            "terrain": ["slag sea", "foundry city", "cooling trench", "ore rail"],
            "factions": ["Iron Compact", "Foundry Local", "Dockside Union", "Rift Brokers"],
        }
    ],
    "eirene": [
        {
            "id": "pollen",
            "name": "Pollen",
            "type": "garden world",
            "dominantFaction": "Green Choir",
            "wealth": "Affluent",
            "placeCount": 5100,
            "seed": "eirene-pollen",
            "terrain": ["orchard continent", "seed monastery", "canal farm", "cloud forest"],
            "factions": ["Green Choir", "Wayfarer Compact", "Civic Mandate", "Independent Freeholders"],
        }
    ],
    "morrow": [
        {
            "id": "blackglass",
            "name": "Blackglass",
            "type": "fractured world",
            "dominantFaction": "Unclaimed",
            "wealth": "Low",
            "placeCount": 2300,
            "seed": "morrow-blackglass",
            "terrain": ["impact plain", "broken dome", "ash canyon", "buried relay"],
            "factions": ["Unclaimed", "Rift Brokers", "Independent Crews", "Civic Mandate"],
        }
    ],
    "solace": [
        {
            "id": "mercy",
            "name": "Mercy",
            "type": "sanctuary planet",
            "dominantFaction": "Civic Mandate",
            "wealth": "Elite",
            "placeCount": 3900,
            "seed": "solace-mercy",
            "terrain": ["hospital city", "alpine refuge", "sealed valley", "quiet coast"],
            "factions": ["Civic Mandate", "Green Choir", "Wayfarer Compact", "Free Dockyards"],
        }
    ],
}

PLACE_PREFIXES = [
    "Amber",
    "Ash",
    "Blue",
    "Brass",
    "Cinder",
    "Glass",
    "Hollow",
    "Iron",
    "Lantern",
    "Red",
    "Salt",
    "Silver",
    "Still",
    "Waking",
]

PLACE_FEATURES = [
    "Basin",
    "Bridge",
    "Canal",
    "Canyon",
    "Depot",
    "Harbor",
    "Market",
    "Monastery",
    "Observatory",
    "Refinery",
    "Relay",
    "Spire",
    "Town",
    "Vault",
]

PLACE_KINDS = [
    "settlement",
    "industrial site",
    "research site",
    "wilderness site",
    "ruin",
    "port district",
    "resource claim",
]

WEALTH_BANDS = ["Low", "Modest", "Working", "Comfortable", "Affluent", "Elite"]
SECURITY_BANDS = ["Loose", "Managed", "Tight", "Strict"]

SECTOR_SEED = "starless-drift-sector-v2"
STARTING_GALAXY_ID = "aurora-thread"
GALAXY_TARGET = 20
GALAXY_SYSTEM_MAX = 5_000
SECTOR_SYSTEM_TARGET = 3_000
SECTOR_PLANET_MIN_PER_SYSTEM = 1
SECTOR_PLANET_MAX_PER_SYSTEM = 10

GALAXY_SIZE_OPTIONS = [700, 950, 1_400, 2_100, 3_000, 4_200, GALAXY_SYSTEM_MAX]
GALAXY_THEMES = [
    "Settled spur",
    "Ore braid",
    "Garden shoal",
    "Signal dark",
    "Medical archipelago",
    "Rift salvage",
    "Ancient vault",
    "Trade lattice",
]
GALAXY_NAME_PARTS = [
    ("Aurora", "Thread"),
    ("Andara", "Sea"),
    ("Cobalt", "Braid"),
    ("Vesper", "Crown"),
    ("Kite", "Lattice"),
    ("Umbral", "Bloom"),
    ("Hearth", "Vault"),
    ("Glass", "Shoal"),
    ("Nadir", "Coil"),
    ("Warden", "Field"),
    ("Jade", "Rift"),
    ("Echowake", "Reach"),
]

SYSTEM_NAME_PARTS = [
    ("Ardent", "Crown"),
    ("Bastion", "Vale"),
    ("Calyx", "Drift"),
    ("Dawn", "Harbor"),
    ("Ember", "Shoal"),
    ("Faraday", "Wake"),
    ("Gallows", "Light"),
    ("Hearth", "Gate"),
    ("Iris", "Deep"),
    ("Juno", "Crossing"),
    ("Kestrel", "Fall"),
    ("Lacuna", "Bend"),
    ("Mariner", "Well"),
    ("Nadir", "Chain"),
    ("Orison", "Reach"),
    ("Perehelion", "Yard"),
    ("Quarry", "Star"),
    ("Ravel", "Line"),
    ("Sable", "Haven"),
    ("Tallow", "Run"),
    ("Umber", "Cleft"),
    ("Verdant", "Hush"),
    ("Warden", "Rise"),
    ("Xanthe", "Ferry"),
    ("Yarrow", "Span"),
    ("Zephyr", "Mist"),
    ("Aster", "Lock"),
    ("Briar", "Forge"),
    ("Cobalt", "Rim"),
    ("Dusk", "Archive"),
    ("Echelon", "Point"),
    ("Frost", "Quay"),
    ("Glimmer", "Field"),
    ("Horizon", "Vault"),
    ("Ivory", "Rift"),
    ("Juniper", "Fold"),
    ("Kite", "Anchor"),
    ("Lattice", "Moor"),
    ("Mirage", "Basin"),
    ("Northstar", "Bourse"),
    ("Oberon", "Bloom"),
    ("Palisade", "Tide"),
    ("Quiet", "Cairn"),
    ("Rook", "Nest"),
]

SYSTEM_FIRST_NAMES = [
    "Aegis",
    "Alder",
    "Anvil",
    "Argent",
    "Ashen",
    "Beacon",
    "Beryl",
    "Black",
    "Bright",
    "Cairn",
    "Cardinal",
    "Cinder",
    "Copper",
    "Crown",
    "Dagger",
    "Drift",
    "Ebon",
    "Ember",
    "Fallow",
    "Farsong",
    "Gilded",
    "Glass",
    "Grey",
    "Halcyon",
    "Harrow",
    "Helio",
    "Indigo",
    "Iron",
    "Ivory",
    "Jade",
    "Keel",
    "Lantern",
    "Last",
    "Low",
    "Mercy",
    "Mirror",
    "Nickel",
    "Obsidian",
    "Pale",
    "Quartz",
    "Red",
    "Riven",
    "Salt",
    "Sapphire",
    "Shattered",
    "Silver",
    "Starling",
    "Still",
    "Thorn",
    "Umbral",
    "Verdigris",
    "Violet",
    "Wake",
    "White",
    "Winter",
    "Woven",
    "Yellow",
    "Zenith",
]

SYSTEM_SECOND_NAMES = [
    "Anchor",
    "Archive",
    "Basin",
    "Belt",
    "Bloom",
    "Bourse",
    "Bridge",
    "Cairn",
    "Chain",
    "Cleft",
    "Cove",
    "Cradle",
    "Crossing",
    "Crown",
    "Deep",
    "Drift",
    "Fall",
    "Ferry",
    "Field",
    "Fold",
    "Forge",
    "Gate",
    "Harbor",
    "Haven",
    "Hush",
    "Junction",
    "Kiln",
    "Lattice",
    "Light",
    "Line",
    "Lock",
    "Moor",
    "Nest",
    "Point",
    "Quay",
    "Reach",
    "Relay",
    "Rift",
    "Rim",
    "Rise",
    "Run",
    "Shoal",
    "Spindle",
    "Star",
    "Tide",
    "Vale",
    "Vault",
    "Wake",
    "Well",
    "Yard",
]

SYSTEM_ARCHETYPES = [
    {
        "economy": "Mining frontier",
        "faction": "Iron Compact",
        "risk": 0.18,
        "goods": ["ore", "alloys", "ceramics"],
        "description": "mining claims, tug traffic, and refinery beacons spread across a practical dark",
    },
    {
        "economy": "Agricultural habitat",
        "faction": "Green Choir",
        "risk": 0.1,
        "goods": ["grain", "water", "polymers"],
        "description": "orbital farms and patient water haulers keep the local lanes busy",
    },
    {
        "economy": "Research frontier",
        "faction": "Survey League",
        "risk": 0.18,
        "goods": ["circuits", "electronics", "composites", "relics"],
        "description": "survey arrays, probe caches, and old signals make captains slow down",
    },
    {
        "economy": "Medical sanctuary",
        "faction": "Civic Mandate",
        "risk": 0.13,
        "goods": ["medicine", "coolant", "polymers"],
        "description": "clinic traffic and protected convoys turn quiet orbits into careful choreography",
    },
    {
        "economy": "Salvage zone",
        "faction": "Rift Brokers",
        "risk": 0.34,
        "goods": ["relics", "circuits", "alloys", "electronics"],
        "description": "wreckage rights, patched docks, and disputed beacons give every chart a footnote",
    },
    {
        "economy": "Trade hub",
        "faction": "Free Dockyards",
        "risk": 0.15,
        "goods": ["water", "grain", "composites", "coolant"],
        "description": "merchant berths, customs delays, and fuel ledgers make the system louder than most",
    },
]

PLANET_ARCHETYPES = [
    {
        "type": "airless moon",
        "sizeClass": "small",
        "terrain": ["regolith mine", "crater town", "ice shadow", "rail depot"],
        "wealth": "Working",
        "locationRange": (0, 20),
    },
    {
        "type": "dwarf rock",
        "sizeClass": "small",
        "terrain": ["iron ridge", "dust basin", "abandoned claim", "shattered plain"],
        "wealth": "Low",
        "locationRange": (0, 18),
    },
    {
        "type": "ice moon",
        "sizeClass": "small",
        "terrain": ["ice shelf", "brine vent", "shadow crater", "polar relay"],
        "wealth": "Modest",
        "locationRange": (2, 20),
    },
    {
        "type": "fractured world",
        "sizeClass": "small",
        "terrain": ["impact plain", "broken dome", "ash canyon", "buried relay"],
        "wealth": "Low",
        "locationRange": (0, 20),
    },
    {
        "type": "desert planet",
        "sizeClass": "medium",
        "terrain": ["salt flat", "dry canal", "wind city", "buried sea"],
        "wealth": "Working",
        "locationRange": (18, 180),
    },
    {
        "type": "ocean planet",
        "sizeClass": "medium",
        "terrain": ["floating port", "storm reef", "kelp arcology", "tidal rig"],
        "wealth": "Comfortable",
        "locationRange": (40, 360),
    },
    {
        "type": "temperate colony",
        "sizeClass": "large",
        "terrain": ["coastal arcology", "rain plain", "old launch desert", "tidal city"],
        "wealth": "Comfortable",
        "locationRange": (900, 3200),
    },
    {
        "type": "garden world",
        "sizeClass": "large",
        "terrain": ["orchard continent", "seed monastery", "canal farm", "cloud forest"],
        "wealth": "Affluent",
        "locationRange": (1200, 5200),
    },
    {
        "type": "factory planet",
        "sizeClass": "large",
        "terrain": ["slag sea", "foundry city", "cooling trench", "ore rail"],
        "wealth": "Industrial",
        "locationRange": (600, 4300),
    },
    {
        "type": "storm world",
        "sizeClass": "medium",
        "terrain": ["storm shelf", "high observatory", "lightning basin", "floating lab"],
        "wealth": "Research",
        "locationRange": (8, 120),
    },
    {
        "type": "sanctuary planet",
        "sizeClass": "large",
        "terrain": ["hospital city", "alpine refuge", "sealed valley", "quiet coast"],
        "wealth": "Elite",
        "locationRange": (300, 2200),
    },
    {
        "type": "gas giant",
        "sizeClass": "giant",
        "terrain": ["cloud refinery", "magnetic belt", "scoop platform", "storm observatory"],
        "wealth": "Industrial",
        "locationRange": (0, 14),
    },
]

STATION_NAME_PARTS = [
    "Anchor",
    "Array",
    "Bourse",
    "Crown",
    "Dock",
    "Exchange",
    "Gate",
    "Harbor",
    "Lantern",
    "Quay",
    "Ring",
    "Spindle",
    "Vault",
    "Yard",
]

STATION_AREA_TEMPLATES = [
    ("docking", "Docking Collar", "Port services", "Traffic crews, fuel umbilicals, and captains waiting for clearance."),
    ("market", "Exchange Deck", "Commodities exchange", "Price boards, broker booths, and cargo factors crowd the main concourse."),
    ("repair", "Repair Gantry", "Ship maintenance", "Work crews, hull plates, and diagnostic rigs keep the dock awake."),
    ("hab", "Habitat Drum", "Crew services", "Bunks, canteens, and station gossip circle under soft spin gravity."),
    ("customs", "Customs Hall", "Inspection services", "Inspectors watch sealed cargo move through patient scanner gates."),
    ("archive", "Survey Archive", "Research licensing", "Cold data rooms sell local maps, rumors, and old beacon records."),
    ("clinic", "Frontier Clinic", "Medical intake", "Compact triage bays handle shipboard injuries and bad decisions."),
    ("scrap", "Scrap Gallery", "Salvage resale", "Old drones, hull fragments, and maybe-functional components hang in inventory nets."),
]

SYSTEM_STATIONS: dict[str, list[dict[str, Any]]] = {}
SYSTEM_GRAPH: dict[str, list[str]] = {}
GALAXIES: dict[str, dict[str, Any]] = {
    STARTING_GALAXY_ID: {
        "id": STARTING_GALAXY_ID,
        "index": 0,
        "name": "Aurora Thread",
        "size": SECTOR_SYSTEM_TARGET,
        "theme": "Settled spur",
        "risk": 0.14,
        "x": 0.0,
        "y": 0.0,
    }
}
GALAXY_INDEX: dict[str, int] = {STARTING_GALAXY_ID: 0}
GALAXY_ID_BY_INDEX: dict[int, str] = {0: STARTING_GALAXY_ID}
CORE_SYSTEM_IDS = tuple(SYSTEMS)
STARTING_KNOWN_SYSTEM_COUNT = 18
STARTING_KNOWN_SYSTEM_IDS = list(CORE_SYSTEM_IDS)
STARTER_SYSTEM_GATE_OFFSETS = {
    "aurora": [1, 2, 3],
    "kepler": [4],
    "vesta": [5],
    "eirene": [6],
    "solace": [7],
}
SYSTEM_INDEX: dict[str, int] = {system_id: index for index, system_id in enumerate(CORE_SYSTEM_IDS)}
SYSTEM_ID_BY_INDEX: dict[int, str] = {index: system_id for index, system_id in enumerate(CORE_SYSTEM_IDS)}
SYSTEM_GALAXY_INDEX: dict[str, tuple[str, int]] = {
    system_id: (STARTING_GALAXY_ID, index) for system_id, index in SYSTEM_INDEX.items()
}
GALAXY_SYSTEM_ID_BY_INDEX: dict[tuple[str, int], str] = {
    (STARTING_GALAXY_ID, index): system_id for index, system_id in SYSTEM_ID_BY_INDEX.items()
}


def _slug(text: str) -> str:
    return "-".join(part for part in text.lower().replace("'", "").split() if part)


def _choice(rng: random.Random, values: list[Any]) -> Any:
    return values[rng.randrange(len(values))]


def _galaxy_name(index: int) -> str:
    if index < len(GALAXY_NAME_PARTS):
        first, second = GALAXY_NAME_PARTS[index]
        return f"{first} {second}"
    first = SYSTEM_FIRST_NAMES[index % len(SYSTEM_FIRST_NAMES)]
    second = SYSTEM_SECOND_NAMES[(index // len(SYSTEM_FIRST_NAMES)) % len(SYSTEM_SECOND_NAMES)]
    return f"{first} {second} Galaxy"


def _galaxy_id_for_index(index: int) -> str | None:
    if index < 0 or index >= GALAXY_TARGET:
        return None
    if index in GALAXY_ID_BY_INDEX:
        return GALAXY_ID_BY_INDEX[index]
    galaxy_id = _slug(_galaxy_name(index))
    if galaxy_id in GALAXY_INDEX and GALAXY_INDEX[galaxy_id] != index:
        galaxy_id = f"{galaxy_id}-{index + 1:02d}"
    GALAXY_INDEX[galaxy_id] = index
    GALAXY_ID_BY_INDEX[index] = galaxy_id
    return galaxy_id


def _galaxy_index(galaxy_id: str) -> int | None:
    if galaxy_id in GALAXY_INDEX:
        return GALAXY_INDEX[galaxy_id]
    for index in range(GALAXY_TARGET):
        if _galaxy_id_for_index(index) == galaxy_id:
            return index
    return None


def ensure_galaxy(galaxy_id: str | None) -> bool:
    if not galaxy_id:
        return False
    if galaxy_id in GALAXIES:
        return True
    index = _galaxy_index(galaxy_id)
    if index is None or index >= GALAXY_TARGET:
        return False

    rng = random.Random(f"{SECTOR_SEED}:galaxy:{index}")
    theme = _choice(rng, GALAXY_THEMES)
    size = _choice(rng, GALAXY_SIZE_OPTIONS)
    if index == 0:
        size = SECTOR_SYSTEM_TARGET
        theme = "Settled spur"
    GALAXIES[galaxy_id] = {
        "id": galaxy_id,
        "index": index,
        "name": _galaxy_name(index),
        "size": min(GALAXY_SYSTEM_MAX, size),
        "theme": theme,
        "risk": round(rng.uniform(0.08, 0.42), 2),
        "x": round(math.cos(index * 2.17) * (index + 1) * 11.0 + rng.uniform(-2, 2), 2),
        "y": round(math.sin(index * 2.17) * (index + 1) * 11.0 + rng.uniform(-2, 2), 2),
    }
    return True


def galaxy_system_target(galaxy_id: str) -> int:
    ensure_galaxy(galaxy_id)
    return GALAXIES[galaxy_id]["size"]


def system_identity(system_id: str | None) -> tuple[str, int] | None:
    if not system_id:
        return None
    if system_id in SYSTEM_GALAXY_INDEX:
        return SYSTEM_GALAXY_INDEX[system_id]
    if system_id in SYSTEMS:
        galaxy_id = SYSTEMS[system_id].get("galaxyId", STARTING_GALAXY_ID)
        index = SYSTEM_INDEX.get(system_id, 0)
        SYSTEM_GALAXY_INDEX[system_id] = (galaxy_id, index)
        GALAXY_SYSTEM_ID_BY_INDEX[(galaxy_id, index)] = system_id
        return galaxy_id, index
    recovered = recover_generated_system_identity(system_id)
    if recovered:
        return recovered
    return None


def recover_generated_system_identity(system_id: str) -> tuple[str, int] | None:
    possible_galaxies = []
    for galaxy_index in range(GALAXY_TARGET):
        galaxy_id = _galaxy_id_for_index(galaxy_index)
        if galaxy_id == STARTING_GALAXY_ID or system_id.startswith(f"{galaxy_id}-"):
            possible_galaxies.append(galaxy_id)

    for galaxy_id in possible_galaxies:
        start_index = len(CORE_SYSTEM_IDS) if galaxy_id == STARTING_GALAXY_ID else 0
        for index in range(start_index, galaxy_system_target(galaxy_id)):
            generated_index = index - len(CORE_SYSTEM_IDS) + 1 if galaxy_id == STARTING_GALAXY_ID else index + 1
            base_id = _slug(_generated_system_name(generated_index))
            candidate_id = base_id if galaxy_id == STARTING_GALAXY_ID else f"{galaxy_id}-{base_id}"
            if candidate_id != system_id:
                continue
            sort_index = index if galaxy_id == STARTING_GALAXY_ID else (_galaxy_index(galaxy_id) or 0) * GALAXY_SYSTEM_MAX + index
            SYSTEM_INDEX[system_id] = sort_index
            SYSTEM_GALAXY_INDEX[system_id] = (galaxy_id, index)
            GALAXY_SYSTEM_ID_BY_INDEX[(galaxy_id, index)] = system_id
            if galaxy_id == STARTING_GALAXY_ID:
                SYSTEM_ID_BY_INDEX[index] = system_id
            return galaxy_id, index
    return None


def system_galaxy_id(system_id: str | None) -> str:
    identity = system_identity(system_id)
    galaxy_id = identity[0] if identity else STARTING_GALAXY_ID
    ensure_galaxy(galaxy_id)
    return galaxy_id


def same_galaxy(origin: str, destination: str) -> bool:
    ensure_system(origin)
    ensure_system(destination)
    return system_galaxy_id(origin) == system_galaxy_id(destination)


def _generated_market(base: dict[str, int], focus_goods: list[str], risk: float, rng: random.Random) -> dict[str, int]:
    market = {}
    for good, model in GOOD_MARKETS.items():
        if good in focus_goods:
            multiplier = rng.uniform(0.52, 0.86)
        else:
            multiplier = rng.uniform(0.9, 1.34) + risk * 0.18
        market[good] = max(3, round(model["basePrice"] * multiplier))
    market.update({good: price for good, price in base.items() if good in GOODS})
    return market


def _station_area(system_id: str, station_index: int, area_index: int, rng: random.Random, faction: str) -> dict[str, Any]:
    key, label, economy, description = _choice(rng, STATION_AREA_TEMPLATES)
    suffix = "" if area_index == 0 else f" {area_index + 1}"
    return {
        "id": f"{key}-{station_index + 1}-{area_index + 1}",
        "name": f"{label}{suffix}",
        "faction": faction if rng.random() < 0.65 else _choice(rng, [arch["faction"] for arch in SYSTEM_ARCHETYPES]),
        "wealth": _choice(rng, WEALTH_BANDS),
        "economy": economy,
        "security": _choice(rng, SECURITY_BANDS),
        "description": description,
    }


def _generated_station(system_id: str, system: dict[str, Any], station_index: int, rng: random.Random) -> dict[str, Any]:
    station_word = _choice(rng, STATION_NAME_PARTS)
    name = f"{system['name']} {station_word}" if station_index == 0 else f"{_choice(rng, STATION_NAME_PARTS)} {station_index + 1}"
    area_count = rng.randint(2, 6)
    return {
        "id": "primary" if station_index == 0 else f"station-{station_index + 1}",
        "name": name,
        "areas": [_station_area(system_id, station_index, index, rng, system["faction"]) for index in range(area_count)],
    }


def _planet_location_count(planet: dict[str, Any], rng: random.Random) -> int:
    type_text = planet["type"].lower()
    if planet.get("sizeClass") == "small" or any(word in type_text for word in ("moon", "dwarf", "fractured")):
        low, high = 0, 20
    else:
        archetype = next((item for item in PLANET_ARCHETYPES if item["type"] == planet["type"]), None)
        low, high = archetype["locationRange"] if archetype else (10, 180)

    count = rng.randint(low, high)
    if "airless" in type_text or "gas giant" in type_text:
        count = max(0, count - rng.randint(0, 8))
    if planet.get("wealth") in {"Affluent", "Elite", "Industrial"} and high > 20:
        count = max(count, rng.randint(max(low, high // 3), high))
    return max(0, count)


def _generated_planet(system_id: str, system: dict[str, Any], index: int, rng: random.Random) -> dict[str, Any]:
    archetype = _choice(rng, PLANET_ARCHETYPES)
    prefixes = ["Asha", "Belen", "Cair", "Damar", "Eos", "Fane", "Galen", "Hesper", "Ivo", "Jora", "Kara", "Lume"]
    suffixes = ["Prime", "Minor", "Reach", "Cove", "Glass", "Basin", "Ward", "Crown", "Fall", "Deep", "Mere", "Run"]
    name = f"{_choice(rng, prefixes)} {_choice(rng, suffixes)}"
    if index > 0 and rng.random() < 0.55:
        name = f"{name} {index + 1}"
    planet = {
        "id": f"{system_id}-{_slug(name)}-{index + 1}",
        "name": name,
        "type": archetype["type"],
        "sizeClass": archetype["sizeClass"],
        "dominantFaction": system["faction"] if rng.random() < 0.72 else _choice(rng, [arch["faction"] for arch in SYSTEM_ARCHETYPES]),
        "wealth": archetype["wealth"],
        "placeCount": 0,
        "seed": f"{system_id}-{_slug(name)}-{index + 1}",
        "terrain": archetype["terrain"],
        "factions": sorted({system["faction"], _choice(rng, [arch["faction"] for arch in SYSTEM_ARCHETYPES]), "Independent Freeholders"}),
    }
    planet["placeCount"] = _planet_location_count(planet, rng)
    return planet


def _generated_planet_count(system: dict[str, Any], rng: random.Random) -> int:
    economy = system["economy"].lower()
    if "mining" in economy or "salvage" in economy:
        low, high = 5, SECTOR_PLANET_MAX_PER_SYSTEM
    elif "research" in economy:
        low, high = 3, 8
    elif "trade" in economy:
        low, high = 2, 7
    elif "medical" in economy:
        low, high = 2, 6
    elif "agricultural" in economy:
        low, high = 4, 9
    else:
        low, high = SECTOR_PLANET_MIN_PER_SYSTEM, 6

    risk_bonus = round(system["risk"] * 3)
    return max(SECTOR_PLANET_MIN_PER_SYSTEM, min(SECTOR_PLANET_MAX_PER_SYSTEM, rng.randint(low, high) + risk_bonus))


def _generated_system_name(index: int) -> str:
    if index <= len(SYSTEM_NAME_PARTS):
        first, second = SYSTEM_NAME_PARTS[index - 1]
        return f"{first} {second}"

    base_index = index - len(SYSTEM_NAME_PARTS) - 1
    first = SYSTEM_FIRST_NAMES[base_index % len(SYSTEM_FIRST_NAMES)]
    second = SYSTEM_SECOND_NAMES[(base_index // len(SYSTEM_FIRST_NAMES)) % len(SYSTEM_SECOND_NAMES)]
    cycle = base_index // (len(SYSTEM_FIRST_NAMES) * len(SYSTEM_SECOND_NAMES))
    return f"{first} {second}" if cycle == 0 else f"{first} {second} {cycle + 1:02d}"


def _system_id_for_index(index: int, galaxy_id: str = STARTING_GALAXY_ID) -> str | None:
    if not ensure_galaxy(galaxy_id) or index < 0 or index >= galaxy_system_target(galaxy_id):
        return None
    if (galaxy_id, index) in GALAXY_SYSTEM_ID_BY_INDEX:
        return GALAXY_SYSTEM_ID_BY_INDEX[(galaxy_id, index)]
    if galaxy_id == STARTING_GALAXY_ID and index in SYSTEM_ID_BY_INDEX:
        return SYSTEM_ID_BY_INDEX[index]

    generated_index = index - len(CORE_SYSTEM_IDS) + 1 if galaxy_id == STARTING_GALAXY_ID else index + 1
    name = _generated_system_name(generated_index)
    system_id = _slug(name) if galaxy_id == STARTING_GALAXY_ID else f"{galaxy_id}-{_slug(name)}"
    if system_id in SYSTEM_INDEX and SYSTEM_INDEX[system_id] != index:
        system_id = f"{system_id}-{generated_index:04d}"
    sort_index = index if galaxy_id == STARTING_GALAXY_ID else (_galaxy_index(galaxy_id) or 0) * GALAXY_SYSTEM_MAX + index
    SYSTEM_INDEX[system_id] = sort_index
    SYSTEM_GALAXY_INDEX[system_id] = (galaxy_id, index)
    GALAXY_SYSTEM_ID_BY_INDEX[(galaxy_id, index)] = system_id
    if galaxy_id == STARTING_GALAXY_ID:
        SYSTEM_ID_BY_INDEX[index] = system_id
    return system_id


def _system_index(system_id: str) -> int | None:
    identity = system_identity(system_id)
    if identity:
        return identity[1]

    for index in range(len(CORE_SYSTEM_IDS), SECTOR_SYSTEM_TARGET):
        if _system_id_for_index(index) == system_id:
            return index
    return None


def _system_name_for_id(system_id: str) -> str:
    identity = system_identity(system_id)
    if identity is None:
        return system_id.replace("-", " ").title()
    galaxy_id, index = identity
    if galaxy_id == STARTING_GALAXY_ID and index < len(CORE_SYSTEM_IDS):
        return SYSTEMS[system_id]["name"]
    generated_index = index - len(CORE_SYSTEM_IDS) + 1 if galaxy_id == STARTING_GALAXY_ID else index + 1
    return _generated_system_name(generated_index)


def _branch_coordinates(galaxy_id: str, index: int, rng: random.Random) -> tuple[float, float]:
    if index <= 0:
        return 0.0, 0.0
    parent_id = _system_id_for_index((index - 1) // 3, galaxy_id)
    ensure_system(parent_id)
    parent = SYSTEMS[parent_id]
    angle = index * 2.399963229728653 + rng.uniform(-0.34, 0.34)
    distance = rng.uniform(3.2, 7.8) + min(6.0, math.sqrt(index) * 0.035)
    return (
        round(parent["x"] + math.cos(angle) * distance, 2),
        round(parent["y"] + math.sin(angle) * distance, 2),
    )


def ensure_system(system_id: str | None) -> bool:
    if not system_id:
        return False
    if system_id in SYSTEMS:
        SYSTEMS[system_id].setdefault("galaxyId", system_galaxy_id(system_id))
        return True

    identity = system_identity(system_id)
    if identity is None:
        return False
    galaxy_id, index = identity
    if index < 0 or index >= galaxy_system_target(galaxy_id):
        return False
    if galaxy_id == STARTING_GALAXY_ID and index < len(CORE_SYSTEM_IDS):
        return False

    rng = random.Random(f"{SECTOR_SEED}:system:{galaxy_id}:{index}")
    archetype = _choice(rng, SYSTEM_ARCHETYPES)
    x, y = _branch_coordinates(galaxy_id, index, rng)
    risk = max(0.06, min(0.48, archetype["risk"] + rng.uniform(-0.06, 0.08)))
    focus_goods = archetype["goods"][:]
    name = _system_name_for_id(system_id)
    system = {
        "name": name,
        "faction": archetype["faction"],
        "economy": archetype["economy"],
        "x": x,
        "y": y,
        "risk": round(risk, 2),
        "galaxyId": galaxy_id,
        "description": f"{name} is a {archetype['economy'].lower()} where {archetype['description']}.",
        "market": _generated_market({}, focus_goods, risk, rng),
        "focusGoods": focus_goods,
    }
    SYSTEMS[system_id] = system

    for good in focus_goods:
        GOOD_MARKETS[good]["sources"][system_id] = round(rng.uniform(0.52, 0.94), 2)

    station_count = rng.randint(1, 4)
    stations = [_generated_station(system_id, system, station_index, rng) for station_index in range(station_count)]
    STATIONS[system_id] = stations[0]
    SYSTEM_STATIONS[system_id] = stations

    planet_count = _generated_planet_count(system, rng)
    PLANETS[system_id] = [_generated_planet(system_id, system, planet_index, rng) for planet_index in range(planet_count)]
    return True


def branch_system_ids(system_id: str) -> list[str]:
    identity = system_identity(system_id)
    if identity is None:
        return []
    galaxy_id, index = identity
    child_start = index * 3 + 1
    child_end = min(child_start + 3, galaxy_system_target(galaxy_id))
    return [
        child_id
        for child_index in range(child_start, child_end)
        if (child_id := _system_id_for_index(child_index, galaxy_id))
    ]


def starting_known_system_ids() -> list[str]:
    return [
        system_id
        for index in range(STARTING_KNOWN_SYSTEM_COUNT)
        if (system_id := _system_id_for_index(index, STARTING_GALAXY_ID))
    ]


def _expand_sector() -> None:

    for system_id, system in SYSTEMS.items():
        system.setdefault("galaxyId", STARTING_GALAXY_ID)

    for system_id, station in list(STATIONS.items()):
        station.setdefault("id", "primary")
        SYSTEM_STATIONS[system_id] = [station]
        if system_id in {"aurora", "vesta", "morrow", "solace"}:
            extra_rng = random.Random(f"{SECTOR_SEED}:station:{system_id}")
            for station_index in range(1, extra_rng.randint(2, 4)):
                SYSTEM_STATIONS[system_id].append(_generated_station(system_id, SYSTEMS[system_id], station_index, extra_rng))

    for system_id, planets in PLANETS.items():
        for planet in planets:
            planet.setdefault("sizeClass", "small" if any(word in planet["type"] for word in ("moon", "fractured")) else "large")
            planet["placeCount"] = _planet_location_count(planet, random.Random(f"{SECTOR_SEED}:locations:{planet['seed']}"))


def _build_system_graph() -> dict[str, list[str]]:
    return {}


_expand_sector()
STARTING_KNOWN_SYSTEM_IDS = starting_known_system_ids()
SYSTEM_GRAPH = _build_system_graph()

STARTING_LOG = [
    "Flight license accepted.",
    "Dock clamps released from Aurora Station.",
    "The Peregrine awaits your first order.",
]


@dataclass(frozen=True)
class ShipSpec:
    name: str = "Peregrine"
    ship_id: str = "peregrine"
    max_hull: int = 100
    max_fuel: int = 18
    cargo_capacity: int = 28


SHIP = ShipSpec()
SHIP_AI_REPLACEMENT_COST = 5000
SHIP_AI_GENDERS = {"Male", "Female"}

SHIP_UPGRADES = {
    "fuel_tanks": {
        "name": "Auxiliary Fuel Tanks",
        "system": "Endurance",
        "maxTier": 3,
        "costs": [180, 360, 640],
        "effects": ["+6 fuel capacity", "+12 fuel capacity", "+18 fuel capacity"],
        "description": "Pressure-rated tankage for longer burns between station pumps.",
    },
    "cargo_bays": {
        "name": "Modular Cargo Bays",
        "system": "Trade",
        "maxTier": 3,
        "costs": [220, 420, 760],
        "effects": ["+8 cargo capacity", "+16 cargo capacity", "+24 cargo capacity"],
        "description": "Reworked hold frames, better clamps, and cleaner load paths.",
    },
    "hull_plating": {
        "name": "Layered Hull Plating",
        "system": "Survival",
        "maxTier": 3,
        "costs": [200, 460, 820],
        "effects": ["+20 hull integrity", "+40 hull integrity", "+60 hull integrity"],
        "description": "Ablative panels and reinforced spars for rough approaches.",
    },
    "jump_drive": {
        "name": "Tuned Jump Drive",
        "system": "Navigation",
        "maxTier": 3,
        "costs": [260, 560, 980],
        "effects": ["-10% jump fuel", "-18% jump fuel", "-25% jump fuel"],
        "description": "Cleaner burn timing reduces interstellar fuel waste.",
    },
    "maneuver_thrusters": {
        "name": "Maneuvering Thrusters",
        "system": "Local Flight",
        "maxTier": 3,
        "costs": [240, 520, 900],
        "effects": ["-10% local fuel", "-18% local fuel", "-25% local fuel"],
        "description": "Better attitude control for docking, orbit work, launches, and landings.",
    },
}

UPGRADE_MATERIALS = {
    "fuel_tanks": {"alloys": 2, "polymers": 1, "coolant": 1},
    "cargo_bays": {"alloys": 2, "composites": 2, "polymers": 1},
    "hull_plating": {"alloys": 3, "ceramics": 2, "composites": 1},
    "jump_drive": {"electronics": 2, "circuits": 1, "coolant": 1, "relics": 1},
    "maneuver_thrusters": {"alloys": 1, "electronics": 1, "circuits": 1, "coolant": 1},
}

UPGRADE_KEYWORDS = {
    "fuel_tanks": ("fuel", "port", "docking", "dock", "trade", "water", "hauler", "customs"),
    "cargo_bays": ("cargo", "market", "commodities", "trade", "exchange", "bourse", "freighter", "industrial"),
    "hull_plating": ("repair", "forge", "scrap", "salvage", "metal", "industrial", "mine", "foundry", "ore"),
    "jump_drive": ("survey", "research", "archive", "signal", "relic", "observatory", "relay", "ruin", "probe"),
    "maneuver_thrusters": ("docking", "dock", "gantry", "repair", "probe", "port", "customs", "launch"),
}

UPGRADE_PART_LABELS = {
    "fuel_tanks": ("tank baffles", "pressure valves", "fuel manifold kit", "cryogenic seal pack"),
    "cargo_bays": ("hold braces", "mag-clamp rails", "cargo frame kit", "load-balancer lattice"),
    "hull_plating": ("ablative plates", "spar collars", "impact webbing", "armor patch laminate"),
    "jump_drive": ("field coils", "nav harmonics", "phase governor", "beacon sync core"),
    "maneuver_thrusters": ("gimbal rings", "vector nozzles", "attitude jets", "burn sequencer"),
}

TRAVEL_STATES = {"deep_space", "system_space", "orbit", "atmosphere", "landed", "docked"}
JUMP_STATES = {"deep_space", "system_space"}
TRAVEL_STATE_LABELS = {
    "deep_space": "Deep space",
    "system_space": "System space",
    "orbit": "Orbit",
    "atmosphere": "Atmosphere",
    "landed": "Landed",
    "docked": "Docked",
}

CHEAT_FLAGS = {
    "unlimitedFuel": {
        "label": "Unlimited fuel",
        "description": "Fuel is refilled and no travel burns consume it.",
    },
    "unlimitedCredits": {
        "label": "Unlimited credits",
        "description": "Purchases, repairs, refuels, and upgrades skip credit costs.",
    },
    "invulnerableHull": {
        "label": "Invulnerable hull",
        "description": "Hull is restored and damage events cannot reduce it.",
    },
    "freeMaterials": {
        "label": "Free upgrade materials",
        "description": "Ship upgrades ignore cargo material requirements.",
    },
}

PLAYER_GATE_ANCHOR_COST = 1_200
PLAYER_GATE_ANCHOR_MATERIALS = {"alloys": 8, "electronics": 4, "circuits": 4, "relics": 2}


def default_cheats() -> dict[str, bool]:
    return {flag: False for flag in CHEAT_FLAGS}


def normalize_cheats(game: dict[str, Any]) -> None:
    raw = game.get("cheats", {})
    if not isinstance(raw, dict):
        raw = {}
    game["cheats"] = {flag: bool(raw.get(flag, False)) for flag in CHEAT_FLAGS}


def cheat_enabled(game: dict[str, Any], flag: str) -> bool:
    return bool(game.get("cheats", {}).get(flag, False))


def public_cheats(game: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": flag,
            "label": config["label"],
            "description": config["description"],
            "enabled": cheat_enabled(game, flag),
        }
        for flag, config in CHEAT_FLAGS.items()
    ]


def payload_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def apply_hull_damage(game: dict[str, Any], damage: int) -> int:
    if cheat_enabled(game, "invulnerableHull"):
        game["hull"] = max_hull(game)
        return 0
    game["hull"] = max(0, game["hull"] - damage)
    return damage


def can_pay(game: dict[str, Any], price: int) -> bool:
    return cheat_enabled(game, "unlimitedCredits") or game["credits"] >= price


def spend_credits(game: dict[str, Any], price: int) -> int:
    if cheat_enabled(game, "unlimitedCredits"):
        return 0
    game["credits"] -= price
    return price


def create_game() -> dict[str, Any]:
    return {
        "day": 1,
        "location": "aurora",
        "current_place": default_place_id("aurora"),
        "travel_state": "docked",
        "near_body": {
            "type": "station",
            "id": "station:aurora",
            "name": STATIONS["aurora"]["name"],
            "placeId": default_place_id("aurora"),
        },
        "ship_upgrades": {},
        "visited_places": {},
        "planet_offsets": {},
        "known_systems": STARTING_KNOWN_SYSTEM_IDS[:],
        "charted_systems": STARTING_KNOWN_SYSTEM_IDS[:],
        "known_galaxies": [STARTING_GALAXY_ID],
        "used_gates": [],
        "gate_routes": [],
        "player_gate_anchors": [],
        "credits": 650,
        "fuel": SHIP.max_fuel,
        "hull": SHIP.max_hull,
        "player": default_player_profile(),
        "ship_ai": default_ship_ai_profile(),
        "cheats": default_cheats(),
        "reputation": 0,
        "inventory": {good: 0 for good in GOODS},
        "active_mission": None,
        "log": STARTING_LOG[:],
    }


def default_player_profile() -> dict[str, Any]:
    return {
        "health": 100,
        "maxHealth": 100,
        "stamina": 100,
        "maxStamina": 100,
        "stress": 0,
        "armor": 0,
        "injury": "Healthy",
        "stats": {
            "combat": 1,
            "piloting": 2,
            "engineering": 1,
            "charm": 1,
            "grit": 2,
        },
    }


def default_ship_ai_profile(generation: int = 1) -> dict[str, Any]:
    return {
        "shipId": SHIP.ship_id,
        "generation": max(1, int(generation or 1)),
        "configured": False,
        "name": f"{SHIP.name} Factory AI",
        "gender": "Female",
        "description": (
            "A factory-standard ship assistant with a calm voice, basic maintenance routines, "
            "and no imprinted personal history yet."
        ),
        "installedDay": None,
        "replacementCount": max(0, int(generation or 1) - 1),
    }


def public_state(game: dict[str, Any]) -> dict[str, Any]:
    normalize_game(game)
    market_context = public_market_context(game)
    known_systems = ordered_known_systems(game)
    charted_systems = set(game["charted_systems"])
    current_galaxy_id = system_galaxy_id(game["location"])
    current_galaxy_systems = [key for key in known_systems if system_galaxy_id(key) == current_galaxy_id]
    return {
        "day": game["day"],
        "location": game["location"],
        "currentPlace": public_place(game["location"], game["current_place"], game),
        "station": public_station(game["location"], game),
        "stations": public_stations(game["location"], game),
        "planets": public_planets(game["location"], game),
        "visitedPlaceCount": len(game["visited_places"]),
        "currentSystem": _public_system(game["location"], charted=True),
        "systems": [_public_system(key, charted=key in charted_systems) for key in current_galaxy_systems],
        "systemCatalog": [public_system_catalog(key, charted=key in charted_systems, game=game) for key in current_galaxy_systems],
        "currentGalaxy": public_galaxy(current_galaxy_id, discovered=True),
        "knownGalaxies": public_known_galaxies(game),
        "gates": public_gates(game),
        "gateConstruction": public_gate_construction(game),
        "discovery": public_discovery(game),
        "credits": game["credits"],
        "fuel": game["fuel"],
        "maxFuel": max_fuel(game),
        "hull": game["hull"],
        "maxHull": max_hull(game),
        "cheats": public_cheats(game),
        "shipName": SHIP.name,
        "ship": public_ship(game),
        "shipAi": public_ship_ai(game),
        "player": public_player(game),
        "travelState": public_travel_state(game),
        "reputation": game["reputation"],
        "cargoUsed": cargo_used(game),
        "cargoCapacity": cargo_capacity(game),
        "inventory": _public_inventory(game),
        "market": public_market(game),
        "marketContext": market_context,
        "travel": _public_travel(game),
        "missions": generate_missions(game),
        "activeMission": game.get("active_mission"),
        "log": game["log"][-12:],
        "status": status_label(game),
    }


def apply_action(game: dict[str, Any], action_name: str | None, payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    game = deepcopy(game)
    normalize_game(game)

    if game["hull"] <= 0 and action_name not in {
        "repair",
        "rescue_refuel",
        "visit_place",
        "set_cheat",
        "configure_ship_ai",
        "strip_ship_ai",
    }:
        return game, "The Peregrine is disabled. Repairs are the only order the crew can follow."

    handlers = {
        "set_cheat": set_cheat,
        "use_gate": use_gate,
        "build_gate_anchor": build_gate_anchor,
        "travel": travel,
        "local_travel": local_travel,
        "visit_place": visit_place,
        "scan_planet": scan_planet,
        "buy": buy,
        "sell": sell,
        "accept_mission": accept_mission,
        "refuel": refuel,
        "rescue_refuel": rescue_refuel,
        "repair": repair,
        "buy_upgrade": buy_upgrade,
        "configure_ship_ai": configure_ship_ai,
        "strip_ship_ai": strip_ship_ai,
        "explore": explore,
        "wait": wait,
    }
    handler = handlers.get(action_name or "")
    if not handler:
        return game, "Command rejected. The nav console did not recognize that order."

    message = handler(game, payload)
    _add_log(game, message)
    return game, message


def set_cheat(game: dict[str, Any], payload: dict[str, Any]) -> str:
    cheat_id = payload.get("cheat")
    if cheat_id not in CHEAT_FLAGS:
        return "That settings option does not exist."

    enabled = payload_enabled(payload.get("enabled"))
    game["cheats"][cheat_id] = enabled
    label = CHEAT_FLAGS[cheat_id]["label"]

    if enabled and cheat_id == "unlimitedFuel":
        game["fuel"] = max_fuel(game)
    elif enabled and cheat_id == "invulnerableHull":
        game["hull"] = max_hull(game)

    return f"{label} {'enabled' if enabled else 'disabled'}."


def ordered_unique_galaxies(galaxy_ids: list[str]) -> list[str]:
    known = []
    seen = set()
    for galaxy_id in galaxy_ids:
        if galaxy_id in seen or not ensure_galaxy(galaxy_id):
            continue
        seen.add(galaxy_id)
        known.append(galaxy_id)
    return sorted(known, key=lambda item: _galaxy_index(item) or 0)


def public_galaxy(galaxy_id: str, discovered: bool = True) -> dict[str, Any]:
    ensure_galaxy(galaxy_id)
    galaxy = GALAXIES[galaxy_id]
    if not discovered:
        return {
            "id": galaxy_id,
            "name": "Unresolved Galaxy",
            "theme": "Fold shadow",
            "risk": "Unknown",
            "size": "Unknown",
            "x": galaxy["x"],
            "y": galaxy["y"],
            "discovered": False,
        }
    return {
        "id": galaxy_id,
        "name": galaxy["name"],
        "theme": galaxy["theme"],
        "risk": risk_label(galaxy["risk"]),
        "size": galaxy["size"],
        "x": galaxy["x"],
        "y": galaxy["y"],
        "discovered": True,
    }


def public_known_galaxies(game: dict[str, Any]) -> list[dict[str, Any]]:
    known = set(game.get("known_galaxies", [STARTING_GALAXY_ID]))
    return [public_galaxy(galaxy_id, discovered=True) for galaxy_id in ordered_unique_galaxies(list(known))]


def gate_route_key(origin_galaxy: str, destination_galaxy: str) -> str:
    return ">".join(sorted([origin_galaxy, destination_galaxy]))


def record_gate_route(game: dict[str, Any], origin_galaxy: str, destination_galaxy: str) -> None:
    key = gate_route_key(origin_galaxy, destination_galaxy)
    routes = set(game.get("gate_routes", []))
    routes.add(key)
    game["gate_routes"] = sorted(routes)


def galaxies_connected_by_gate(game: dict[str, Any] | None, origin_galaxy: str, destination_galaxy: str) -> bool:
    if origin_galaxy == destination_galaxy:
        return True
    if not game:
        return False
    return gate_route_key(origin_galaxy, destination_galaxy) in set(game.get("gate_routes", []))


def gate_fee(system_id: str, destination_galaxy_id: str) -> int:
    ensure_system(system_id)
    ensure_galaxy(destination_galaxy_id)
    return 140 + round(SYSTEMS[system_id]["risk"] * 120) + round(GALAXIES[destination_galaxy_id]["risk"] * 90)


def next_galaxy_id(galaxy_id: str, offset: int = 1) -> str | None:
    index = _galaxy_index(galaxy_id)
    if index is None:
        return None
    return _galaxy_id_for_index((index + offset) % GALAXY_TARGET)


def gate_destination_system(galaxy_id: str, local_index: int = 0) -> str | None:
    ensure_galaxy(galaxy_id)
    return _system_id_for_index(min(local_index, galaxy_system_target(galaxy_id) - 1), galaxy_id)


def generated_gate_specs(system_id: str) -> list[dict[str, Any]]:
    ensure_system(system_id)
    galaxy_id, index = system_identity(system_id) or (STARTING_GALAXY_ID, 0)
    system = SYSTEMS[system_id]
    specs = []

    system_gate_offsets = STARTER_SYSTEM_GATE_OFFSETS.get(system_id, [])
    if not system_gate_offsets:
        has_system_gate = (
            ("trade" in system["economy"].lower() and index % 19 == 0)
            or ("medical" in system["economy"].lower() and index % 31 == 0)
            or index % 67 == 12
        )
        if has_system_gate:
            system_gate_offsets = [1 + (index % 2)]

    seen_destinations = set()
    for offset in system_gate_offsets:
        destination_galaxy = next_galaxy_id(galaxy_id, offset)
        if not destination_galaxy or destination_galaxy in seen_destinations:
            continue
        seen_destinations.add(destination_galaxy)
        destination_system = gate_destination_system(destination_galaxy, offset % 5)
        if not destination_system:
            continue
        specs.append(
            {
                "id": f"system-fold-{system_id}-{destination_galaxy}",
                "type": "system",
                "label": "System-built fold gate",
                "originSystemId": system_id,
                "destinationGalaxyId": destination_galaxy,
                "destinationSystemId": destination_system,
                "fee": gate_fee(system_id, destination_galaxy),
                "timeCost": 1,
                "riskValue": max(0.04, GALAXIES[destination_galaxy]["risk"] * 0.45),
                "hidden": False,
            }
        )

    has_ancient_gate = system_id == "morrow" or index % 137 == 8
    if has_ancient_gate:
        destination_galaxy = next_galaxy_id(galaxy_id, 6 + (index % 3))
        destination_system = gate_destination_system(destination_galaxy, 2 + (index % 5)) if destination_galaxy else None
        if destination_galaxy and destination_system:
            specs.append(
                {
                    "id": f"ancient-fold-{system_id}-{destination_galaxy}",
                    "type": "ancient",
                    "label": "Ancient fold aperture",
                    "originSystemId": system_id,
                    "destinationGalaxyId": destination_galaxy,
                    "destinationSystemId": destination_system,
                    "fee": 0,
                    "timeCost": 1,
                    "riskValue": 0.34,
                    "hidden": True,
                }
            )
    return specs


def player_gate_specs(game: dict[str, Any], system_id: str) -> list[dict[str, Any]]:
    anchors = ordered_unique_systems(game.get("player_gate_anchors", []))
    if system_id not in anchors:
        return []
    specs = []
    for destination in anchors:
        if destination == system_id:
            continue
        ensure_system(destination)
        destination_galaxy = system_galaxy_id(destination)
        specs.append(
            {
                "id": f"player-fold-{system_id}-{destination}",
                "type": "player",
                "label": "Player-built fold anchor",
                "originSystemId": system_id,
                "destinationGalaxyId": destination_galaxy,
                "destinationSystemId": destination,
                "fee": 0,
                "timeCost": 1,
                "riskValue": 0.06,
                "hidden": False,
            }
        )
    return specs


def gate_specs_for_system(game: dict[str, Any], system_id: str) -> list[dict[str, Any]]:
    return [*generated_gate_specs(system_id), *player_gate_specs(game, system_id)]


def public_gate(game: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    used = spec["id"] in set(game.get("used_gates", []))
    hidden = bool(spec["hidden"] and not used)
    destination_system = spec["destinationSystemId"]
    destination_galaxy = spec["destinationGalaxyId"]
    at_origin = spec["originSystemId"] == game["location"]
    can_use = at_origin and game["travel_state"] == "system_space"
    blocked = ""
    if not at_origin:
        blocked = "Travel to this system before using its local fold gate."
    elif not can_use:
        blocked = f"Fold gates require system space. Current state: {travel_state_label(game)}."
    if can_use and spec["fee"] > 0 and not can_pay(game, spec["fee"]):
        can_use = False
        blocked = f"Gate fee requires {spec['fee']} credits."

    return {
        "id": spec["id"],
        "type": spec["type"],
        "typeLabel": spec["label"],
        "originSystemId": spec["originSystemId"],
        "destinationGalaxyId": "" if hidden else destination_galaxy,
        "destinationGalaxyName": "Hidden fold shadow" if hidden else GALAXIES[destination_galaxy]["name"],
        "destinationSystemId": "" if hidden else destination_system,
        "destinationSystemName": "Unknown destination" if hidden else _system_name_for_id(destination_system),
        "destinationPreview": (
            "Ancient aperture. Destination telemetry is unreadable until first transit."
            if hidden
            else f"Fold overlap resolves near {_system_name_for_id(destination_system)} in {GALAXIES[destination_galaxy]['name']}."
        ),
        "fee": spec["fee"],
        "timeCost": spec["timeCost"],
        "risk": risk_label(spec["riskValue"]),
        "riskValue": spec["riskValue"],
        "hidden": hidden,
        "used": used,
        "canUse": can_use,
        "blockedReason": blocked,
    }


def public_gates(game: dict[str, Any], system_id: str | None = None) -> list[dict[str, Any]]:
    target_system = system_id or game["location"]
    return [public_gate(game, spec) for spec in gate_specs_for_system(game, target_system)]


def find_gate_spec(game: dict[str, Any], gate_id: str | None) -> dict[str, Any] | None:
    return next((gate for gate in gate_specs_for_system(game, game["location"]) if gate["id"] == gate_id), None)


def public_gate_construction(game: dict[str, Any]) -> dict[str, Any]:
    anchors = set(game.get("player_gate_anchors", []))
    existing = game["location"] in anchors
    missing = missing_materials(game, PLAYER_GATE_ANCHOR_MATERIALS)
    blocked = ""
    if existing:
        blocked = "Fold anchor already installed in this system."
    elif game["travel_state"] != "docked":
        blocked = "Dock at the primary station before deploying a fold anchor."
    elif not cheat_enabled(game, "freeMaterials") and missing:
        blocked = f"Missing materials: {materials_text(missing)}."
    elif not can_pay(game, PLAYER_GATE_ANCHOR_COST):
        blocked = f"Needs {PLAYER_GATE_ANCHOR_COST} credits."

    return {
        "price": PLAYER_GATE_ANCHOR_COST,
        "materials": [
            {
                "id": good,
                "name": GOODS[good]["name"],
                "required": quantity,
                "owned": game["inventory"].get(good, 0),
                "missing": 0
                if cheat_enabled(game, "freeMaterials")
                else max(0, quantity - game["inventory"].get(good, 0)),
                "waived": cheat_enabled(game, "freeMaterials"),
            }
            for good, quantity in PLAYER_GATE_ANCHOR_MATERIALS.items()
        ],
        "anchors": len(anchors),
        "installedHere": existing,
        "canBuild": not blocked,
        "blockedReason": blocked,
    }


def use_gate(game: dict[str, Any], payload: dict[str, Any]) -> str:
    gate = find_gate_spec(game, payload.get("gateId"))
    if not gate:
        return "No active fold gate matches that command in the current system."
    if game["travel_state"] != "system_space":
        return f"Fold gate alignment requires system space. Current state: {travel_state_label(game)}."
    if gate["fee"] > 0 and not can_pay(game, gate["fee"]):
        return f"Gate fee requires {gate['fee']} credits."

    origin_system = game["location"]
    origin_galaxy = system_galaxy_id(origin_system)
    destination = gate["destinationSystemId"]
    ensure_system(destination)
    destination_galaxy = system_galaxy_id(destination)
    paid = spend_credits(game, gate["fee"])
    game["day"] += gate["timeCost"]
    game["location"] = destination
    game["current_place"] = default_place_id(destination)
    chart_system(game, destination)
    game["known_galaxies"] = ordered_unique_galaxies([*game.get("known_galaxies", []), destination_galaxy])
    game["used_gates"] = sorted({*game.get("used_gates", []), gate["id"]})
    record_gate_route(game, origin_galaxy, destination_galaxy)
    set_travel_position(game, "system_space", "system", destination)
    fee_text = "no fee" if gate["fee"] <= 0 else f"{paid or gate['fee']} credits"
    if paid == 0 and gate["fee"] > 0 and cheat_enabled(game, "unlimitedCredits"):
        fee_text = f"unlimited credits covered {gate['fee']} credits"
    hidden_note = " Ancient telemetry resolved after transit." if gate["type"] == "ancient" else ""
    return (
        f"Coordinate fold complete from {SYSTEMS[origin_system]['name']} to {SYSTEMS[destination]['name']} "
        f"in {GALAXIES[destination_galaxy]['name']} for {fee_text}.{hidden_note}"
    )


def build_gate_anchor(game: dict[str, Any], payload: dict[str, Any]) -> str:
    construction = public_gate_construction(game)
    if not construction["canBuild"]:
        return construction["blockedReason"]
    if not cheat_enabled(game, "freeMaterials"):
        for good, quantity in PLAYER_GATE_ANCHOR_MATERIALS.items():
            game["inventory"][good] -= quantity
    spend_credits(game, PLAYER_GATE_ANCHOR_COST)
    game["player_gate_anchors"] = ordered_unique_systems([*game.get("player_gate_anchors", []), game["location"]])
    game["day"] += 2
    return (
        f"Player-built fold anchor deployed at {SYSTEMS[game['location']]['name']} "
        f"for {PLAYER_GATE_ANCHOR_COST} credits and {materials_text(PLAYER_GATE_ANCHOR_MATERIALS)}."
    )


def travel(game: dict[str, Any], payload: dict[str, Any]) -> str:
    destination = payload.get("destination")
    if not ensure_system(destination):
        return "No matching destination exists in the current nav charts."
    if destination not in set(game["known_systems"]):
        return "That signal has not been discovered in the current nav charts."
    if destination == game["location"]:
        return "You are already in that system."

    if game["travel_state"] not in JUMP_STATES:
        return f"Jump blocked while {travel_state_label(game)}. Reach open system space before plotting an interstellar burn."
    if not same_galaxy(game["location"], destination):
        return (
            f"Intergalactic jump blocked. {SYSTEMS[destination]['name']} is in "
            f"{GALAXIES[system_galaxy_id(destination)]['name']}; use a coordinate fold gate."
        )

    cost = ship_jump_fuel_cost(game, game["location"], destination)
    has_unlimited_fuel = cheat_enabled(game, "unlimitedFuel")
    if not has_unlimited_fuel and game["fuel"] < cost:
        if payload.get("risky"):
            return risky_interstellar_travel(game, destination, cost)
        return f"Not enough fuel for the burn to {SYSTEMS[destination]['name']}."

    if has_unlimited_fuel:
        game["fuel"] = max_fuel(game)
    else:
        game["fuel"] -= cost
    game["day"] += max(1, math.ceil(cost / 2))
    game["location"] = destination
    newly_charted = destination not in set(game["charted_systems"])
    chart_system(game, destination)
    game["current_place"] = default_place_id(destination)
    set_travel_position(game, "system_space", "system", destination)
    if has_unlimited_fuel:
        arrival = f"Arrived at {SYSTEMS[destination]['name']}. Unlimited fuel covered the {cost} fuel burn."
    else:
        arrival = f"Arrived at {SYSTEMS[destination]['name']} after spending {cost} fuel."
    if newly_charted:
        arrival = f"{arrival} The uncharted signal resolved into a charted system."
    event = travel_event(game, destination)
    mission = check_mission_delivery(game)
    return " ".join(part for part in [arrival, event, mission] if part)


def local_travel(game: dict[str, Any], payload: dict[str, Any]) -> str:
    movement = payload.get("movement")
    preview = local_route_preview(
        game,
        movement,
        planet_id=payload.get("planetId"),
        place_id=payload.get("placeId"),
    )
    if preview["blockedReason"]:
        return preview["blockedReason"]
    if preview["isCurrent"]:
        return preview["currentMessage"]

    payment = spend_fuel_for_local_route(game, preview, payload.get("risky"))
    if payment:
        return payment

    final_state = preview["finalState"]
    final_body = preview["finalBody"]
    place_id = payload.get("placeId")
    if movement == "land" and place_id:
        place = public_place(game["location"], place_id, game)
        if not place or place["category"] != "planet":
            return "That landing site is not on the current charts."
        previous_visits = game["visited_places"].get(place_id, 0)
        game["current_place"] = place_id
        game["visited_places"][place_id] = previous_visits + 1
        set_travel_position(game, "landed", "planet", place["planetId"], place_id)
        outcome = planet_visit_event(game, place, previous_visits > 0)
        note = game.pop("_pending_travel_note", "")
        return (
            f"Landed at {place['name']} on {place['planetName']} after spending "
            f"{preview['fuelCost']} fuel. {outcome} {note}".strip()
        )

    if movement == "dock_station":
        game["current_place"] = default_place_id(game["location"])
        set_travel_position(game, "docked", "station", f"station:{game['location']}", default_place_id(game["location"]))
    elif final_state == "orbit":
        set_travel_position(game, "orbit", "planet", final_body["id"])
    elif final_state == "system_space":
        set_travel_position(game, "system_space", "system", game["location"])
    else:
        set_travel_position(game, final_state, final_body["type"], final_body["id"], final_body.get("placeId"))

    note = game.pop("_pending_travel_note", "")
    return f"{preview['successMessage']} {note}".strip()


def visit_place(game: dict[str, Any], payload: dict[str, Any]) -> str:
    place_id = payload.get("placeId")
    place = public_place(game["location"], place_id, game)
    if not place:
        return "That local destination is not on the current charts."

    if place["category"] == "station" and game["travel_state"] != "docked":
        preview = local_route_preview(game, "dock_station")
        if preview["blockedReason"]:
            return preview["blockedReason"]
        payment = spend_fuel_for_local_route(game, preview, payload.get("risky"))
        if payment:
            return payment
        set_travel_position(game, "docked", "station", f"station:{game['location']}", place_id)

    if place["category"] == "planet":
        preview = local_route_preview(game, "land", place_id=place_id)
        if preview["blockedReason"]:
            return preview["blockedReason"]
        if not is_landed_at_place(game, place_id):
            payment = spend_fuel_for_local_route(game, preview, payload.get("risky"))
            if payment:
                return payment

    previous_visits = game["visited_places"].get(place_id, 0)
    game["current_place"] = place_id
    game["visited_places"][place_id] = previous_visits + 1

    if place["category"] == "planet":
        set_travel_position(game, "landed", "planet", place["planetId"], place_id)
        if is_landed_at_place(game, place_id):
            game["day"] += 1
        outcome = planet_visit_event(game, place, previous_visits > 0)
        note = game.pop("_pending_travel_note", "")
        return f"Expedition reached {place['name']} on {place['planetName']}. {outcome} {note}".strip()

    set_travel_position(game, "docked", "station", f"station:{game['location']}", place_id)
    note = game.pop("_pending_travel_note", "")
    return (
        f"Moved through {place['stationName']} to {place['name']}. "
        f"{place['faction']} controls this {place['wealth'].lower()} {place['economy'].lower()} area. {note}"
    ).strip()


def scan_planet(game: dict[str, Any], payload: dict[str, Any]) -> str:
    planet_id = payload.get("planetId")
    planet = find_planet(game["location"], planet_id)
    if not planet:
        return "No matching planet exists in this system."
    if planet["placeCount"] <= 0:
        return f"{planet['name']} has no charted landing locations to rotate through."

    current_offset = game["planet_offsets"].get(planet_id, 0)
    next_offset = (current_offset + PLANET_SAMPLE_SIZE) % planet["placeCount"]
    game["planet_offsets"][planet_id] = next_offset
    start = next_offset + 1
    end = min(next_offset + PLANET_SAMPLE_SIZE, planet["placeCount"])
    if end - start + 1 < PLANET_SAMPLE_SIZE:
        end = planet["placeCount"]

    return f"Survey filters for {planet['name']} now show landing sites {start}-{end} of {planet['placeCount']}."


def buy(game: dict[str, Any], payload: dict[str, Any]) -> str:
    good = payload.get("good")
    quantity = parse_quantity(payload.get("quantity"))
    if good not in GOODS:
        return "That cargo code is not traded in this sector."
    if quantity <= 0:
        return "Choose a positive amount of cargo to buy."

    unit_price = market_price(game, good)["price"]
    price = unit_price * quantity
    needed_space = GOODS[good]["weight"] * quantity
    if not can_pay(game, price):
        return f"Not enough credits to buy {quantity} {GOODS[good]['name']}."
    if cargo_used(game) + needed_space > cargo_capacity(game):
        return "The hold cannot fit that much cargo."

    paid = spend_credits(game, price)
    game["inventory"][good] += quantity
    if paid == 0 and price > 0 and cheat_enabled(game, "unlimitedCredits"):
        return f"Bought {quantity} {GOODS[good]['name']}. Unlimited credits covered {price} credits at {unit_price} each."
    return f"Bought {quantity} {GOODS[good]['name']} for {price} credits at {unit_price} each."


def sell(game: dict[str, Any], payload: dict[str, Any]) -> str:
    good = payload.get("good")
    quantity = parse_quantity(payload.get("quantity"))
    if good not in GOODS:
        return "That cargo code is not traded in this sector."
    if quantity <= 0:
        return "Choose a positive amount of cargo to sell."
    if game["inventory"].get(good, 0) < quantity:
        return f"You do not have {quantity} {GOODS[good]['name']} in the hold."

    unit_price = market_price(game, good)["price"]
    price = unit_price * quantity
    game["inventory"][good] -= quantity
    game["credits"] += price
    return f"Sold {quantity} {GOODS[good]['name']} for {price} credits at {unit_price} each."


def accept_mission(game: dict[str, Any], payload: dict[str, Any]) -> str:
    if game.get("active_mission"):
        return "You already have an active contract. Finish it before taking another."

    mission_id = payload.get("missionId")
    mission = next((item for item in generate_missions(game) if item["id"] == mission_id), None)
    if not mission:
        return "That contract is no longer available."
    if cargo_used(game) + mission["cargoWeight"] > cargo_capacity(game):
        return "The mission cargo will not fit in your hold."

    game["active_mission"] = mission
    return f"Accepted contract: deliver {mission['cargo']} to {SYSTEMS[mission['destination']]['name']} by day {mission['dueDay']}."


def refuel(game: dict[str, Any], payload: dict[str, Any]) -> str:
    if cheat_enabled(game, "unlimitedFuel"):
        game["fuel"] = max_fuel(game)
        return "Unlimited fuel is active. Tanks are full without using station pumps."

    if game["travel_state"] != "docked":
        return "Station refuel requires docking. Call a rescue service if you are stranded away from port."

    quantity = parse_quantity(payload.get("quantity"))
    missing = max_fuel(game) - game["fuel"]
    if quantity <= 0:
        quantity = missing

    quantity = min(quantity, missing)
    if quantity <= 0:
        return "Fuel tanks are already full."

    price = fuel_price(game["location"]) * quantity
    if not cheat_enabled(game, "unlimitedCredits") and game["credits"] < price:
        quantity = game["credits"] // fuel_price(game["location"])
        price = fuel_price(game["location"]) * quantity
    if quantity <= 0:
        return "Not enough credits to refuel."

    paid = spend_credits(game, price)
    game["fuel"] += quantity
    if paid == 0 and price > 0 and cheat_enabled(game, "unlimitedCredits"):
        return f"Loaded {quantity} fuel. Unlimited credits covered {price} credits."
    return f"Loaded {quantity} fuel for {price} credits."


def rescue_refuel(game: dict[str, Any], payload: dict[str, Any]) -> str:
    if cheat_enabled(game, "unlimitedFuel"):
        game["fuel"] = max_fuel(game)
        return "Unlimited fuel is active. Tanks are full without calling rescue."

    if game["travel_state"] == "docked":
        return "You are already docked. Station pumps are cheaper than a rescue call."

    quantity = parse_quantity(payload.get("quantity"))
    missing = max_fuel(game) - game["fuel"]
    if quantity <= 0:
        quantity = min(8, missing)
    quantity = min(quantity, missing)
    if quantity <= 0:
        return "Fuel tanks are already full."

    landed = game["travel_state"] in {"landed", "atmosphere"}
    provider = "surface fuel service" if landed else "rescue tanker"
    delay = 2 if landed else 1
    service_fee = 65 if landed else 45
    price = service_fee + (fuel_price(game["location"]) + (5 if landed else 3)) * quantity
    debt_note = ""
    if not cheat_enabled(game, "unlimitedCredits") and game["credits"] < price:
        game["reputation"] -= 1
        debt_note = " The unpaid balance damaged your reputation."

    paid = spend_credits(game, price)
    game["fuel"] += quantity
    game["day"] += delay
    if paid == 0 and price > 0 and cheat_enabled(game, "unlimitedCredits"):
        return (
            f"{provider.title()} delivered {quantity} fuel after {delay} day{'s' if delay != 1 else ''}. "
            f"Unlimited credits covered {price} credits."
        )
    return f"{provider.title()} delivered {quantity} fuel after {delay} day{'s' if delay != 1 else ''} for {price} credits.{debt_note}"


def repair(game: dict[str, Any], payload: dict[str, Any]) -> str:
    if cheat_enabled(game, "invulnerableHull"):
        game["hull"] = max_hull(game)
        return "Invulnerable hull is active. Hull integrity is restored to maximum."

    amount = parse_quantity(payload.get("quantity"))
    missing = max_hull(game) - game["hull"]
    if amount <= 0:
        amount = missing

    amount = min(amount, missing)
    if amount <= 0:
        return "Hull integrity is already at maximum."

    cost_per_point = repair_price(game["location"])
    price = cost_per_point * amount
    if not cheat_enabled(game, "unlimitedCredits") and game["credits"] < price:
        amount = game["credits"] // cost_per_point
        price = amount * cost_per_point
    if amount <= 0:
        return "Not enough credits for repairs."

    paid = spend_credits(game, price)
    game["hull"] += amount
    if paid == 0 and price > 0 and cheat_enabled(game, "unlimitedCredits"):
        return f"Repaired {amount} hull. Unlimited credits covered {price} credits."
    return f"Repaired {amount} hull for {price} credits."


def clean_ai_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").replace("\x00", "").split())
    return text[:limit].strip()


def configure_ship_ai(game: dict[str, Any], payload: dict[str, Any]) -> str:
    profile = game["ship_ai"]
    if profile.get("configured"):
        return f"{profile['name']}'s core personality is locked. Strip the AI core before imprinting a replacement."

    name = clean_ai_text(payload.get("name"), 42) or f"{SHIP.name} AI"
    gender = clean_ai_text(payload.get("gender"), 16)
    if gender not in SHIP_AI_GENDERS:
        return "Ship AI gender must be Male or Female."

    description = clean_ai_text(payload.get("description"), 900)
    if len(description) < 24:
        return "Add a longer AI personality paragraph before imprinting the core."

    profile.update(
        {
            "configured": True,
            "name": name,
            "gender": gender,
            "description": description,
            "installedDay": game["day"],
        }
    )
    return f"Imprinted {name} into the {SHIP.name}'s AI core. This personality is now locked to the ship."


def strip_ship_ai(game: dict[str, Any], payload: dict[str, Any]) -> str:
    profile = game["ship_ai"]
    if not profile.get("configured"):
        return "The ship is still running a factory AI profile. There is no custom core to strip."

    price = SHIP_AI_REPLACEMENT_COST
    if not cheat_enabled(game, "unlimitedCredits") and game["credits"] < price:
        return f"AI core extraction requires {price} credits. The process is intentionally expensive and invasive."

    paid = spend_credits(game, price)
    next_generation = int(profile.get("generation", 1)) + 1
    game["ship_ai"] = default_ship_ai_profile(next_generation)
    if paid == 0 and price > 0 and cheat_enabled(game, "unlimitedCredits"):
        return f"Stripped the old AI core. Unlimited credits covered the {price} credit extraction."
    return f"Stripped the old AI core for {price} credits. The {SHIP.name} is back on a blank factory assistant."


def buy_upgrade(game: dict[str, Any], payload: dict[str, Any]) -> str:
    upgrade_id = payload.get("upgradeId")
    if upgrade_id not in SHIP_UPGRADES:
        return "That upgrade does not exist in the Peregrine service catalog."

    tier = upgrade_tier(game, upgrade_id)
    spec = SHIP_UPGRADES[upgrade_id]
    if tier >= spec["maxTier"]:
        return f"{spec['name']} is already at maximum tier."

    offer = upgrade_offer(game, upgrade_id)
    if not offer["canInstall"]:
        return offer["blockedReason"]

    next_tier = offer["nextTier"]
    price = offer["price"]
    materials_waived = cheat_enabled(game, "freeMaterials")
    credits_waived = cheat_enabled(game, "unlimitedCredits")
    if not materials_waived:
        for good, quantity in offer["materials"].items():
            game["inventory"][good] -= quantity

    before_hull = max_hull(game)
    spend_credits(game, price)
    game.setdefault("ship_upgrades", {})[upgrade_id] = next_tier
    hull_gain = max_hull(game) - before_hull
    if hull_gain > 0:
        game["hull"] += hull_gain

    effect = spec["effects"][next_tier - 1]
    cost_text = (
        f"for {price} credits and {materials_text(offer['materials'])}"
        if not (credits_waived or materials_waived)
        else f"with {'unlimited credits' if credits_waived else f'{price} credits'} and {'free materials' if materials_waived else materials_text(offer['materials'])}"
    )
    return (
        f"Installed {offer['quality']} {spec['name']} tier {next_tier} at {offer['serviceName']} "
        f"{cost_text}. {effect}."
    )


def explore(game: dict[str, Any], payload: dict[str, Any]) -> str:
    system = SYSTEMS[game["location"]]
    game["day"] += 1
    discovered = reveal_branch_systems(game, game["location"])
    if discovered:
        names = ", ".join(_signal_label(system_id) for system_id in discovered)
        return f"Long-range scans from {system['name']} revealed {len(discovered)} uncharted signal{'s' if len(discovered) != 1 else ''}: {names}."

    roll = random.random()

    if roll < system["risk"] * 0.6:
        damage = random.randint(6, 16)
        applied_damage = apply_hull_damage(game, damage)
        if applied_damage == 0:
            return f"A bad scan path clipped debris near {system['name']}. Invulnerable hull absorbed the impact."
        return f"A bad scan path clipped debris near {system['name']}. Hull lost {damage} integrity."

    if roll < 0.38:
        reward = random.randint(35, 95)
        game["credits"] += reward
        return f"Survey data from {system['name']} sold for {reward} credits."

    if roll < 0.58:
        good = random.choice(list(GOODS))
        if cargo_used(game) + GOODS[good]["weight"] <= cargo_capacity(game):
            game["inventory"][good] += 1
            return f"Recovered 1 {GOODS[good]['name']} from an abandoned cargo pod."
        return "Found an abandoned cargo pod, but the hold was too full to recover it."

    game["reputation"] += 1
    return f"Mapped a clean transit lane through {system['name']}. Reputation increased."


def wait(game: dict[str, Any], payload: dict[str, Any]) -> str:
    game["day"] += 1
    mission = game.get("active_mission")
    if mission and game["day"] > mission["dueDay"]:
        penalty = min(90, mission["reward"] // 3)
        game["credits"] = max(0, game["credits"] - penalty)
        game["reputation"] -= 2
        game["active_mission"] = None
        return f"The {mission['title']} contract expired. Late fees cost {penalty} credits."

    return "The crew takes a maintenance day. Nothing explodes, which counts as progress."


def local_route_preview(
    game: dict[str, Any],
    movement: str | None,
    planet_id: str | None = None,
    place_id: str | None = None,
) -> dict[str, Any]:
    movement = movement or ""
    state = game.get("travel_state", "docked")
    cursor_state = state
    cursor_planet = current_near_planet_id(game)
    target_planet_id = planet_id
    target_place = None

    if place_id:
        target_place = plain_place(game["location"], place_id, game)
        if not target_place or target_place["category"] != "planet":
            return blocked_local_preview(movement, "That landing site is not on the current charts.")
        target_planet_id = target_place["planetId"]

    segments: list[dict[str, Any]] = []
    blocked_reason = ""
    is_current = False
    current_message = ""
    final_state = cursor_state
    final_body = game.get("near_body", inferred_near_body(game))

    def block(message: str) -> None:
        nonlocal blocked_reason
        blocked_reason = message

    def add(segment: dict[str, Any]) -> None:
        segments.append(segment)

    def to_system_space() -> None:
        nonlocal cursor_state, cursor_planet
        if cursor_state in {"system_space", "deep_space"}:
            return
        if cursor_state == "docked":
            add(undock_segment())
            cursor_state = "system_space"
            cursor_planet = None
            return
        if cursor_state == "orbit":
            planet = find_planet(game["location"], cursor_planet)
            add(leave_orbit_segment(planet))
            cursor_state = "system_space"
            cursor_planet = None
            return
        if cursor_state in {"landed", "atmosphere"}:
            planet = find_planet(game["location"], cursor_planet)
            if not planet:
                block("Launch blocked because the current planet is no longer on the local charts.")
                return
            add(ascent_segment(planet))
            add(leave_orbit_segment(planet))
            cursor_state = "system_space"
            cursor_planet = None

    def to_orbit(target_planet: dict[str, Any]) -> None:
        nonlocal cursor_state, cursor_planet
        if cursor_state == "orbit" and cursor_planet == target_planet["id"]:
            return
        if cursor_state in {"landed", "atmosphere"} and cursor_planet == target_planet["id"]:
            add(ascent_segment(target_planet))
            cursor_state = "orbit"
            cursor_planet = target_planet["id"]
            return
        to_system_space()
        if blocked_reason:
            return
        add(enter_orbit_segment(target_planet))
        cursor_state = "orbit"
        cursor_planet = target_planet["id"]

    if movement == "undock":
        if cursor_state != "docked":
            is_current = cursor_state in {"system_space", "deep_space"}
            current_message = "The ship is already clear of station clamps." if is_current else "Undock is only available from a station berth."
            if not is_current:
                block(current_message)
        else:
            add(undock_segment())
            final_state = "system_space"
            final_body = {"type": "system", "id": game["location"], "name": SYSTEMS[game["location"]]["name"]}
    elif movement == "dock_station":
        if cursor_state == "docked":
            is_current = True
            current_message = "The ship is already docked."
        elif cursor_state == "deep_space":
            block("Docking requires reaching a star system first.")
        else:
            to_system_space()
            if not blocked_reason:
                add(dock_segment())
                final_state = "docked"
                final_body = {
                    "type": "station",
                    "id": f"station:{game['location']}",
                    "name": STATIONS[game["location"]]["name"],
                    "placeId": default_place_id(game["location"]),
                }
    elif movement == "enter_orbit":
        planet = find_planet(game["location"], target_planet_id)
        if not planet:
            block("No matching planet exists in this system.")
        elif cursor_state == "orbit" and cursor_planet == planet["id"]:
            is_current = True
            current_message = f"The ship is already holding orbit over {planet['name']}."
        else:
            to_orbit(planet)
            final_state = "orbit"
            final_body = {"type": "planet", "id": planet["id"], "name": planet["name"]}
    elif movement == "launch":
        planet = find_planet(game["location"], cursor_planet)
        if cursor_state not in {"landed", "atmosphere"}:
            block("Launch is only available from a planet surface.")
        elif not planet:
            block("Launch blocked because the current planet is no longer on the local charts.")
        else:
            add(ascent_segment(planet))
            final_state = "orbit"
            final_body = {"type": "planet", "id": planet["id"], "name": planet["name"]}
    elif movement == "leave_orbit":
        if cursor_state != "orbit":
            block("Leaving orbit requires the ship to already be in orbit.")
        else:
            planet = find_planet(game["location"], cursor_planet)
            add(leave_orbit_segment(planet))
            final_state = "system_space"
            final_body = {"type": "system", "id": game["location"], "name": SYSTEMS[game["location"]]["name"]}
    elif movement == "return_to_system_space":
        if cursor_state in {"system_space", "deep_space"}:
            is_current = True
            current_message = "The ship is already in open system space."
        else:
            to_system_space()
            final_state = "system_space"
            final_body = {"type": "system", "id": game["location"], "name": SYSTEMS[game["location"]]["name"]}
    elif movement == "land":
        if not target_place:
            block("Choose a planet place before landing.")
        else:
            planet = find_planet(game["location"], target_planet_id)
            if not planet:
                block("No matching planet exists in this system.")
            elif is_landed_at_place(game, place_id):
                is_current = True
                current_message = f"The ship is already down at {target_place['name']}."
            elif cursor_state == "landed" and cursor_planet == planet["id"]:
                add(surface_traverse_segment(target_place))
                final_state = "landed"
                final_body = {
                    "type": "planet",
                    "id": planet["id"],
                    "name": planet["name"],
                    "placeId": place_id,
                }
            else:
                to_orbit(planet)
                if not blocked_reason:
                    add(descent_segment(planet))
                    final_state = "landed"
                    final_body = {
                        "type": "planet",
                        "id": planet["id"],
                        "name": planet["name"],
                        "placeId": place_id,
                    }
    else:
        block("The nav console did not recognize that local movement.")

    if blocked_reason:
        return blocked_local_preview(movement, blocked_reason)

    return build_local_preview(
        game,
        movement,
        segments,
        final_state,
        final_body,
        is_current=is_current,
        current_message=current_message,
    )


def build_local_preview(
    game: dict[str, Any],
    movement: str,
    segments: list[dict[str, Any]],
    final_state: str,
    final_body: dict[str, Any],
    is_current: bool = False,
    current_message: str = "",
) -> dict[str, Any]:
    raw_fuel = sum(segment["fuelCost"] for segment in segments)
    fuel = ship_local_fuel_cost(game, segments)
    time = sum(segment["timeCost"] for segment in segments)
    risk_value = max([segment["riskValue"] for segment in segments] or [0.0])
    warnings = []
    has_unlimited_fuel = cheat_enabled(game, "unlimitedFuel")
    if not has_unlimited_fuel and fuel > game["fuel"]:
        warnings.append(f"Fuel shortfall: needs {fuel}, tanks hold {game['fuel']}.")
    if any(segment["kind"] == "ascent" and segment.get("gravity", 0) >= 1.35 for segment in segments):
        warnings.append("High-gravity launch.")
    if any(segment["kind"] == "descent" and segment.get("atmosphereDensity", 0) >= 1.35 for segment in segments):
        warnings.append("Dense-atmosphere landing.")

    movement_label = movement.replace("_", " ").title()
    destination = final_body.get("name") or SYSTEMS[game["location"]]["name"]
    segment_names = ", ".join(segment["name"] for segment in segments) if segments else "No burn required"
    success = f"{movement_label} complete: {destination}."
    if fuel:
        if has_unlimited_fuel:
            success = f"{success} Unlimited fuel covered the {fuel} fuel burn."
        else:
            success = f"{success} Spent {fuel} fuel."

    return {
        "action": movement,
        "label": movement_label,
        "fuelCost": fuel,
        "baseFuelCost": raw_fuel,
        "timeCost": time,
        "timeLabel": time_label(time),
        "risk": risk_label(risk_value),
        "riskValue": risk_value,
        "canAfford": has_unlimited_fuel or game["fuel"] >= fuel,
        "blockedReason": "",
        "warnings": warnings,
        "segments": segments,
        "summary": segment_names,
        "finalState": final_state,
        "finalBody": final_body,
        "isCurrent": is_current,
        "currentMessage": current_message,
        "successMessage": success,
    }


def blocked_local_preview(movement: str, reason: str) -> dict[str, Any]:
    return {
        "action": movement,
        "label": (movement or "movement").replace("_", " ").title(),
        "fuelCost": 0,
        "baseFuelCost": 0,
        "timeCost": 0,
        "timeLabel": "blocked",
        "risk": "Managed",
        "riskValue": 0,
        "canAfford": False,
        "blockedReason": reason,
        "warnings": [reason],
        "segments": [],
        "summary": reason,
        "finalState": "",
        "finalBody": {},
        "isCurrent": False,
        "currentMessage": reason,
        "successMessage": reason,
    }


def spend_fuel_for_local_route(game: dict[str, Any], preview: dict[str, Any], risky: bool = False) -> str:
    cost = preview["fuelCost"]
    if cheat_enabled(game, "unlimitedFuel"):
        game["fuel"] = max_fuel(game)
        game["day"] += preview["timeCost"]
        return ""
    if cost > game["fuel"]:
        if risky:
            return risky_local_travel(game, preview)
        return (
            f"Insufficient fuel for {preview['label'].lower()}: needs {cost}, "
            f"tanks hold {game['fuel']}. Refuel, call rescue, or choose a risky attempt."
        )

    game["fuel"] -= cost
    game["day"] += preview["timeCost"]
    return ""


def risky_local_travel(game: dict[str, Any], preview: dict[str, Any]) -> str:
    shortfall = max(1, preview["fuelCost"] - game["fuel"])
    game["fuel"] = 0
    game["day"] += max(1, preview["timeCost"] + 1)
    fail_chance = min(0.75, 0.22 + shortfall * 0.11 + preview["riskValue"] * 0.5)
    damage = random.randint(4, 10) + shortfall * 3
    applied_damage = apply_hull_damage(game, damage)
    if random.random() < fail_chance:
        damage_note = (
            "Invulnerable hull absorbed the damage"
            if applied_damage == 0
            else f"Hull lost {applied_damage}"
        )
        return (
            f"Risky {preview['label'].lower()} failed with a {shortfall} fuel shortfall. "
            f"{damage_note}; the ship is stranded and broadcasting a distress beacon."
        )

    game["_pending_travel_note"] = (
        "Risky under-fueled burn scraped the hull, but invulnerability absorbed the damage."
        if applied_damage == 0
        else f"Risky under-fueled burn caused {applied_damage} hull damage."
    )
    return ""


def risky_interstellar_travel(game: dict[str, Any], destination: str, cost: int) -> str:
    shortfall = max(1, cost - game["fuel"])
    game["fuel"] = 0
    game["day"] += max(1, math.ceil(cost / 2)) + 1
    damage = random.randint(8, 18) + shortfall * 4
    applied_damage = apply_hull_damage(game, damage)
    fail_chance = min(0.8, 0.28 + shortfall * 0.1 + SYSTEMS[destination]["risk"])
    if random.random() < fail_chance:
        damage_note = (
            "Invulnerable hull absorbed the damage"
            if applied_damage == 0
            else f"Hull lost {applied_damage}"
        )
        return (
            f"Risky jump failed before reaching {SYSTEMS[destination]['name']}. "
            f"{damage_note}; the ship is stranded in open space."
        )

    game["location"] = destination
    chart_system(game, destination)
    game["current_place"] = default_place_id(destination)
    set_travel_position(game, "system_space", "system", destination)
    mission = check_mission_delivery(game)
    return " ".join(
        part
        for part in [
            (
                "Invulnerable hull absorbed the rough arrival."
                if applied_damage == 0
                else f"Risky jump reached {SYSTEMS[destination]['name']} with empty tanks and {applied_damage} hull damage."
            ),
            mission,
        ]
        if part
    )


def undock_segment() -> dict[str, Any]:
    return travel_segment("undock", "Undock from station", 1, 0, 0.02)


def dock_segment() -> dict[str, Any]:
    return travel_segment("dock", "Dock at station", 1, 0, 0.02)


def enter_orbit_segment(planet: dict[str, Any]) -> dict[str, Any]:
    stats = planet_flight_stats(planet)
    fuel = 2 + math.ceil(stats["gravity"] * 0.8)
    risk = 0.03 + stats["landingDifficulty"] * 0.015
    return travel_segment("orbit", f"Transfer to {planet['name']} orbit", fuel, 1, risk, gravity=stats["gravity"])


def leave_orbit_segment(planet: dict[str, Any] | None) -> dict[str, Any]:
    name = planet["name"] if planet else "planetary"
    return travel_segment("leave_orbit", f"Leave {name} orbit", 1, 0, 0.03)


def descent_segment(planet: dict[str, Any]) -> dict[str, Any]:
    stats = planet_flight_stats(planet)
    fuel = max(1, math.ceil(1 + stats["gravity"] * 0.9 + stats["atmosphereDensity"] * 1.15))
    risk = min(0.48, 0.04 + stats["landingDifficulty"] * 0.045)
    return travel_segment(
        "descent",
        f"Descend through {planet['name']} approach",
        fuel,
        1,
        risk,
        gravity=stats["gravity"],
        atmosphereDensity=stats["atmosphereDensity"],
    )


def ascent_segment(planet: dict[str, Any]) -> dict[str, Any]:
    stats = planet_flight_stats(planet)
    fuel = max(2, math.ceil(2 + stats["gravity"] * 2.4 + stats["atmosphereDensity"] * 0.8))
    risk = min(0.55, 0.05 + stats["gravity"] * 0.08 + stats["atmosphereDensity"] * 0.035)
    return travel_segment(
        "ascent",
        f"Launch from {planet['name']}",
        fuel,
        1,
        risk,
        gravity=stats["gravity"],
        atmosphereDensity=stats["atmosphereDensity"],
    )


def surface_traverse_segment(place: dict[str, Any]) -> dict[str, Any]:
    risk = min(0.42, 0.02 + place.get("hazardValue", 0.08) * 0.6)
    return travel_segment("surface", f"Surface traverse to {place['name']}", 0, 1, risk)


def travel_segment(kind: str, name: str, fuel: int, time: int, risk: float, **extra: Any) -> dict[str, Any]:
    segment = {
        "kind": kind,
        "name": name,
        "fuelCost": max(0, fuel),
        "timeCost": max(0, time),
        "timeLabel": time_label(time),
        "risk": risk_label(risk),
        "riskValue": round(risk, 3),
    }
    segment.update(extra)
    return segment


def time_label(days: int) -> str:
    if days <= 0:
        return "same day"
    if days == 1:
        return "1 day"
    return f"{days} days"


def planet_flight_stats(planet: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(f"{planet['seed']}:flight-stats")
    type_text = planet["type"].lower()
    if "moon" in type_text:
        size = rng.uniform(0.25, 0.55)
        atmosphere = rng.uniform(0.0, 0.12)
    elif "storm" in type_text:
        size = rng.uniform(0.9, 1.45)
        atmosphere = rng.uniform(1.35, 2.2)
    elif "garden" in type_text or "temperate" in type_text or "sanctuary" in type_text:
        size = rng.uniform(0.82, 1.25)
        atmosphere = rng.uniform(0.72, 1.22)
    elif "factory" in type_text:
        size = rng.uniform(1.05, 1.65)
        atmosphere = rng.uniform(0.55, 1.45)
    elif "fractured" in type_text:
        size = rng.uniform(0.55, 1.15)
        atmosphere = rng.uniform(0.08, 0.65)
    else:
        size = rng.uniform(0.65, 1.35)
        atmosphere = rng.uniform(0.18, 1.2)

    density = rng.uniform(0.72, 1.58)
    mass = max(0.08, size**3 * density)
    gravity = max(0.03, mass / max(0.12, size**2))
    landing_difficulty = min(5.0, 1 + gravity * 1.45 + atmosphere * 0.85 + rng.uniform(0, 0.45))
    return {
        "size": round(size, 2),
        "mass": round(mass, 2),
        "gravity": round(gravity, 2),
        "atmosphereDensity": round(atmosphere, 2),
        "landingDifficulty": round(landing_difficulty, 2),
    }


def public_travel_state(game: dict[str, Any]) -> dict[str, Any]:
    state = game["travel_state"]
    near = game.get("near_body", inferred_near_body(game))
    can_jump = state in JUMP_STATES
    options = []
    if state == "docked":
        options.append(local_route_preview(game, "undock"))
    elif state in {"system_space", "deep_space"}:
        options.append(local_route_preview(game, "dock_station"))
    elif state == "orbit":
        options.append(local_route_preview(game, "leave_orbit"))
        options.append(local_route_preview(game, "dock_station"))
    elif state in {"landed", "atmosphere"}:
        options.append(local_route_preview(game, "launch"))
        options.append(local_route_preview(game, "dock_station"))

    return {
        "state": state,
        "label": TRAVEL_STATE_LABELS[state],
        "near": near,
        "nearLabel": near.get("name", SYSTEMS[game["location"]]["name"]),
        "canJump": can_jump,
        "jumpBlockedReason": "" if can_jump else f"Jump requires system space. Current state: {TRAVEL_STATE_LABELS[state]}.",
        "rescueAvailable": state != "docked" and game["fuel"] < max_fuel(game),
        "options": options,
    }


def set_travel_position(
    game: dict[str, Any],
    state: str,
    body_type: str,
    body_id: str,
    place_id: str | None = None,
) -> None:
    game["travel_state"] = state
    name = SYSTEMS[game["location"]]["name"]
    if body_type == "station":
        name = STATIONS[game["location"]]["name"]
    elif body_type == "planet":
        planet = find_planet(game["location"], body_id)
        name = planet["name"] if planet else body_id

    game["near_body"] = {
        "type": body_type,
        "id": body_id,
        "name": name,
        "placeId": place_id,
    }


def valid_near_body(game: dict[str, Any], near: dict[str, Any]) -> bool:
    body_type = near.get("type")
    body_id = near.get("id")
    if body_type == "system":
        return body_id in {game["location"], None}
    if body_type == "station":
        return body_id == f"station:{game['location']}"
    if body_type == "planet":
        return bool(find_planet(game["location"], body_id))
    return False


def inferred_near_body(game: dict[str, Any]) -> dict[str, Any]:
    state = game.get("travel_state", "docked")
    place = plain_place(game["location"], game.get("current_place"), game)
    if state == "docked":
        return {
            "type": "station",
            "id": f"station:{game['location']}",
            "name": STATIONS[game["location"]]["name"],
            "placeId": game.get("current_place"),
        }
    if state in {"landed", "atmosphere", "orbit"} and place and place["category"] == "planet":
        return {
            "type": "planet",
            "id": place["planetId"],
            "name": place["planetName"],
            "placeId": place["id"] if state == "landed" else None,
        }
    planets = PLANETS.get(game["location"], [])
    if state == "orbit" and planets:
        return {"type": "planet", "id": planets[0]["id"], "name": planets[0]["name"], "placeId": None}
    return {"type": "system", "id": game["location"], "name": SYSTEMS[game["location"]]["name"], "placeId": None}


def current_near_planet_id(game: dict[str, Any]) -> str | None:
    near = game.get("near_body") or {}
    if near.get("type") == "planet":
        return near.get("id")
    place = plain_place(game["location"], game.get("current_place"), game)
    if place and place["category"] == "planet":
        return place["planetId"]
    return None


def is_landed_at_place(game: dict[str, Any], place_id: str | None) -> bool:
    near = game.get("near_body") or {}
    return game.get("travel_state") == "landed" and near.get("placeId") == place_id


def travel_state_label(game: dict[str, Any]) -> str:
    return TRAVEL_STATE_LABELS.get(game.get("travel_state"), "Unknown")


def planet_visit_event(game: dict[str, Any], place: dict[str, Any], revisiting: bool) -> str:
    if revisiting:
        return "The crew updates old notes; this place has already paid out its first survey lead."

    rng = random.Random(f"visit:{place['id']}")
    roll = rng.random()
    hazard = place["hazardValue"]

    if roll < hazard:
        damage = rng.randint(4, 14)
        applied_damage = apply_hull_damage(game, damage)
        if applied_damage == 0:
            return f"Local trouble at the {place['kind']} bounced harmlessly off the invulnerable hull."
        return f"Local trouble at the {place['kind']} cost {damage} hull integrity."

    if roll < 0.42:
        reward = rng.randint(25, 120)
        game["credits"] += reward
        return f"First survey rights sold for {reward} credits."

    if roll < 0.62:
        good = rng.choice(list(GOODS))
        if cargo_used(game) + GOODS[good]["weight"] <= cargo_capacity(game):
            game["inventory"][good] += 1
            return f"The landing team recovered 1 {GOODS[good]['name']}."
        return "The landing team found salvage, but the hold was too full to lift it."

    game["reputation"] += 1
    return f"The visit opened a useful contact with {place['faction']}. Reputation increased."


def travel_event(game: dict[str, Any], destination: str) -> str:
    risk = SYSTEMS[destination]["risk"]
    roll = random.random()
    if roll < risk:
        damage = random.randint(5, 18)
        applied_damage = apply_hull_damage(game, damage)
        if applied_damage == 0:
            return "Raiders shadowed the final approach, but invulnerable hull plating ignored the damage."
        return f"Raiders shadowed the final approach. The ship took {damage} hull damage."
    if roll < risk + 0.12:
        reward = random.randint(20, 70)
        game["credits"] += reward
        return f"A patrol paid {reward} credits for updated beacon telemetry."
    return ""


def check_mission_delivery(game: dict[str, Any]) -> str:
    mission = game.get("active_mission")
    if not mission or mission["destination"] != game["location"]:
        return ""

    if game["day"] <= mission["dueDay"]:
        bonus = max(0, mission["dueDay"] - game["day"]) * 8
        total = mission["reward"] + bonus
        game["credits"] += total
        game["reputation"] += 2
        game["active_mission"] = None
        return f"Contract completed. Payment received: {total} credits."

    penalty = min(120, mission["reward"] // 2)
    game["credits"] = max(0, game["credits"] + mission["reward"] - penalty)
    game["reputation"] -= 1
    game["active_mission"] = None
    return f"Contract delivered late. Net payment after penalties: {mission['reward'] - penalty} credits."


def generate_missions(game: dict[str, Any]) -> list[dict[str, Any]]:
    current = game["location"]
    rng = random.Random(f"{current}-{game['day']}-{game['reputation']}")
    current_galaxy = system_galaxy_id(current)
    destinations = [
        key
        for key in ordered_known_systems(game)
        if key != current and key in set(game["charted_systems"]) and system_galaxy_id(key) == current_galaxy
    ]
    rng.shuffle(destinations)
    cargo_names = ["sealed vaccines", "survey probes", "machine prayers", "orchard cultures", "encrypted ledgers"]
    missions = []

    for index, destination in enumerate(destinations[:3]):
        distance = fuel_cost(current, destination)
        due = game["day"] + distance + rng.randint(3, 6)
        reward = 85 + distance * 28 + rng.randint(0, 65) + max(0, game["reputation"]) * 3
        cargo = cargo_names[rng.randrange(len(cargo_names))]
        missions.append(
            {
                "id": f"{current}-{destination}-{game['day']}-{index}",
                "title": f"{SYSTEMS[destination]['name']} courier run",
                "destination": destination,
                "cargo": cargo,
                "cargoWeight": rng.randint(2, 5),
                "reward": reward,
                "dueDay": due,
                "risk": risk_label(SYSTEMS[destination]["risk"]),
            }
        )

    return missions


def upgrade_tier(game: dict[str, Any], upgrade_id: str) -> int:
    raw_tier = game.get("ship_upgrades", {}).get(upgrade_id, 0)
    try:
        tier = int(raw_tier)
    except (TypeError, ValueError):
        tier = 0
    max_tier = SHIP_UPGRADES.get(upgrade_id, {}).get("maxTier", 0)
    return max(0, min(max_tier, tier))


def upgrade_cost(upgrade_id: str, next_tier: int) -> int:
    return SHIP_UPGRADES[upgrade_id]["costs"][next_tier - 1]


def upgrade_service_context(game: dict[str, Any]) -> dict[str, Any]:
    place = plain_place(game["location"], game.get("current_place"), game)
    if not place:
        return {
            "available": False,
            "place": None,
            "serviceName": SYSTEMS[game["location"]]["name"],
            "summary": "No local shipyard contact is selected.",
            "offered": set(),
            "blockedReason": "Select a station area or suitable planet location before installing upgrades.",
        }

    if game["travel_state"] == "docked" and place["category"] == "station":
        available = True
        blocked = ""
    elif game["travel_state"] in {"landed", "atmosphere"} and place["category"] == "planet":
        available = planet_place_has_shipyard(place)
        blocked = "" if available else f"{place['name']} has no shipyard crew or field mechanic."
    elif place["category"] == "station":
        available = False
        blocked = "Dock at the station before opening shipyard work orders."
    else:
        available = False
        blocked = "Land at a serviced planet location or dock at a station before installing upgrades."

    offered = location_upgrade_offers(game, place) if available else set()
    return {
        "available": available,
        "place": place,
        "serviceName": place["name"],
        "summary": service_summary(game, place, offered, available),
        "offered": offered,
        "blockedReason": blocked,
    }


def planet_place_has_shipyard(place: dict[str, Any]) -> bool:
    text = place_search_text(place)
    direct_terms = ("port district", "industrial site", "resource claim", "research site", "settlement")
    if any(term in text for term in direct_terms):
        return True
    if "salvage" in text or "rare goods" in text or "local contact" in text:
        rng = random.Random(f"field-yard:{place['id']}")
        return rng.random() < 0.45
    return False


def service_summary(game: dict[str, Any], place: dict[str, Any], offered: set[str], available: bool) -> str:
    if not available:
        return "No install-capable ship service is available at the current position."
    names = [SHIP_UPGRADES[upgrade_id]["system"] for upgrade_id in SHIP_UPGRADES if upgrade_id in offered]
    if not names:
        return f"{place['name']} can service the ship, but no compatible upgrade line is in stock today."
    local = place.get("economy", place.get("kind", "local yard")).lower()
    return f"{place['name']} is a {local} service point specializing in {', '.join(names)} work."


def location_upgrade_offers(game: dict[str, Any], place: dict[str, Any]) -> set[str]:
    text = f"{place_search_text(place)} {SYSTEMS[game['location']]['economy'].lower()} {SYSTEMS[game['location']]['faction'].lower()}"
    source_goods = {good for good, model in GOOD_MARKETS.items() if game["location"] in model["sources"]}
    scores: dict[str, float] = {}
    for upgrade_id, keywords in UPGRADE_KEYWORDS.items():
        rng = random.Random(f"upgrade-offer:{game['location']}:{place['id']}:{upgrade_id}")
        score = rng.random() * 1.1
        score += sum(1.15 for keyword in keywords if keyword in text)
        if upgrade_id in {"fuel_tanks", "cargo_bays"} and {"water", "grain"} & source_goods:
            score += 0.7
        if upgrade_id in {"cargo_bays", "hull_plating", "maneuver_thrusters"} and "ore" in source_goods:
            score += 0.8
        if upgrade_id in {"jump_drive", "maneuver_thrusters"} and "circuits" in source_goods:
            score += 0.8
        if upgrade_id == "jump_drive" and "relics" in source_goods:
            score += 0.9
        if place["category"] == "station":
            score += 0.35
        scores[upgrade_id] = score

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    offer_count = 2 + (1 if ranked[2][1] >= 2.2 else 0)
    return {upgrade_id for upgrade_id, _score in ranked[:offer_count]}


def place_search_text(place: dict[str, Any]) -> str:
    values = [
        place.get("name", ""),
        place.get("stationName", ""),
        place.get("planetName", ""),
        place.get("kind", ""),
        place.get("terrain", ""),
        place.get("economy", ""),
        place.get("faction", ""),
        place.get("wealth", ""),
        place.get("security", ""),
        place.get("opportunity", ""),
        place.get("description", ""),
    ]
    return " ".join(str(value).lower() for value in values)


def upgrade_offer(game: dict[str, Any], upgrade_id: str) -> dict[str, Any]:
    spec = SHIP_UPGRADES[upgrade_id]
    tier = upgrade_tier(game, upgrade_id)
    maxed = tier >= spec["maxTier"]
    next_tier = min(spec["maxTier"], tier + 1)
    context = upgrade_service_context(game)
    materials = {} if maxed else upgrade_materials(game, upgrade_id, next_tier, context.get("place"))
    price = 0 if maxed else location_upgrade_price(game, upgrade_id, next_tier, context.get("place"), upgrade_id in context["offered"])
    blocked_reason = ""
    if maxed:
        blocked_reason = "Maximum tier installed."
    elif not context["available"]:
        blocked_reason = context["blockedReason"]
    elif upgrade_id not in context["offered"]:
        blocked_reason = f"{context['serviceName']} does not stock {spec['system'].lower()} upgrades."
    elif not cheat_enabled(game, "freeMaterials") and missing_materials(game, materials):
        blocked_reason = f"Missing materials: {materials_text(missing_materials(game, materials))}."
    elif not cheat_enabled(game, "unlimitedCredits") and game["credits"] < price:
        blocked_reason = f"Needs {price} credits."

    quality = upgrade_quality(game, upgrade_id, context.get("place"))
    return {
        "upgradeId": upgrade_id,
        "serviceName": context["serviceName"],
        "serviceSummary": context["summary"],
        "availableHere": context["available"] and upgrade_id in context["offered"],
        "quality": quality,
        "partsLabel": upgrade_parts_label(upgrade_id, context.get("place"), next_tier),
        "nextTier": next_tier,
        "price": price,
        "materials": materials,
        "canInstall": not blocked_reason,
        "blockedReason": blocked_reason,
    }


def upgrade_materials(game: dict[str, Any], upgrade_id: str, next_tier: int, place: dict[str, Any] | None) -> dict[str, int]:
    rng = random.Random(f"upgrade-materials:{game['location']}:{place['id'] if place else 'space'}:{upgrade_id}:{next_tier}")
    requirements = {
        good: quantity * next_tier
        for good, quantity in UPGRADE_MATERIALS[upgrade_id].items()
    }
    local_goods = [good for good, model in GOOD_MARKETS.items() if game["location"] in model["sources"]]
    if local_goods:
        extra_good = rng.choice(local_goods)
    else:
        extra_good = rng.choice(list(GOODS))
    requirements[extra_good] = requirements.get(extra_good, 0) + max(1, next_tier - 1)

    if place and place.get("wealth") in {"Low", "Modest"}:
        if "alloys" in requirements:
            requirements["alloys"] += 1
        elif "ore" in requirements:
            requirements["ore"] += 1
    if place and place.get("security") in {"Tight", "Strict"}:
        if "electronics" in requirements:
            requirements["electronics"] += 1
        elif "circuits" in requirements:
            requirements["circuits"] += 1
    return {good: quantity for good, quantity in requirements.items() if quantity > 0}


def location_upgrade_price(
    game: dict[str, Any],
    upgrade_id: str,
    next_tier: int,
    place: dict[str, Any] | None,
    available_here: bool,
) -> int:
    base = upgrade_cost(upgrade_id, next_tier)
    if not place:
        return base
    rng = random.Random(f"upgrade-price:{game['location']}:{place['id']}:{upgrade_id}:{next_tier}")
    modifier = rng.uniform(0.88, 1.18)
    if place.get("wealth") in {"Low", "Modest"}:
        modifier *= 0.92
    elif place.get("wealth") in {"Affluent", "Elite"}:
        modifier *= 1.12
    if place.get("security") in {"Tight", "Strict"}:
        modifier *= 1.06
    if available_here:
        modifier *= 0.94
    return max(20, round(base * modifier))


def upgrade_quality(game: dict[str, Any], upgrade_id: str, place: dict[str, Any] | None) -> str:
    if not place:
        return "remote"
    rng = random.Random(f"upgrade-quality:{game['location']}:{place['id']}:{upgrade_id}")
    labels = ["field-built", "yard-standard", "specialist", "bespoke"]
    index = rng.randrange(len(labels))
    if place.get("wealth") in {"Affluent", "Elite"}:
        index = min(len(labels) - 1, index + 1)
    if place.get("wealth") in {"Low", "Modest"}:
        index = max(0, index - 1)
    return labels[index]


def upgrade_parts_label(upgrade_id: str, place: dict[str, Any] | None, next_tier: int) -> str:
    rng = random.Random(f"upgrade-parts:{place['id'] if place else 'space'}:{upgrade_id}:{next_tier}")
    return rng.choice(UPGRADE_PART_LABELS[upgrade_id])


def missing_materials(game: dict[str, Any], materials: dict[str, int]) -> dict[str, int]:
    return {
        good: quantity - game["inventory"].get(good, 0)
        for good, quantity in materials.items()
        if game["inventory"].get(good, 0) < quantity
    }


def materials_text(materials: dict[str, int]) -> str:
    if not materials:
        return "no materials"
    return ", ".join(f"{quantity} {GOODS[good]['name']}" for good, quantity in materials.items())


def ship_stats(game: dict[str, Any]) -> dict[str, Any]:
    fuel_tier = upgrade_tier(game, "fuel_tanks")
    cargo_tier = upgrade_tier(game, "cargo_bays")
    hull_tier = upgrade_tier(game, "hull_plating")
    jump_tier = upgrade_tier(game, "jump_drive")
    thruster_tier = upgrade_tier(game, "maneuver_thrusters")
    jump_multipliers = [1.0, 0.9, 0.82, 0.75]
    local_multipliers = [1.0, 0.9, 0.82, 0.75]
    return {
        "maxFuel": SHIP.max_fuel + fuel_tier * 6,
        "maxHull": SHIP.max_hull + hull_tier * 20,
        "cargoCapacity": SHIP.cargo_capacity + cargo_tier * 8,
        "jumpFuelMultiplier": jump_multipliers[jump_tier],
        "localFuelMultiplier": local_multipliers[thruster_tier],
        "jumpFuelDiscount": round((1 - jump_multipliers[jump_tier]) * 100),
        "localFuelDiscount": round((1 - local_multipliers[thruster_tier]) * 100),
    }


def max_fuel(game: dict[str, Any]) -> int:
    return ship_stats(game)["maxFuel"]


def max_hull(game: dict[str, Any]) -> int:
    return ship_stats(game)["maxHull"]


def cargo_capacity(game: dict[str, Any]) -> int:
    return ship_stats(game)["cargoCapacity"]


def ship_jump_fuel_cost(game: dict[str, Any], origin: str, destination: str) -> int:
    base_cost = fuel_cost(origin, destination)
    if base_cost <= 0:
        return 0
    multiplier = ship_stats(game)["jumpFuelMultiplier"]
    return max(1, math.ceil(base_cost * multiplier))


def ship_local_fuel_cost(game: dict[str, Any], segments: list[dict[str, Any]]) -> int:
    base_cost = sum(segment["fuelCost"] for segment in segments)
    if base_cost <= 0:
        return 0
    multiplier = ship_stats(game)["localFuelMultiplier"]
    return max(1, math.ceil(base_cost * multiplier))


def public_ship(game: dict[str, Any]) -> dict[str, Any]:
    stats = ship_stats(game)
    context = upgrade_service_context(game)
    upgrades = []
    for upgrade_id, spec in SHIP_UPGRADES.items():
        tier = upgrade_tier(game, upgrade_id)
        offer = upgrade_offer(game, upgrade_id)
        maxed = tier >= spec["maxTier"]
        upgrades.append(
            {
                "id": upgrade_id,
                "name": spec["name"],
                "system": spec["system"],
                "description": spec["description"],
                "tier": tier,
                "maxTier": spec["maxTier"],
                "currentEffect": spec["effects"][tier - 1] if tier else "Stock system",
                "nextEffect": "" if maxed else spec["effects"][tier],
                "nextCost": offer["price"],
                "materials": [
                    {
                        "id": good,
                        "name": GOODS[good]["name"],
                        "required": quantity,
                        "owned": game["inventory"].get(good, 0),
                        "missing": 0
                        if cheat_enabled(game, "freeMaterials")
                        else max(0, quantity - game["inventory"].get(good, 0)),
                        "waived": cheat_enabled(game, "freeMaterials"),
                    }
                    for good, quantity in offer["materials"].items()
                ],
                "materialsText": materials_text(offer["materials"]),
                "quality": offer["quality"],
                "partsLabel": offer["partsLabel"],
                "availableHere": offer["availableHere"],
                "serviceName": offer["serviceName"],
                "canInstall": offer["canInstall"],
                "blockedReason": offer["blockedReason"],
            }
        )

    return {
        "name": SHIP.name,
        "id": SHIP.ship_id,
        "stats": stats,
        "upgrades": upgrades,
        "canInstall": context["available"],
        "serviceLocation": context["serviceName"],
        "serviceSummary": context["summary"],
        "installBlockedReason": "" if context["available"] else context["blockedReason"],
    }


def public_ship_ai(game: dict[str, Any]) -> dict[str, Any]:
    profile = game["ship_ai"]
    return {
        "shipId": profile["shipId"],
        "generation": profile["generation"],
        "configured": bool(profile["configured"]),
        "name": profile["name"],
        "gender": profile["gender"],
        "description": profile["description"],
        "installedDay": profile["installedDay"],
        "replacementCount": profile["replacementCount"],
        "replacementCost": SHIP_AI_REPLACEMENT_COST,
        "canStrip": bool(profile["configured"])
        and (cheat_enabled(game, "unlimitedCredits") or game["credits"] >= SHIP_AI_REPLACEMENT_COST),
        "lockedReason": "Personality locked to this ship once imprinted."
        if profile["configured"]
        else "No custom personality has been imprinted yet.",
    }


def public_player(game: dict[str, Any]) -> dict[str, Any]:
    profile = game["player"]
    return {
        "health": profile["health"],
        "maxHealth": profile["maxHealth"],
        "stamina": profile["stamina"],
        "maxStamina": profile["maxStamina"],
        "stress": profile["stress"],
        "armor": profile["armor"],
        "injury": profile["injury"],
        "stats": profile["stats"],
    }


def normalize_player(game: dict[str, Any]) -> None:
    defaults = default_player_profile()
    raw = game.get("player")
    if not isinstance(raw, dict):
        raw = {}
    raw_stats = raw.get("stats") if isinstance(raw.get("stats"), dict) else {}
    stats = {}
    for key, default_value in defaults["stats"].items():
        value = parse_quantity(raw_stats.get(key)) if key in raw_stats else default_value
        stats[key] = min(10, max(0, value))

    max_health = min(999, max(1, parse_quantity(raw.get("maxHealth")) if "maxHealth" in raw else defaults["maxHealth"]))
    max_stamina = min(999, max(1, parse_quantity(raw.get("maxStamina")) if "maxStamina" in raw else defaults["maxStamina"]))
    health = parse_quantity(raw.get("health")) if "health" in raw else max_health
    stamina = parse_quantity(raw.get("stamina")) if "stamina" in raw else max_stamina
    stress = parse_quantity(raw.get("stress")) if "stress" in raw else defaults["stress"]
    armor = parse_quantity(raw.get("armor")) if "armor" in raw else defaults["armor"]
    injury = clean_ai_text(raw.get("injury"), 48) or defaults["injury"]

    game["player"] = {
        "health": min(max_health, max(0, health)),
        "maxHealth": max_health,
        "stamina": min(max_stamina, max(0, stamina)),
        "maxStamina": max_stamina,
        "stress": min(100, max(0, stress)),
        "armor": min(100, max(0, armor)),
        "injury": injury,
        "stats": stats,
    }


def normalize_ship_ai(game: dict[str, Any]) -> None:
    raw = game.get("ship_ai")
    if not isinstance(raw, dict):
        raw = default_ship_ai_profile()
    generation = max(1, parse_quantity(raw.get("generation")) or 1)
    replacement_count = max(0, parse_quantity(raw.get("replacementCount")) or generation - 1)
    configured = bool(raw.get("configured"))
    name = clean_ai_text(raw.get("name"), 42)
    gender = clean_ai_text(raw.get("gender"), 16)
    description = clean_ai_text(raw.get("description"), 900)

    if gender not in SHIP_AI_GENDERS:
        gender = "Female"
    if not name:
        name = f"{SHIP.name} AI" if configured else f"{SHIP.name} Factory AI"
    if not description:
        description = default_ship_ai_profile(generation)["description"]

    game["ship_ai"] = {
        "shipId": clean_ai_text(raw.get("shipId"), 48) or SHIP.ship_id,
        "generation": generation,
        "configured": configured,
        "name": name,
        "gender": gender,
        "description": description,
        "installedDay": raw.get("installedDay") if configured else None,
        "replacementCount": replacement_count,
    }


def normalize_game(game: dict[str, Any]) -> None:
    ensure_system(game["location"])
    normalize_cheats(game)
    normalize_player(game)
    normalize_ship_ai(game)
    game.setdefault("visited_places", {})
    game.setdefault("planet_offsets", {})
    game.setdefault("ship_upgrades", {})
    game["ship_upgrades"] = {
        upgrade_id: upgrade_tier(game, upgrade_id)
        for upgrade_id in SHIP_UPGRADES
        if upgrade_tier(game, upgrade_id) > 0
    }
    game.setdefault("known_systems", ["aurora"])
    game.setdefault("charted_systems", ["aurora"])
    game.setdefault("known_galaxies", [STARTING_GALAXY_ID])
    game.setdefault("used_gates", [])
    game.setdefault("gate_routes", [])
    game.setdefault("player_gate_anchors", [])
    starter_systems = STARTING_KNOWN_SYSTEM_IDS if STARTING_GALAXY_ID in game["known_galaxies"] else []
    game["known_systems"] = ordered_unique_systems([*starter_systems, *game["known_systems"], game["location"]])
    game["charted_systems"] = ordered_unique_systems([*starter_systems, *game["charted_systems"], game["location"]])
    game["known_galaxies"] = ordered_unique_galaxies([*game["known_galaxies"], system_galaxy_id(game["location"])])
    game["used_gates"] = sorted(set(str(gate_id) for gate_id in game.get("used_gates", [])))
    game["gate_routes"] = sorted(set(str(route) for route in game.get("gate_routes", [])))
    game["player_gate_anchors"] = ordered_unique_systems(game.get("player_gate_anchors", []))
    game["fuel"] = min(game.get("fuel", max_fuel(game)), max_fuel(game))
    game["hull"] = min(game.get("hull", max_hull(game)), max_hull(game))
    if cheat_enabled(game, "unlimitedFuel"):
        game["fuel"] = max_fuel(game)
    if cheat_enabled(game, "invulnerableHull"):
        game["hull"] = max_hull(game)
    game.setdefault("current_place", default_place_id(game["location"]))
    if not place_belongs_to_system(game["current_place"], game["location"]):
        game["current_place"] = default_place_id(game["location"])

    if game.get("travel_state") not in TRAVEL_STATES:
        game["travel_state"] = "landed" if place_category(game["current_place"]) == "planet" else "docked"

    near = game.get("near_body")
    if not isinstance(near, dict) or not valid_near_body(game, near):
        game["near_body"] = inferred_near_body(game)


def ordered_unique_systems(system_ids: list[str]) -> list[str]:
    known = []
    seen = set()
    for system_id in system_ids:
        if system_id in seen or not ensure_system(system_id):
            continue
        seen.add(system_id)
        known.append(system_id)
    return sorted(
        known,
        key=lambda system_id: (
            _galaxy_index(system_galaxy_id(system_id)) or 0,
            _system_index(system_id) or 0,
        ),
    )


def ordered_known_systems(game: dict[str, Any]) -> list[str]:
    return ordered_unique_systems(game.get("known_systems", ["aurora"]))


def chart_system(game: dict[str, Any], system_id: str) -> None:
    game["known_systems"] = ordered_unique_systems([*game.get("known_systems", []), system_id])
    game["charted_systems"] = ordered_unique_systems([*game.get("charted_systems", []), system_id])
    game["known_galaxies"] = ordered_unique_galaxies([*game.get("known_galaxies", []), system_galaxy_id(system_id)])


def reveal_branch_systems(game: dict[str, Any], system_id: str) -> list[str]:
    known = set(game.get("known_systems", []))
    discovered = [child for child in branch_system_ids(system_id) if child not in known and ensure_system(child)]
    if discovered:
        game["known_systems"] = ordered_unique_systems([*game.get("known_systems", []), *discovered])
    return discovered


def public_discovery(game: dict[str, Any]) -> dict[str, Any]:
    current_galaxy = system_galaxy_id(game["location"])
    known = {system_id for system_id in game["known_systems"] if system_galaxy_id(system_id) == current_galaxy}
    charted = {system_id for system_id in game["charted_systems"] if system_galaxy_id(system_id) == current_galaxy}
    galaxy_size = galaxy_system_target(current_galaxy)
    return {
        "known": len(known),
        "charted": len(charted),
        "uncharted": len(known - charted),
        "total": galaxy_size,
        "potentialPlanets": galaxy_size * SECTOR_PLANET_MAX_PER_SYSTEM,
        "generatedPlanets": sum(len(planets) for planets in PLANETS.values()),
        "currentBranches": len([child for child in branch_system_ids(game["location"]) if child not in known]),
        "knownGalaxies": len(game.get("known_galaxies", [])),
    }


def default_place_id(system_id: str) -> str:
    first_area = STATIONS[system_id]["areas"][0]["id"]
    return f"station:{system_id}:{first_area}"


def place_belongs_to_system(place_id: str | None, system_id: str) -> bool:
    if not place_id:
        return False

    parts = place_id.split(":")
    if len(parts) != 3:
        return False

    category, local_id, detail = parts
    if category == "station":
        return local_id == system_id and any(area["id"] == detail for area in STATIONS[system_id]["areas"])
    if category == "planet":
        planet = find_planet(system_id, local_id)
        return bool(planet and 1 <= parse_quantity(detail) <= planet["placeCount"])
    return False


def place_category(place_id: str | None) -> str:
    if not place_id:
        return ""
    return place_id.split(":", 1)[0]


def public_station(system_id: str, game: dict[str, Any]) -> dict[str, Any]:
    station = STATIONS[system_id]
    return {
        "id": f"station:{system_id}",
        "stationId": station.get("id", "primary"),
        "name": station["name"],
        "movement": local_route_preview(game, "dock_station") if system_id == game["location"] else None,
        "areas": [public_station_area(system_id, area, game) for area in station["areas"]],
    }


def public_stations(system_id: str, game: dict[str, Any]) -> list[dict[str, Any]]:
    stations = []
    for station in SYSTEM_STATIONS.get(system_id, [STATIONS[system_id]]):
        primary = station is STATIONS[system_id] or station.get("id") == "primary"
        stations.append(
            {
                "id": f"station:{system_id}:{station.get('id', 'primary')}",
                "stationId": station.get("id", "primary"),
                "name": station["name"],
                "primary": primary,
                "areaCount": len(station["areas"]),
                "areas": (
                    [public_station_area(system_id, area, game) for area in station["areas"]]
                    if primary
                    else [public_catalog_station_area(station, area) for area in station["areas"]]
                ),
            }
        )
    return stations


def public_station_area(system_id: str, area: dict[str, Any], game: dict[str, Any]) -> dict[str, Any]:
    place_id = f"station:{system_id}:{area['id']}"
    visits = game["visited_places"].get(place_id, 0)
    return {
        "id": place_id,
        "category": "station",
        "name": area["name"],
        "stationName": STATIONS[system_id]["name"],
        "kind": "station area",
        "faction": area["faction"],
        "wealth": area["wealth"],
        "economy": area["economy"],
        "security": area["security"],
        "description": area["description"],
        "visited": visits > 0,
        "visits": visits,
    }


def public_catalog_station_area(station: dict[str, Any], area: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"{station.get('id', 'primary')}:{area['id']}",
        "category": "station",
        "name": area["name"],
        "stationName": station["name"],
        "kind": "station area",
        "faction": area["faction"],
        "wealth": area["wealth"],
        "economy": area["economy"],
        "security": area["security"],
        "description": area["description"],
        "visited": False,
        "visits": 0,
    }


def public_planets(system_id: str, game: dict[str, Any]) -> list[dict[str, Any]]:
    planets = []
    for planet in PLANETS.get(system_id, []):
        place_count = planet["placeCount"]
        if place_count <= 0:
            offset = 0
            places = []
            shown_start = 0
            shown_end = 0
            land_preview = blocked_local_preview("land", f"{planet['name']} has no charted landing locations.")
        else:
            offset = game["planet_offsets"].get(planet["id"], 0) % place_count
            sample_size = min(PLANET_SAMPLE_SIZE, place_count)
            places = [
                public_planet_place(planet, ((offset + index) % place_count) + 1, game)
                for index in range(sample_size)
            ]
            shown_start = offset + 1
            shown_end = min(offset + sample_size, place_count)
            land_preview = local_route_preview(
                game,
                "land",
                place_id=f"planet:{planet['id']}:{offset + 1}",
            )
        planets.append(
            {
                "id": planet["id"],
                "name": planet["name"],
                "type": planet["type"],
                "dominantFaction": planet["dominantFaction"],
                "wealth": planet["wealth"],
                "flightStats": planet_flight_stats(planet),
                "orbitPreview": local_route_preview(game, "enter_orbit", planet_id=planet["id"]),
                "landPreview": land_preview,
                "placeCount": place_count,
                "shownStart": shown_start,
                "shownEnd": shown_end,
                "places": places,
            }
        )
    return planets


def public_system_catalog(system_id: str, charted: bool = True, game: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_system(system_id)
    if not charted:
        system = SYSTEMS[system_id]
        return {
            **_public_system(system_id, charted=False),
            "station": None,
            "stations": [],
            "planets": [],
            "resources": [],
            "marketNotes": {"cheapest": [], "expensive": []},
            "gates": [],
            "signalReading": signal_reading(system_id),
            "estimatedDistance": "Unresolved",
            "hiddenSummary": f"Unresolved readings suggest {system['economy'].lower()} signatures, but no reliable local catalog exists yet.",
        }

    system = SYSTEMS[system_id]
    stations = public_catalog_stations(system_id)
    planets = []
    for planet in PLANETS.get(system_id, []):
        planets.append(
            {
                "id": planet["id"],
                "name": planet["name"],
                "type": planet["type"],
                "dominantFaction": planet["dominantFaction"],
                "wealth": planet["wealth"],
                "placeCount": planet["placeCount"],
                "terrain": planet["terrain"],
                "factions": planet["factions"],
                "flightStats": planet_flight_stats(planet),
                "resourceHints": planet_resource_hints(planet),
            }
        )

    return {
        **_public_system(system_id, charted=True),
        "station": stations[0],
        "stations": stations,
        "planets": planets,
        "resources": public_system_resources(system_id),
        "gates": public_gates(game, system_id) if game else [],
        "marketNotes": {
            "cheapest": cheapest_market_goods(system_id),
            "expensive": expensive_market_goods(system_id),
        },
    }


def public_catalog_stations(system_id: str) -> list[dict[str, Any]]:
    stations = []
    for station in SYSTEM_STATIONS.get(system_id, [STATIONS[system_id]]):
        stations.append(
            {
                "id": f"station:{system_id}:{station.get('id', 'primary')}",
                "stationId": station.get("id", "primary"),
                "name": station["name"],
                "areaCount": len(station["areas"]),
                "areas": [
                    {
                        "id": area["id"],
                        "name": area["name"],
                        "faction": area["faction"],
                        "wealth": area["wealth"],
                        "economy": area["economy"],
                        "security": area["security"],
                    }
                    for area in station["areas"]
                ],
            }
        )
    return stations


def public_system_resources(system_id: str) -> list[dict[str, Any]]:
    ensure_system(system_id)
    resources = []
    for good, model in GOOD_MARKETS.items():
        local_price = SYSTEMS[system_id]["market"][good]
        is_source = system_id in model["sources"]
        if is_source:
            abundance = model["sources"][system_id]
            note = f"Native source: {model['sourceLabel']}"
            richness = "Primary"
        elif local_price <= model["basePrice"] * 0.9:
            abundance = 0.9
            note = "Strong local market signal"
            richness = "Secondary"
        else:
            abundance = 0.0
            note = "Imported or limited"
            richness = "Trace"

        resources.append(
            {
                "id": good,
                "name": GOODS[good]["name"],
                "localPrice": local_price,
                "richness": richness,
                "abundance": round(abundance, 2),
                "note": note,
            }
        )

    return sorted(resources, key=lambda item: (item["richness"] != "Primary", item["localPrice"], item["name"]))


def cheapest_market_goods(system_id: str) -> list[dict[str, Any]]:
    ensure_system(system_id)
    ranked = sorted(SYSTEMS[system_id]["market"].items(), key=lambda item: item[1])
    return [{"id": good, "name": GOODS[good]["name"], "price": price} for good, price in ranked[:3]]


def expensive_market_goods(system_id: str) -> list[dict[str, Any]]:
    ensure_system(system_id)
    ranked = sorted(SYSTEMS[system_id]["market"].items(), key=lambda item: item[1], reverse=True)
    return [{"id": good, "name": GOODS[good]["name"], "price": price} for good, price in ranked[:3]]


def planet_resource_hints(planet: dict[str, Any]) -> list[str]:
    text = " ".join([planet["type"], planet["wealth"], *planet["terrain"]]).lower()
    hints = []
    rules = [
        (("mine", "ore", "regolith"), "Ore"),
        (("factory", "foundry", "slag", "forge"), "Alloys"),
        (("dust", "desert", "salt", "ash", "kiln"), "Ceramics"),
        (("ice", "tidal", "coastal", "canal", "garden"), "Water"),
        (("orchard", "farm", "garden", "forest"), "Grain"),
        (("orchard", "forest", "clinic", "habitat"), "Polymers"),
        (("hospital", "sanctuary", "medical"), "Medicine"),
        (("observatory", "lab", "relay", "factory"), "Circuits"),
        (("observatory", "lab", "relay", "probe"), "Electronics"),
        (("floating", "cloud", "shipyard", "factory"), "Composites"),
        (("ice", "storm", "cloud", "hospital", "station"), "Coolant"),
        (("ruin", "ash", "impact", "buried", "fractured"), "Relics"),
    ]
    for keywords, label in rules:
        if any(keyword in text for keyword in keywords):
            hints.append(label)
    return hints[:4] or ["Survey data"]


def public_place(system_id: str, place_id: str | None, game: dict[str, Any]) -> dict[str, Any] | None:
    place = plain_place(system_id, place_id, game)
    if place and place["category"] == "planet":
        place["movement"] = local_route_preview(game, "land", place_id=place["id"])
    return place


def plain_place(system_id: str, place_id: str | None, game: dict[str, Any]) -> dict[str, Any] | None:
    if not place_belongs_to_system(place_id, system_id):
        return None

    parts = place_id.split(":")
    if parts[0] == "station":
        area = next(item for item in STATIONS[system_id]["areas"] if item["id"] == parts[2])
        return public_station_area(system_id, area, game)

    planet = find_planet(system_id, parts[1])
    place = generate_planet_place(planet, parse_quantity(parts[2]))
    visits = game["visited_places"].get(place["id"], 0)
    place["visited"] = visits > 0
    place["visits"] = visits
    return place


def public_planet_place(planet: dict[str, Any], index: int, game: dict[str, Any]) -> dict[str, Any]:
    place = generate_planet_place(planet, index)
    visits = game["visited_places"].get(place["id"], 0)
    place["visited"] = visits > 0
    place["visits"] = visits
    place["movement"] = local_route_preview(game, "land", place_id=place["id"])
    return place


def generate_planet_place(planet: dict[str, Any], index: int) -> dict[str, Any]:
    index = min(max(1, index), planet["placeCount"])
    rng = random.Random(f"{planet['seed']}:{index}")
    prefix = rng.choice(PLACE_PREFIXES)
    feature = rng.choice(PLACE_FEATURES)
    terrain = rng.choice(planet["terrain"])
    kind = rng.choice(PLACE_KINDS)
    faction = rng.choice(planet["factions"])
    wealth = rng.choice(WEALTH_BANDS)
    security = rng.choice(SECURITY_BANDS)
    hazard = min(0.42, 0.05 + WEALTH_BANDS.index(wealth) * 0.01 + rng.random() * 0.16)
    opportunity = rng.choice(["trade lead", "survey data", "salvage", "local contact", "rare goods", "rumor"])
    name = f"{prefix} {feature} {index:04d}"

    return {
        "id": f"planet:{planet['id']}:{index}",
        "category": "planet",
        "planetId": planet["id"],
        "planetName": planet["name"],
        "index": index,
        "name": name,
        "kind": kind,
        "terrain": terrain,
        "faction": faction,
        "wealth": wealth,
        "security": security,
        "hazard": risk_label(hazard),
        "hazardValue": hazard,
        "opportunity": opportunity,
        "description": (
            f"A {wealth.lower()} {kind} in the {terrain}, influenced by {faction}. "
            f"Survey notes flag {opportunity} and {security.lower()} security."
        ),
    }


def find_planet(system_id: str, planet_id: str | None) -> dict[str, Any] | None:
    return next((planet for planet in PLANETS.get(system_id, []) if planet["id"] == planet_id), None)


def public_market(game: dict[str, Any]) -> list[dict[str, Any]]:
    return [market_price(game, good) for good in GOODS]


def public_market_context(game: dict[str, Any]) -> dict[str, Any]:
    place = public_place(game["location"], game["current_place"], game)
    return {
        "name": place["name"],
        "category": place["category"],
        "summary": (
            f"Prices reflect {SYSTEMS[game['location']]['name']} supply routes plus "
            f"local {place['wealth'].lower()} {place.get('economy', place.get('kind', 'market')).lower()} modifiers."
        ),
    }


def market_prices(game: dict[str, Any]) -> dict[str, int]:
    return {good: market_price(game, good)["price"] for good in GOODS}


def market_price(game: dict[str, Any], good: str) -> dict[str, Any]:
    normalize_game(game)
    model = GOOD_MARKETS[good]
    source = closest_source(game["location"], good, game)
    source_system = source["system"]
    source_distance = source["fuelDistance"]
    regional_multiplier = source["abundance"] + source_distance * model["transport"]
    risk_multiplier = 1 + SYSTEMS[game["location"]]["risk"] * 0.08
    place = public_place(game["location"], game["current_place"], game)
    local_multiplier, local_note = local_market_modifier(place, good)
    price = max(1, round(model["basePrice"] * regional_multiplier * risk_multiplier * local_multiplier))

    return {
        "id": good,
        "name": GOODS[good]["name"],
        "weight": GOODS[good]["weight"],
        "price": price,
        "source": SYSTEMS[source_system]["name"],
        "sourceDistance": source_distance,
        "sourceDistanceLabel": "gate tariff" if source.get("viaGate") else f"{source_distance} fuel",
        "sourceLabel": model["sourceLabel"],
        "localNote": local_note,
        "scarcity": scarcity_label(source_distance),
    }


def closest_source(system_id: str, good: str, game: dict[str, Any] | None = None) -> dict[str, Any]:
    model = GOOD_MARKETS[good]
    ranked = []
    current_galaxy = system_galaxy_id(system_id)
    for source_system, abundance in model["sources"].items():
        ensure_system(source_system)
        source_galaxy = system_galaxy_id(source_system)
        if source_galaxy != current_galaxy and not galaxies_connected_by_gate(game, current_galaxy, source_galaxy):
            continue
        via_gate = source_galaxy != current_galaxy
        distance = (
            0
            if source_system == system_id
            else round(8 + GALAXIES[source_galaxy]["risk"] * 12)
            if via_gate
            else fuel_cost(system_id, source_system)
        )
        delivered = abundance + distance * model["transport"]
        ranked.append(
            {
                "system": source_system,
                "abundance": abundance,
                "fuelDistance": distance,
                "deliveredMultiplier": delivered,
                "viaGate": via_gate,
            }
        )
    if not ranked:
        return {
            "system": system_id,
            "abundance": 1.18,
            "fuelDistance": 0,
            "deliveredMultiplier": 1.18,
            "viaGate": False,
        }
    return min(ranked, key=lambda item: item["deliveredMultiplier"])


def scarcity_label(source_distance: int) -> str:
    if source_distance == 0:
        return "Local surplus"
    if source_distance <= 5:
        return "Regional supply"
    if source_distance <= 9:
        return "Imported"
    return "Rare import"


def local_market_modifier(place: dict[str, Any], good: str) -> tuple[float, str]:
    modifier = wealth_modifier(place.get("wealth", "Working"), good)
    notes = [f"{place.get('wealth', 'Working')} wealth"]
    economy_text = " ".join(
        str(place.get(key, ""))
        for key in ("economy", "kind", "terrain", "opportunity")
    ).lower()

    keyword_rules = [
        (("agricultural", "orchard", "farm", "garden", "canal"), {"grain": 0.78, "water": 0.86, "polymers": 0.84}, "local food supply"),
        (("ice shadow", "ice mine", "tidal", "coastal", "water"), {"water": 0.78, "coolant": 0.88}, "local water access"),
        (
            ("foundry", "forge", "industrial", "refinery", "factory", "ore", "mining", "resource claim"),
            {"ore": 0.78, "alloys": 0.76, "ceramics": 0.84, "composites": 0.9, "circuits": 0.93, "water": 1.08, "grain": 1.1},
            "industrial supply chain",
        ),
        (
            ("research", "archive", "observatory", "lab", "relay"),
            {"circuits": 0.84, "electronics": 0.82, "composites": 0.9, "coolant": 0.94, "medicine": 0.95, "relics": 0.92},
            "research procurement",
        ),
        (("medical", "clinic", "hospital", "pharma", "sanctuary"), {"medicine": 0.72, "polymers": 0.86, "coolant": 0.88, "water": 0.94}, "medical supply contract"),
        (
            ("salvage", "scrap", "auction", "ruin", "wreckage"),
            {"circuits": 0.8, "electronics": 0.82, "alloys": 0.86, "relics": 0.78, "ore": 0.88, "medicine": 1.1},
            "salvage market",
        ),
        (
            ("commodities", "exchange", "bourse", "market"),
            {
                "water": 0.95,
                "grain": 0.95,
                "ore": 0.95,
                "alloys": 0.96,
                "polymers": 0.96,
                "ceramics": 0.96,
                "composites": 0.97,
                "coolant": 0.96,
                "electronics": 0.97,
                "medicine": 0.97,
                "circuits": 0.97,
                "relics": 0.98,
            },
            "bulk exchange",
        ),
        (("black", "underdeck", "loose"), {"ore": 0.88, "alloys": 0.9, "electronics": 0.9, "circuits": 0.9, "relics": 0.9, "medicine": 1.08}, "informal market"),
        (("diplomatic", "embassy", "elite"), {"medicine": 1.1, "electronics": 1.08, "relics": 1.18, "grain": 1.05}, "prestige demand"),
        (("port", "docking", "depot", "harbor"), {"water": 0.96, "grain": 0.96, "ore": 0.98, "alloys": 0.98, "coolant": 0.96, "electronics": 0.98, "circuits": 0.98}, "port competition"),
    ]

    for keywords, modifiers, note in keyword_rules:
        if any(keyword in economy_text for keyword in keywords) and good in modifiers:
            modifier *= modifiers[good]
            notes.append(note)

    security = place.get("security", "Managed")
    if security in {"Tight", "Strict"}:
        modifier *= 1.04 if good != "medicine" else 1.02
        notes.append(f"{security.lower()} tariffs")
    elif security == "Loose":
        modifier *= 0.97 if good in {"ore", "alloys", "electronics", "circuits", "relics"} else 1.01
        notes.append("loose customs")

    return max(0.55, min(1.65, modifier)), ", ".join(notes[:3])


def wealth_modifier(wealth: str, good: str) -> float:
    if wealth in {"Low", "Modest"}:
        return 0.92 if good in {"water", "grain", "ore", "alloys", "polymers", "ceramics"} else 1.04
    if wealth == "Working":
        return 1.0
    if wealth in {"Comfortable", "Industrial", "Research"}:
        return 1.02
    if wealth in {"Affluent", "Elite"}:
        return 1.12 if good in {"medicine", "electronics", "circuits", "relics", "composites"} else 1.05
    if wealth == "Volatile":
        return 0.92 if good in {"ore", "alloys", "electronics", "circuits", "relics"} else 1.15
    return 1.0


def cargo_used(game: dict[str, Any]) -> int:
    return sum(GOODS[good]["weight"] * amount for good, amount in game["inventory"].items())


def fuel_cost(origin: str, destination: str) -> int:
    ensure_system(origin)
    ensure_system(destination)
    start = SYSTEMS[origin]
    end = SYSTEMS[destination]
    distance = math.sqrt((start["x"] - end["x"]) ** 2 + (start["y"] - end["y"]) ** 2)
    return max(1, math.ceil(distance * 2.2))


def fuel_price(location: str) -> int:
    return 7 + math.ceil(SYSTEMS[location]["risk"] * 10)


def repair_price(location: str) -> int:
    return 4 + math.ceil(SYSTEMS[location]["risk"] * 8)


def parse_quantity(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def status_label(game: dict[str, Any]) -> str:
    if game["hull"] <= 0:
        return "Disabled"
    if any(game.get("cheats", {}).values()):
        return "Cheats active"
    if game["fuel"] <= 3:
        return "Low fuel"
    if cargo_used(game) >= cargo_capacity(game):
        return "Hold full"
    if game.get("active_mission"):
        return "On contract"
    return "Free trader"


def risk_label(value: float) -> str:
    if value >= 0.3:
        return "Severe"
    if value >= 0.18:
        return "Elevated"
    return "Managed"


def _signal_label(system_id: str) -> str:
    index = (_system_index(system_id) or 0) + 1
    return f"Uncharted Signal {index:02d}"


def signal_reading(system_id: str) -> str:
    ensure_system(system_id)
    system = SYSTEMS[system_id]
    focus_goods = system.get("focusGoods") or [
        good
        for good, price in sorted(system["market"].items(), key=lambda item: item[1])
        if good in GOODS
    ][:2]
    readings = {
        "water": "water ice and refinery chatter",
        "grain": "biomass reflectors and habitat heat",
        "ore": "dense metallic bodies",
        "medicine": "clinic-band traffic",
        "circuits": "fabricator noise",
        "relics": "irregular archive beacons",
        "alloys": "refinery heat and alloy massing",
        "polymers": "polymer vats and chemical storage",
        "ceramics": "kiln signatures and heat-shield stock",
        "composites": "composite fabrication noise",
        "coolant": "thermal plant traffic",
        "electronics": "electronics assembly chatter",
    }
    hints = [readings.get(good, GOODS[good]["name"].lower()) for good in focus_goods[:2]]
    economy = system["economy"].lower()
    risk = risk_label(system["risk"]).lower()
    return f"Long-range scans show {risk} hazard signatures, {economy} emissions, and traces of {', '.join(hints)}."


def _public_system(key: str, charted: bool = True) -> dict[str, Any]:
    ensure_system(key)
    system = SYSTEMS[key]
    if not charted:
        return {
            "id": key,
            "name": _signal_label(key),
            "faction": "Unknown",
            "economy": "Uncharted signal",
            "description": signal_reading(key),
            "x": system["x"],
            "y": system["y"],
            "galaxyId": system_galaxy_id(key),
            "galaxyName": GALAXIES[system_galaxy_id(key)]["name"],
            "risk": "Unknown",
            "charted": False,
            "signalReading": signal_reading(key),
        }

    return {
        "id": key,
        "name": system["name"],
        "faction": system["faction"],
        "economy": system["economy"],
        "description": system["description"],
        "x": system["x"],
        "y": system["y"],
        "galaxyId": system_galaxy_id(key),
        "galaxyName": GALAXIES[system_galaxy_id(key)]["name"],
        "risk": risk_label(system["risk"]),
        "charted": True,
    }


def _public_market(system: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": good, "name": GOODS[good]["name"], "weight": GOODS[good]["weight"], "price": price}
        for good, price in system["market"].items()
    ]


def _public_inventory(game: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": good,
            "name": GOODS[good]["name"],
            "amount": game["inventory"].get(good, 0),
            "weight": GOODS[good]["weight"],
        }
        for good in GOODS
    ]


def _public_travel(game: dict[str, Any]) -> list[dict[str, Any]]:
    origin = game["location"]
    can_jump = game["travel_state"] in JUMP_STATES
    has_unlimited_fuel = cheat_enabled(game, "unlimitedFuel")
    charted_systems = set(game["charted_systems"])
    current_galaxy = system_galaxy_id(origin)
    routes = []
    for key in ordered_known_systems(game):
        if system_galaxy_id(key) != current_galaxy:
            continue
        charted = key in charted_systems
        public_system = _public_system(key, charted=charted)
        cost = 0 if key == origin else ship_jump_fuel_cost(game, origin, key)
        time = 0 if key == origin else max(1, math.ceil(cost / 2))
        routes.append(
            {
                "id": key,
                "name": public_system["name"],
                "fuelCost": cost,
                "timeCost": time,
                "risk": public_system["risk"],
                "charted": charted,
                "disabled": key == origin,
                "canCommit": key != origin and can_jump and (has_unlimited_fuel or game["fuel"] >= cost),
                "blockedReason": (
                    "Current system"
                    if key == origin
                    else ""
                    if can_jump
                    else f"Jump requires system space. Current state: {travel_state_label(game)}."
                ),
                "discoveryNote": "" if charted else "Travel here to resolve the signal and chart the system.",
                "warning": (
                    f"Needs {cost} fuel; tanks hold {game['fuel']}."
                    if key != origin and can_jump and not has_unlimited_fuel and game["fuel"] < cost
                    else ""
                ),
            }
        )
    return routes


def _add_log(game: dict[str, Any], message: str) -> None:
    game["log"].append(f"Day {game['day']}: {message}")
    game["log"] = game["log"][-40:]

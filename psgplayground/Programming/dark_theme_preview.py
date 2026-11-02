"""
10 custom dark PySimpleGUI themes + previewer.
- "View All" shows every theme in ONE window (like the built-in previewer).
- Click a theme button for a full interactive preview.
Run:  python dark_theme_preview.py
"""
import re
import PySimpleGUI as sg

CUSTOM_THEMES = {
    # ----- 5 more: dark with vivid colorful highlights -----
    "NeonPink": {
        "BACKGROUND": "#0a0510", "TEXT": "#e8d6e6",
        "INPUT": "#160d1e", "TEXT_INPUT": "#f5e8f3", "SCROLL": "#160d1e",
        "BUTTON": ("#14020e", "#ff2d95"), "PROGRESS": ("#ff2d95", "#160d1e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ElectricLime": {
        "BACKGROUND": "#070a05", "TEXT": "#dbe8d0",
        "INPUT": "#101508", "TEXT_INPUT": "#ecf5e2", "SCROLL": "#101508",
        "BUTTON": ("#0c1202", "#a6e22e"), "PROGRESS": ("#c3ff3d", "#101508"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "AzurePulse": {
        "BACKGROUND": "#040810", "TEXT": "#d0e0f2",
        "INPUT": "#0a1220", "TEXT_INPUT": "#e2eefa", "SCROLL": "#0a1220",
        "BUTTON": ("#031024", "#1e9bff"), "PROGRESS": ("#1e9bff", "#0a1220"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SolarYellow": {
        "BACKGROUND": "#0a0904", "TEXT": "#e8e2c8",
        "INPUT": "#171408", "TEXT_INPUT": "#f5f0da", "SCROLL": "#171408",
        "BUTTON": ("#141002", "#ffd400"), "PROGRESS": ("#ffd400", "#171408"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "VividCoral": {
        "BACKGROUND": "#0b0505", "TEXT": "#ecd7d2",
        "INPUT": "#1a0d0c", "TEXT_INPUT": "#f7e7e2", "SCROLL": "#1a0d0c",
        "BUTTON": ("#1c0704", "#ff6f61"), "PROGRESS": ("#ff6f61", "#1a0d0c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- original 5 -----
    "DarkSlate": {
        "BACKGROUND": "#1e2229", "TEXT": "#d7dde4",
        "INPUT": "#2b313b", "TEXT_INPUT": "#e6ebf1", "SCROLL": "#2b313b",
        "BUTTON": ("#e6ebf1", "#3a4250"), "PROGRESS": ("#5c7cfa", "#2b313b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MidnightPurple": {
        "BACKGROUND": "#17141f", "TEXT": "#d9d4e7",
        "INPUT": "#241f31", "TEXT_INPUT": "#e8e3f5", "SCROLL": "#241f31",
        "BUTTON": ("#ffffff", "#6c4fbf"), "PROGRESS": ("#9b7bff", "#241f31"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonAmber": {
        "BACKGROUND": "#121212", "TEXT": "#e0e0e0",
        "INPUT": "#1f1f1f", "TEXT_INPUT": "#f5f5f5", "SCROLL": "#1f1f1f",
        "BUTTON": ("#121212", "#ffb300"), "PROGRESS": ("#ffb300", "#1f1f1f"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DeepOceanTeal": {
        "BACKGROUND": "#0f1b24", "TEXT": "#cfe6e6",
        "INPUT": "#16262f", "TEXT_INPUT": "#e0f2f1", "SCROLL": "#16262f",
        "BUTTON": ("#02231f", "#2ec4b6"), "PROGRESS": ("#2ec4b6", "#16262f"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "EmberForge": {
        "BACKGROUND": "#1a1615", "TEXT": "#e8ddd6",
        "INPUT": "#2a2321", "TEXT_INPUT": "#f3ebe5", "SCROLL": "#2a2321",
        "BUTTON": ("#ffffff", "#c0392b"), "PROGRESS": ("#ff6b4a", "#2a2321"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 new: darker darks (near-black backgrounds) -----
    "VoidBlue": {
        "BACKGROUND": "#05070d", "TEXT": "#c9d4e3",
        "INPUT": "#0d1220", "TEXT_INPUT": "#dde6f2", "SCROLL": "#0d1220",
        "BUTTON": ("#dde6f2", "#1b2b4a"), "PROGRESS": ("#3d6bff", "#0d1220"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PitchGreen": {
        "BACKGROUND": "#040806", "TEXT": "#b9d6c4",
        "INPUT": "#0a130e", "TEXT_INPUT": "#d3ecdc", "SCROLL": "#0a130e",
        "BUTTON": ("#eafff2", "#1f7a4d"), "PROGRESS": ("#2ecc71", "#0a130e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ObsidianRed": {
        "BACKGROUND": "#070404", "TEXT": "#e0c9c9",
        "INPUT": "#140b0b", "TEXT_INPUT": "#f0dcdc", "SCROLL": "#140b0b",
        "BUTTON": ("#ffffff", "#7a1f1f"), "PROGRESS": ("#e74c3c", "#140b0b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "AbyssViolet": {
        "BACKGROUND": "#060410", "TEXT": "#cfc6e8",
        "INPUT": "#0f0a20", "TEXT_INPUT": "#e2dbf5", "SCROLL": "#0f0a20",
        "BUTTON": ("#e2dbf5", "#3a2a7a"), "PROGRESS": ("#8a63ff", "#0f0a20"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "TrueBlackMono": {
        "BACKGROUND": "#000000", "TEXT": "#cccccc",
        "INPUT": "#0d0d0d", "TEXT_INPUT": "#eeeeee", "SCROLL": "#0d0d0d",
        "BUTTON": ("#000000", "#9e9e9e"), "PROGRESS": ("#bdbdbd", "#0d0d0d"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 more extra-dark -----
    "NightCyan": {
        "BACKGROUND": "#020a0d", "TEXT": "#bfe3ec",
        "INPUT": "#07161c", "TEXT_INPUT": "#d8f2f8", "SCROLL": "#07161c",
        "BUTTON": ("#e6fbff", "#0e5a6e"), "PROGRESS": ("#00bcd4", "#07161c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BlackGold": {
        "BACKGROUND": "#0a0803", "TEXT": "#e3d7b8",
        "INPUT": "#171307", "TEXT_INPUT": "#f2ead2", "SCROLL": "#171307",
        "BUTTON": ("#0a0803", "#c9a227"), "PROGRESS": ("#e6b800", "#171307"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ShadowMagenta": {
        "BACKGROUND": "#0b040a", "TEXT": "#e6c9de",
        "INPUT": "#180a15", "TEXT_INPUT": "#f4dcee", "SCROLL": "#180a15",
        "BUTTON": ("#ffffff", "#7a1f5e"), "PROGRESS": ("#e91e8c", "#180a15"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DuskOrange": {
        "BACKGROUND": "#0a0602", "TEXT": "#e8d5bf",
        "INPUT": "#181008", "TEXT_INPUT": "#f5e6d3", "SCROLL": "#181008",
        "BUTTON": ("#fff3e0", "#8a4a12"), "PROGRESS": ("#ff8c1a", "#181008"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "IceStorm": {
        "BACKGROUND": "#04070a", "TEXT": "#cdd9e5",
        "INPUT": "#0c1319", "TEXT_INPUT": "#e2ecf5", "SCROLL": "#0c1319",
        "BUTTON": ("#04070a", "#7fa8c9"), "PROGRESS": ("#9fc6e8", "#0c1319"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 more: extra-dark with muted/darker accents -----
    "GraphiteMoss": {
        "BACKGROUND": "#060806", "TEXT": "#aeb8ae",
        "INPUT": "#101510", "TEXT_INPUT": "#c8d2c8", "SCROLL": "#101510",
        "BUTTON": ("#c8d2c8", "#2e3b2e"), "PROGRESS": ("#5a6e5a", "#101510"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SlateWine": {
        "BACKGROUND": "#080506", "TEXT": "#b8a8ad",
        "INPUT": "#140d10", "TEXT_INPUT": "#d2c2c8", "SCROLL": "#140d10",
        "BUTTON": ("#d2c2c8", "#3d2229"), "PROGRESS": ("#6e3d4a", "#140d10"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DimIndigo": {
        "BACKGROUND": "#050508", "TEXT": "#a8aabb",
        "INPUT": "#0d0e15", "TEXT_INPUT": "#c2c4d5", "SCROLL": "#0d0e15",
        "BUTTON": ("#c2c4d5", "#252a45"), "PROGRESS": ("#4a5280", "#0d0e15"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "AshTeal": {
        "BACKGROUND": "#050808", "TEXT": "#a4b5b5",
        "INPUT": "#0e1515", "TEXT_INPUT": "#c0d0d0", "SCROLL": "#0e1515",
        "BUTTON": ("#c0d0d0", "#22403d"), "PROGRESS": ("#3f6b66", "#0e1515"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "UmberStone": {
        "BACKGROUND": "#080604", "TEXT": "#b5aa9c",
        "INPUT": "#15100b", "TEXT_INPUT": "#d0c5b7", "SCROLL": "#15100b",
        "BUTTON": ("#d0c5b7", "#403225"), "PROGRESS": ("#6e5940", "#15100b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 more muted-accent extra-dark -----
    "SteelHarbor": {
        "BACKGROUND": "#050708", "TEXT": "#a5b0ba",
        "INPUT": "#0d1215", "TEXT_INPUT": "#c2ccd5", "SCROLL": "#0d1215",
        "BUTTON": ("#c2ccd5", "#28353f"), "PROGRESS": ("#4d6475", "#0d1215"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CopperDust": {
        "BACKGROUND": "#080505", "TEXT": "#b8a49a",
        "INPUT": "#150e0c", "TEXT_INPUT": "#d3c0b6", "SCROLL": "#150e0c",
        "BUTTON": ("#d3c0b6", "#4a2f24"), "PROGRESS": ("#7d5240", "#150e0c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MutedMauve": {
        "BACKGROUND": "#070508", "TEXT": "#b0a4b2",
        "INPUT": "#120d14", "TEXT_INPUT": "#cabfcc", "SCROLL": "#120d14",
        "BUTTON": ("#cabfcc", "#38293d"), "PROGRESS": ("#5f4a66", "#120d14"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DeepFern": {
        "BACKGROUND": "#040705", "TEXT": "#9fb3a6",
        "INPUT": "#0b120d", "TEXT_INPUT": "#bccec3", "SCROLL": "#0b120d",
        "BUTTON": ("#bccec3", "#1f3a2b"), "PROGRESS": ("#3d6650", "#0b120d"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CharcoalRose": {
        "BACKGROUND": "#070505", "TEXT": "#b3a2a4",
        "INPUT": "#130d0e", "TEXT_INPUT": "#cdbec0", "SCROLL": "#130d0e",
        "BUTTON": ("#cdbec0", "#402a2e"), "PROGRESS": ("#6b464c", "#130d0e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 rich deep reds (saturated, DarkRed-style) -----
    "CrimsonVelvet": {
        "BACKGROUND": "#6e0f24", "TEXT": "#f9d276",
        "INPUT": "#8f1530", "TEXT_INPUT": "#ffffff", "SCROLL": "#8f1530",
        "BUTTON": ("#f9d276", "#8f1530"), "PROGRESS": ("#f9d276", "#8f1530"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "WineCellar": {
        "BACKGROUND": "#5c0e1e", "TEXT": "#f2e3c9",
        "INPUT": "#7a1428", "TEXT_INPUT": "#ffffff", "SCROLL": "#7a1428",
        "BUTTON": ("#f2e3c9", "#8f1a30"), "PROGRESS": ("#e8b04a", "#7a1428"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RubyDepth": {
        "BACKGROUND": "#7a0f33", "TEXT": "#ffd9e3",
        "INPUT": "#9c1542", "TEXT_INPUT": "#ffffff", "SCROLL": "#9c1542",
        "BUTTON": ("#ffffff", "#b81a4e"), "PROGRESS": ("#ff8fb0", "#9c1542"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "FirebrickHall": {
        "BACKGROUND": "#701a10", "TEXT": "#ffe2c4",
        "INPUT": "#8f2416", "TEXT_INPUT": "#ffffff", "SCROLL": "#8f2416",
        "BUTTON": ("#ffe2c4", "#a52d1a"), "PROGRESS": ("#ffab5e", "#8f2416"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ScarletTheatre": {
        "BACKGROUND": "#611016", "TEXT": "#f5d7a8",
        "INPUT": "#801820", "TEXT_INPUT": "#ffffff", "SCROLL": "#801820",
        "BUTTON": ("#611016", "#e0a94a"), "PROGRESS": ("#e0a94a", "#801820"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 rich red accents on other dark backgrounds -----
    "RichRedNavy": {
        "BACKGROUND": "#0d1530", "TEXT": "#d6dcf0",
        "INPUT": "#182348", "TEXT_INPUT": "#eaeefa", "SCROLL": "#182348",
        "BUTTON": ("#ffffff", "#a01530"), "PROGRESS": ("#d42045", "#182348"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RichRedForest": {
        "BACKGROUND": "#0e2416", "TEXT": "#cfe4d3",
        "INPUT": "#173822", "TEXT_INPUT": "#e3f2e7", "SCROLL": "#173822",
        "BUTTON": ("#ffffff", "#a4132e"), "PROGRESS": ("#d41f42", "#173822"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RichRedPlum": {
        "BACKGROUND": "#241031", "TEXT": "#e2d4ec",
        "INPUT": "#371a4a", "TEXT_INPUT": "#f0e7f7", "SCROLL": "#371a4a",
        "BUTTON": ("#ffffff", "#b3123f"), "PROGRESS": ("#e0295c", "#371a4a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RichRedCharcoal": {
        "BACKGROUND": "#1c1e22", "TEXT": "#dcdee2",
        "INPUT": "#2b2e34", "TEXT_INPUT": "#eceef1", "SCROLL": "#2b2e34",
        "BUTTON": ("#ffffff", "#a91630"), "PROGRESS": ("#d92244", "#2b2e34"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RichRedBronze": {
        "BACKGROUND": "#2a1a0e", "TEXT": "#ecd9c2",
        "INPUT": "#402917", "TEXT_INPUT": "#f6e9d8", "SCROLL": "#402917",
        "BUTTON": ("#ffe8dc", "#9e1a20"), "PROGRESS": ("#cc2830", "#402917"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 dark blues -----
    "SapphireDeep": {
        "BACKGROUND": "#0a1230", "TEXT": "#cdd8f2",
        "INPUT": "#141f48", "TEXT_INPUT": "#e2e9f8", "SCROLL": "#141f48",
        "BUTTON": ("#ffffff", "#1f3a8f"), "PROGRESS": ("#3d6bff", "#141f48"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CobaltMine": {
        "BACKGROUND": "#0c1626", "TEXT": "#c9dcf0",
        "INPUT": "#15243c", "TEXT_INPUT": "#dfecf8", "SCROLL": "#15243c",
        "BUTTON": ("#e6f2ff", "#1d4f8f"), "PROGRESS": ("#2e7dd4", "#15243c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PrussianDusk": {
        "BACKGROUND": "#0b1a24", "TEXT": "#c4dbe8",
        "INPUT": "#132a38", "TEXT_INPUT": "#dcecf5", "SCROLL": "#132a38",
        "BUTTON": ("#dcecf5", "#1a4b66"), "PROGRESS": ("#2e83b3", "#132a38"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "IndigoWell": {
        "BACKGROUND": "#100d2b", "TEXT": "#d0cbee",
        "INPUT": "#1b1642", "TEXT_INPUT": "#e4e0f6", "SCROLL": "#1b1642",
        "BUTTON": ("#ffffff", "#3b2f9e"), "PROGRESS": ("#6a5ae0", "#1b1642"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MidnightHarbor": {
        "BACKGROUND": "#071120", "TEXT": "#c2d4e8",
        "INPUT": "#0f1e33", "TEXT_INPUT": "#dae7f4", "SCROLL": "#0f1e33",
        "BUTTON": ("#071120", "#4a90d9"), "PROGRESS": ("#4a90d9", "#0f1e33"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 dark greens -----
    "EmeraldVault": {
        "BACKGROUND": "#07231a", "TEXT": "#c8e8da",
        "INPUT": "#0d3628", "TEXT_INPUT": "#ddf3e9", "SCROLL": "#0d3628",
        "BUTTON": ("#ffffff", "#12805a"), "PROGRESS": ("#1fb583", "#0d3628"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ForestFloor": {
        "BACKGROUND": "#101c0e", "TEXT": "#d0e0c8",
        "INPUT": "#1b2e18", "TEXT_INPUT": "#e2eedb", "SCROLL": "#1b2e18",
        "BUTTON": ("#e2eedb", "#33591f"), "PROGRESS": ("#5c8f3a", "#1b2e18"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "JadeTemple": {
        "BACKGROUND": "#0a201e", "TEXT": "#c6e4de",
        "INPUT": "#123330", "TEXT_INPUT": "#dcf1ec", "SCROLL": "#123330",
        "BUTTON": ("#0a201e", "#3fbf9f"), "PROGRESS": ("#3fbf9f", "#123330"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "OliveNight": {
        "BACKGROUND": "#171a0c", "TEXT": "#dadec2",
        "INPUT": "#262b14", "TEXT_INPUT": "#eaeed8", "SCROLL": "#262b14",
        "BUTTON": ("#eaeed8", "#4d5420"), "PROGRESS": ("#8a9636", "#262b14"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PineShadow": {
        "BACKGROUND": "#0c1812", "TEXT": "#c2d8ca",
        "INPUT": "#15281e", "TEXT_INPUT": "#d9ebdf", "SCROLL": "#15281e",
        "BUTTON": ("#ffffff", "#1e5c38"), "PROGRESS": ("#2e8a54", "#15281e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 5 dark oranges -----
    "AmberMine": {
        "BACKGROUND": "#231708", "TEXT": "#f0dcc0",
        "INPUT": "#38250e", "TEXT_INPUT": "#f8ead6", "SCROLL": "#38250e",
        "BUTTON": ("#231708", "#e69422"), "PROGRESS": ("#e69422", "#38250e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BurntSienna": {
        "BACKGROUND": "#201007", "TEXT": "#ecd5c2",
        "INPUT": "#331b0e", "TEXT_INPUT": "#f5e5d6", "SCROLL": "#331b0e",
        "BUTTON": ("#ffffff", "#a8501e"), "PROGRESS": ("#d97633", "#331b0e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CopperKettle": {
        "BACKGROUND": "#1c120a", "TEXT": "#e8d2ba",
        "INPUT": "#2e1f12", "TEXT_INPUT": "#f2e3d0", "SCROLL": "#2e1f12",
        "BUTTON": ("#f2e3d0", "#8f5a24"), "PROGRESS": ("#c98338", "#2e1f12"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PumpkinCellar": {
        "BACKGROUND": "#241206", "TEXT": "#f2d8bc",
        "INPUT": "#3a1e0a", "TEXT_INPUT": "#f9e8d2", "SCROLL": "#3a1e0a",
        "BUTTON": ("#241206", "#f28c28"), "PROGRESS": ("#f28c28", "#3a1e0a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RustHearth": {
        "BACKGROUND": "#1e0e08", "TEXT": "#e9d0c4",
        "INPUT": "#321911", "TEXT_INPUT": "#f3e1d7", "SCROLL": "#321911",
        "BUTTON": ("#ffffff", "#b34a1e"), "PROGRESS": ("#e06a2e", "#321911"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 20 dark themes with slightly muted accents, good button contrast -----
    "DenimFade": {
        "BACKGROUND": "#131a24", "TEXT": "#ccd6e2",
        "INPUT": "#1f2a38", "TEXT_INPUT": "#e0e8f0", "SCROLL": "#1f2a38",
        "BUTTON": ("#ffffff", "#3e5c80"), "PROGRESS": ("#5b80a8", "#1f2a38"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "StormGlass": {
        "BACKGROUND": "#141a1e", "TEXT": "#c8d4da",
        "INPUT": "#212a30", "TEXT_INPUT": "#dde6eb", "SCROLL": "#212a30",
        "BUTTON": ("#141a1e", "#7396a8"), "PROGRESS": ("#7396a8", "#212a30"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CadetHour": {
        "BACKGROUND": "#101a1c", "TEXT": "#c4d6d8",
        "INPUT": "#1b2a2d", "TEXT_INPUT": "#dbe9ea", "SCROLL": "#1b2a2d",
        "BUTTON": ("#ffffff", "#38666b"), "PROGRESS": ("#549298", "#1b2a2d"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SeafoamShade": {
        "BACKGROUND": "#0f1c18", "TEXT": "#c6dcd4",
        "INPUT": "#1a2e27", "TEXT_INPUT": "#dcece6", "SCROLL": "#1a2e27",
        "BUTTON": ("#0f1c18", "#6bb39a"), "PROGRESS": ("#6bb39a", "#1a2e27"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SageBrush": {
        "BACKGROUND": "#161a13", "TEXT": "#d2d8c8",
        "INPUT": "#242a1f", "TEXT_INPUT": "#e3e8db", "SCROLL": "#242a1f",
        "BUTTON": ("#161a13", "#8ba173"), "PROGRESS": ("#8ba173", "#242a1f"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "JuniperSmoke": {
        "BACKGROUND": "#121c16", "TEXT": "#c8d8cd",
        "INPUT": "#1e2e24", "TEXT_INPUT": "#dceae1", "SCROLL": "#1e2e24",
        "BUTTON": ("#ffffff", "#3c6b4f"), "PROGRESS": ("#5c9376", "#1e2e24"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MossVelvet": {
        "BACKGROUND": "#151a0f", "TEXT": "#d3d9c4",
        "INPUT": "#232b1a", "TEXT_INPUT": "#e4e9d8", "SCROLL": "#232b1a",
        "BUTTON": ("#e4e9d8", "#55662e"), "PROGRESS": ("#7c9445", "#232b1a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MustardCask": {
        "BACKGROUND": "#1c1810", "TEXT": "#e0d6bc",
        "INPUT": "#2d271a", "TEXT_INPUT": "#ede5d2", "SCROLL": "#2d271a",
        "BUTTON": ("#1c1810", "#c2a24a"), "PROGRESS": ("#c2a24a", "#2d271a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "OchreDusk": {
        "BACKGROUND": "#1d150c", "TEXT": "#e2d4be",
        "INPUT": "#2f2315", "TEXT_INPUT": "#eee3d2", "SCROLL": "#2f2315",
        "BUTTON": ("#ffffff", "#8f6a2e"), "PROGRESS": ("#bc9142", "#2f2315"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "TerracottaKiln": {
        "BACKGROUND": "#1d120d", "TEXT": "#e4d0c4",
        "INPUT": "#2f1f16", "TEXT_INPUT": "#f0e1d7", "SCROLL": "#2f1f16",
        "BUTTON": ("#ffffff", "#9c5138"), "PROGRESS": ("#c47355", "#2f1f16"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ClayHearth": {
        "BACKGROUND": "#1a1210", "TEXT": "#ddccc4",
        "INPUT": "#2b1f1a", "TEXT_INPUT": "#ebdfd8", "SCROLL": "#2b1f1a",
        "BUTTON": ("#1a1210", "#b3785e"), "PROGRESS": ("#b3785e", "#2b1f1a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SalmonAsh": {
        "BACKGROUND": "#1c1414", "TEXT": "#e2d0ce",
        "INPUT": "#2d2120", "TEXT_INPUT": "#efe1df", "SCROLL": "#2d2120",
        "BUTTON": ("#1c1414", "#c98a80"), "PROGRESS": ("#c98a80", "#2d2120"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RosewoodDim": {
        "BACKGROUND": "#1b1114", "TEXT": "#dfcdd2",
        "INPUT": "#2c1d21", "TEXT_INPUT": "#ecdfe3", "SCROLL": "#2c1d21",
        "BUTTON": ("#ffffff", "#8a4256"), "PROGRESS": ("#b3647a", "#2c1d21"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MulberryDusk": {
        "BACKGROUND": "#190f1a", "TEXT": "#dccbde",
        "INPUT": "#2a1c2c", "TEXT_INPUT": "#eadfec", "SCROLL": "#2a1c2c",
        "BUTTON": ("#ffffff", "#77406e"), "PROGRESS": ("#a05e95", "#2a1c2c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "HeatherField": {
        "BACKGROUND": "#161320", "TEXT": "#d4cfe2",
        "INPUT": "#252033", "TEXT_INPUT": "#e5e1f0", "SCROLL": "#252033",
        "BUTTON": ("#161320", "#9a8fc2"), "PROGRESS": ("#9a8fc2", "#252033"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PeriwinkleNight": {
        "BACKGROUND": "#131522", "TEXT": "#ced3e8",
        "INPUT": "#202438", "TEXT_INPUT": "#e0e4f2", "SCROLL": "#202438",
        "BUTTON": ("#ffffff", "#4d5a99"), "PROGRESS": ("#7383c2", "#202438"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SlateBlueEve": {
        "BACKGROUND": "#12161f", "TEXT": "#cbd3de",
        "INPUT": "#1e2531", "TEXT_INPUT": "#dee5ed", "SCROLL": "#1e2531",
        "BUTTON": ("#dee5ed", "#42536e"), "PROGRESS": ("#66799a", "#1e2531"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "TaupeCellar": {
        "BACKGROUND": "#181410", "TEXT": "#dcd2c6",
        "INPUT": "#28211a", "TEXT_INPUT": "#eae2d8", "SCROLL": "#28211a",
        "BUTTON": ("#eae2d8", "#6e5c48"), "PROGRESS": ("#96806a", "#28211a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PewterMist": {
        "BACKGROUND": "#15171a", "TEXT": "#d0d4d9",
        "INPUT": "#23262b", "TEXT_INPUT": "#e2e5e9", "SCROLL": "#23262b",
        "BUTTON": ("#15171a", "#9aa4b0"), "PROGRESS": ("#9aa4b0", "#23262b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DoveShadow": {
        "BACKGROUND": "#17161a", "TEXT": "#d5d3da",
        "INPUT": "#26242b", "TEXT_INPUT": "#e5e3ea", "SCROLL": "#26242b",
        "BUTTON": ("#ffffff", "#5c5870"), "PROGRESS": ("#8a85a3", "#26242b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 10 more muted blues -----
    "HarborMist": {
        "BACKGROUND": "#121826", "TEXT": "#cbd5e0",
        "INPUT": "#1e2740", "TEXT_INPUT": "#dfe6ee", "SCROLL": "#1e2740",
        "BUTTON": ("#ffffff", "#40628c"), "PROGRESS": ("#6488b3", "#1e2740"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "FjordNight": {
        "BACKGROUND": "#101726", "TEXT": "#c7d3e0",
        "INPUT": "#1b253c", "TEXT_INPUT": "#dce5ee", "SCROLL": "#1b253c",
        "BUTTON": ("#101726", "#7a9cc0"), "PROGRESS": ("#7a9cc0", "#1b253c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "GlacierDeep": {
        "BACKGROUND": "#111a28", "TEXT": "#c9d7e0",
        "INPUT": "#1c2a40", "TEXT_INPUT": "#dde9ef", "SCROLL": "#1c2a40",
        "BUTTON": ("#dde9ef", "#3a5a6e"), "PROGRESS": ("#5e8aa3", "#1c2a40"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "NavyWool": {
        "BACKGROUND": "#121428", "TEXT": "#ccd0e0",
        "INPUT": "#1e2240", "TEXT_INPUT": "#dfe2ee", "SCROLL": "#1e2240",
        "BUTTON": ("#ffffff", "#3d4a7a"), "PROGRESS": ("#5f6ea3", "#1e2240"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BlueSpruce": {
        "BACKGROUND": "#101a22", "TEXT": "#c6d6d6",
        "INPUT": "#1b2b38", "TEXT_INPUT": "#dbe9e9", "SCROLL": "#1b2b38",
        "BUTTON": ("#101a22", "#6ba0a8"), "PROGRESS": ("#6ba0a8", "#1b2b38"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CornflowerDusk": {
        "BACKGROUND": "#14182e", "TEXT": "#cfd4e6",
        "INPUT": "#212748", "TEXT_INPUT": "#e1e5f2", "SCROLL": "#212748",
        "BUTTON": ("#14182e", "#8194cc"), "PROGRESS": ("#8194cc", "#212748"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SteelTwilight": {
        "BACKGROUND": "#131724", "TEXT": "#ccd3da",
        "INPUT": "#20263a", "TEXT_INPUT": "#dfe4ea", "SCROLL": "#20263a",
        "BUTTON": ("#ffffff", "#4a6075"), "PROGRESS": ("#70889e", "#20263a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "MarineLayer": {
        "BACKGROUND": "#0f1a2a", "TEXT": "#c5d5e0",
        "INPUT": "#1a2b44", "TEXT_INPUT": "#dbe8ef", "SCROLL": "#1a2b44",
        "BUTTON": ("#dbe8ef", "#2e556e"), "PROGRESS": ("#4d80a0", "#1a2b44"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "InkwellBlue": {
        "BACKGROUND": "#14172c", "TEXT": "#ced2e4",
        "INPUT": "#212544", "TEXT_INPUT": "#e0e3f0", "SCROLL": "#212544",
        "BUTTON": ("#ffffff", "#4a4f8f"), "PROGRESS": ("#7278b8", "#212544"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DuskHorizon": {
        "BACKGROUND": "#121a2c", "TEXT": "#cad6e2",
        "INPUT": "#1e2a46", "TEXT_INPUT": "#dee8f0", "SCROLL": "#1e2a46",
        "BUTTON": ("#121a2c", "#93aec4"), "PROGRESS": ("#93aec4", "#1e2a46"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 10 more muted greens -----
    "FernHollow": {
        "BACKGROUND": "#10200f", "TEXT": "#cbdacd",
        "INPUT": "#1c331a", "TEXT_INPUT": "#deece0", "SCROLL": "#1c331a",
        "BUTTON": ("#ffffff", "#446e50"), "PROGRESS": ("#699678", "#1c331a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "LichenStone": {
        "BACKGROUND": "#141e10", "TEXT": "#d0d7ca",
        "INPUT": "#22321c", "TEXT_INPUT": "#e1e7dc", "SCROLL": "#22321c",
        "BUTTON": ("#141e10", "#93a883"), "PROGRESS": ("#93a883", "#22321c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "EucalyptusNight": {
        "BACKGROUND": "#0f2016", "TEXT": "#c8d8d0",
        "INPUT": "#1a3424", "TEXT_INPUT": "#dcebe3", "SCROLL": "#1a3424",
        "BUTTON": ("#0f2016", "#7aa891"), "PROGRESS": ("#7aa891", "#1a3424"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "IvyWall": {
        "BACKGROUND": "#0e1e06", "TEXT": "#ccd8c0",
        "INPUT": "#19300e", "TEXT_INPUT": "#deead4", "SCROLL": "#19300e",
        "BUTTON": ("#ffffff", "#4a662a"), "PROGRESS": ("#6f9142", "#19300e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "SeagrassBed": {
        "BACKGROUND": "#0d2013", "TEXT": "#c6d8cf",
        "INPUT": "#173420", "TEXT_INPUT": "#daebe2", "SCROLL": "#173420",
        "BUTTON": ("#daebe2", "#2e5c46"), "PROGRESS": ("#4d8a6c", "#173420"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "WillowShade": {
        "BACKGROUND": "#12200c", "TEXT": "#cfd8c4",
        "INPUT": "#1f3416", "TEXT_INPUT": "#e0e8d7", "SCROLL": "#1f3416",
        "BUTTON": ("#12200c", "#a0b585"), "PROGRESS": ("#a0b585", "#1f3416"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "ThymeGarden": {
        "BACKGROUND": "#112012", "TEXT": "#ccd8ce",
        "INPUT": "#1d331e", "TEXT_INPUT": "#dfe9e0", "SCROLL": "#1d331e",
        "BUTTON": ("#ffffff", "#527a5c"), "PROGRESS": ("#77a283", "#1d331e"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "VerdigrisPatina": {
        "BACKGROUND": "#0e2018", "TEXT": "#c7d8d4",
        "INPUT": "#183428", "TEXT_INPUT": "#dbeae7", "SCROLL": "#183428",
        "BUTTON": ("#dbeae7", "#2f6157"), "PROGRESS": ("#4f8e82", "#183428"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BasilNight": {
        "BACKGROUND": "#0e1f0a", "TEXT": "#c9d8c5",
        "INPUT": "#183212", "TEXT_INPUT": "#dcead8", "SCROLL": "#183212",
        "BUTTON": ("#ffffff", "#3f6e3a"), "PROGRESS": ("#639659", "#183212"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CelladonVault": {
        "BACKGROUND": "#112014", "TEXT": "#ccdad1",
        "INPUT": "#1d3421", "TEXT_INPUT": "#dfebe4", "SCROLL": "#1d3421",
        "BUTTON": ("#112014", "#8fb8a0"), "PROGRESS": ("#8fb8a0", "#1d3421"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 25 high-contrast accent-on-colored-background (RichRedForest style) -----
    # 5 green accents
    "GreenOnNavy": {
        "BACKGROUND": "#0d1530", "TEXT": "#d6dcf0",
        "INPUT": "#182348", "TEXT_INPUT": "#eaeefa", "SCROLL": "#182348",
        "BUTTON": ("#ffffff", "#1e8a4d"), "PROGRESS": ("#2ebd6e", "#182348"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "GreenOnPlum": {
        "BACKGROUND": "#241031", "TEXT": "#e2d4ec",
        "INPUT": "#371a4a", "TEXT_INPUT": "#f0e7f7", "SCROLL": "#371a4a",
        "BUTTON": ("#ffffff", "#1f9455"), "PROGRESS": ("#2fc975", "#371a4a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "GreenOnCharcoal": {
        "BACKGROUND": "#1c1e22", "TEXT": "#dcdee2",
        "INPUT": "#2b2e34", "TEXT_INPUT": "#eceef1", "SCROLL": "#2b2e34",
        "BUTTON": ("#ffffff", "#1d7a45"), "PROGRESS": ("#2aa860", "#2b2e34"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "GreenOnUmber": {
        "BACKGROUND": "#2a1a0e", "TEXT": "#ecd9c2",
        "INPUT": "#402917", "TEXT_INPUT": "#f6e9d8", "SCROLL": "#402917",
        "BUTTON": ("#ffffff", "#2a8a3e"), "PROGRESS": ("#3cba57", "#402917"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "GreenOnMaroon": {
        "BACKGROUND": "#2e0d16", "TEXT": "#ead2d8",
        "INPUT": "#451523", "TEXT_INPUT": "#f4e3e8", "SCROLL": "#451523",
        "BUTTON": ("#ffffff", "#1f8f5c"), "PROGRESS": ("#2ec27e", "#451523"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # 5 blue accents
    "BlueOnForest": {
        "BACKGROUND": "#0e2416", "TEXT": "#cfe4d3",
        "INPUT": "#173822", "TEXT_INPUT": "#e3f2e7", "SCROLL": "#173822",
        "BUTTON": ("#ffffff", "#1d5fb8"), "PROGRESS": ("#3585e8", "#173822"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BlueOnPlum": {
        "BACKGROUND": "#241031", "TEXT": "#e2d4ec",
        "INPUT": "#371a4a", "TEXT_INPUT": "#f0e7f7", "SCROLL": "#371a4a",
        "BUTTON": ("#ffffff", "#2361c2"), "PROGRESS": ("#4188ee", "#371a4a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BlueOnCharcoal": {
        "BACKGROUND": "#1c1e22", "TEXT": "#dcdee2",
        "INPUT": "#2b2e34", "TEXT_INPUT": "#eceef1", "SCROLL": "#2b2e34",
        "BUTTON": ("#ffffff", "#1d5aa8"), "PROGRESS": ("#3a80d6", "#2b2e34"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BlueOnUmber": {
        "BACKGROUND": "#2a1a0e", "TEXT": "#ecd9c2",
        "INPUT": "#402917", "TEXT_INPUT": "#f6e9d8", "SCROLL": "#402917",
        "BUTTON": ("#ffffff", "#2465b0"), "PROGRESS": ("#428ade", "#402917"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BlueOnWine": {
        "BACKGROUND": "#2e0d1a", "TEXT": "#ead2da",
        "INPUT": "#451528", "TEXT_INPUT": "#f4e3ea", "SCROLL": "#451528",
        "BUTTON": ("#ffffff", "#1f63bd"), "PROGRESS": ("#3d89e8", "#451528"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # 5 brown accents
    "BrownOnNavy": {
        "BACKGROUND": "#0d1530", "TEXT": "#d6dcf0",
        "INPUT": "#182348", "TEXT_INPUT": "#eaeefa", "SCROLL": "#182348",
        "BUTTON": ("#f5e8d8", "#7a4a22"), "PROGRESS": ("#a86c38", "#182348"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BrownOnForest": {
        "BACKGROUND": "#0e2416", "TEXT": "#cfe4d3",
        "INPUT": "#173822", "TEXT_INPUT": "#e3f2e7", "SCROLL": "#173822",
        "BUTTON": ("#f5e8d8", "#80522a"), "PROGRESS": ("#ad7442", "#173822"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BrownOnCharcoal": {
        "BACKGROUND": "#1c1e22", "TEXT": "#dcdee2",
        "INPUT": "#2b2e34", "TEXT_INPUT": "#eceef1", "SCROLL": "#2b2e34",
        "BUTTON": ("#f5e8d8", "#754924"), "PROGRESS": ("#a06a3a", "#2b2e34"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BrownOnPlum": {
        "BACKGROUND": "#241031", "TEXT": "#e2d4ec",
        "INPUT": "#371a4a", "TEXT_INPUT": "#f0e7f7", "SCROLL": "#371a4a",
        "BUTTON": ("#f5e8d8", "#7d4e26"), "PROGRESS": ("#aa703e", "#371a4a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "BrownOnSlate": {
        "BACKGROUND": "#12161f", "TEXT": "#cbd3de",
        "INPUT": "#1e2531", "TEXT_INPUT": "#dee5ed", "SCROLL": "#1e2531",
        "BUTTON": ("#f5e8d8", "#7a4c28"), "PROGRESS": ("#a86e40", "#1e2531"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # 5 muted orange accents
    "OrangeOnNavy": {
        "BACKGROUND": "#0d1530", "TEXT": "#d6dcf0",
        "INPUT": "#182348", "TEXT_INPUT": "#eaeefa", "SCROLL": "#182348",
        "BUTTON": ("#241206", "#c4802e"), "PROGRESS": ("#dc9840", "#182348"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "OrangeOnForest": {
        "BACKGROUND": "#0e2416", "TEXT": "#cfe4d3",
        "INPUT": "#173822", "TEXT_INPUT": "#e3f2e7", "SCROLL": "#173822",
        "BUTTON": ("#241206", "#c07a2a"), "PROGRESS": ("#d8923c", "#173822"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "OrangeOnPlum": {
        "BACKGROUND": "#241031", "TEXT": "#e2d4ec",
        "INPUT": "#371a4a", "TEXT_INPUT": "#f0e7f7", "SCROLL": "#371a4a",
        "BUTTON": ("#241206", "#c8842f"), "PROGRESS": ("#e09c42", "#371a4a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "OrangeOnCharcoal": {
        "BACKGROUND": "#1c1e22", "TEXT": "#dcdee2",
        "INPUT": "#2b2e34", "TEXT_INPUT": "#eceef1", "SCROLL": "#2b2e34",
        "BUTTON": ("#241206", "#bd7c2c"), "PROGRESS": ("#d4943e", "#2b2e34"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "OrangeOnTealDeep": {
        "BACKGROUND": "#0a2024", "TEXT": "#cde2e6",
        "INPUT": "#123338", "TEXT_INPUT": "#e0f0f2", "SCROLL": "#123338",
        "BUTTON": ("#241206", "#c4802e"), "PROGRESS": ("#dc9840", "#123338"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # 5 muted yellow accents
    "YellowOnNavy": {
        "BACKGROUND": "#0d1530", "TEXT": "#d6dcf0",
        "INPUT": "#182348", "TEXT_INPUT": "#eaeefa", "SCROLL": "#182348",
        "BUTTON": ("#1c1608", "#c2a83a"), "PROGRESS": ("#dcc050", "#182348"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "YellowOnForest": {
        "BACKGROUND": "#0e2416", "TEXT": "#cfe4d3",
        "INPUT": "#173822", "TEXT_INPUT": "#e3f2e7", "SCROLL": "#173822",
        "BUTTON": ("#1c1608", "#bda438"), "PROGRESS": ("#d6bc4e", "#173822"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "YellowOnPlum": {
        "BACKGROUND": "#241031", "TEXT": "#e2d4ec",
        "INPUT": "#371a4a", "TEXT_INPUT": "#f0e7f7", "SCROLL": "#371a4a",
        "BUTTON": ("#1c1608", "#c6ac3d"), "PROGRESS": ("#e0c454", "#371a4a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "YellowOnCharcoal": {
        "BACKGROUND": "#1c1e22", "TEXT": "#dcdee2",
        "INPUT": "#2b2e34", "TEXT_INPUT": "#eceef1", "SCROLL": "#2b2e34",
        "BUTTON": ("#1c1608", "#baa236"), "PROGRESS": ("#d2ba4c", "#2b2e34"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "YellowOnMaroon": {
        "BACKGROUND": "#2e0d16", "TEXT": "#ead2d8",
        "INPUT": "#451523", "TEXT_INPUT": "#f4e3e8", "SCROLL": "#451523",
        "BUTTON": ("#1c1608", "#c2a83a"), "PROGRESS": ("#dcc050", "#451523"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 10 themes inspired by award-winning / popular designer palettes -----
    "ZincLayer": {          # zinc near-black with layered surfaces (modern SaaS dark mode)
        "BACKGROUND": "#09090b", "TEXT": "#d4d4d8",
        "INPUT": "#18181b", "TEXT_INPUT": "#e4e4e7", "SCROLL": "#27272a",
        "BUTTON": ("#ffffff", "#3f3f46"), "PROGRESS": ("#60a5fa", "#18181b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "TokyoDusk": {          # deep navy with soft blue/purple, Tokyo Night style
        "BACKGROUND": "#1a1b26", "TEXT": "#c0caf5",
        "INPUT": "#24283b", "TEXT_INPUT": "#d5ddf8", "SCROLL": "#24283b",
        "BUTTON": ("#1a1b26", "#7aa2f7"), "PROGRESS": ("#bb9af7", "#24283b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PastelMocha": {        # warm dark base with soothing pastel accents, Catppuccin style
        "BACKGROUND": "#1e1e2e", "TEXT": "#cdd6f4",
        "INPUT": "#313244", "TEXT_INPUT": "#dee4f8", "SCROLL": "#313244",
        "BUTTON": ("#1e1e2e", "#cba6f7"), "PROGRESS": ("#f5c2a7", "#313244"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "PolarFrost": {         # cool arctic blue-grays with frost accent, Nord style
        "BACKGROUND": "#242933", "TEXT": "#d8dee9",
        "INPUT": "#2e3440", "TEXT_INPUT": "#e5e9f0", "SCROLL": "#2e3440",
        "BUTTON": ("#242933", "#88c0d0"), "PROGRESS": ("#81a1c1", "#2e3440"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "VampirePlum": {        # gray-purple base with vivid purple, Dracula style
        "BACKGROUND": "#22232e", "TEXT": "#e6e6f0",
        "INPUT": "#33354a", "TEXT_INPUT": "#f1f1f8", "SCROLL": "#33354a",
        "BUTTON": ("#f8f8f2", "#6d4fa4"), "PROGRESS": ("#b085f5", "#33354a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "EarthenHearth": {      # warm earthy browns with amber/orange, Gruvbox style
        "BACKGROUND": "#24211c", "TEXT": "#e0d6b8",
        "INPUT": "#37322a", "TEXT_INPUT": "#ece4ce", "SCROLL": "#37322a",
        "BUTTON": ("#24211c", "#d6913d"), "PROGRESS": ("#c9b458", "#37322a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "DimmedRepo": {         # blue-gray dimmed surfaces, GitHub Dark Dimmed style
        "BACKGROUND": "#22272e", "TEXT": "#c9d1d9",
        "INPUT": "#2d333b", "TEXT_INPUT": "#dbe2e9", "SCROLL": "#2d333b",
        "BUTTON": ("#ffffff", "#3d6a9e"), "PROGRESS": ("#5c9bd6", "#2d333b"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "RosePetalNight": {     # muted purple-black with rose and gold, Rose Pine style
        "BACKGROUND": "#191724", "TEXT": "#e0def4",
        "INPUT": "#26233a", "TEXT_INPUT": "#ebe9f8", "SCROLL": "#26233a",
        "BUTTON": ("#191724", "#d68fa8"), "PROGRESS": ("#e0b874", "#26233a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CinemaNeon": {         # rich black with controlled neon accents (streaming-platform style)
        "BACKGROUND": "#0b0b10", "TEXT": "#d8d8e2",
        "INPUT": "#17171f", "TEXT_INPUT": "#e8e8f0", "SCROLL": "#17171f",
        "BUTTON": ("#0b0b10", "#00d4e8"), "PROGRESS": ("#e838a8", "#17171f"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "TransformTeal": {      # deep neutral with 2026 trend teal accent
        "BACKGROUND": "#0e1414", "TEXT": "#cbdcda",
        "INPUT": "#1a2424", "TEXT_INPUT": "#deecea", "SCROLL": "#1a2424",
        "BUTTON": ("#ffffff", "#0e7a70"), "PROGRESS": ("#18a89a", "#1a2424"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    # ----- 10 CarbonAmber variants with progressively dimmer ambers -----
    "CarbonHoney": {
        "BACKGROUND": "#121212", "TEXT": "#e0dcd2",
        "INPUT": "#1f1f1f", "TEXT_INPUT": "#f0ede6", "SCROLL": "#1f1f1f",
        "BUTTON": ("#121212", "#e8a520"), "PROGRESS": ("#e8a520", "#1f1f1f"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonOchre": {
        "BACKGROUND": "#121212", "TEXT": "#dfdacf",
        "INPUT": "#1f1f1f", "TEXT_INPUT": "#efece4", "SCROLL": "#1f1f1f",
        "BUTTON": ("#121212", "#d49628"), "PROGRESS": ("#d49628", "#1f1f1f"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonCaramel": {
        "BACKGROUND": "#131211", "TEXT": "#ded8cc",
        "INPUT": "#201e1c", "TEXT_INPUT": "#eeebe2", "SCROLL": "#201e1c",
        "BUTTON": ("#131211", "#c28a30"), "PROGRESS": ("#c28a30", "#201e1c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonBronze": {
        "BACKGROUND": "#131211", "TEXT": "#dcd5c8",
        "INPUT": "#201e1c", "TEXT_INPUT": "#ece8de", "SCROLL": "#201e1c",
        "BUTTON": ("#131211", "#b07d2e"), "PROGRESS": ("#b07d2e", "#201e1c"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonCider": {
        "BACKGROUND": "#141210", "TEXT": "#dad3c5",
        "INPUT": "#211e1a", "TEXT_INPUT": "#eae6db", "SCROLL": "#211e1a",
        "BUTTON": ("#141210", "#a8742a"), "PROGRESS": ("#a8742a", "#211e1a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonToffee": {
        "BACKGROUND": "#141210", "TEXT": "#d8d0c2",
        "INPUT": "#211e1a", "TEXT_INPUT": "#e8e4d8", "SCROLL": "#211e1a",
        "BUTTON": ("#f5ecd8", "#9a6a2c"), "PROGRESS": ("#9a6a2c", "#211e1a"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonBurntAmber": {
        "BACKGROUND": "#131110", "TEXT": "#d6cec0",
        "INPUT": "#201d19", "TEXT_INPUT": "#e6e2d6", "SCROLL": "#201d19",
        "BUTTON": ("#f5ecd8", "#8f5f24"), "PROGRESS": ("#8f5f24", "#201d19"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonRustAmber": {
        "BACKGROUND": "#131110", "TEXT": "#d5ccbe",
        "INPUT": "#201d19", "TEXT_INPUT": "#e5e0d4", "SCROLL": "#201d19",
        "BUTTON": ("#f5ecd8", "#855426"), "PROGRESS": ("#855426", "#201d19"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonAntiqueGold": {
        "BACKGROUND": "#121110", "TEXT": "#d3cabb",
        "INPUT": "#1f1c18", "TEXT_INPUT": "#e3ded2", "SCROLL": "#1f1c18",
        "BUTTON": ("#f5ecd8", "#7a5220"), "PROGRESS": ("#7a5220", "#1f1c18"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
    "CarbonMolasses": {
        "BACKGROUND": "#121110", "TEXT": "#d0c7b8",
        "INPUT": "#1f1c18", "TEXT_INPUT": "#e0dbcf", "SCROLL": "#1f1c18",
        "BUTTON": ("#f5ecd8", "#6b4a1e"), "PROGRESS": ("#6b4a1e", "#1f1c18"),
        "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
    },
}

for name, spec in CUSTOM_THEMES.items():
    sg.theme_add_new(name, spec)

# ---------- Key constants ----------
K_GRID = '-GRID-'
K_PROGRESS = '-PROGRESS-'
KT_PROGRESS = lambda name: (K_PROGRESS, name)
K_PREVIEW_BTN = '-PREVIEW BTN-'
KT_PREVIEW_BTN = lambda name: (K_PREVIEW_BTN, name)
K_SCROLL_UP = '-SCROLL UP-'
K_SCROLL_DOWN = '-SCROLL DOWN-'
K_SCROLL_PGUP = '-SCROLL PGUP-'
K_SCROLL_PGDN = '-SCROLL PGDN-'
K_SCROLL_HOME = '-SCROLL HOME-'
K_SCROLL_END = '-SCROLL END-'
K_ESC = '-ESC-'


def theme_tile(name):
    """A near-full-size sample of one theme, colored explicitly so all fit in one window."""
    t = CUSTOM_THEMES[name]
    bg, fg = t["BACKGROUND"], t["TEXT"]
    ib, it = t["INPUT"], t["TEXT_INPUT"]
    btn = t["BUTTON"]
    accent = t["PROGRESS"][0]
    col = [
        [sg.Text(name, background_color=bg, text_color=fg, font=("Segoe UI", 13, "bold"))],
        [sg.Text("Sample text", background_color=bg, text_color=fg), sg.Input("Sample input", size=(18, 1), background_color=ib, text_color=it)],
        [sg.Button("Preview", key=KT_PREVIEW_BTN(name), button_color=btn, size=(10, 1)),
         sg.Checkbox("Checkbox", default=True, background_color=bg, text_color=fg, checkbox_color=ib),
         sg.Radio("Radio", f"R-{name}", default=True, background_color=bg, text_color=fg, circle_color=ib)],
        [sg.Slider(range=(0, 100), default_value=60, orientation="h", size=(28, 12), background_color=bg, text_color=fg, trough_color=ib)],
        [sg.ProgressBar(100, orientation="h", size=(28, 12), bar_color=(accent, ib), key=KT_PROGRESS(name))],
        [sg.Listbox(["List item 1", "List item 2", "List item 3"], size=(30, 3), background_color=ib, text_color=it, no_scrollbar=True)],
    ]
    return sg.Column(col, background_color=bg, pad=(8, 8))


def view_all():
    """All themes in a single window, grid layout (like built-in previewer)."""
    sg.theme("DarkSlate")
    names = list(CUSTOM_THEMES)
    per_row = 5
    rows = [[theme_tile(n) for n in names[i:i + per_row]] for i in range(0, len(names), per_row)]
    layout = [[sg.Text("Click any button to open a full preview of that theme.", font=("Segoe UI", 10))]]
    grid = sg.Column(rows, scrollable=True, vertical_scroll_only=True, size=(1700, 1150), expand_x=True, expand_y=True, key=K_GRID)
    layout += [[grid], [sg.Button("Close")]]
    win = sg.Window("All Dark Themes", layout, finalize=True, resizable=True)
    win.TKroot.resizable(False, True)                                   # lock X, allow Y resizing
    # Repack so the Close row owns the bottom edge and the grid (packed last) gives up space first when the window shrinks
    grid_row, close_row = win[K_GRID].ParentRowFrame, win["Close"].ParentRowFrame
    grid_row.pack_forget(), close_row.pack_forget()
    close_row.pack(side="bottom", fill="x")
    grid_row.pack(side="top", fill="both", expand=True)
    win.bring_to_front(), win.force_focus()
    win.bind("<Up>", K_SCROLL_UP), win.bind("<Down>", K_SCROLL_DOWN), win.bind("<Prior>", K_SCROLL_PGUP), win.bind("<Next>", K_SCROLL_PGDN)
    win.bind("<Home>", K_SCROLL_HOME), win.bind("<End>", K_SCROLL_END), win.bind("<Escape>", K_ESC)
    canvas = win[K_GRID].Widget.canvas
    # The repack breaks PSG's built-in wheel hook, and Enter/Leave rebinding fails because in tk, moving onto a child widget (the tiles) sends <Leave> to the
    # parent frame. So instead catch the wheel at the toplevel and scroll whenever the pointer is anywhere over the grid, tiles included.
    sf = win[K_GRID].Widget
    def wheel_over_grid(ev):
        w = win.TKroot.winfo_containing(ev.x_root, ev.y_root)
        while w is not None and w is not sf:
            w = w.master
        if w is sf:
            canvas.yview_scroll(-1 if ev.delta > 0 else 1, "units")
    win.TKroot.bind("<MouseWheel>", wheel_over_grid, add="+")
    for n in names:
        win[KT_PROGRESS(n)].update(65)
    while True:
        ev, _ = win.read()
        if ev in (sg.WIN_CLOSED, "Close", K_ESC):
            break
        if ev == K_SCROLL_UP:
            canvas.yview_scroll(-1, "units")
        elif ev == K_SCROLL_DOWN:
            canvas.yview_scroll(1, "units")
        elif ev == K_SCROLL_PGUP:
            canvas.yview_scroll(-1, "pages")
        elif ev == K_SCROLL_PGDN:
            canvas.yview_scroll(1, "pages")
        elif ev == K_SCROLL_HOME:
            canvas.yview_moveto(0.0)
        elif ev == K_SCROLL_END:
            canvas.yview_moveto(1.0)
        if isinstance(ev, tuple) and ev[0] == K_PREVIEW_BTN:
            win.hide()
            sample_window(ev[1])
            win.un_hide()
    win.close()


def theme_dict_code(theme_name):
    """Format the theme spec as a snake_case variable assignment, ready to paste."""
    var = re.sub(r"(?<!^)(?=[A-Z])", "_", theme_name).lower()
    t = CUSTOM_THEMES[theme_name]
    body = " ".join(f'"{k}": {v!r},' for k, v in t.items())
    lines = [f"{var} = {{{body}}}", "", f"sg.theme_add_new('{theme_name}', {var})", f"sg.theme('{theme_name}')"]
    return "\n".join(lines)


def sample_window(theme_name):
    """Full interactive demo window in the chosen theme."""
    sg.theme(theme_name)
    layout = [
        [sg.Text(f"Theme: {theme_name}", font=("Segoe UI", 14, "bold"))],
        [sg.Text("Sample text"), sg.Input("Sample input", size=(20, 1))],
        [sg.Combo(["Option A", "Option B"], default_value="Option A", size=(15, 1)), sg.Checkbox("Checkbox", default=True), sg.Radio("Radio", "R1", default=True)],
        [sg.Slider(range=(0, 100), default_value=60, orientation="h", size=(30, 15))],
        [sg.ProgressBar(100, orientation="h", size=(30, 15), key=K_PROGRESS)],
        [sg.Listbox(["List item 1", "List item 2", "List item 3"], size=(30, 3))],
        [sg.Button("OK"), sg.Button("Cancel"), sg.Button("Copy Dict"), sg.Button("Close Preview")],
    ]
    win = sg.Window(f"Preview - {theme_name}", layout, finalize=True)
    win.bring_to_front(), win.force_focus()
    win[K_PROGRESS].update(65)
    while True:
        ev, _ = win.read()
        if ev == "Copy Dict":
            sg.clipboard_set(theme_dict_code(theme_name))
            sg.popup_quick_message("Theme dict copied to clipboard", auto_close_duration=1.5, background_color="#333333", text_color="#ffffff")
        elif ev in (sg.WIN_CLOSED, "Close Preview"):
            break
    win.close()


def main():
    sg.theme("DarkSlate")
    names = list(CUSTOM_THEMES)
    per_row = 5
    btn_rows = [[sg.Button(n, size=(18, 1), button_color=CUSTOM_THEMES[n]["BUTTON"]) for n in names[i:i + per_row]] for i in range(0, len(names), per_row)]
    layout = [[sg.Text("Dark theme chooser", font=("Segoe UI", 12, "bold"))], [sg.Button("View All (one window)", size=(22, 1))], [sg.HorizontalSeparator()]]
    layout += btn_rows
    layout += [[sg.HorizontalSeparator()], [sg.Button("Exit")]]
    win = sg.Window("Dark Theme Chooser", layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT)
    while True:
        ev, _ = win.read()
        if ev in (sg.WIN_CLOSED, "Exit"):
            break
        if ev == "View All (one window)":
            win.hide(); view_all(); win.un_hide()
        elif ev in CUSTOM_THEMES:
            sample_window(ev)

        #------       Standard right click menu stuff      ------#
        if ev == 'Edit Me':
            sg.execute_editor(__file__)
        elif ev == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), location=win.current_location(use_anchor=sg.WIN_ANCHOR_CENTER), location_anchor=sg.WIN_ANCHOR_CENTER, keep_on_top=True, non_blocking=True)
    win.close()


if __name__ == "__main__":
    main()
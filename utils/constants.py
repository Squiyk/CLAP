"""Constants used throughout the CLAP application."""
from typing import Tuple

# Thread allocation constants
DEFAULT_CPU_COUNT = 4
CPU_RESERVATION = 2  # Number of cores to reserve for system

# UI Style constants - Frame styling
FRAME_FG_COLOR_LIGHT = "white"
FRAME_FG_COLOR_DARK = "#2B2B2B"
FRAME_FG_COLOR: Tuple[str, str] = (FRAME_FG_COLOR_LIGHT, FRAME_FG_COLOR_DARK)

FRAME_CORNER_RADIUS = 10
FRAME_BORDER_WIDTH = 1

FRAME_BORDER_COLOR_LIGHT = "#E0E0E0"
FRAME_BORDER_COLOR_DARK = "#404040"
FRAME_BORDER_COLOR: Tuple[str, str] = (FRAME_BORDER_COLOR_LIGHT, FRAME_BORDER_COLOR_DARK)

# UI Style constants - Text/Label styling
LABEL_TEXT_COLOR_LIGHT = "gray10"
LABEL_TEXT_COLOR_DARK = "gray90"
LABEL_TEXT_COLOR: Tuple[str, str] = (LABEL_TEXT_COLOR_LIGHT, LABEL_TEXT_COLOR_DARK)

TOOL_LABEL_FONT_SIZE = 18
TOOL_LABEL_FONT_WEIGHT = "bold"
TOOL_LABEL_FONT_FAMILY = "Proxima Nova"

# UI Style constants - Button styling
RUN_BUTTON_HEIGHT = 45
RUN_BUTTON_FG_COLOR = "#6A5ACD"
RUN_BUTTON_FONT_SIZE = 15
RUN_BUTTON_FONT_WEIGHT = "bold"
RUN_BUTTON_FONT_FAMILY = "Proxima Nova"

SIDEBAR_BUTTON_FG_COLOR = "#0078D7"

# Subprocess timeout constants
PROCESS_TERMINATION_TIMEOUT = 5  # seconds

# Page names
PAGES_WITH_FORM_VALUES = ["registration", "connectome", "roi", "segmentation"]
DEFAULT_PAGE = "home"

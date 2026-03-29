"""Styled widget factory functions for CLAP application."""
import customtkinter as ctk
from typing import Optional, Callable
from utils.constants import (
    FRAME_FG_COLOR,
    FRAME_CORNER_RADIUS,
    FRAME_BORDER_WIDTH,
    FRAME_BORDER_COLOR,
    LABEL_TEXT_COLOR,
    TOOL_LABEL_FONT_SIZE,
    TOOL_LABEL_FONT_WEIGHT,
    TOOL_LABEL_FONT_FAMILY,
    RUN_BUTTON_HEIGHT,
    RUN_BUTTON_FG_COLOR,
    RUN_BUTTON_FONT_SIZE,
    RUN_BUTTON_FONT_WEIGHT,
    RUN_BUTTON_FONT_FAMILY,
)


def create_tool_frame(parent: ctk.CTkBaseClass) -> ctk.CTkFrame:
    """
    Create a standardized tool frame with consistent styling.
    
    This function creates a frame with the standard CLAP tool appearance
    including proper colors, corner radius, and borders that adapt to
    light and dark modes.
    
    Args:
        parent: The parent widget to place this frame in
        
    Returns:
        A configured CTkFrame instance
        
    Example:
        >>> frame = create_tool_frame(parent_widget)
        >>> frame.grid(row=0, column=0, pady=20, padx=20, sticky="ew")
    """
    return ctk.CTkFrame(
        parent,
        fg_color=FRAME_FG_COLOR,
        corner_radius=FRAME_CORNER_RADIUS,
        border_width=FRAME_BORDER_WIDTH,
        border_color=FRAME_BORDER_COLOR
    )


def create_tool_label(
    parent: ctk.CTkBaseClass,
    text: str,
    font_size: int = TOOL_LABEL_FONT_SIZE,
    font_weight: str = TOOL_LABEL_FONT_WEIGHT,
    font_family: str = TOOL_LABEL_FONT_FAMILY
) -> ctk.CTkLabel:
    """
    Create a standardized tool label with consistent styling.
    
    This function creates a label with the standard CLAP tool heading
    appearance including proper font, size, weight, and colors that
    adapt to light and dark modes.
    
    Args:
        parent: The parent widget to place this label in
        text: The text to display in the label
        font_size: Font size in points (default: from constants)
        font_weight: Font weight (e.g., "normal", "bold") (default: from constants)
        font_family: Font family name (default: from constants)
        
    Returns:
        A configured CTkLabel instance
        
    Example:
        >>> label = create_tool_label(frame, "Registration Tool")
        >>> label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
    """
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(family=font_family, size=font_size, weight=font_weight),
        text_color=LABEL_TEXT_COLOR
    )


def create_run_button(
    parent: ctk.CTkBaseClass,
    text: str,
    command: Callable,
    height: int = RUN_BUTTON_HEIGHT,
    fg_color: str = RUN_BUTTON_FG_COLOR,
    font_size: int = RUN_BUTTON_FONT_SIZE,
    font_weight: str = RUN_BUTTON_FONT_WEIGHT,
    font_family: str = RUN_BUTTON_FONT_FAMILY
) -> ctk.CTkButton:
    """
    Create a standardized run button with consistent styling.
    
    This function creates a button with the standard CLAP run button
    appearance including proper height, color, and font styling.
    
    Args:
        parent: The parent widget to place this button in
        text: The text to display on the button (e.g., "RUN REGISTRATION")
        command: The callback function to execute when button is clicked
        height: Button height in pixels (default: from constants)
        fg_color: Foreground/background color (default: from constants)
        font_size: Font size in points (default: from constants)
        font_weight: Font weight (e.g., "normal", "bold") (default: from constants)
        font_family: Font family name (default: from constants)
        
    Returns:
        A configured CTkButton instance
        
    Example:
        >>> button = create_run_button(
        ...     frame, 
        ...     "RUN REGISTRATION",
        ...     command=start_registration
        ... )
        >>> button.grid(row=5, column=0, pady=10, padx=10, sticky="ew")
    """
    return ctk.CTkButton(
        parent,
        text=text,
        height=height,
        fg_color=fg_color,
        font=ctk.CTkFont(family=font_family, size=font_size, weight=font_weight),
        command=command
    )


def create_standard_label(
    parent: ctk.CTkBaseClass,
    text: str,
    font_size: int = 13,
    font_family: str = TOOL_LABEL_FONT_FAMILY
) -> ctk.CTkLabel:
    """
    Create a standard label for form fields and descriptions.
    
    This function creates a label with standard styling for use in
    forms and descriptions throughout the application.
    
    Args:
        parent: The parent widget to place this label in
        text: The text to display in the label
        font_size: Font size in points (default: 13)
        font_family: Font family name (default: from constants)
        
    Returns:
        A configured CTkLabel instance
        
    Example:
        >>> label = create_standard_label(frame, "Output Directory:")
        >>> label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    """
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(family=font_family, size=font_size),
        text_color=LABEL_TEXT_COLOR
    )

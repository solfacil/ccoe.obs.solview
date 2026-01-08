"""
Color utilities for SolView logging.
Provides ANSI color codes and colored formatting for log output.
"""


class LogColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    ORANGE = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"


def get_color_for_level(level: str) -> str:
    """
    Get color code for a log level.
    
    Args:
        level: Log level name (e.g., "INFO", "ERROR", "DEBUG")
        
    Returns:
        ANSI color code string
    """
    colors = {
        "TRACE": LogColors.CYAN,
        "DEBUG": LogColors.BLUE,
        "INFO": LogColors.GREEN,
        "SUCCESS": LogColors.GREEN,
        "WARNING": LogColors.ORANGE,
        "ERROR": LogColors.RED,
        "CRITICAL": LogColors.RED,
    }
    return colors.get(level.upper(), LogColors.RESET)


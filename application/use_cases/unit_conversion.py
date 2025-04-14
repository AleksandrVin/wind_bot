"""
Use cases for unit conversions in the wind sports Telegram bot.
"""

def ms_to_knots(speed_ms: float) -> float:
    """Convert wind speed from m/s to knots"""
    return speed_ms * 1.94384


def knots_to_ms(speed_knots: float) -> float:
    """Convert wind speed from knots to m/s"""
    return speed_knots / 1.94384

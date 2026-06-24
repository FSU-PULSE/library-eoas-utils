"""Unit conversion helpers for plotting and layout."""


def cm2inch(value: float) -> float:
    """Convert centimeters to inches.

    Args:
        value: Length in centimeters.

    Returns:
        Equivalent length in inches.
    """
    return value / 2.54

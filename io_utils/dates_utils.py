"""Calendar helpers for day-of-year conversions used in satellite file naming."""

import numpy as np
from datetime import date, datetime, timedelta


def get_days_from_month(
    month: int, year: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Return zero-based day indices for a month and matching day-of-year values.

    Args:
        month: Month index in ``1..12``.
        year: Calendar year. Defaults to the current year when ``None``.

    Returns:
        A tuple ``(days_of_month, days_of_year)`` of 1-D ``numpy`` integer
        arrays. ``days_of_month`` spans ``0 .. n_days-1`` within the month.
        ``days_of_year`` spans the corresponding 1-based day-of-year indices
        for that month.

    Assumptions:
        Uses the standard Gregorian calendar via ``datetime.date``.
    """
    if year is None:
        year = datetime.now().year

    first_jan = date(year, 1, 1)
    first_month = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    days_of_year = np.arange(
        first_month.toordinal() - first_jan.toordinal() + 1,
        next_month.toordinal() - first_jan.toordinal() + 1,
    )
    days_of_month = np.arange(0, next_month.toordinal() - first_month.toordinal())
    return days_of_month, days_of_year


def get_day_of_year_from_month_and_day(
    month: int, day_of_month: int, year: int | None = None
) -> int:
    """Convert a calendar date to a 1-based day-of-year index.

    Args:
        month: Month index in ``1..12``.
        day_of_month: Day of month in ``1..31`` (validated by ``date``).
        year: Calendar year. Defaults to the current year when ``None``.

    Returns:
        Day of year in ``1..366``.
    """
    if year is None:
        year = datetime.now().year

    first_jan = date(year, 1, 1)
    day_of_year = date(year, month, day_of_month).toordinal() - first_jan.toordinal() + 1
    return day_of_year


def get_month_and_day_of_month_from_day_of_year(
    day_of_year: int, year: int | None = None
) -> tuple[int, int]:
    """Convert a 1-based day-of-year index to month and day of month.

    Args:
        day_of_year: Day of year in ``1..366``.
        year: Calendar year. Defaults to the current year when ``None``.

    Returns:
        Tuple ``(month, day)`` with month in ``1..12``.
    """
    if year is None:
        year = datetime.now().year

    date_jan = date(year, 1, 1)
    curr_date = date_jan + timedelta(days=int(day_of_year) - 1)
    return curr_date.month, curr_date.day

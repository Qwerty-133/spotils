"""Pretty printing time durations."""
import datetime
import re
import typing as t

import arrow
from dateutil.relativedelta import relativedelta

_DURATION_REGEX = re.compile(
    r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
    r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
    r"((?P<hours>\d+?) ?(hours|hour|H|h) ?)?"
    r"((?P<minutes>\d+?) ?(minutes|minute|M|m) ?)?"
    r"((?P<seconds>\d+?) ?(seconds|second|S|s))?"
)


def _stringify_time_unit(value: int, unit: str) -> str:
    """
    Return a string to represent a value and time unit.

    It ensures that it uses the right plural form of the unit.
    >>> _stringify_time_unit(1, "seconds")
    "1 second"
    >>> _stringify_time_unit(24, "hours")
    "24 hours"
    >>> _stringify_time_unit(0, "minutes")
    "less than a minute"
    """
    if unit == "seconds" and value == 0:
        return "0 seconds"
    elif value == 1:
        return f"{value} {unit[:-1]}"
    elif value == 0:
        return f"less than a {unit[:-1]}"
    else:
        return f"{value} {unit}"


def humanize_delta(
    delta: relativedelta, precision: str = "seconds", max_units: int = 1
) -> str:
    """
    Return a human-readable version of the relativedelta.

    precision specifies the smallest unit of time to include
    (e.g. "seconds", "minutes").
    max_units specifies the maximum number of units of time to include
    (e.g. 1 may include days but not hours).
    """
    if max_units <= 0:
        raise ValueError("max_units must be positive")

    units = (
        ("years", delta.years),
        ("months", delta.months),
        ("days", delta.days),
        ("hours", delta.hours),
        ("minutes", delta.minutes),
        ("seconds", delta.seconds),
    )

    # Add the time units that are >0, but stop at accuracy or max_units.
    time_strings = []
    unit_count = 0
    for unit, value in units:
        if value:
            time_strings.append(_stringify_time_unit(value, unit))
            unit_count += 1

        if unit == precision or unit_count >= max_units:
            break

    # Add the 'and' between the last two units, if necessary
    if len(time_strings) > 1:
        time_strings[-1] = f"{time_strings[-2]} and {time_strings[-1]}"
        del time_strings[-2]

    # If nothing has been found, just make the value 0 precision,
    # e.g. `0 days`.
    if not time_strings:
        humanized = _stringify_time_unit(0, precision)
    else:
        humanized = ", ".join(time_strings)

    return humanized


def time_between_now_and(
    datetime_: datetime.datetime,
    precision: str = "seconds",
    max_units: int = 6,
) -> str:
    """
    Return a readable string for the difference now and a datetime.

    Takes a datetime and returns a human-readable string that
    describes how long the difference between the current datetime
    and that datetime is.
    precision specifies the smallest unit of time to include
    (e.g. "seconds", "minutes").
    max_units specifies the maximum number of units of time to include
    (e.g. 1 may include days but not hours).
    """
    now = datetime.datetime.utcnow()
    delta = abs(relativedelta(datetime_, now))

    return humanize_delta(delta, precision, max_units)


def time_since(
    past_datetime: datetime.datetime,
    precision: str = "seconds",
    max_units: int = 6,
) -> str:
    """
    Return a human-readable string for how long ago a datetime was.

    precision specifies the smallest unit of time to include
    (e.g. "seconds", "minutes").
    max_units specifies the maximum number of units of time to include
    (e.g. 1 may include days but not hours).
    """
    return f"{time_between_now_and(past_datetime, precision, max_units)} ago"


def parse_duration_string(duration: str) -> t.Optional[relativedelta]:
    """
    Convert a `duration` string to a relativedelta object.

    The following symbols are supported for each unit of time:
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `M`, `m`, `minute`, `minutes`
    - seconds: `S`, `s`, `second`, `seconds`
    The units need to be provided in descending order of magnitude.
    Return None if the `duration` string cannot be parsed according to
    the symbols above.
    """
    match = _DURATION_REGEX.fullmatch(duration)
    if not match:
        return None

    duration_dict = {
        unit: int(amount)
        for unit, amount in match.groupdict(default=0).items()
    }
    delta = relativedelta(**duration_dict)

    return delta


def relativedelta_to_timedelta(delta: relativedelta) -> datetime.timedelta:
    """Convert a relativedelta object to a timedelta object."""
    utcnow = arrow.utcnow()
    return utcnow + delta - utcnow


def parse_interval(interval: str) -> int:
    """
    Convert `interval` into seconds.

    The following symbols are supported for each unit of time:
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `M`, `m`, `minute`, `minutes`
    - seconds: `S`, `s`, `second`, `seconds`
    The units need to be provided in descending order of magnitude.
    Return None if the `interval` string cannot be parsed according to
    the symbols above.
    """
    relativedelta = parse_duration_string(interval)
    if relativedelta:
        seconds = relativedelta_to_timedelta(relativedelta).total_seconds()
        return int(seconds)
    else:
        raise ValueError(f"Invalid interval: {interval}")

from datetime import datetime
import pandas as pd
from config import Config

_EVENING_CUTOFF = datetime.strptime("6:00 PM", "%I:%M %p")


def _parse_time(t: str) -> datetime:
    return datetime.strptime(t.strip(), "%I:%M %p")


def load_schedule() -> pd.DataFrame:
    return pd.read_csv(Config.DGROUP_SCHEDULE)


def find_schedule(
    age_group: str,
    marital_status: str,
    day: str,
    preferred_time: str,
) -> str:
    """Return a schedule description string, or empty string if not found."""
    df = load_schedule()
    df = df[df["satellite"].str.lower() == Config.CCF_SATELLITE.lower()]
    df = df[df["day"].str.lower() == day.lower()]
    df = df[df["age_group"].str.lower() == age_group.lower()]
    df = df[df["marital_status"].str.lower() == marital_status.lower()]

    if df.empty:
        return ""

    if preferred_time in ("afternoon", "evening"):
        times = df["start_time"].apply(_parse_time)
        if preferred_time == "afternoon":
            df = df[times < _EVENING_CUTOFF]
        else:
            df = df[times >= _EVENING_CUTOFF]

    if df.empty:
        return ""

    row = df.iloc[0]
    return (
        f"The group on {row['day']} for {row['age_group']} ({row['marital_status']}) "
        f"is led by {row['leader']} and runs from {row['start_time']} to {row['end_time']}."
    )

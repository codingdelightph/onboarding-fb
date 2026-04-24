import pandas as pd
from config import Config


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

    row = df.iloc[0]
    return (
        f"The group on {row['day']} for {row['age_group']} ({row['marital_status']}) "
        f"is led by {row['leader']} and runs from {row['start_time']} to {row['end_time']}."
    )

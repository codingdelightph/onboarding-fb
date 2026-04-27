import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_BASE = Path(__file__).parent


class Config:
    PAGE_ACCESS_TOKEN: str = os.getenv("PAGE_ACCESS_TOKEN", "")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "")
    APP_SECRET: str = os.getenv("APP_SECRET", "")
    CCF_SATELLITE: str = os.getenv("CCF_SATELLITE", "Imus")
    PAGE_INBOX_APP_ID: str = os.getenv("PAGE_INBOX_APP_ID", "3374491019519787")

    DGROUP_SCHEDULE: str = str(_BASE / "data" / "imus_dgroup_schedule.csv")
    LIFESTAGE: str = str(_BASE / "data" / "imus_lifestage.csv")
    SCHEDULE_OPTIONS: str = str(_BASE / "data" / "schedule_options.csv")

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    eia_api_key: Optional[str] = os.getenv("EIA_API_KEY")
    default_region: str = os.getenv("DEFAULT_REGION", "Texas")
    data_dir: str = os.getenv("DATA_DIR", "data")


settings = Settings()


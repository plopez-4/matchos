from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class MatchEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0", "1.1"] = "1.1"
    event_id: str = Field(min_length=1, max_length=100)
    match_id: str = Field(min_length=1, max_length=100)
    sequence: int = Field(ge=1)
    period: Literal[1, 2] = 1
    match_second: int = Field(ge=0, le=9000)
    team_id: Literal["home", "away"]
    player_id: str = Field(min_length=1, max_length=100)
    type: Literal["kickoff", "pass", "shot", "goal", "recovery"]
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    source: Literal["synthetic"] = "synthetic"
    possession_id: str | None = Field(default=None, min_length=1, max_length=100)
    end_x: float | None = Field(default=None, ge=0, le=100)
    end_y: float | None = Field(default=None, ge=0, le=100)
    outcome: Literal["complete", "saved", "blocked", "missed", "goal"] | None = None
    related_event_id: str | None = Field(default=None, min_length=1, max_length=100)

class CatchUpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    since_sequence: int = Field(default=0, ge=0)
    audience: Literal["casual", "advanced"] = "casual"

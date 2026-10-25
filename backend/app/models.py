from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class MatchEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0", "1.1", "1.2"] = "1.1"
    event_id: str = Field(min_length=1, max_length=100)
    match_id: str = Field(min_length=1, max_length=100)
    sequence: int = Field(ge=1)
    period: Literal[1, 2] = 1
    match_second: int = Field(ge=0, le=9000)
    team_id: Literal["home", "away"]
    player_id: str = Field(min_length=1, max_length=100)
    type: Literal["kickoff", "pass", "shot", "goal", "recovery", "substitution", "red_card", "half_end", "match_end"]
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    source: Literal["synthetic"] = "synthetic"
    possession_id: str | None = Field(default=None, min_length=1, max_length=100)
    end_x: float | None = Field(default=None, ge=0, le=100)
    end_y: float | None = Field(default=None, ge=0, le=100)
    outcome: Literal["complete", "intercepted", "saved", "blocked", "missed", "goal"] | None = None
    related_event_id: str | None = Field(default=None, min_length=1, max_length=100)
    team_name: str | None = Field(default=None, min_length=1, max_length=100)
    player_name: str | None = Field(default=None, min_length=1, max_length=100)
    recipient_player_id: str | None = Field(default=None, min_length=1, max_length=100)
    recipient_player_name: str | None = Field(default=None, min_length=1, max_length=100)
    player_shirt_number: int | None = Field(default=None, ge=1, le=99)
    recipient_player_shirt_number: int | None = Field(default=None, ge=1, le=99)
    player_position: Literal['GK', 'DEF', 'MID', 'FWD'] | None = None
    recipient_player_position: Literal['GK', 'DEF', 'MID', 'FWD'] | None = None
    roster_version: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_full_feed(self):
        if self.schema_version == "1.2" and self.type == "pass":
            if self.end_x is None or self.end_y is None or not self.recipient_player_id:
                raise ValueError("Full-feed passes require destination coordinates and recipient")
            if self.recipient_player_id == self.player_id:
                raise ValueError("A player cannot pass to themselves")
            if not self.recipient_player_id.startswith(self.team_id + "-"):
                raise ValueError("The intended pass recipient must be on the same team")
            if self.outcome not in ("complete", "intercepted"):
                raise ValueError("Full-feed passes require a complete or intercepted outcome")
        return self

class CatchUpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    since_sequence: int = Field(default=0, ge=0)
    audience: Literal["casual", "advanced"] = "casual"

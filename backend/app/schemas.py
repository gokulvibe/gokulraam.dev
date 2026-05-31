from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TilAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    stored_path: str
    mime_type: str
    size_bytes: int


class TilPostBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body_md: str = ""
    tags: list[str] = Field(default_factory=list)
    draft: bool = False


class TilPostCreate(TilPostBase):
    pass


class TilPostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    body_md: str | None = None
    tags: list[str] | None = None
    draft: bool | None = None


class TilPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    body_md: str
    body_html: str = ""
    tags: list[str]
    draft: bool
    created_at: datetime
    updated_at: datetime
    attachments: list[TilAttachmentOut] = []


class LoginIn(BaseModel):
    username: str
    password: str


class StatsOut(BaseModel):
    path: str
    views: int


class NowItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    label: str
    value: str
    order: int
    updated_at: datetime


class NowItemUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=500)


class UsesItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    slug: str
    name: str
    note: str
    order: int
    updated_at: datetime


class UsesItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=300)


class BadmintonPlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    country: str
    flag: str
    discipline: str
    next_event: str
    order: int
    updated_at: datetime


class BadmintonPlayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    country: str | None = Field(default=None, min_length=1, max_length=8)
    flag: str | None = Field(default=None, max_length=8)
    discipline: str | None = Field(default=None, max_length=40)
    next_event: str | None = Field(default=None, max_length=120)


class BadmintonTournamentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    dates: str
    location: str
    tier: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    source_url: str = ""
    order: int
    updated_at: datetime


class BadmintonTournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    dates: str | None = Field(default=None, max_length=60)
    location: str | None = Field(default=None, max_length=80)
    tier: str | None = Field(default=None, max_length=40)


class BadmintonMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    tournament_id: int
    opponent: str
    round: str
    scheduled_at: datetime | None = None
    status: str
    score: str
    updated_at: datetime


# ─── Work / Projects ──────────────────────────────────────────


class WorkRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    section: str
    title: str
    organization: str
    location: str
    dates: str
    bullets: str
    stack: str
    link: str
    order: int


class WorkRoleUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    organization: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=80)
    dates: str | None = Field(default=None, max_length=60)
    bullets: str | None = None
    stack: str | None = Field(default=None, max_length=400)
    link: str | None = Field(default=None, max_length=300)


class WorkAwardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    title: str
    year: str
    organization: str
    description: str
    order: int


class WorkAwardUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    year: str | None = Field(default=None, max_length=20)
    organization: str | None = Field(default=None, max_length=120)
    description: str | None = None


class WorkCertificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    issuer: str
    order: int


class WorkCertificationUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    issuer: str | None = Field(default=None, max_length=120)


class WorkEducationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    school: str
    degree: str
    gpa: str
    dates: str
    coursework: str
    note: str
    order: int


class WorkEducationUpdate(BaseModel):
    school: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=200)
    gpa: str | None = Field(default=None, max_length=20)
    dates: str | None = Field(default=None, max_length=60)
    coursework: str | None = Field(default=None, max_length=400)
    note: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    title: str
    year: str
    summary: str
    stack: str
    link: str
    award_tag: str
    featured: bool
    order: int


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    year: str | None = Field(default=None, max_length=20)
    summary: str | None = None
    stack: str | None = Field(default=None, max_length=400)
    link: str | None = Field(default=None, max_length=300)
    award_tag: str | None = Field(default=None, max_length=120)
    featured: bool | None = None


# ─── Profile ──────────────────────────────────────────────────


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    role_title: str
    organization: str
    location_short: str
    location_full: str
    email: str
    phone: str
    github_url: str
    linkedin_url: str
    cv_url: str
    intro_paragraph: str
    about_paragraph: str
    summary: str
    skills_csv: str
    casual_about: str = ""
    casual_interests: str = ""


class ProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, max_length=80)
    role_title: str | None = Field(default=None, max_length=120)
    organization: str | None = Field(default=None, max_length=120)
    location_short: str | None = Field(default=None, max_length=80)
    location_full: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    github_url: str | None = Field(default=None, max_length=200)
    linkedin_url: str | None = Field(default=None, max_length=200)
    cv_url: str | None = Field(default=None, max_length=200)
    intro_paragraph: str | None = None
    about_paragraph: str | None = None
    summary: str | None = None
    skills_csv: str | None = Field(default=None, max_length=600)
    casual_about: str | None = None
    casual_interests: str | None = Field(default=None, max_length=300)


class ProfileStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    label: str
    primary: str
    secondary: str
    order: int


class ProfileStatUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=40)
    primary: str | None = Field(default=None, max_length=120)
    secondary: str | None = Field(default=None, max_length=160)


class SpecialtyItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    gloss: str
    metric: str
    order: int


class SpecialtyItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    gloss: str | None = Field(default=None, max_length=160)
    metric: str | None = Field(default=None, max_length=16)


# ─── Status ping ──────────────────────────────────────────────


class StatusOut(BaseModel):
    """Public read shape. The server computes 'aliveness' so the client doesn't have to."""
    state: str
    detail: str
    started_at: datetime
    last_seen_at: datetime
    age_seconds: int               # seconds since last_seen_at
    aliveness: str                 # "live" | "idle" | "away"


class StatusPingIn(BaseModel):
    state: str = Field(min_length=1, max_length=40)
    detail: str = Field(default="", max_length=200)
    # If state is unchanged from the last ping, the server preserves started_at
    # so durations make sense. If state changes, started_at resets.

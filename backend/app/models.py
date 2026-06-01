from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TilPost(Base):
    __tablename__ = "til_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    body_md: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(String(500), default="")  # comma-separated
    draft: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    attachments: Mapped[list["TilAttachment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class TilAttachment(Base):
    __tablename__ = "til_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("til_posts.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(300))
    stored_path: Mapped[str] = mapped_column(String(500))  # relative to UPLOADS_DIR
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    post: Mapped[TilPost] = relationship(back_populates="attachments")


class NowItem(Base):
    """Fixed-slug rows for the /now section. Slug + label are read-only;
    only `value` is editable. Seven seeded entries: headline + 6 facets.
    """
    __tablename__ = "now_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(40))
    value: Mapped[str] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Profile(Base):
    """Singleton record (always id=1) holding identity, contact, and bio fields
    used by the homepage hero AND /resume header. Edited inline like everything else."""
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identity
    first_name: Mapped[str] = mapped_column(String(80), default="")
    last_name: Mapped[str] = mapped_column(String(80), default="")
    role_title: Mapped[str] = mapped_column(String(120), default="")
    organization: Mapped[str] = mapped_column(String(120), default="")
    location_short: Mapped[str] = mapped_column(String(80), default="")
    location_full: Mapped[str] = mapped_column(String(160), default="")

    # Contact
    email: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    github_url: Mapped[str] = mapped_column(String(200), default="")
    linkedin_url: Mapped[str] = mapped_column(String(200), default="")
    cv_url: Mapped[str] = mapped_column(String(200), default="/resume.pdf")

    # Long-form copy
    intro_paragraph: Mapped[str] = mapped_column(Text, default="")  # hero face
    about_paragraph: Mapped[str] = mapped_column(Text, default="")  # hero detail
    summary: Mapped[str] = mapped_column(Text, default="")          # resume header

    # Skills chip cloud (CSV)
    skills_csv: Mapped[str] = mapped_column(String(600), default="")

    # Casual ("Daylight" theme) — plain-English bio for non-dev visitors
    # and 3-4 interest words shown as bullets. Both editable inline.
    casual_about: Mapped[str] = mapped_column(Text, default="")
    casual_interests: Mapped[str] = mapped_column(String(300), default="")  # CSV

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class ProfileStat(Base):
    """The four stat tiles on the hero face (Title / Locale / Class / Available)."""
    __tablename__ = "profile_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(40))
    primary: Mapped[str] = mapped_column(String(120))
    secondary: Mapped[str] = mapped_column(String(160), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class SpecialtyItem(Base):
    """Tiles in the hero-detail 'specialties' grid. 9 entries by default.
    Each has a name, a short gloss, and an optional metric badge (e.g. '6×')."""
    __tablename__ = "profile_specialties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(80))
    gloss: Mapped[str] = mapped_column(String(160), default="")
    metric: Mapped[str] = mapped_column(String(16), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WorkRole(Base):
    """A job role on /work. `section` discriminates Saama vs freelance.
    `bullets` is newline-separated text; `stack` is comma-separated chips."""
    __tablename__ = "work_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    section: Mapped[str] = mapped_column(String(40))   # "saama" | "freelance"
    title: Mapped[str] = mapped_column(String(120))
    organization: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(80), default="")
    dates: Mapped[str] = mapped_column(String(60))
    bullets: Mapped[str] = mapped_column(Text, default="")   # one per line
    stack: Mapped[str] = mapped_column(String(400), default="")  # CSV
    link: Mapped[str] = mapped_column(String(300), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WorkAward(Base):
    __tablename__ = "work_awards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    year: Mapped[str] = mapped_column(String(20))
    organization: Mapped[str] = mapped_column(String(120), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WorkCertification(Base):
    __tablename__ = "work_certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    issuer: Mapped[str] = mapped_column(String(120))
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WorkEducation(Base):
    __tablename__ = "work_education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    school: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str] = mapped_column(String(200))
    gpa: Mapped[str] = mapped_column(String(20), default="")
    dates: Mapped[str] = mapped_column(String(60))
    coursework: Mapped[str] = mapped_column(String(400), default="")   # CSV chips
    note: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Project(Base):
    """Portfolio projects. `featured=True` ones appear on /work as selected highlights."""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    year: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(Text, default="")
    stack: Mapped[str] = mapped_column(String(400), default="")   # CSV chips
    link: Mapped[str] = mapped_column(String(300), default="")
    award_tag: Mapped[str] = mapped_column(String(120), default="")
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class BadmintonPlayer(Base):
    """Players that Gokul follows. Slug is the stable identifier; everything
    else (name, country, flag, discipline, next_event) is admin-editable.
    Designed multi-tenant-ready: when site_id is added later, queries scope by site."""
    __tablename__ = "badminton_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(8))   # IND, MAS, etc.
    flag: Mapped[str] = mapped_column(String(8))      # emoji 🇮🇳
    discipline: Mapped[str] = mapped_column(String(40))  # "Men's Singles", "Men's Doubles"
    next_event: Mapped[str] = mapped_column(String(120), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class BadmintonTournament(Base):
    """Upcoming BWF tournaments. `dates` is a free-form display string the
    admin can edit; `start_date`/`end_date` are populated (when known) by the
    scraper and used for sorting + live-detection."""
    __tablename__ = "badminton_tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    dates: Mapped[str] = mapped_column(String(60))         # "02–07 Jun 2026"
    location: Mapped[str] = mapped_column(String(80))
    tier: Mapped[str] = mapped_column(String(40))          # "Super 1000", "Super 500"
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_url: Mapped[str] = mapped_column(String(400), default="")  # set by scraper
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class BadmintonMatch(Base):
    """One scraped match involving a tracked player. Refreshed daily.
    Older completed matches are pruned by the scraper."""
    __tablename__ = "badminton_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("badminton_players.id", ondelete="CASCADE"), index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("badminton_tournaments.id", ondelete="CASCADE"), index=True)
    opponent: Mapped[str] = mapped_column(String(200))
    round: Mapped[str] = mapped_column(String(40), default="")    # R64, R32, R16, QF, SF, F
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")  # scheduled|live|done
    score: Mapped[str] = mapped_column(String(80), default="")    # e.g. "21-18 19-21 21-15"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class UsesItem(Base):
    """Rows for the /uses inventory. Category + slug fixed; name + note editable.
    Seeded once with 32 entries across 7 categories (code, runtime, hardware,
    sound, court, fitness, daily).
    """
    __tablename__ = "uses_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    slug: Mapped[str] = mapped_column(String(60))
    name: Mapped[str] = mapped_column(String(200))
    note: Mapped[str] = mapped_column(String(300), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MuseumExhibit(Base):
    """A single 'room' in the friends-only museum at /museum. Six seeded by
    default; admin edits the title/kicker/body/photo_url inline."""
    __tablename__ = "museum_exhibits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    room_label: Mapped[str] = mapped_column(String(40))      # "ROOM I · ENTRANCE"
    title: Mapped[str] = mapped_column(String(160))
    kicker: Mapped[str] = mapped_column(String(200), default="")
    body_md: Mapped[str] = mapped_column(Text, default="")
    photo_url: Mapped[str] = mapped_column(String(400), default="")
    photo_caption: Mapped[str] = mapped_column(String(160), default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class StatusPing(Base):
    """Single-row record holding the admin's latest 'currently' state.
    Updated via POST /api/status (admin-only). Read by /api/status (public)."""
    __tablename__ = "status_pings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(40))      # coding · court · reading · afk · etc.
    detail: Mapped[str] = mapped_column(String(200), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Photo(Base):
    """A single photo on /photos. External image URL (no R2 dependency).
    Captions, taken-at, and url are all admin-editable inline."""
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(400), default="")
    caption: Mapped[str] = mapped_column(String(300), default="")
    taken_at: Mapped[str] = mapped_column(String(40), default="")  # free-form (e.g. "Coimbatore · Mar 2025")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Book(Base):
    """A book on /bookshelf. Status discriminates the section it appears in.
    All fields editable inline by admin."""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="want")  # reading | finished | want
    year: Mapped[str] = mapped_column(String(20), default="")
    link: Mapped[str] = mapped_column(String(400), default="")     # buy/preview link
    cover_url: Mapped[str] = mapped_column(String(400), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class GuestbookEntry(Base):
    """Anonymous (or signed) note left by a visitor. No auth required to write,
    but anything with a honeypot value gets dropped at the API. Admin can
    delete entries; otherwise everything is visible."""
    __tablename__ = "guestbook_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), default="")    # optional; "anonymous" if empty
    message: Mapped[str] = mapped_column(Text)                    # required
    # Lightweight rate-limit fingerprint — we only store a hash of the IP so we
    # can collapse rapid duplicate posts, never the raw IP itself.
    ip_hash: Mapped[str] = mapped_column(String(64), default="")
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class PageView(Base):
    __tablename__ = "page_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String(300), index=True)
    referrer: Mapped[str] = mapped_column(String(500), default="")
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

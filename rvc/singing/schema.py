from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class NoteEvent:
    """Represents a single singing note in beat-based coordinates."""

    start_beat: float
    duration_beats: float
    midi_note: int
    lyric: str = "la"
    velocity: float = 1.0
    phonemes: list[str] = field(default_factory=list)
    pitch_bend: list[float] = field(default_factory=list)
    vibrato_depth: float = 0.0
    vibrato_rate: float = 5.5
    dynamics: float = 1.0
    tension: float = 0.0
    breathiness: float = 0.0
    gender: float = 0.0


@dataclass
class SingingTrack:
    name: str
    language: str = "en"
    notes: list[NoteEvent] = field(default_factory=list)


@dataclass
class SingingProject:
    title: str
    bpm: float = 120.0
    tpqn: int = 480
    time_signature: str = "4/4"
    tracks: list[SingingTrack] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

from __future__ import annotations

from rvc.singing.schema import NoteEvent, SingingProject, SingingTrack


def parse_ust(path: str) -> SingingProject:
    project = SingingProject(title="UST Import")
    track = SingingTrack(name="Vocal", language="ja")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f]

    current: dict[str, str] = {}
    start_ticks = 0
    tempo = 120.0

    def flush_note(note_data: dict[str, str], offset_ticks: int):
        if not note_data or "Length" not in note_data or "NoteNum" not in note_data:
            return None
        length = int(note_data.get("Length", "0"))
        lyric = note_data.get("Lyric", "la")
        midi_note = int(note_data.get("NoteNum", "60"))
        return NoteEvent(
            start_beat=offset_ticks / project.tpqn,
            duration_beats=length / project.tpqn,
            midi_note=midi_note,
            lyric=lyric,
            velocity=1.0,
        ), length

    for line in lines:
        if line.startswith("Tempo="):
            tempo = float(line.split("=", 1)[1]) / 100.0
            continue
        if line.startswith("[#"):
            result = flush_note(current, start_ticks)
            if result:
                note, note_length = result
                track.notes.append(note)
                start_ticks += note_length
            current = {}
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            current[k] = v

    result = flush_note(current, start_ticks)
    if result:
        note, _ = result
        track.notes.append(note)

    project.bpm = tempo
    project.tracks = [track]
    return project

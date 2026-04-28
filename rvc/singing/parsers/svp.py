from __future__ import annotations

import json

from rvc.singing.schema import NoteEvent, SingingProject, SingingTrack


def parse_svp(path: str) -> SingingProject:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    bpm = 120.0
    tempo = data.get("time", {}).get("tempo")
    if isinstance(tempo, list) and tempo:
        bpm = float(tempo[0].get("bpm", 120.0))

    project = SingingProject(title=data.get("name", "SVP Import"), bpm=bpm)
    track = SingingTrack(name="Vocal", language="en")

    for sv_track in data.get("tracks", []):
        for group_ref in sv_track.get("mainGroup", {}).get("notes", []):
            onset = int(group_ref.get("onset", 0))
            duration = int(group_ref.get("duration", 480))
            pitch = int(group_ref.get("pitch", 60))
            lyric = group_ref.get("lyrics", "la")
            track.notes.append(
                NoteEvent(
                    start_beat=onset / project.tpqn,
                    duration_beats=duration / project.tpqn,
                    midi_note=pitch,
                    lyric=lyric,
                )
            )

    project.tracks = [track]
    return project

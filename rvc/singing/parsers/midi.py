from __future__ import annotations

import mido

from rvc.singing.schema import NoteEvent, SingingProject, SingingTrack


def parse_midi(path: str) -> SingingProject:
    mf = mido.MidiFile(path)
    tpqn = mf.ticks_per_beat
    bpm = 120.0
    for tr in mf.tracks:
        for msg in tr:
            if msg.type == "set_tempo":
                bpm = mido.tempo2bpm(msg.tempo)
                break

    project = SingingProject(title="MIDI Import", bpm=bpm, tpqn=tpqn)
    track = SingingTrack(name="Vocal", language="en")

    active: dict[int, tuple[int, int]] = {}
    lyrics_by_tick: dict[int, str] = {}

    tick = 0
    for msg in mf.tracks[0]:
        tick += msg.time
        if msg.type == "lyrics":
            lyrics_by_tick[tick] = msg.text.strip() or "la"

    tick = 0
    for msg in mf.tracks[0]:
        tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            active[msg.note] = (tick, msg.velocity)
        elif msg.type in {"note_off", "note_on"} and msg.note in active:
            start_tick, velocity = active.pop(msg.note)
            end_tick = tick
            lyric = lyrics_by_tick.get(start_tick, "la")
            track.notes.append(
                NoteEvent(
                    start_beat=start_tick / tpqn,
                    duration_beats=max((end_tick - start_tick) / tpqn, 0.125),
                    midi_note=msg.note,
                    lyric=lyric,
                    velocity=velocity / 127.0,
                )
            )

    project.tracks = [track]
    return project

from __future__ import annotations

import xml.etree.ElementTree as ET

from rvc.singing.schema import NoteEvent, SingingProject, SingingTrack


def _find_text(node: ET.Element, tag: str, default: str = "") -> str:
    child = node.find(f".//{tag}")
    return child.text if child is not None and child.text is not None else default


def parse_vsqx(path: str) -> SingingProject:
    tree = ET.parse(path)
    root = tree.getroot()

    bpm = 120.0
    tempo_node = root.find(".//tempo")
    if tempo_node is not None and tempo_node.text:
        bpm = float(tempo_node.text) / 100.0

    project = SingingProject(title="VSQX Import", bpm=bpm)
    track = SingingTrack(name="Vocal", language="ja")

    for note in root.findall(".//note"):
        pos_tick = int(_find_text(note, "t", "0"))
        dur_tick = int(_find_text(note, "dur", "120"))
        note_num = int(_find_text(note, "n", "60"))
        lyric = _find_text(note, "y", "la")
        vel = int(_find_text(note, "v", "64")) / 127.0
        track.notes.append(
            NoteEvent(
                start_beat=pos_tick / project.tpqn,
                duration_beats=dur_tick / project.tpqn,
                midi_note=note_num,
                lyric=lyric,
                velocity=vel,
            )
        )

    project.tracks = [track]
    return project

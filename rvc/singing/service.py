from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from rvc.singing.parsers.common import parse_project
from rvc.singing.phonemizer import lyrics_to_phonemes
from rvc.singing.renderer import render_project_audio, render_with_rvc, export_audio
from rvc.singing.schema import SingingProject


def load_and_enrich_project(path: str, language: str | None = None) -> SingingProject:
    project = parse_project(path)
    for track in project.tracks:
        if language:
            track.language = language
        for note in track.notes:
            note.phonemes = lyrics_to_phonemes(note.lyric, track.language)
    return project


def project_to_dataframe(project: SingingProject) -> pd.DataFrame:
    rows = []
    for ti, track in enumerate(project.tracks):
        for ni, note in enumerate(track.notes):
            rows.append(
                {
                    "track": ti,
                    "note": ni,
                    "start_beat": note.start_beat,
                    "duration_beats": note.duration_beats,
                    "midi_note": note.midi_note,
                    "lyric": note.lyric,
                    "phonemes": " ".join(note.phonemes),
                    "velocity": note.velocity,
                    "dynamics": note.dynamics,
                    "vibrato_depth": note.vibrato_depth,
                    "vibrato_rate": note.vibrato_rate,
                    "tension": note.tension,
                    "breathiness": note.breathiness,
                }
            )
    return pd.DataFrame(rows)


def save_project_json(project: SingingProject, output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(project.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def render_preview(project: SingingProject, output_path: str) -> str:
    audio = render_project_audio(project)
    return export_audio(audio, 44100, output_path, "wav")


def export_project_stub(project: SingingProject, export_path: str, export_type: str) -> str:
    export_type = export_type.lower()
    content = project.to_dict()
    content["export_type"] = export_type
    Path(export_path).write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    return export_path


def render_project(
    project: SingingProject,
    model_path: str,
    index_path: str,
    output_path: str,
    export_format: str,
    pitch_shift: int,
    index_rate: float,
    protect: float,
    formant_shift: float,
):
    return render_with_rvc(
        project=project,
        model_path=model_path,
        index_path=index_path,
        output_path=output_path,
        export_format=export_format,
        pitch_shift=pitch_shift,
        index_rate=index_rate,
        protect=protect,
        formant_shift=formant_shift,
    )

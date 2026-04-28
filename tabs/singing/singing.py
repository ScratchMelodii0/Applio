from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt

from assets.i18n.i18n import I18nAuto
from rvc.singing.service import (
    export_project_stub,
    load_and_enrich_project,
    project_to_dataframe,
    render_preview,
    render_project,
    save_project_json,
)
from tabs.inference.inference import default_weight, extract_model_and_epoch, get_files, match_index

i18n = I18nAuto()


def _project_plot(df):
    fig, ax = plt.subplots(figsize=(12, 4), facecolor="#10131a")
    ax.set_facecolor("#161b22")
    for _, row in df.iterrows():
        ax.broken_barh([(row["start_beat"], row["duration_beats"])], (row["midi_note"] - 0.4, 0.8), facecolors="#4f8cff", alpha=0.85)
        ax.text(row["start_beat"] + 0.02, row["midi_note"] + 0.05, str(row["lyric"]), color="#f7f7f7", fontsize=8)
    ax.set_title("Piano Roll", color="#f7f7f7")
    ax.set_xlabel("Beats", color="#f7f7f7")
    ax.set_ylabel("MIDI Note", color="#f7f7f7")
    ax.tick_params(colors="#f7f7f7")
    fig.tight_layout()
    return fig


def _project_from_json(project_json: str):
    from rvc.singing.schema import NoteEvent, SingingProject, SingingTrack

    data: dict[str, Any] = json.loads(project_json)
    tracks = []
    for track in data.get("tracks", []):
        notes = [NoteEvent(**n) for n in track.get("notes", [])]
        tracks.append(SingingTrack(name=track.get("name", "Vocal"), language=track.get("language", "en"), notes=notes))
    return SingingProject(
        title=data.get("title", "Project"),
        bpm=float(data.get("bpm", 120.0)),
        tpqn=int(data.get("tpqn", 480)),
        time_signature=data.get("time_signature", "4/4"),
        tracks=tracks,
        metadata=data.get("metadata", {}),
    )


def _load_project(file_path: str, language: str):
    project = load_and_enrich_project(file_path, language=language)
    df = project_to_dataframe(project)
    return json.dumps(project.to_dict(), ensure_ascii=False), df, _project_plot(df), f"Loaded {len(df)} notes."


def _render_preview(project_json: str):
    return render_preview(_project_from_json(project_json), os.path.join("assets", "audios", "singing_preview.wav"))


def _load_project_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _render_final(project_json: str, model_file: str, index_file: str, output_path: str, export_format: str, pitch_shift: int, index_rate: float, protect: float, formant_shift: float):
    return render_project(
        project=_project_from_json(project_json),
        model_path=model_file,
        index_path=index_file,
        output_path=output_path,
        export_format=export_format,
        pitch_shift=pitch_shift,
        index_rate=index_rate,
        protect=protect,
        formant_shift=formant_shift,
    )


def project_editor_tab():
    with gr.Row():
        score_file = gr.File(label=i18n("Import Score (.ust/.midi/.vsqx/.svp)"), type="filepath", file_types=[".ust", ".mid", ".midi", ".vsqx", ".svp"])
        language = gr.Dropdown(label=i18n("Language"), choices=["en", "ja", "es"], value="en", interactive=True)
        load_btn = gr.Button(i18n("Load Project"), variant="primary")

    project_state = gr.Textbox(label=i18n("Project JSON"), lines=8)
    status = gr.Textbox(label=i18n("Status"), interactive=False)
    note_table = gr.Dataframe(label=i18n("Notes / Lyrics / Phonemes / Expression"), interactive=False)
    piano_roll = gr.Plot(label=i18n("Piano Roll"))
    preview_btn = gr.Button(i18n("Realtime Preview"))
    preview_audio = gr.Audio(label=i18n("Preview"), type="filepath")

    with gr.Row():
        save_json = gr.Button(i18n("Save Internal Project JSON"))
        json_path = gr.Textbox(value=os.path.join("assets", "projects", "singing_project.json"), label=i18n("JSON Path"))
        json_output = gr.Textbox(label=i18n("Saved JSON"))

    load_btn.click(_load_project, [score_file, language], [project_state, note_table, piano_roll, status])
    preview_btn.click(_render_preview, [project_state], [preview_audio])
    save_json.click(lambda project_json, out_path: save_project_json(_project_from_json(project_json), out_path), [project_state, json_path], [json_output])


def text_to_singing_tab():
    project_json_file = gr.File(label=i18n("Load Project JSON from Project Editor"), type="filepath", file_types=[".json"])
    project_state = gr.Textbox(label=i18n("Project JSON"), lines=8)

    with gr.Row():
        model_file = gr.Dropdown(label=i18n("Voice Model"), choices=sorted(get_files("model"), key=extract_model_and_epoch), value=default_weight, interactive=True)
        index_file = gr.Dropdown(label=i18n("Index File"), choices=sorted(get_files("index")), value=match_index(default_weight), interactive=True)

    with gr.Row():
        pitch_shift = gr.Slider(-24, 24, value=0, step=1, label=i18n("Global Pitch Shift"))
        index_rate = gr.Slider(0.0, 1.0, value=0.75, step=0.01, label=i18n("VC Strength"))
        protect = gr.Slider(0.0, 0.5, value=0.33, step=0.01, label=i18n("Protect Consonants"))
        formant_shift = gr.Slider(-0.5, 0.5, value=0.0, step=0.01, label=i18n("Gender/Formant Shift"))

    output_path = gr.Textbox(value=os.path.join("assets", "audios", "singing_render.wav"), label=i18n("Output Path"))
    export_format = gr.Radio(["wav", "mp3", "ogg"], value="wav", label=i18n("Export Format"))
    render_btn = gr.Button(i18n("Render Singing"), variant="primary")
    render_audio = gr.Audio(label=i18n("Rendered Singing"), type="filepath")

    with gr.Accordion(i18n("Export Project"), open=False):
        export_type = gr.Dropdown(choices=["UST", "MIDI", "VSQX"], value="UST", label=i18n("Target format"))
        export_path = gr.Textbox(value=os.path.join("assets", "projects", "singing_export.json"), label=i18n("Export path"))
        export_btn = gr.Button(i18n("Export Project"))
        export_result = gr.Textbox(label=i18n("Export file"))

    project_json_file.change(_load_project_json, [project_json_file], [project_state])
    render_btn.click(_render_final, [project_state, model_file, index_file, output_path, export_format, pitch_shift, index_rate, protect, formant_shift], [render_audio])
    export_btn.click(lambda project_json, e_type, e_path: export_project_stub(_project_from_json(project_json), e_path, e_type), [project_state, export_type, export_path], [export_result])

from __future__ import annotations

import math
import os
import tempfile

import ffmpeg
import librosa
import numpy as np
import soundfile as sf

from rvc.singing.phonemizer import lyrics_to_phonemes
from rvc.singing.schema import NoteEvent, SingingProject


SAMPLE_RATE = 44100


def midi_to_freq(midi_note: int) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def _note_wave(note: NoteEvent, bpm: float, language: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    seconds = max((60.0 / bpm) * note.duration_beats, 0.05)
    samples = int(seconds * sr)
    t = np.linspace(0, seconds, samples, endpoint=False)

    freq = midi_to_freq(note.midi_note)
    vibrato = note.vibrato_depth * np.sin(2.0 * np.pi * note.vibrato_rate * t)
    instantaneous_freq = freq * (2.0 ** (vibrato / 12.0))
    phase = 2.0 * np.pi * np.cumsum(instantaneous_freq) / sr

    phonemes = note.phonemes or lyrics_to_phonemes(note.lyric, language=language)
    consonant_boost = 0.15 if phonemes and phonemes[0][0].lower() not in "aeiou" else 0.0

    fundamental = np.sin(phase)
    harmonic = 0.35 * np.sin(2 * phase + note.tension)
    breath = note.breathiness * np.random.randn(samples)

    attack = int(0.02 * sr)
    release = int(0.04 * sr)
    envelope = np.ones(samples)
    envelope[:attack] = np.linspace(0.0, 1.0, attack)
    envelope[-release:] = np.linspace(1.0, 0.0, release)

    wave = (fundamental + harmonic + breath) * envelope
    wave *= note.velocity * note.dynamics * (1.0 + consonant_boost)
    return wave.astype(np.float32)


def render_project_audio(project: SingingProject, track_index: int = 0, sr: int = SAMPLE_RATE) -> np.ndarray:
    if not project.tracks:
        return np.zeros(sr, dtype=np.float32)

    track = project.tracks[track_index]
    if not track.notes:
        return np.zeros(sr, dtype=np.float32)

    total_beats = max(n.start_beat + n.duration_beats for n in track.notes)
    total_seconds = (60.0 / project.bpm) * total_beats + 0.5
    out = np.zeros(int(total_seconds * sr), dtype=np.float32)

    for note in track.notes:
        wave = _note_wave(note, project.bpm, track.language, sr=sr)
        start_sample = int((60.0 / project.bpm) * note.start_beat * sr)
        end_sample = min(start_sample + len(wave), len(out))
        out[start_sample:end_sample] += wave[: end_sample - start_sample]

        # Gentle portamento overlap/crossfade with previous note tails.
        fade_len = min(int(0.01 * sr), end_sample - start_sample)
        if fade_len > 1:
            fade = np.linspace(0.9, 1.0, fade_len)
            out[start_sample : start_sample + fade_len] *= fade

    peak = np.max(np.abs(out))
    if peak > 0:
        out /= peak * 1.02

    return out


def apply_rvc_timbre(
    input_wav: str,
    output_wav: str,
    model_path: str,
    index_path: str,
    pitch_shift: int,
    index_rate: float,
    protect: float,
    formant_shift: float,
):
    from core import import_voice_converter

    infer_pipeline = import_voice_converter()
    infer_pipeline.convert_audio(
        audio_input_path=input_wav,
        audio_output_path=output_wav,
        model_path=model_path,
        index_path=index_path,
        pitch=pitch_shift,
        index_rate=index_rate,
        protect=protect,
        f0_method="rmvpe",
        split_audio=False,
        f0_autotune=True,
        f0_autotune_strength=0.6,
        proposed_pitch=False,
        proposed_pitch_threshold=155.0,
        clean_audio=False,
        clean_strength=0.5,
        export_format="WAV",
        embedder_model="contentvec",
        embedder_model_custom=None,
        post_process=False,
        formant_shifting=abs(formant_shift) > 1e-4,
        formant_qfrency=1.0 + formant_shift,
        formant_timbre=1.0,
        reverb=False,
        pitch_shift=False,
        limiter=False,
        gain=False,
        distortion=False,
        chorus=False,
        bitcrush=False,
        clipping=False,
        compressor=False,
        delay=False,
        sid=0,
    )


def export_audio(audio: np.ndarray, sample_rate: int, output_path: str, export_format: str) -> str:
    export_format = export_format.lower()
    target = os.path.splitext(output_path)[0] + f".{export_format}"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_path = temp_wav.name

    sf.write(temp_path, audio, sample_rate)

    if export_format == "wav":
        os.replace(temp_path, target)
        return target

    stream = ffmpeg.input(temp_path)
    stream = ffmpeg.output(stream, target, acodec="libmp3lame" if export_format == "mp3" else None)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)
    os.remove(temp_path)
    return target


def render_with_rvc(
    project: SingingProject,
    model_path: str,
    index_path: str,
    output_path: str,
    export_format: str = "wav",
    pitch_shift: int = 0,
    index_rate: float = 0.7,
    protect: float = 0.33,
    formant_shift: float = 0.0,
) -> str:
    raw_audio = render_project_audio(project)

    with tempfile.NamedTemporaryFile(suffix="_singing_seed.wav", delete=False) as seed_file:
        seed_path = seed_file.name
    with tempfile.NamedTemporaryFile(suffix="_singing_rvc.wav", delete=False) as rvc_file:
        rvc_path = rvc_file.name

    sf.write(seed_path, raw_audio, SAMPLE_RATE)
    apply_rvc_timbre(
        input_wav=seed_path,
        output_wav=rvc_path,
        model_path=model_path,
        index_path=index_path,
        pitch_shift=pitch_shift,
        index_rate=index_rate,
        protect=protect,
        formant_shift=formant_shift,
    )

    converted, sr = librosa.load(rvc_path, sr=SAMPLE_RATE, mono=True)
    os.remove(seed_path)
    os.remove(rvc_path)

    return export_audio(converted, sr, output_path, export_format)

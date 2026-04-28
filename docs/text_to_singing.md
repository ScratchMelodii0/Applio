# Applio Text-to-Singing Extension Architecture

## Overview
This extension adds two new UI pages:
1. **Project Editor**: import/edit/preview score projects (.UST/.MIDI/.VSQX/.SVP).
2. **Text-to-Singing**: render project notes through a singing synthesis front-end and then timbre-convert with RVC models.

## Pipeline
1. Parse score file into a normalized `SingingProject` schema.
2. Run multilingual lyric-to-phoneme mapping.
3. Generate expressive note waveforms (pitch, vibrato, dynamics, breathiness, tension).
4. Concatenate notes with light crossfades/portamento smoothing.
5. Send rendered waveform to Applio RVC inference (`VoiceConverter.convert_audio`) for voice timbre conversion.
6. Export final render as WAV/MP3/OGG.

## Key folders
- `rvc/singing/`: backend singing modules.
- `rvc/singing/parsers/`: score importers for UST/MIDI/VSQX/SVP.
- `tabs/singing/`: Gradio UI for project editing + rendering.
- `assets/phonemes/`: lightweight multilingual dictionary.

## Notes
- Export back to UST/MIDI/VSQX is currently a structured compatibility stub that writes project content for future formatter expansion.
- Real-time preview currently renders a lightweight local preview waveform from the normalized project without invoking RVC for speed.

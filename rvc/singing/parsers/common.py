from __future__ import annotations

from pathlib import Path

from rvc.singing.schema import SingingProject


def parse_project(path: str) -> SingingProject:
    extension = Path(path).suffix.lower()
    if extension == ".ust":
        from rvc.singing.parsers.ust import parse_ust

        return parse_ust(path)
    if extension in {".mid", ".midi"}:
        from rvc.singing.parsers.midi import parse_midi

        return parse_midi(path)
    if extension == ".vsqx":
        from rvc.singing.parsers.vsqx import parse_vsqx

        return parse_vsqx(path)
    if extension == ".svp":
        from rvc.singing.parsers.svp import parse_svp

        return parse_svp(path)

    raise ValueError(f"Unsupported project format: {extension}")

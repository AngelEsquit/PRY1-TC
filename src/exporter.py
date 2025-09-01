from __future__ import annotations
import json
import subprocess
from pathlib import Path
from .automaton import Automaton

def automaton_to_dict(a: Automaton) -> dict:
    norm = a.relabel_sequential()
    trans_list = []
    for src, mp in norm.transitions.items():
        for sym, dests in mp.items():
            for d in dests:
                label = "" if sym == "ε" else sym
                trans_list.append((int(src), label, int(d)))
    return {
        "ESTADOS": [int(s) for s in sorted(norm.states, key=lambda x: int(x))],
        "SIMBOLOS": sorted(sym for sym in norm.alphabet),
        "INICIO": [int(norm.initial)] if norm.initial is not None else [],
        "ACEPTACION": [int(s) for s in sorted(norm.accepts, key=lambda x: int(x))],
        "TRANSICIONES": trans_list,
    }


def export_json(a: Automaton, path: str) -> None:
    data = automaton_to_dict(a)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_dot(a: Automaton, path: str) -> None:
    dot_content = a.to_dot()
    with open(path, "w", encoding="utf-8") as f:
        f.write(dot_content)


def export_image(a: Automaton, path: str, format: str = "png") -> bool:
    dot_content = a.to_dot()
    dot_content_safe = dot_content.replace("ε", "epsilon")
    try:
        result = subprocess.run(
            ["dot", f"-T{format}", "-o", path],
            input=dot_content_safe,
            text=True,
            capture_output=True,
            check=True,
            encoding='utf-8'
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


__all__ = ["export_json", "automaton_to_dict", "export_dot", "export_image"]

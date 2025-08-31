from __future__ import annotations
import json
from .automaton import Automaton

# Exporta el autómata en el formato de especificación textual (como JSON)

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

__all__ = ["export_json", "automaton_to_dict"]

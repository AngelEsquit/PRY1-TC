from __future__ import annotations
from typing import Dict, Set, FrozenSet, List
from automaton import Automaton

# Minimización de Hopcroft para DFA

def minimize_hopcroft(dfa: Automaton) -> Automaton:
    if not dfa.is_deterministic():
        raise ValueError("minimize_hopcroft requiere un DFA determinista")
    if dfa.initial is None:
        raise ValueError("DFA sin estado inicial")

    dfa.remove_unreachable()

    alphabet = sorted(dfa.alphabet)
    F = set(dfa.accepts)
    Q = set(dfa.states)
    NF = Q - F

    # Partición inicial
    P: List[Set[str]] = [F, NF] if NF else [F]
    W: List[Set[str]] = [F.copy()]

    def target(src: str, sym: str) -> str | None:
        ts = dfa.transitions.get(src, {}).get(sym, set())
        if len(ts) == 1:
            return next(iter(ts))
        return None

    while W:
        A = W.pop()
        for sym in alphabet:
            # Preimagen de A bajo sym
            X = {q for q in Q if target(q, sym) in A}
            if not X:
                continue
            new_P: List[Set[str]] = []
            for Y in P:
                inter = Y & X
                diff = Y - X
                if inter and diff:
                    new_P.append(inter)
                    new_P.append(diff)
                    if Y in W:
                        W.remove(Y)
                        W.append(inter)
                        W.append(diff)
                    else:
                        # añadir la parte más pequeña a W
                        if len(inter) <= len(diff):
                            W.append(inter)
                        else:
                            W.append(diff)
                else:
                    new_P.append(Y)
            P = new_P

    # Construcción del DFA mínimo
    # Elegir nombres: si el bloque tiene tamaño 1 conservar el nombre original.
    # Si se fusionan varios, crear nombre nuevo "mX".
    rep_map: Dict[str, str] = {}
    block_names: Dict[FrozenSet[str], str] = {}
    mcount = 0
    for block in P:
        bset = frozenset(block)
        if len(block) == 1:
            name = next(iter(block))
        else:
            name = f"m{mcount}"
            mcount += 1
        block_names[bset] = name
        for s in block:
            rep_map[s] = name

    min_dfa = Automaton()
    for block in P:
        bset = frozenset(block)
        name = block_names[bset]
        accept = any(s in F for s in block)
        initial = dfa.initial in block
        min_dfa.add_state(name, accept=accept, initial=initial)
    for s, mp in dfa.transitions.items():
        for sym, dests in mp.items():
            if len(dests) != 1:
                continue
            (d,) = tuple(dests)
            min_dfa.add_transition(rep_map[s], sym, rep_map[d])
    return min_dfa

__all__ = ["minimize_hopcroft"]

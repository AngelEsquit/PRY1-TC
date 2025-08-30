from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, Dict, Optional, Iterable, FrozenSet, List, Tuple

# Definimos un símbolo especial para epsilon
EPSILON = "ε"

@dataclass
class Automaton:
    """Representa un autómata finito (posiblemente no determinista con transiciones ε).

    Este diseño es deliberadamente simple para fines educativos.
    - Los estados se representan como strings (o enteros casteados a string).
    - transiciones: dict estado -> dict simbolo -> conjunto de estados destino.
    - initial: estado inicial.
    - accepts: conjunto de estados de aceptación.
    - alphabet: símbolos distintos de EPSILON.
    """

    states: Set[str] = field(default_factory=set)
    alphabet: Set[str] = field(default_factory=set)
    transitions: Dict[str, Dict[str, Set[str]]] = field(default_factory=dict)
    initial: Optional[str] = None
    accepts: Set[str] = field(default_factory=set)

    # ---------------- Construcción básica -----------------
    def add_state(self, name: str, *, accept: bool = False, initial: bool = False) -> None:
        if name in self.states:
            # Permitir idempotencia
            if accept:
                self.accepts.add(name)
            if initial:
                self.initial = name
            return
        self.states.add(name)
        self.transitions.setdefault(name, {})
        if accept:
            self.accepts.add(name)
        if initial:
            self.initial = name

    def add_transition(self, src: str, symbol: str, dest: str) -> None:
        if src not in self.states or dest not in self.states:
            raise ValueError("Estado inexistente en la transición")
        if symbol != EPSILON:
            self.alphabet.add(symbol)
        bucket = self.transitions[src].setdefault(symbol, set())
        bucket.add(dest)

    # ---------------- Consultas -----------------
    def get_transitions(self, state: str, symbol: str) -> Set[str]:
        return set(self.transitions.get(state, {}).get(symbol, set()))

    def epsilon_closure(self, states: Iterable[str]) -> Set[str]:
        """Devuelve la ε-clausura de un conjunto de estados."""
        stack = list(states)
        closure = set(states)
        while stack:
            s = stack.pop()
            for nxt in self.transitions.get(s, {}).get(EPSILON, set()):
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
        return closure

    # ---------------- Simulación -----------------
    def simulate_nfa(self, input_str: str) -> bool:
        if self.initial is None:
            raise ValueError("Autómata sin estado inicial")
        current = self.epsilon_closure({self.initial})
        for ch in input_str:
            next_states: Set[str] = set()
            for s in current:
                for dest in self.get_transitions(s, ch):
                    next_states.update(self.epsilon_closure({dest}))
            current = next_states
            if not current:
                break
        return any(s in self.accepts for s in current)

    def is_deterministic(self) -> bool:
        for s, trans in self.transitions.items():
            if EPSILON in trans:
                return False
            for sym, dests in trans.items():
                if len(dests) > 1:
                    return False
        return True

    def simulate_dfa(self, input_str: str) -> bool:
        if not self.is_deterministic():
            raise ValueError("simulate_dfa: el autómata no es determinista")
        if self.initial is None:
            raise ValueError("Autómata sin estado inicial")
        state = self.initial
        for ch in input_str:
            dests = self.get_transitions(state, ch)
            if len(dests) != 1:
                return False  # transición no definida o no determinista
            (state,) = tuple(dests)
        return state in self.accepts

    # ---------------- Determinización (subset construction) -----------------
    def determinize(self) -> Automaton:
        if self.initial is None:
            raise ValueError("Autómata sin estado inicial")

        if self.is_deterministic():
            return self  # Ya es DFA

        start_closure = frozenset(self.epsilon_closure({self.initial}))
        dfa = Automaton()
        # map conjunto de estados NFA -> nombre estado DFA
        mapping: Dict[FrozenSet[str], str] = {start_closure: "q0"}
        dfa.add_state("q0", initial=True, accept=any(s in self.accepts for s in start_closure))

        pending: List[FrozenSet[str]] = [start_closure]
        used_names = 1

        while pending:
            current_set = pending.pop(0)
            current_name = mapping[current_set]
            # Recorremos alfabeto explícito (sin epsilon)
            for sym in sorted(self.alphabet):
                # Calcular movimiento y luego clausura epsilon de cada destino
                move: Set[str] = set()
                for nfa_state in current_set:
                    for dest in self.get_transitions(nfa_state, sym):
                        move.update(self.epsilon_closure({dest}))
                if not move:
                    continue
                frozen = frozenset(move)
                if frozen not in mapping:
                    new_name = f"q{used_names}"
                    used_names += 1
                    mapping[frozen] = new_name
                    dfa.add_state(new_name, accept=any(s in self.accepts for s in frozen))
                    pending.append(frozen)
                dfa_src = current_name
                dfa_dst = mapping[frozen]
                dfa.add_transition(dfa_src, sym, dfa_dst)

        return dfa

    # ---------------- Utilidades -----------------
    def clone(self) -> "Automaton":
        new = Automaton()
        new.states = set(self.states)
        new.alphabet = set(self.alphabet)
        new.initial = self.initial
        new.accepts = set(self.accepts)
        for s, mp in self.transitions.items():
            new.transitions[s] = {sym: set(dests) for sym, dests in mp.items()}
        return new

    def relabel_sequential(self) -> "Automaton":
        """Devuelve un nuevo autómata con estados renombrados a 0..n-1.
        Conserva estructura; útil para exportar en formato solicitado."""
        mapping: Dict[str, str] = {}
        if self.initial is not None and self.initial in self.states:
            ordered = [self.initial] + sorted(s for s in self.states if s != self.initial)
        else:
            ordered = sorted(self.states)
        for i, s in enumerate(ordered):
            mapping[s] = str(i)
        new = Automaton()
        for old, new_name in mapping.items():
            new.add_state(new_name, accept=old in self.accepts, initial=(old == self.initial))
        for src, mp in self.transitions.items():
            for sym, dests in mp.items():
                for d in dests:
                    new.add_transition(mapping[src], sym, mapping[d])
        return new

    def simulate_dfa_path(self, input_str: str) -> Tuple[List[str], bool]:
        """Simula (asumiendo DFA) devolviendo la lista de estados visitados (incluye inicial) y aceptación."""
        if not self.is_deterministic():
            raise ValueError("simulate_dfa_path: requiere DFA")
        if self.initial is None:
            raise ValueError("Autómata sin inicial")
        path = [self.initial]
        current = self.initial
        for ch in input_str:
            dests = self.get_transitions(current, ch)
            if len(dests) != 1:
                return path, False
            (current,) = tuple(dests)
            path.append(current)
        return path, current in self.accepts

    def remove_unreachable(self) -> None:
        if self.initial is None:
            return
        reachable = set()
        stack = [self.initial]
        while stack:
            s = stack.pop()
            if s in reachable:
                continue
            reachable.add(s)
            for trans in self.transitions.get(s, {}).values():
                for d in trans:
                    if d not in reachable:
                        stack.append(d)
        # Filtrar
        for s in list(self.states):
            if s not in reachable:
                self.states.remove(s)
                self.transitions.pop(s, None)
                self.accepts.discard(s)

    def to_dot(self, name: str = "Automaton") -> str:
        lines = [f"digraph {name} {{", "rankdir=LR;"]
        # Estado ficticio para flecha inicial
        if self.initial is not None:
            lines.append("__start__ [shape=point];")
        for s in sorted(self.states):
            shape = "doublecircle" if s in self.accepts else "circle"
            lines.append(f"{s} [shape={shape}];")
        if self.initial is not None:
            lines.append(f"__start__ -> {self.initial};")
        for src in sorted(self.states):
            for sym, dests in self.transitions[src].items():
                label = sym
                for dst in sorted(dests):
                    lines.append(f"{src} -> {dst} [label=\"{label}\"]; ")
        lines.append("}")
        return "\n".join(lines)

__all__ = ["Automaton", "EPSILON"]

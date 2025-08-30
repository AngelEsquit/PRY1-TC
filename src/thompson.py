from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from automaton import Automaton, EPSILON

@dataclass
class Fragment:
    start: str
    accepts: List[str]


def _new_state(counter: List[int]) -> str:
    s = f"s{counter[0]}"
    counter[0] += 1
    return s


def postfix_to_nfa(postfix: str) -> Automaton:
    """Construye un AFN usando Thompson a partir de una regex en postfix.
    Operadores: | alternancia, . concatenación, * estrella, + uno o más.
    Símbolo ε permitido en entrada postfix.
    """
    stack: List[Fragment] = []
    counter = [0]
    nfa = Automaton()

    for ch in postfix:
        if ch == '*':
            frag = stack.pop()
            start = _new_state(counter)
            end = _new_state(counter)
            nfa.add_state(start, initial=False)
            nfa.add_state(end)
            # epsilon a antiguo inicio y al nuevo fin
            nfa.add_transition(start, EPSILON, frag.start)
            nfa.add_transition(start, EPSILON, end)
            # de aceptaciones antiguas epsilon al inicio y al nuevo fin
            for a in frag.accepts:
                nfa.add_transition(a, EPSILON, frag.start)
                nfa.add_transition(a, EPSILON, end)
            stack.append(Fragment(start, [end]))
        elif ch == '+':
            frag = stack.pop()
            # A+ = AA*
            # Creamos estrella sobre copia
            # Reutilizamos construyendo A seguido de A*
            # Implementación directa: A+ = A concatenado con A*
            # Para eficiencia: similar a estrella pero sin epsilon directo al nuevo fin
            start = _new_state(counter)
            end = _new_state(counter)
            nfa.add_state(start)
            nfa.add_state(end)
            nfa.add_transition(start, EPSILON, frag.start)
            for a in frag.accepts:
                # bucle
                nfa.add_transition(a, EPSILON, frag.start)
                nfa.add_transition(a, EPSILON, end)
            stack.append(Fragment(start, [end]))
        elif ch == '.':
            frag2 = stack.pop()
            frag1 = stack.pop()
            # conectar aceptaciones de frag1 con inicio de frag2
            for a in frag1.accepts:
                nfa.add_transition(a, EPSILON, frag2.start)
            stack.append(Fragment(frag1.start, frag2.accepts))
        elif ch == '|':
            frag2 = stack.pop()
            frag1 = stack.pop()
            start = _new_state(counter)
            end = _new_state(counter)
            nfa.add_state(start)
            nfa.add_state(end)
            nfa.add_transition(start, EPSILON, frag1.start)
            nfa.add_transition(start, EPSILON, frag2.start)
            for a in frag1.accepts:
                nfa.add_transition(a, EPSILON, end)
            for a in frag2.accepts:
                nfa.add_transition(a, EPSILON, end)
            stack.append(Fragment(start, [end]))
        else:
            # símbolo literal (incluye ε)
            start = _new_state(counter)
            end = _new_state(counter)
            nfa.add_state(start)
            nfa.add_state(end)
            if ch == EPSILON:
                nfa.add_transition(start, EPSILON, end)
            else:
                nfa.add_transition(start, ch, end)
            stack.append(Fragment(start, [end]))

    if len(stack) != 1:
        raise ValueError("Regex postfix inválida (pila final != 1)")

    frag = stack.pop()
    # Ajustar estados inicial y de aceptación
    nfa.initial = frag.start
    for a in frag.accepts:
        nfa.accepts.add(a)
    # Añadir estados faltantes (los que pudieron crearse sin registrar) -> ya se registraron al add_state
    return nfa

__all__ = ["postfix_to_nfa"]

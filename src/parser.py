from __future__ import annotations
from typing import List

# Operadores soportados: | alternancia, concatenación implícita, * estrella, + uno o más, () agrupación
# Se convierte a postfix (notación inversa polaca) usando Shunting Yard adaptado para concatenación implícita.

OP_UNARY = {"*", "+"}
OP_BINARY = {"|", "."}  # usamos "." como operador explícito de concatenación interno
PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3}
RIGHT_ASSOC = {"*", "+"}

EPSILON_SYMBOLS = {"ε", "e"}  # se normaliza a "ε"


def to_postfix(regex: str) -> str:
    # Limpia espacios
    regex = regex.replace(" ", "")
    # Inserta operador de concatenación explícito
    tokens: List[str] = []
    i = 0
    while i < len(regex):
        c = regex[i]
        tokens.append(c)
        i += 1
    # Insertar '.' donde corresponda: entre ( símbolo ) * + y símbolo/(
    output: List[str] = []
    augmented: List[str] = []
    for idx, t in enumerate(tokens):
        augmented.append(t)
        if idx < len(tokens) - 1:
            a, b = t, tokens[idx + 1]
            if (a not in {"|", "("} and b not in {"|", ")", "*", "+"}):
                augmented.append(".")
            if (a in {"*", "+", ")"} and b not in {"|", ")", "*", "+"}):
                augmented.append(".")
    # Shunting Yard
    stack: List[str] = []
    for t in augmented:
        if t == "(":
            stack.append(t)
        elif t == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Paréntesis desbalanceados")
            stack.pop()
        elif t in PRECEDENCE:
            while stack and stack[-1] != "(" and (
                PRECEDENCE[stack[-1]] > PRECEDENCE[t] or (
                    PRECEDENCE[stack[-1]] == PRECEDENCE[t] and t not in RIGHT_ASSOC
                )
            ):
                output.append(stack.pop())
            stack.append(t)
        else:
            # símbolo (incluyendo ε designado)
            if t in EPSILON_SYMBOLS:
                output.append("ε")
            else:
                output.append(t)
    while stack:
        op = stack.pop()
        if op in {"(", ")"}:
            raise ValueError("Paréntesis desbalanceados al final")
        output.append(op)
    return "".join(output)

__all__ = ["to_postfix"]

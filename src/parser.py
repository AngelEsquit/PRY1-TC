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
    if not regex:
        raise ValueError("Regex vacía")
    
    for char in regex:
        if not (char.isalnum() or char in "|*+()εe "):
            raise ValueError(f"Caracter no valido: '{char}'")
    
    regex = regex.replace(" ", "")
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
            if ((a not in {"|", "(", ")", "*", "+"} and b not in {"|", ")", "*", "+"}) or
                (a in {"*", "+", ")"} and b not in {"|", ")", "*", "+"})):
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
                raise ValueError("Parentesis desbalanceados: ')' sin '(' correspondiente")
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
            raise ValueError("Parentesis desbalanceados: '(' sin ')' correspondiente")
        output.append(op)
    
    result = "".join(output)
    if not result:
        raise ValueError("Regex inválida: resultado vacio")
    
    return result

__all__ = ["to_postfix"]

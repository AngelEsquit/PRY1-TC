from __future__ import annotations
from typing import List, Set
import re
import string

#operadores soportados: | alternancia, concatenacion implicita, * estrella, + uno o mas, () agrupacion
#? cero o una vez, . cualquier caracter, [] clases de caracteres, {} repeticiones
#se convierte a postfix (notacion inversa polaca) usando shunting yard adaptado para concatenacion implicita.

OP_UNARY = {"*", "+", "?"}
OP_BINARY = {"|", "."}  #usamos "." como operador explicito de concatenacion interno
PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3, "?": 3}
RIGHT_ASSOC = {"*", "+", "?"}

EPSILON_SYMBOLS = {"ε", "e"}  #se normaliza a "ε"
SPECIAL_CHARS = {"|", "*", "+", "?", "(", ")", "[", "]", "{", "}", "\\", "^", "$", ".", "-"}
VALID_ESCAPE_CHARS = {"n", "t", "r", "\\", "(", ")", "[", "]", "{", "}", "|", "*", "+", "?", ".", "^", "$"}

class RegexValidationError(ValueError):
    """Excepción específica para errores de validación de regex"""
    pass


def validate_regex(regex: str) -> None:
    """
    Valida que la regex sea sintácticamente correcta antes del procesamiento.
    
    Args:
        regex: La expresión regular a validar
        
    Raises:
        RegexValidationError: Si la regex tiene errores sintácticos
    """
    if not regex:
        raise RegexValidationError("Regex vacía")
    
    if len(regex) > 1000:
        raise RegexValidationError("Regex demasiado larga (máximo 1000 caracteres)")
    
    #verificar paréntesis balanceados
    paren_count = 0
    bracket_count = 0
    brace_count = 0
    
    i = 0
    while i < len(regex):
        char = regex[i]
        
        if char == '\\':
            #verificar escape valido
            if i + 1 >= len(regex):
                raise RegexValidationError("Backslash al final de regex")
            next_char = regex[i + 1]
            if next_char not in VALID_ESCAPE_CHARS:
                raise RegexValidationError(f"Escape inválido: \\{next_char}")
            i += 2
            continue
            
        elif char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
            if paren_count < 0:
                raise RegexValidationError("Paréntesis desbalanceados: ')' sin '(' correspondiente")
                
        elif char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
            if bracket_count < 0:
                raise RegexValidationError("Corchetes desbalanceados: ']' sin '[' correspondiente")
                
        elif char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count < 0:
                raise RegexValidationError("Llaves desbalanceadas: '}' sin '{' correspondiente")
        
        i += 1
    
    if paren_count != 0:
        raise RegexValidationError("Paréntesis desbalanceados: '(' sin ')' correspondiente")
    if bracket_count != 0:
        raise RegexValidationError("Corchetes desbalanceados: '[' sin ']' correspondiente")
    if brace_count != 0:
        raise RegexValidationError("Llaves desbalanceadas: '{' sin '}' correspondiente")
    
    #verificar operadores validos
    _validate_operators(regex)


def _validate_operators(regex: str) -> None:
    """Valida que los operadores estén en posiciones correctas"""
    cleaned_regex = _remove_escapes(regex)
    
    for i, char in enumerate(cleaned_regex):
        if char in {'*', '+', '?'}:
            if i == 0:
                raise RegexValidationError(f"Operador '{char}' al inicio de regex")
            prev_char = cleaned_regex[i-1]
            if prev_char in {'|', '('}:
                raise RegexValidationError(f"Operador '{char}' despues de '{prev_char}'")
            #validar operadores unarios consecutivos
            if prev_char in {'*', '+', '?'}:
                raise RegexValidationError(f"Operadores unarios consecutivos: '{prev_char}{char}'")
        
        elif char == '|':
            if i == 0 or i == len(cleaned_regex) - 1:
                raise RegexValidationError("Operador '|' en posición inválida")
            if cleaned_regex[i-1] in {'|', '('} or cleaned_regex[i+1] in {'|', ')'}:
                raise RegexValidationError("Operador '|' mal posicionado")


def _remove_escapes(regex: str) -> str:
    """Remueve caracteres escapados para validación de operadores"""
    result = []
    i = 0
    while i < len(regex):
        if regex[i] == '\\' and i + 1 < len(regex):
            result.append('a')  #reemplazar escape con símbolo genérico
            i += 2
        else:
            result.append(regex[i])
            i += 1
    return ''.join(result)


def expand_character_classes(regex: str) -> str:
    """
    Expande clases de caracteres [abc], [a-z], etc. a alternativas.
    
    Args:
        regex: Regex con posibles clases de caracteres
        
    Returns:
        Regex expandida sin clases de caracteres
    """
    result = []
    i = 0
    
    while i < len(regex):
        if regex[i] == '\\' and i + 1 < len(regex):
            #manejar escape
            result.append(regex[i:i+2])
            i += 2
        elif regex[i] == '[':
            #encontrar el cierre del corchete
            j = i + 1
            while j < len(regex) and regex[j] != ']':
                if regex[j] == '\\':
                    j += 2
                else:
                    j += 1
            
            if j >= len(regex):
                raise RegexValidationError("Clase de caracteres sin cerrar")
            
            #expandir la clase
            char_class = regex[i+1:j]
            expanded = _expand_char_class(char_class)
            result.append(f"({expanded})")
            i = j + 1
        else:
            result.append(regex[i])
            i += 1
    
    return ''.join(result)


def _expand_char_class(char_class: str) -> str:
    """Expande una clase de caracteres a alternativas"""
    if not char_class:
        raise RegexValidationError("Clase de caracteres vacía")
    
    chars = set()
    i = 0
    
    while i < len(char_class):
        if char_class[i] == '\\' and i + 1 < len(char_class):
            #caracter escapado
            next_char = char_class[i + 1]
            if next_char == 'n':
                chars.add('\n')
            elif next_char == 't':
                chars.add('\t')
            elif next_char == 'r':
                chars.add('\r')
            else:
                chars.add(next_char)
            i += 2
        elif i + 2 < len(char_class) and char_class[i + 1] == '-':
            #rango de caracteres
            start_char = char_class[i]
            end_char = char_class[i + 2]
            if ord(start_char) > ord(end_char):
                raise RegexValidationError(f"Rango inválido: {start_char}-{end_char}")
            
            for code in range(ord(start_char), ord(end_char) + 1):
                chars.add(chr(code))
            i += 3
        else:
            chars.add(char_class[i])
            i += 1
    
    if not chars:
        raise RegexValidationError("Clase de caracteres vacia despues de expansion")
    
    return '|'.join(sorted(chars))


def expand_quantifiers(regex: str) -> str:
    """
    Expande cuantificadores {n}, {n,m} a repeticiones explicitas.
    
    Args:
        regex: Regex con posibles cuantificadores
        
    Returns:
        Regex expandida sin cuantificadores de repeticion
    """
    result = []
    i = 0
    
    while i < len(regex):
        if regex[i] == '\\' and i + 1 < len(regex):
            result.append(regex[i:i+2])
            i += 2
        elif regex[i] == '{':
            #encontrar el elemento anterior
            if not result:
                raise RegexValidationError("Cuantificador sin elemento previo")
            
            #encontrar el cierre de la llave
            j = i + 1
            while j < len(regex) and regex[j] != '}':
                j += 1
            
            if j >= len(regex):
                raise RegexValidationError("Cuantificador sin cerrar")
            
            quantifier = regex[i+1:j]
            expanded = _expand_quantifier(result, quantifier)
            result = expanded
            i = j + 1
        else:
            result.append(regex[i])
            i += 1
    
    return ''.join(result)


def _expand_quantifier(preceding: List[str], quantifier: str) -> List[str]:
    """Expande un cuantificador específico"""
    if ',' in quantifier:
        #{n,m} formato
        parts = quantifier.split(',')
        if len(parts) != 2:
            raise RegexValidationError(f"Cuantificador inválido: {{{quantifier}}}")
        
        try:
            min_rep = int(parts[0]) if parts[0] else 0
            max_rep = int(parts[1]) if parts[1] else min_rep + 5  #limite arbitrario
        except ValueError:
            raise RegexValidationError(f"Cuantificador invalido: {{{quantifier}}}")
    else:
        #{n} formato
        try:
            min_rep = max_rep = int(quantifier)
        except ValueError:
            raise RegexValidationError(f"Cuantificador invalido: {{{quantifier}}}")
    
    if min_rep < 0 or max_rep < 0 or min_rep > max_rep:
        raise RegexValidationError(f"Cuantificador invalido: {{{quantifier}}}")
    
    if max_rep > 20:  #limite para evitar explosion exponencial
        raise RegexValidationError("Cuantificador demasiado grande (maximo 20)")
    
    #tomar el ultimo elemento o grupo
    if preceding and preceding[-1] == ')':
        #buscar el grupo completo
        paren_count = 1
        start = len(preceding) - 2
        while start >= 0 and paren_count > 0:
            if preceding[start] == ')':
                paren_count += 1
            elif preceding[start] == '(':
                paren_count -= 1
            start -= 1
        start += 1
        element = ''.join(preceding[start:])
        result = preceding[:start]
    else:
        #tomar el ultimo caracter
        element = preceding[-1] if preceding else ''
        result = preceding[:-1] if preceding else []
    
    #expandir el cuantificador
    if min_rep == max_rep:
        #repeticion exacta
        for _ in range(min_rep):
            result.append(element)
    else:
        #rango de repeticiones - usar ? para hacer opcionales
        for i in range(min_rep):
            result.append(element)
        for i in range(max_rep - min_rep):
            result.append(f"({element})?")
    
    return result


def process_special_chars(regex: str) -> str:
    """
    Procesa caracteres especiales como ., \n, \t, etc.
    
    Args:
        regex: Regex con posibles caracteres especiales
        
    Returns:
        Regex procesada
    """
    result = []
    i = 0
    
    while i < len(regex):
        if regex[i] == '\\' and i + 1 < len(regex):
            next_char = regex[i + 1]
            if next_char == 'n':
                result.append('\n')
            elif next_char == 't':
                result.append('\t')
            elif next_char == 'r':
                result.append('\r')
            elif next_char == '\\':
                result.append('\\')
            elif next_char in SPECIAL_CHARS:
                result.append(next_char)
            else:
                result.append(next_char)
            i += 2
        elif regex[i] == '.':
            #punto = cualquier caracter (simplificado a letras y digitos)
            any_char = '|'.join(string.ascii_letters + string.digits)
            result.append(f"({any_char})")
            i += 1
        else:
            result.append(regex[i])
            i += 1
    
    return ''.join(result)


def to_postfix(regex: str) -> str:
    """
    Convierte una expresion regular a notacion postfix.
    
    Operadores soportados:
    - | (alternancia)
    - * (cero o mas)
    - + (uno o mas)  
    - ? (cero o uno)
    - () (agrupación)
    - [] (clases de caracteres)
    - {} (repeticiones)
    - . (cualquier caracter)
    - \\\\ (escape)
    
    Args:
        regex: Expresión regular en notación infija
        
    Returns:
        Expresión regular en notación postfix
        
    Raises:
        RegexValidationError: Si la regex es inválida
    """
    if not regex:
        raise RegexValidationError("Regex vacía")
    
    try:
        #paso 1: Validar sintaxis
        validate_regex(regex)
        
        #paso 2: Expandir clases de caracteres [abc], [a-z]
        regex = expand_character_classes(regex)
        
        #paso 3: Expandir cuantificadores {n}, {n,m}
        regex = expand_quantifiers(regex)
        
        #paso 4: procesar caracteres especiales \n, \t, .
        regex = process_special_chars(regex)
        
        #paso 5: verificar caracteres validos despues del procesamiento
        for char in regex:
            if not (char.isalnum() or char in "|*+?()εe \n\t\r\\"):
                raise RegexValidationError(f"Caracter no valido: '{char}'")
        
        #paso 6: tokenizar
        regex = regex.replace(" ", "")
        tokens: List[str] = []
        i = 0
        while i < len(regex):
            c = regex[i]
            tokens.append(c)
            i += 1
            
        #paso 7: insertar operadores de concatenacion explicitos
        augmented: List[str] = []
        for idx, t in enumerate(tokens):
            augmented.append(t)
            if idx < len(tokens) - 1:
                a, b = t, tokens[idx + 1]
                if ((a not in {"|", "(", ")", "*", "+", "?"} and b not in {"|", ")", "*", "+", "?"}) or
                    (a in {"*", "+", "?", ")"} and b not in {"|", ")", "*", "+", "?"})):
                    augmented.append(".")
        
        #paso 8: algoritmo shunting yard
        output: List[str] = []
        stack: List[str] = []
        
        for t in augmented:
            if t == "(":
                stack.append(t)
            elif t == ")":
                while stack and stack[-1] != "(":
                    output.append(stack.pop())
                if not stack:
                    raise RegexValidationError("Paréntesis desbalanceados: ')' sin '(' correspondiente")
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
                #simbolo (incluyendo ε)
                if t in EPSILON_SYMBOLS:
                    output.append("ε")
                else:
                    output.append(t)
        
        while stack:
            op = stack.pop()
            if op in {"(", ")"}:
                raise RegexValidationError("Paréntesis desbalanceados: '(' sin ')' correspondiente")
            output.append(op)
        
        result = "".join(output)
        if not result:
            raise RegexValidationError("Regex inválida: resultado vacío")
        
        return result
        
    except RegexValidationError:
        raise
    except Exception as e:
        raise RegexValidationError(f"Error procesando regex: {str(e)}")


__all__ = ["to_postfix", "validate_regex", "RegexValidationError"]

from pathlib import Path
from src.parser import to_postfix
from src.thompson import postfix_to_nfa
from src.hopcroft import minimize_hopcroft
from src.exporter import export_json, export_dot, export_image

from src.automaton import EPSILON

# CLI muy simple basada en input() para cubrir especificaciones:
# 1. Ingresar regex
# 2. Construir AFN, AFD, AFD mínimo
# 3. Exportar cada uno
# 4. Simular cadenas en el AFD mínimo mostrando la traza

def main():
    print("=== Proyecto Teoría de la Computación ===")
    print("Construcción de automatas finitos a partir de regex")
    print("Operadores soportados: |, *, +, (, )")
    print("Simbolos: letras, dígitos, ε (épsilon)")
    print()
    
    while True:
        regex = input("Ingrese regex r: ").strip()
        if not regex:
            print("Error: Expresión vacia")
            continue
        
        try:
            postfix = to_postfix(regex)
            print(f"Postfix: {postfix}")
            break
        except ValueError as e:
            print(f"Error en regex: {e}")
            continue
    
    try:
        nfa = postfix_to_nfa(postfix)
        print(f"AFN: estados={len(nfa.states)} aceptacion={len(nfa.accepts)}")
        dfa = nfa.determinize()
        print(f"AFD: estados={len(dfa.states)} aceptacion={len(dfa.accepts)}")
        dfa_min = minimize_hopcroft(dfa)
        print(f"AFD mínimo: estados={len(dfa_min.states)} aceptacion={len(dfa_min.accepts)}")
    except Exception as e:
        print(f"Error en construcción: {e}")
        return

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    
    try:
        export_json(nfa, str(out_dir / "afn.json"))
        export_json(dfa, str(out_dir / "afd.json"))
        export_json(dfa_min, str(out_dir / "afd_min.json"))
        
        export_dot(nfa, str(out_dir / "afn.dot"))
        export_dot(dfa, str(out_dir / "afd.dot"))
        export_dot(dfa_min, str(out_dir / "afd_min.dot"))
    except Exception as e:
        print(f"Error en exportación: {e}")
        return
    
    images_generated = 0
    if export_image(nfa, str(out_dir / "afn.png")):
        print("--- Imagen AFN generado: ./out/afn.png")
        images_generated += 1
    else:
        print("--- No se pudo generar imagen AFN")
        
    if export_image(dfa, str(out_dir / "afd.png")):
        print("--- Imagen AFD generada: ./out/afd.png")
        images_generated += 1
    else:
        print("--- No se pudo generar imagen AFD")
        
    if export_image(dfa_min, str(out_dir / "afd_min.png")):
        print("--- Imagen AFD minimo generado: ./out/afd_min.png")
        images_generated += 1
    else:
        print("--- No se pudo generar imagen AFD minimo")
    
    if images_generated == 0:
        print()
        print("Friendly reminder:")
        print("Para ver los autómatas como graficos, ve el README")
        print()
    
    print("Archivos exportados en ./out")

    print()
    print("SIMULACIÓN DE CADENAS (AFD mínimo):")
    while True:
        w = input("Cadena a simular (vacio para salir): ")
        if w == "":
            break
        
        try:
            valid_symbols = dfa_min.alphabet
            for char in w:
                if char not in valid_symbols:
                    print(f"Error: Simbolo '{char}' no valido. Simbolo válidos: {sorted(valid_symbols)}")
                    raise ValueError("Simbolo no valido")
            
            path, accepted = dfa_min.simulate_dfa_path(w)
            print("Trayectoria: ", " -> ".join(path))
            print("Resultado: ", "SI" if accepted else "NO")
        except Exception as e:
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el user")
    except Exception as e:
        print(f"Error: {e}")

from pathlib import Path
from src.parser import to_postfix
from src.thompson import postfix_to_nfa
from src.hopcroft import minimize_hopcroft
from src.exporter import export_json

from src.automaton import EPSILON

# CLI muy simple basada en input() para cubrir especificaciones:
# 1. Ingresar regex
# 2. Construir AFN, AFD, AFD mínimo
# 3. Exportar cada uno
# 4. Simular cadenas en el AFD mínimo mostrando la traza

def main():
    print("=== Proyecto Teoría de la Computación ===")
    regex = input("Ingrese expresión regular r: ").strip()
    postfix = to_postfix(regex)
    print(f"Postfix: {postfix}")
    nfa = postfix_to_nfa(postfix)
    print(f"AFN: estados={len(nfa.states)} aceptacion={len(nfa.accepts)}")
    dfa = nfa.determinize()
    print(f"AFD: estados={len(dfa.states)} aceptacion={len(dfa.accepts)}")
    dfa_min = minimize_hopcroft(dfa)
    print(f"AFD mínimo: estados={len(dfa_min.states)} aceptacion={len(dfa_min.accepts)}")

    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    export_json(nfa, str(out_dir / "afn.json"))
    export_json(dfa, str(out_dir / "afd.json"))
    export_json(dfa_min, str(out_dir / "afd_min.json"))
    print("Archivos exportados en ./out")

    while True:
        w = input("Cadena a simular (vacío para salir): ")
        if w == "":
            break
        path, accepted = dfa_min.simulate_dfa_path(w)
        print("Trayectoria: ", " -> ".join(path))
        print("Resultado: ", "SI" if accepted else "NO")

if __name__ == "__main__":
    main()

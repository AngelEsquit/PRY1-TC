import argparse
import sys
from pathlib import Path
from typing import List, Optional
from src.parser import to_postfix, RegexValidationError
from src.thompson import postfix_to_nfa
from src.hopcroft import minimize_hopcroft
from src.exporter import (
    export_json, export_dot, export_image, 
    export_interactive_html, export_step_by_step_simulation
)
from src.automaton import EPSILON

def create_parser() -> argparse.ArgumentParser:
    """Crear parser de argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Construcción de autómatas finitos a partir de expresiones regulares",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                          # Modo interactivo
  python main.py -r "a*b+"               # Procesar regex específica
  python main.py -r "a|b" --no-images    # Sin generar imágenes
  python main.py -r "a*" -o custom_dir   # Directorio de salida personalizado
  python main.py -f regexes.txt          # Procesar archivo con múltiples regex
  python main.py -r "a*b" --html         # Generar visualización HTML
  python main.py -r "a*b" -s "ab,aab"    # Simular cadenas específicas
  
Operadores soportados:
  |    - Alternancia (or)
  *    - Cero o más repeticiones
  +    - Una o más repeticiones
  ?    - Cero o una repetición
  ()   - Agrupación
  []   - Clases de caracteres (ej: [abc], [a-z])
  {}   - Repeticiones específicas (ej: a{2}, a{1,3})
  .    - Cualquier carácter
  \\   - Escape de caracteres especiales
        """
    )
    
    # Grupo principal
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "-r", "--regex", 
        type=str,
        help="Expresión regular a procesar"
    )
    input_group.add_argument(
        "-f", "--file",
        type=str,
        help="Archivo con expresiones regulares (una por línea)"
    )
    
    # Opciones de salida
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="out",
        help="Directorio de salida (default: out)"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="No generar imágenes PNG"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generar visualización HTML interactiva"
    )
    parser.add_argument(
        "--enhanced-dot",
        action="store_true",
        help="Usar formato DOT mejorado con colores"
    )
    
    # Opciones de simulación
    parser.add_argument(
        "-s", "--simulate",
        type=str,
        help="Cadenas a simular separadas por comas (ej: 'ab,aab,b')"
    )
    parser.add_argument(
        "--step-by-step",
        action="store_true",
        help="Generar simulación paso a paso en HTML"
    )
    
    # Opciones de comportamiento
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Salida detallada"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Silenciar salida no esencial"
    )
    parser.add_argument(
        "--no-minimization",
        action="store_true",
        help="No minimizar el AFD"
    )
    
    return parser


def process_regex(regex: str, args) -> Optional[dict]:
    """
    Procesar una expresión regular individual.
    
    Returns:
        Dict con los autómatas generados o None si hay error
    """
    try:
        if not args.quiet:
            print(f"Procesando regex: {regex}")
        
        # Paso 1: Convertir a postfix
        postfix = to_postfix(regex)
        if args.verbose:
            print(f"  Postfix: {postfix}")
        
        # Paso 2: Construir AFN
        nfa = postfix_to_nfa(postfix)
        if args.verbose:
            print(f"  AFN: {len(nfa.states)} estados, {len(nfa.accepts)} aceptación")
        
        # Paso 3: Determinizar
        dfa = nfa.determinize()
        if args.verbose:
            print(f"  AFD: {len(dfa.states)} estados, {len(dfa.accepts)} aceptación")
        
        # Paso 4: Minimizar (opcional)
        if not args.no_minimization:
            dfa_min = minimize_hopcroft(dfa)
            if args.verbose:
                print(f"  AFD mínimo: {len(dfa_min.states)} estados, {len(dfa_min.accepts)} aceptación")
        else:
            dfa_min = dfa
            if args.verbose:
                print("  Minimización omitida")
        
        return {
            'regex': regex,
            'postfix': postfix,
            'nfa': nfa,
            'dfa': dfa,
            'dfa_min': dfa_min
        }
        
    except (RegexValidationError, ValueError) as e:
        print(f"Error procesando '{regex}': {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error inesperado procesando '{regex}': {e}", file=sys.stderr)
        return None


def export_automata(result: dict, args, output_dir: Path) -> None:
    """Exportar autómatas en los formatos solicitados"""
    regex = result['regex']
    nfa = result['nfa']
    dfa = result['dfa']
    dfa_min = result['dfa_min']
    
    # Sanitizar nombre de archivo
    safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in regex[:20])
    
    try:
        # Exportar JSON
        export_json(nfa, str(output_dir / f"{safe_name}_afn.json"))
        export_json(dfa, str(output_dir / f"{safe_name}_afd.json"))
        export_json(dfa_min, str(output_dir / f"{safe_name}_afd_min.json"))
        
        # Exportar DOT
        enhanced = args.enhanced_dot
        export_dot(nfa, str(output_dir / f"{safe_name}_afn.dot"), enhanced=enhanced)
        export_dot(dfa, str(output_dir / f"{safe_name}_afd.dot"), enhanced=enhanced)
        export_dot(dfa_min, str(output_dir / f"{safe_name}_afd_min.dot"), enhanced=enhanced)
        
        if not args.quiet:
            print(f"  Archivos JSON y DOT exportados para '{regex}'")
        
        # Exportar imágenes PNG
        if not args.no_images:
            images_generated = 0
            
            if export_image(nfa, str(output_dir / f"{safe_name}_afn.png"), enhanced=enhanced):
                if args.verbose:
                    print(f"  ✓ Imagen AFN generada: {safe_name}_afn.png")
                images_generated += 1
            else:
                if args.verbose:
                    print(f"  ✗ No se pudo generar imagen AFN")
            
            if export_image(dfa, str(output_dir / f"{safe_name}_afd.png"), enhanced=enhanced):
                if args.verbose:
                    print(f"  ✓ Imagen AFD generada: {safe_name}_afd.png")
                images_generated += 1
            else:
                if args.verbose:
                    print(f"  ✗ No se pudo generar imagen AFD")
            
            if export_image(dfa_min, str(output_dir / f"{safe_name}_afd_min.png"), enhanced=enhanced):
                if args.verbose:
                    print(f"  ✓ Imagen AFD mínimo generada: {safe_name}_afd_min.png")
                images_generated += 1
            else:
                if args.verbose:
                    print(f"  ✗ No se pudo generar imagen AFD mínimo")
            
            if images_generated == 0 and not args.quiet:
                print("  Nota: Para generar imágenes, instala Graphviz:")
                print("    Ubuntu/Debian: sudo apt-get install graphviz")
                print("    macOS: brew install graphviz")
                print("    Windows: https://graphviz.org/download/")
        
        # Exportar HTML interactivo
        if args.html:
            html_path = output_dir / f"{safe_name}_interactive.html"
            if export_interactive_html(dfa_min, str(html_path)):
                if not args.quiet:
                    print(f"  ✓ Visualización HTML generada: {html_path.name}")
            else:
                if args.verbose:
                    print(f"  ✗ No se pudo generar HTML interactivo")
        
    except Exception as e:
        print(f"Error exportando '{regex}': {e}", file=sys.stderr)


def simulate_strings(result: dict, strings: List[str], args, output_dir: Path) -> None:
    """Simular cadenas en el AFD mínimo"""
    dfa_min = result['dfa_min']
    regex = result['regex']
    
    if not dfa_min.is_dfa():
        print(f"Error: El autómata para '{regex}' no es determinista", file=sys.stderr)
        return
    
    if not args.quiet:
        print(f"\nSimulación en AFD mínimo para '{regex}':")
    
    for string in strings:
        try:
            # Verificar símbolos válidos
            valid_symbols = dfa_min.alphabet | {EPSILON}
            for char in string:
                if char not in valid_symbols:
                    print(f"  '{string}': Error - símbolo '{char}' no válido")
                    print(f"    Símbolos válidos: {sorted(valid_symbols - {EPSILON})}")
                    continue
            
            path, accepted = dfa_min.simulate_dfa_path(string)
            status = "ACEPTADA" if accepted else "RECHAZADA"
            
            if args.verbose:
                print(f"  '{string}': {status}")
                print(f"    Trayectoria: {' → '.join(path)}")
            else:
                print(f"  '{string}': {status} ({' → '.join(path)})")
            
            # Generar simulación paso a paso en HTML si se solicita
            if args.step_by_step:
                safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in regex[:20])
                safe_string = "".join(c if c.isalnum() or c in '-_' else '_' for c in string)
                html_path = output_dir / f"{safe_name}_sim_{safe_string}.html"
                
                if export_step_by_step_simulation(dfa_min, string, str(html_path)):
                    if args.verbose:
                        print(f"    ✓ Simulación paso a paso: {html_path.name}")
                
        except Exception as e:
            print(f"  '{string}': Error - {e}")


def interactive_mode():
    """Modo interactivo original"""
    print("=== Proyecto Teoría de la Computación ===")
    print("Construcción de automatas finitos a partir de regex")
    print("Operadores soportados: |, *, +, ?, (), [], {}, ., \\")
    print("Símbolos: letras, dígitos, ε (épsilon)")
    print("Para ayuda detallada: python main.py --help")
    print()
    
    while True:
        regex = input("Ingrese regex r (o 'quit' para salir): ").strip()
        if regex.lower() in ['quit', 'exit', 'q']:
            break
        if not regex:
            print("Error: Expresión vacía")
            continue
        
        # Simular argumentos para el modo interactivo
        class Args:
            quiet = False
            verbose = False
            no_minimization = False
            no_images = False
            html = False
            enhanced_dot = True
            step_by_step = False
        
        args = Args()
        
        result = process_regex(regex, args)
        if not result:
            continue
        
        # Exportar archivos
        out_dir = Path("out")
        out_dir.mkdir(exist_ok=True)
        export_automata(result, args, out_dir)
        
        print("Archivos exportados en ./out")
        print()
        print("SIMULACIÓN DE CADENAS (AFD mínimo):")
        
        while True:
            w = input("Cadena a simular (vacío para nueva regex): ")
            if w == "":
                break
            
            simulate_strings(result, [w], args, out_dir)


def main():
    """Función principal mejorada con CLI avanzado"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validar argumentos
    if args.quiet and args.verbose:
        print("Error: --quiet y --verbose son mutuamente excluyentes", file=sys.stderr)
        return 1
    
    # Crear directorio de salida
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Modo interactivo si no se especifica regex ni archivo
    if not args.regex and not args.file:
        try:
            interactive_mode()
            return 0
        except KeyboardInterrupt:
            print("\nPrograma interrumpido por el usuario")
            return 0
    
    # Recopilar expresiones regulares
    regexes = []
    
    if args.regex:
        regexes.append(args.regex)
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                file_regexes = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                regexes.extend(file_regexes)
        except FileNotFoundError:
            print(f"Error: Archivo '{args.file}' no encontrado", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error leyendo archivo '{args.file}': {e}", file=sys.stderr)
            return 1
    
    if not regexes:
        print("Error: No hay expresiones regulares para procesar", file=sys.stderr)
        return 1
    
    # Procesar cada regex
    successful_results = []
    errors = 0
    
    for regex in regexes:
        result = process_regex(regex, args)
        if result:
            successful_results.append(result)
            export_automata(result, args, output_dir)
        else:
            errors += 1
    
    # Simulación de cadenas
    if args.simulate and successful_results:
        strings = [s.strip() for s in args.simulate.split(',') if s.strip()]
        
        if not args.quiet:
            print(f"\n=== Simulación de cadenas ===")
        
        for result in successful_results:
            simulate_strings(result, strings, args, output_dir)
    
    # Resumen final
    if not args.quiet:
        print(f"\n=== Resumen ===")
        print(f"Regex procesadas: {len(regexes)}")
        print(f"Exitosas: {len(successful_results)}")
        print(f"Errores: {errors}")
        print(f"Archivos generados en: {output_dir}")
    
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)

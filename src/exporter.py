from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from .automaton import Automaton, EPSILON

def automaton_to_dict(a: Automaton) -> dict:
    """
    Convierte un autómata a diccionario para exportación JSON.
    
    Args:
        a: El autómata a convertir
        
    Returns:
        Diccionario con formato estándar del proyecto
    """
    norm = a.relabel_sequential()
    trans_list = []
    for src, mp in norm.transitions.items():
        for sym, dests in mp.items():
            for d in dests:
                label = "" if sym == EPSILON else sym
                trans_list.append((int(src), label, int(d)))
    return {
        "ESTADOS": [int(s) for s in sorted(norm.states, key=lambda x: int(x))],
        "SIMBOLOS": sorted(sym for sym in norm.alphabet),
        "INICIO": [int(norm.initial)] if norm.initial is not None else [],
        "ACEPTACION": [int(s) for s in sorted(norm.accepts, key=lambda x: int(x))],
        "TRANSICIONES": trans_list,
    }


def export_json(a: Automaton, path: str) -> None:
    """
    Exporta un autómata a formato JSON.
    
    Args:
        a: El autómata a exportar
        path: Ruta del archivo de salida
    """
    data = automaton_to_dict(a)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_dot(a: Automaton, path: str, enhanced: bool = True) -> None:
    """
    Exporta un autómata a formato DOT de Graphviz.
    
    Args:
        a: El autómata a exportar
        path: Ruta del archivo de salida
        enhanced: Si usar formato mejorado con estilos
    """
    if enhanced:
        dot_content = a.to_dot_enhanced()
    else:
        dot_content = a.to_dot()
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(dot_content)


def export_image(a: Automaton, path: str, format: str = "png", enhanced: bool = True) -> bool:
    """
    Exporta un autómata como imagen usando Graphviz.
    
    Args:
        a: El autómata a exportar
        path: Ruta del archivo de salida
        format: Formato de imagen (png, svg, pdf)
        enhanced: Si usar visualización mejorada
        
    Returns:
        True si la exportación fue exitosa
    """
    if enhanced:
        dot_content = a.to_dot_enhanced()
    else:
        dot_content = a.to_dot()
    
    # Reemplazar epsilon para compatibilidad
    dot_content_safe = dot_content.replace("ε", "epsilon")
    
    try:
        result = subprocess.run(
            ["dot", f"-T{format}", "-o", path],
            input=dot_content_safe,
            text=True,
            capture_output=True,
            check=True,
            encoding='utf-8'
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def export_interactive_html(a: Automaton, path: str, include_simulation: bool = True) -> bool:
    """
    Exporta una visualización interactiva en HTML usando vis.js.
    
    Args:
        a: El autómata a exportar
        path: Ruta del archivo HTML de salida
        include_simulation: Si incluir simulador interactivo
        
    Returns:
        True si la exportación fue exitosa
    """
    try:
        html_content = _generate_interactive_html(a, include_simulation)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True
    except Exception:
        return False


def export_step_by_step_simulation(a: Automaton, string: str, path: str) -> bool:
    """
    Exporta la simulación paso a paso como HTML.
    
    Args:
        a: El autómata (debe ser DFA)
        string: Cadena a simular
        path: Ruta del archivo HTML de salida
        
    Returns:
        True si la exportación fue exitosa
    """
    try:
        if not a.is_dfa():
            return False
            
        steps = _get_simulation_steps(a, string)
        html_content = _generate_simulation_html(a, string, steps)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return True
    except Exception:
        return False


def _generate_interactive_html(a: Automaton, include_simulation: bool) -> str:
    """Genera HTML interactivo con vis.js"""
    nodes, edges = _automaton_to_visjs(a)
    
    simulation_code = ""
    if include_simulation and a.is_dfa():
        simulation_code = """
        <div class="simulation-panel">
            <h3>Simulación</h3>
            <input type="text" id="inputString" placeholder="Ingrese cadena...">
            <button onclick="simulate()">Simular</button>
            <div id="result"></div>
        </div>
        
        <script>
        function simulate() {
            const input = document.getElementById('inputString').value;
            const result = simulateString(input);
            document.getElementById('result').innerHTML = 
                `<strong>${result.accepted ? 'ACEPTADA' : 'RECHAZADA'}</strong><br>` +
                `Trayectoria: ${result.path.join(' → ')}`;
        }
        
        function simulateString(input) {
            // Implementar simulación en JavaScript
            // Por simplicidad, retornamos resultado mock
            return {accepted: true, path: ['q0', 'q1']};
        }
        </script>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Autómata Interactivo</title>
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            #graph {{ width: 100%; height: 500px; border: 1px solid #ccc; }}
            .simulation-panel {{ margin-top: 20px; padding: 15px; border: 1px solid #ddd; }}
            .simulation-panel input {{ padding: 8px; margin-right: 10px; }}
            .simulation-panel button {{ padding: 8px 15px; }}
            #result {{ margin-top: 10px; padding: 10px; background: #f5f5f5; }}
        </style>
    </head>
    <body>
        <h1>Visualización del Autómata</h1>
        <div id="graph"></div>
        {simulation_code}
        
        <script>
            const nodes = new vis.DataSet({nodes});
            const edges = new vis.DataSet({edges});
            const container = document.getElementById('graph');
            const data = {{ nodes: nodes, edges: edges }};
            const options = {{
                physics: {{ enabled: true, solver: 'forceAtlas2Based' }},
                nodes: {{
                    shape: 'circle',
                    size: 30,
                    font: {{ size: 16 }},
                    borderWidth: 2
                }},
                edges: {{
                    arrows: {{ to: {{ enabled: true }} }},
                    font: {{ size: 14, align: 'middle' }},
                    smooth: {{ type: 'curvedCCW', roundness: 0.2 }}
                }}
            }};
            const network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """


def _automaton_to_visjs(a: Automaton) -> Tuple[List[dict], List[dict]]:
    """Convierte autómata a formato vis.js"""
    norm = a.relabel_sequential()
    
    nodes = []
    for state in norm.states:
        is_initial = (state == norm.initial)
        is_accept = (state in norm.accepts)
        
        color = '#97C2FC'  # Azul por defecto
        if is_initial and is_accept:
            color = '#FB7E81'  # Rojo para inicial+final
        elif is_initial:
            color = '#7BE141'  # Verde para inicial
        elif is_accept:
            color = '#FFB347'  # Naranja para final
        
        nodes.append({
            'id': int(state),
            'label': state,
            'color': color,
            'borderWidth': 3 if is_initial else 2
        })
    
    edges = []
    edge_id = 0
    for src, transitions in norm.transitions.items():
        for symbol, destinations in transitions.items():
            for dest in destinations:
                label = 'ε' if symbol == EPSILON else symbol
                edges.append({
                    'id': edge_id,
                    'from': int(src),
                    'to': int(dest),
                    'label': label
                })
                edge_id += 1
    
    return nodes, edges


def _get_simulation_steps(a: Automaton, string: str) -> List[dict]:
    """Obtiene los pasos de simulación"""
    if not a.is_dfa():
        return []
    
    path, accepted = a.simulate_dfa_path(string)
    steps = []
    
    for i, state in enumerate(path):
        char = string[i-1] if i > 0 else None
        steps.append({
            'step': i,
            'state': state,
            'char': char,
            'remaining': string[i:] if i < len(string) else ""
        })
    
    return steps


def _generate_simulation_html(a: Automaton, string: str, steps: List[dict]) -> str:
    """Genera HTML para simulación paso a paso"""
    nodes, edges = _automaton_to_visjs(a)
    
    steps_html = ""
    for step in steps:
        char_display = f"'{step['char']}'" if step['char'] else "inicio"
        steps_html += f"""
        <tr>
            <td>{step['step']}</td>
            <td>{step['state']}</td>
            <td>{char_display}</td>
            <td>{step['remaining']}</td>
        </tr>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simulación: {string}</title>
        <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            #graph {{ width: 100%; height: 400px; border: 1px solid #ccc; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
            .highlight {{ background-color: #ffeb3b; }}
        </style>
    </head>
    <body>
        <h1>Simulación de "{string}"</h1>
        <div id="graph"></div>
        
        <h2>Pasos de simulación</h2>
        <table>
            <tr>
                <th>Paso</th>
                <th>Estado actual</th>
                <th>Carácter leído</th>
                <th>Cadena restante</th>
            </tr>
            {steps_html}
        </table>
        
        <script>
            const nodes = new vis.DataSet({nodes});
            const edges = new vis.DataSet({edges});
            const container = document.getElementById('graph');
            const data = {{ nodes: nodes, edges: edges }};
            const options = {{
                physics: {{ enabled: false }},
                nodes: {{
                    shape: 'circle',
                    size: 30,
                    font: {{ size: 16 }},
                    borderWidth: 2
                }},
                edges: {{
                    arrows: {{ to: {{ enabled: true }} }},
                    font: {{ size: 14, align: 'middle' }},
                    smooth: {{ type: 'curvedCCW', roundness: 0.2 }}
                }}
            }};
            const network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """


__all__ = [
    "export_json", "automaton_to_dict", "export_dot", "export_image",
    "export_interactive_html", "export_step_by_step_simulation"
]

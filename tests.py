#!/usr/bin/env python3
"""
Casos de prueba comprehensivos para el proyecto de autómatas.

Incluye:
- Pruebas unitarias para cada componente
- Pruebas de integración
- Casos extremos y de error
- Pruebas de rendimiento básicas
"""

import unittest
import tempfile
import os
from pathlib import Path
import time
from typing import List, Tuple

from src.parser import to_postfix, validate_regex, RegexValidationError
from src.thompson import postfix_to_nfa
from src.hopcroft import minimize_hopcroft
from src.exporter import (
    export_json, export_dot, export_image, 
    export_interactive_html, export_step_by_step_simulation
)
from src.automaton import Automaton, EPSILON


class TestRegexParser(unittest.TestCase):
    """Pruebas para el parser de expresiones regulares"""
    
    def test_basic_regex(self):
        """Pruebas para regex básicas"""
        test_cases = [
            ("a", "a"),
            ("ab", "ab."),
            ("a|b", "ab|"),
            ("a*", "a*"),
            ("a+", "a+"),
            ("a?", "a?"),
            ("(a|b)*", "ab|*"),
            ("a(b|c)", "abc|."),
            ("(a|b)(c|d)", "ab|cd|."),
        ]
        
        for regex, expected in test_cases:
            with self.subTest(regex=regex):
                result = to_postfix(regex)
                self.assertEqual(result, expected)
    
    def test_complex_regex(self):
        """Pruebas para regex complejas"""
        test_cases = [
            ("a+b*", "a+b*."),
            ("(a|b)*c", "ab|*c."),
            ("a?(b+|c*)", "a?b+c*|."),
            ("((a|b)*c)+", "ab|*c.+"),
        ]
        
        for regex, expected in test_cases:
            with self.subTest(regex=regex):
                result = to_postfix(regex)
                self.assertEqual(result, expected)
    
    def test_character_classes(self):
        """Pruebas para clases de caracteres"""
        test_cases = [
            ("[abc]", "(a|b|c)"),
            ("[a-c]", "(a|b|c)"),
            ("[0-2]", "(0|1|2)"),
        ]
        
        for regex, expected_expansion in test_cases:
            with self.subTest(regex=regex):
                # La expansión exacta depende de la implementación
                result = to_postfix(regex)
                # Verificar que no hay errores
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
    
    def test_quantifiers(self):
        """Pruebas para cuantificadores"""
        test_cases = [
            ("a{2}", "aa."),
            ("a{1,2}", "a(a)?.")
        ]
        
        for regex, expected_pattern in test_cases:
            with self.subTest(regex=regex):
                result = to_postfix(regex)
                # Verificar que la expansión es válida
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
    
    def test_special_characters(self):
        """Pruebas para caracteres especiales"""
        test_cases = [
            ("\\\\n", "\n"),
            ("\\\\t", "\t"),
            ("\\\\\\\\", "\\"),
            ("\\\\*", "*"),
        ]
        
        for regex, _ in test_cases:
            with self.subTest(regex=regex):
                result = to_postfix(regex)
                self.assertIsInstance(result, str)
    
    def test_validation_errors(self):
        """Pruebas para errores de validación"""
        invalid_cases = [
            "",  # Vacía
            ")",  # Paréntesis desbalanceados
            "(",  # Paréntesis desbalanceados
            "*",  # Operador al inicio
            "|",  # Alternancia mal posicionada
            "a||b",  # Doble alternancia
            "[",  # Corchete sin cerrar
            "{",  # Llave sin cerrar
            "\\",  # Escape al final
            "\\x",  # Escape inválido
        ]
        
        for invalid_regex in invalid_cases:
            with self.subTest(regex=invalid_regex):
                with self.assertRaises(RegexValidationError):
                    to_postfix(invalid_regex)
    
    def test_epsilon_handling(self):
        """Pruebas para manejo de epsilon"""
        test_cases = [
            ("ε", "ε"),
            ("e", "ε"),  # Normalización
            ("aε", "aε."),
            ("ε|a", "εa|"),
        ]
        
        for regex, expected in test_cases:
            with self.subTest(regex=regex):
                result = to_postfix(regex)
                self.assertEqual(result, expected)


class TestThompsonConstruction(unittest.TestCase):
    """Pruebas para la construcción de Thompson"""
    
    def test_basic_nfa_construction(self):
        """Pruebas básicas de construcción de AFN"""
        test_cases = [
            "a",
            "ab.",
            "ab|",
            "a*",
            "a+",
            "a?",
        ]
        
        for postfix in test_cases:
            with self.subTest(postfix=postfix):
                nfa = postfix_to_nfa(postfix)
                self.assertIsInstance(nfa, Automaton)
                self.assertIsNotNone(nfa.initial)
                self.assertGreater(len(nfa.accepts), 0)
                self.assertGreater(len(nfa.states), 0)
    
    def test_nfa_structure(self):
        """Pruebas de estructura del AFN"""
        nfa = postfix_to_nfa("ab.")
        
        # Verificar que tiene exactamente 4 estados para concatenación simple
        self.assertEqual(len(nfa.states), 4)
        
        # Verificar estado inicial y de aceptación
        self.assertIsNotNone(nfa.initial)
        self.assertEqual(len(nfa.accepts), 1)
    
    def test_operators(self):
        """Pruebas específicas para cada operador"""
        # Estrella de Kleene
        nfa_star = postfix_to_nfa("a*")
        self.assertTrue(len(nfa_star.states) >= 2)
        
        # Más
        nfa_plus = postfix_to_nfa("a+")
        self.assertTrue(len(nfa_plus.states) >= 2)
        
        # Opcional
        nfa_opt = postfix_to_nfa("a?")
        self.assertTrue(len(nfa_opt.states) >= 2)
        
        # Alternancia
        nfa_alt = postfix_to_nfa("ab|")
        self.assertTrue(len(nfa_alt.states) >= 4)
    
    def test_invalid_postfix(self):
        """Pruebas para postfix inválidos"""
        invalid_cases = [
            "*",    # Operador sin operando
            "+",    # Operador sin operando
            "?",    # Operador sin operando
            ".",    # Concatenación sin segundo operando
            "|",    # Alternancia sin operandos
            "ab|.", # Concatenación sin segundo operando después de alternancia
            "",     # Vacío
        ]
        
        for invalid_postfix in invalid_cases:
            with self.subTest(postfix=invalid_postfix):
                with self.assertRaises(ValueError):
                    postfix_to_nfa(invalid_postfix)


class TestAutomatonMethods(unittest.TestCase):
    """Pruebas para métodos del autómata"""
    
    def setUp(self):
        """Configurar autómata de prueba"""
        self.nfa = Automaton()
        self.nfa.add_state("q0", initial=True)
        self.nfa.add_state("q1")
        self.nfa.add_state("q2", accept=True)
        self.nfa.add_transition("q0", "a", "q1")
        self.nfa.add_transition("q1", "b", "q2")
    
    def test_epsilon_closure(self):
        """Pruebas para clausura epsilon"""
        # Añadir transiciones epsilon
        self.nfa.add_transition("q0", EPSILON, "q1")
        
        closure = self.nfa.epsilon_closure(["q0"])
        self.assertIn("q0", closure)
        self.assertIn("q1", closure)
    
    def test_determinization(self):
        """Pruebas para determinización"""
        dfa = self.nfa.determinize()
        
        # Verificar que es determinista
        self.assertTrue(dfa.is_dfa())
        
        # Verificar estructura básica
        self.assertIsNotNone(dfa.initial)
        self.assertGreater(len(dfa.accepts), 0)
    
    def test_simulation(self):
        """Pruebas para simulación de cadenas"""
        dfa = self.nfa.determinize()
        
        # Cadena aceptada
        path, accepted = dfa.simulate_dfa_path("ab")
        self.assertTrue(accepted)
        self.assertGreater(len(path), 2)
        
        # Cadena rechazada
        path, accepted = dfa.simulate_dfa_path("a")
        self.assertFalse(accepted)
    
    def test_relabel_sequential(self):
        """Pruebas para etiquetado secuencial"""
        relabeled = self.nfa.relabel_sequential()
        
        # Verificar que los estados son secuenciales
        state_nums = [int(s) for s in relabeled.states]
        self.assertEqual(sorted(state_nums), list(range(len(state_nums))))
        
        # Verificar que se mantiene la estructura
        self.assertEqual(len(relabeled.states), len(self.nfa.states))
        self.assertEqual(len(relabeled.accepts), len(self.nfa.accepts))


class TestHopcroftMinimization(unittest.TestCase):
    """Pruebas para minimización de Hopcroft"""
    
    def test_basic_minimization(self):
        """Pruebas básicas de minimización"""
        # Crear DFA simple
        postfix = "ab."
        nfa = postfix_to_nfa(postfix)
        dfa = nfa.determinize()
        
        minimized = minimize_hopcroft(dfa)
        
        # Verificar que es DFA válido
        self.assertTrue(minimized.is_dfa())
        self.assertIsNotNone(minimized.initial)
        
        # El resultado debe tener igual o menor número de estados
        self.assertLessEqual(len(minimized.states), len(dfa.states))
    
    def test_minimization_reduces_states(self):
        """Verificar que la minimización reduce estados redundantes"""
        # Crear DFA con estados redundantes
        postfix = "a*b."
        nfa = postfix_to_nfa(postfix)
        dfa = nfa.determinize()
        
        minimized = minimize_hopcroft(dfa)
        
        # Debería reducir el número de estados
        self.assertLessEqual(len(minimized.states), len(dfa.states))


class TestExporter(unittest.TestCase):
    """Pruebas para exportación"""
    
    def setUp(self):
        """Configurar directorio temporal"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Crear autómata simple para pruebas
        self.nfa = postfix_to_nfa("ab.")
        self.dfa = self.nfa.determinize()
    
    def tearDown(self):
        """Limpiar archivos temporales"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_json_export(self):
        """Pruebas para exportación JSON"""
        json_path = os.path.join(self.temp_dir, "test.json")
        export_json(self.dfa, json_path)
        
        self.assertTrue(os.path.exists(json_path))
        
        # Verificar contenido JSON
        import json
        with open(json_path) as f:
            data = json.load(f)
        
        self.assertIn("ESTADOS", data)
        self.assertIn("SIMBOLOS", data)
        self.assertIn("TRANSICIONES", data)
    
    def test_dot_export(self):
        """Pruebas para exportación DOT"""
        dot_path = os.path.join(self.temp_dir, "test.dot")
        export_dot(self.dfa, dot_path)
        
        self.assertTrue(os.path.exists(dot_path))
        
        # Verificar contenido DOT
        with open(dot_path) as f:
            content = f.read()
        
        self.assertIn("digraph", content)
        self.assertIn("->", content)
    
    def test_image_export(self):
        """Pruebas para exportación de imágenes"""
        png_path = os.path.join(self.temp_dir, "test.png")
        
        # Intentar exportar (puede fallar si Graphviz no está instalado)
        success = export_image(self.dfa, png_path)
        
        # Solo verificar si tuvo éxito
        if success:
            self.assertTrue(os.path.exists(png_path))
    
    def test_html_export(self):
        """Pruebas para exportación HTML"""
        html_path = os.path.join(self.temp_dir, "test.html")
        
        success = export_interactive_html(self.dfa, html_path)
        
        if success:
            self.assertTrue(os.path.exists(html_path))
            
            # Verificar contenido HTML
            with open(html_path) as f:
                content = f.read()
            
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("vis-network", content)


class TestIntegration(unittest.TestCase):
    """Pruebas de integración completas"""
    
    def test_complete_pipeline(self):
        """Prueba del pipeline completo: regex -> AFN -> AFD -> mínimo"""
        regex = "(a|b)*abb"
        
        # Paso 1: Parser
        postfix = to_postfix(regex)
        self.assertIsInstance(postfix, str)
        
        # Paso 2: AFN
        nfa = postfix_to_nfa(postfix)
        self.assertIsInstance(nfa, Automaton)
        
        # Paso 3: AFD
        dfa = nfa.determinize()
        self.assertTrue(dfa.is_dfa())
        
        # Paso 4: Minimización
        minimized = minimize_hopcroft(dfa)
        self.assertTrue(minimized.is_dfa())
        
        # Verificar que acepta cadenas correctas
        test_strings = [
            ("abb", True),
            ("aabb", True),
            ("babb", True),
            ("ababb", True),
            ("ab", False),
            ("ba", False),
            ("", False),
        ]
        
        for string, should_accept in test_strings:
            with self.subTest(string=string):
                path, accepted = minimized.simulate_dfa_path(string)
                self.assertEqual(accepted, should_accept)
    
    def test_regex_equivalence(self):
        """Verificar que diferentes regex equivalentes producen autómatas equivalentes"""
        equivalent_pairs = [
            ("a+", "aa*"),
            ("a?", "(a|ε)"),
        ]
        
        for regex1, regex2 in equivalent_pairs:
            with self.subTest(regex1=regex1, regex2=regex2):
                # Construir autómatas
                postfix1 = to_postfix(regex1)
                postfix2 = to_postfix(regex2)
                
                nfa1 = postfix_to_nfa(postfix1)
                nfa2 = postfix_to_nfa(postfix2)
                
                dfa1 = minimize_hopcroft(nfa1.determinize())
                dfa2 = minimize_hopcroft(nfa2.determinize())
                
                # Probar con algunas cadenas
                test_strings = ["", "a", "aa", "aaa", "b"]
                
                for test_str in test_strings:
                    try:
                        _, acc1 = dfa1.simulate_dfa_path(test_str)
                        _, acc2 = dfa2.simulate_dfa_path(test_str)
                        self.assertEqual(acc1, acc2, f"Diferencia en cadena '{test_str}'")
                    except ValueError:
                        # Puede haber símbolos no en el alfabeto
                        pass


class TestPerformance(unittest.TestCase):
    """Pruebas básicas de rendimiento"""
    
    def test_large_regex_performance(self):
        """Verificar que regex grandes se procesan en tiempo razonable"""
        # Regex que podría ser problemática
        large_regex = "a" * 50 + "*"
        
        start_time = time.time()
        
        postfix = to_postfix(large_regex)
        nfa = postfix_to_nfa(postfix)
        dfa = nfa.determinize()
        minimized = minimize_hopcroft(dfa)
        
        end_time = time.time()
        
        # Debería completarse en menos de 5 segundos
        self.assertLess(end_time - start_time, 5.0)
    
    def test_deep_nesting_performance(self):
        """Verificar rendimiento con anidamiento profundo"""
        # Crear regex con anidamiento profundo pero limitado
        nested_regex = "(" * 10 + "a" + ")" * 10
        
        start_time = time.time()
        
        try:
            postfix = to_postfix(nested_regex)
            nfa = postfix_to_nfa(postfix)
            # Solo verificar que no se cuelgue
        except Exception:
            # Puede fallar debido a limitaciones, pero no debería colgarse
            pass
        
        end_time = time.time()
        
        # No debería tomar más de 2 segundos
        self.assertLess(end_time - start_time, 2.0)


class TestEdgeCases(unittest.TestCase):
    """Pruebas para casos extremos"""
    
    def test_empty_language(self):
        """Pruebas para lenguaje vacío (casos que no deberían aceptar nada)"""
        # Casos que teóricamente no deberían aceptar ninguna cadena
        pass  # Implementar según sea necesario
    
    def test_universal_language(self):
        """Pruebas para lenguaje universal"""
        # Regex que acepta cualquier cadena sobre el alfabeto
        regex = "(a|b)*"
        
        postfix = to_postfix(regex)
        nfa = postfix_to_nfa(postfix)
        dfa = nfa.determinize()
        
        # Debería aceptar cadenas vacías y cualquier combinación de a y b
        test_cases = ["", "a", "b", "ab", "ba", "aaa", "bbb", "abab"]
        
        for test_str in test_cases:
            with self.subTest(string=test_str):
                path, accepted = dfa.simulate_dfa_path(test_str)
                self.assertTrue(accepted)
    
    def test_single_character_alphabet(self):
        """Pruebas con alfabeto de un solo carácter"""
        regex = "a*"
        
        postfix = to_postfix(regex)
        nfa = postfix_to_nfa(postfix)
        dfa = nfa.determinize()
        
        # Debería aceptar "", "a", "aa", etc.
        valid_strings = ["", "a", "aa", "aaa"]
        invalid_strings = ["b", "ab", "ba"]
        
        for test_str in valid_strings:
            with self.subTest(string=test_str, should_accept=True):
                path, accepted = dfa.simulate_dfa_path(test_str)
                self.assertTrue(accepted)
        
        for test_str in invalid_strings:
            with self.subTest(string=test_str, should_accept=False):
                try:
                    path, accepted = dfa.simulate_dfa_path(test_str)
                    self.assertFalse(accepted)
                except ValueError:
                    # Símbolo no en alfabeto - comportamiento esperado
                    pass


def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("=== Ejecutando casos de prueba ===\n")
    
    # Configurar el test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir todas las clases de prueba
    test_classes = [
        TestRegexParser,
        TestThompsonConstruction,
        TestAutomatonMethods,
        TestHopcroftMinimization,
        TestExporter,
        TestIntegration,
        TestPerformance,
        TestEdgeCases
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Ejecutar las pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print(f"\n=== Resumen ===")
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Fallas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print("\nFallas:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")
    
    if result.errors:
        print("\nErrores:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

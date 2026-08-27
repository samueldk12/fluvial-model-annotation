# -*- coding: utf-8 -*-
"""
Executor Automatizado de Suíte de Testes (Unitários, Integração e Benchmarks).
Executa todos os testes do diretório tests/ e exibe um relatório estruturado.
"""

import os
import sys
import time
import unittest

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)


def run_all_tests():
    print("=" * 80)
    print("   SISTEMA NAVAL INTELIGENTE — EXECUTOR DE TESTES AUTOMATIZADOS")
    print("=" * 80)
    print(f"Diretório Raiz: {project_dir}")
    print(f"Início da Execução: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    loader = unittest.TestLoader()
    start_dir = os.path.join(project_dir, "tests")
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    t0 = time.time()
    result = runner.run(suite)
    elapsed = time.time() - t0

    print("\n" + "=" * 80)
    print("                     RELATÓRIO FINAL DE VALIDAÇÃO")
    print("=" * 80)
    print(f"Total de Testes Executados: {result.testsRun}")
    print(f"Testes Aprovados (Pass):   {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falhas (Failures):         {len(result.failures)}")
    print(f"Erros (Errors):            {len(result.errors)}")
    print(f"Tempo Total:               {elapsed:.2f} segundos")

    if result.wasSuccessful():
        print("\n>>> SUCESSO: 100% DOS TESTES AUTOMATIZADOS PASSARAM COM ÊXITO! <<<")
        print("=" * 80 + "\n")
        return 0
    else:
        print("\n>>> ATENÇÃO: HOUVE FALHAS OU ERROS NA SUÍTE DE TESTES <<<")
        print("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

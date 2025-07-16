#!/usr/bin/env python3
"""
Script para ejecutar tests del proyecto OnlineChatService
"""

import os
import sys
import subprocess
import argparse

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔥 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando: {command}")
        print(f"Código de salida: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def install_test_dependencies():
    """Instalar dependencias de testing"""
    print("📦 Instalando dependencias de testing...")
    return run_command("pip install -r requirements-test.txt", "Instalando dependencias de testing")

def run_websocket_tests():
    """Ejecutar solo tests de WebSocket"""
    return run_command("pytest tests/ -m websocket -v", "Ejecutando tests de WebSocket")

def run_unit_tests():
    """Ejecutar solo tests unitarios"""
    return run_command("pytest tests/ -m unit -v", "Ejecutando tests unitarios")

def run_integration_tests():
    """Ejecutar solo tests de integración"""
    return run_command("pytest tests/ -m integration -v", "Ejecutando tests de integración")

def run_all_tests():
    """Ejecutar todos los tests"""
    return run_command("pytest tests/ -v", "Ejecutando todos los tests")

def run_tests_with_coverage():
    """Ejecutar tests con reporte de cobertura"""
    # Instalar coverage si no está instalado
    run_command("pip install coverage", "Instalando coverage")
    
    success = run_command(
        "coverage run -m pytest tests/ -v", 
        "Ejecutando tests con medición de cobertura"
    )
    
    if success:
        run_command("coverage report", "Reporte de cobertura")
        run_command("coverage html", "Generando reporte HTML de cobertura")
        print("\n📊 Reporte HTML generado en: htmlcov/index.html")
    
    return success

def run_fast_tests():
    """Ejecutar tests rápidos (excluyendo tests lentos)"""
    return run_command("pytest tests/ -m \"not slow\" -v", "Ejecutando tests rápidos")

def lint_code():
    """Ejecutar linting del código"""
    print("🔍 Ejecutando linting...")
    
    # Instalar flake8 si no está instalado
    run_command("pip install flake8", "Instalando flake8")
    
    return run_command(
        "flake8 tests/ --max-line-length=100 --ignore=E501,W503", 
        "Verificando calidad del código de tests"
    )

def main():
    parser = argparse.ArgumentParser(description="Ejecutar tests del proyecto OnlineChatService")
    parser.add_argument("--install", action="store_true", help="Instalar dependencias de testing")
    parser.add_argument("--websocket", action="store_true", help="Ejecutar solo tests de WebSocket")
    parser.add_argument("--unit", action="store_true", help="Ejecutar solo tests unitarios")
    parser.add_argument("--integration", action="store_true", help="Ejecutar solo tests de integración")
    parser.add_argument("--fast", action="store_true", help="Ejecutar tests rápidos (sin tests lentos)")
    parser.add_argument("--coverage", action="store_true", help="Ejecutar tests con reporte de cobertura")
    parser.add_argument("--lint", action="store_true", help="Ejecutar linting del código")
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los tests")
    
    args = parser.parse_args()
    
    print("🚀 OnlineChatService - Test Runner")
    print("=" * 60)
    
    success = True
    
    # Si no se especifica ningún argumento, mostrar ayuda
    if not any(vars(args).values()):
        print("🔧 Opciones disponibles:")
        print("  --install     : Instalar dependencias de testing")
        print("  --websocket   : Ejecutar tests de WebSocket")
        print("  --unit        : Ejecutar tests unitarios")
        print("  --integration : Ejecutar tests de integración")
        print("  --fast        : Ejecutar tests rápidos")
        print("  --coverage    : Ejecutar tests con cobertura")
        print("  --lint        : Verificar calidad del código")
        print("  --all         : Ejecutar todos los tests")
        print("\n💡 Ejemplo: python run_tests.py --install --websocket")
        return
    
    if args.install:
        success &= install_test_dependencies()
    
    if args.lint:
        success &= lint_code()
    
    if args.websocket:
        success &= run_websocket_tests()
    elif args.unit:
        success &= run_unit_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.fast:
        success &= run_fast_tests()
    elif args.coverage:
        success &= run_tests_with_coverage()
    elif args.all:
        success &= run_all_tests()
    
    if success:
        print("\n✅ Todos los tests se ejecutaron exitosamente!")
    else:
        print("\n❌ Algunos tests fallaron. Revisa los errores arriba.")
        sys.exit(1)

if __name__ == "__main__":
    main() 
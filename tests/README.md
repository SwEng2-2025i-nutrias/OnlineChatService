# 🧪 Tests para OnlineChatService

Este directorio contiene todos los tests unitarios e integración para verificar la funcionalidad de los WebSockets y demás componentes del servicio de chat.

## 📁 Estructura de Tests

```
tests/
├── __init__.py                    # Configuración de tests
├── conftest.py                    # Fixtures y configuración de pytest
├── test_websocket_handlers.py     # Tests para manejadores WebSocket
├── test_websocket_server.py       # Tests para servidor WebSocket
├── test_websocket_integration.py  # Tests de integración completos
└── README.md                      # Esta documentación
```

## 🏷️ Marcadores de Tests

Los tests están organizados con los siguientes marcadores:

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.websocket` - Tests específicos de WebSocket
- `@pytest.mark.slow` - Tests que toman más tiempo en ejecutarse

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias de Testing

```bash
# Instalar dependencias específicas para tests
pip install -r requirements-test.txt

# O usar el script automatizado
python run_tests.py --install
```

### 2. Dependencias Incluidas

- `pytest` - Framework de testing
- `pytest-asyncio` - Soporte para tests async
- `pytest-mock` - Herramientas de mocking
- `python-socketio[client]` - Cliente WebSocket para tests
- `httpx` - Cliente HTTP async para tests
- `faker` - Generación de datos de prueba

## 🔧 Ejecutar Tests

### Usando el Script Automatizado

```bash
# Ver todas las opciones disponibles
python run_tests.py

# Instalar dependencias y ejecutar tests de WebSocket
python run_tests.py --install --websocket

# Ejecutar solo tests unitarios
python run_tests.py --unit

# Ejecutar tests de integración
python run_tests.py --integration

# Ejecutar tests rápidos (sin tests marcados como 'slow')
python run_tests.py --fast

# Ejecutar todos los tests
python run_tests.py --all

# Ejecutar tests con reporte de cobertura
python run_tests.py --coverage

# Verificar calidad del código
python run_tests.py --lint
```

### Usando Pytest Directamente

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar solo tests de WebSocket
pytest tests/ -m websocket -v

# Ejecutar tests unitarios
pytest tests/ -m unit -v

# Ejecutar tests de integración
pytest tests/ -m integration -v

# Ejecutar tests excluyendo los lentos
pytest tests/ -m "not slow" -v

# Ejecutar test específico
pytest tests/test_websocket_handlers.py::TestWebSocketHandlers::test_send_message_success -v

# Ejecutar con reporte de cobertura
coverage run -m pytest tests/ -v
coverage report
coverage html
```

## 📊 Tests Incluidos

### 🔌 Tests de WebSocket Handlers (`test_websocket_handlers.py`)

- ✅ Verificación de autenticación de sesiones
- ✅ Creación exitosa de chats
- ✅ Envío de mensajes con validaciones
- ✅ Manejo de errores (usuario no participante, chat no encontrado)
- ✅ Obtención de chats de usuario
- ✅ Obtención de mensajes de chat

### 🖥️ Tests de WebSocket Server (`test_websocket_server.py`)

- ✅ Conexión con token válido/inválido
- ✅ Autenticación via evento `authenticate`
- ✅ Unirse a chats con validaciones
- ✅ Limpieza de conexiones al desconectar
- ✅ Manejo de errores de autenticación

### 🔄 Tests de Integración (`test_websocket_integration.py`)

- ✅ Flujo completo: conectar → autenticar → crear chat → enviar mensaje
- ✅ Múltiples usuarios en chat grupal
- ✅ Indicadores de escritura (typing)
- ✅ Manejo de errores en flujos completos
- ✅ Métodos de broadcast del servidor
- ✅ Limpieza de conexiones en errores

## 🎯 Cobertura de Tests

Los tests cubren las siguientes funcionalidades principales:

### ✅ Funcionalidades Probadas

1. **Autenticación WebSocket**
   - Validación de tokens JWT
   - Manejo de sesiones
   - Eventos de autenticación

2. **Gestión de Chats**
   - Creación de chats privados/grupales
   - Validación de participantes
   - Obtención de chats por usuario

3. **Mensajería**
   - Envío de mensajes con validaciones
   - Verificación de permisos
   - Manejo de attachments
   - Actualización de contadores no leídos

4. **Gestión de Salas**
   - Unirse/salir de chats
   - Indicadores de escritura
   - Broadcast de eventos

5. **Manejo de Errores**
   - Autenticación fallida
   - Parámetros inválidos
   - Permisos insuficientes
   - Conexiones perdidas

## 🛠️ Configuración de Fixtures

### Fixtures Principales (`conftest.py`)

- `valid_jwt_token` - Token JWT válido para testing
- `invalid_jwt_token` - Token JWT inválido
- `test_user_data` - Datos de usuario de prueba
- `sample_chat` - Chat de ejemplo con participantes
- `sample_message` - Mensaje de ejemplo
- `sample_attachment` - Archivo adjunto de ejemplo
- `mock_chat_repository` - Mock del repositorio de chats
- `mock_message_repository` - Mock del repositorio de mensajes
- `websocket_test_client` - Cliente WebSocket para tests

## 🐛 Debugging Tests

### Ver Output Detallado

```bash
# Ejecutar con output detallado
pytest tests/ -v -s

# Ver logs en tiempo real
pytest tests/ -v -s --log-cli-level=INFO

# Ejecutar test específico con debugging
pytest tests/test_websocket_handlers.py::TestWebSocketHandlers::test_send_message_success -v -s --pdb
```

### Verificar Mocks

```bash
# Ejecutar con información de mocks
pytest tests/ -v --tb=short
```

## 📈 Métricas y Reportes

### Reporte de Cobertura

```bash
# Generar reporte de cobertura
python run_tests.py --coverage

# Ver reporte en terminal
coverage report

# Generar reporte HTML
coverage html
# Abre: htmlcov/index.html
```

### Calidad del Código

```bash
# Verificar estilo de código
python run_tests.py --lint

# O directamente
flake8 tests/ --max-line-length=100
```

## 🚨 CI/CD Integration

Para integrar en pipelines de CI/CD:

```yaml
# Ejemplo para GitHub Actions
- name: Install test dependencies
  run: pip install -r requirements-test.txt

- name: Run WebSocket tests
  run: pytest tests/ -m websocket -v

- name: Run all tests with coverage
  run: |
    coverage run -m pytest tests/ -v
    coverage xml
```

## 🔍 Troubleshooting

### Errores Comunes

1. **ImportError en fixtures**
   ```bash
   # Asegúrate de que el path está configurado
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   ```

2. **Tests de integración lentos**
   ```bash
   # Ejecutar solo tests rápidos
   pytest tests/ -m "not slow" -v
   ```

3. **Mocks no funcionan**
   ```bash
   # Verificar que se están usando las fixtures correctas
   pytest tests/ -v --fixtures
   ```


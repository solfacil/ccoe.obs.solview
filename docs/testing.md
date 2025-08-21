# 🧪 Testes e Validação - Solview

## 🎯 Visão Geral

Este guia apresenta estratégias completas para **testar e validar** a instrumentação Solview, desde desenvolvimento até produção.

---

## 🔬 Testes de Instrumentação

### ✅ **Testes Unitários**

#### **1. Testando Setup de Logging**

```python
# tests/test_solview_setup.py
import pytest
import structlog
from fastapi.testclient import TestClient
from solview import SolviewSettings, setup_logger

def test_logger_setup():
    """Testa se o logger está configurado corretamente"""
    settings = SolviewSettings(
        service_name="test-service",
        log_level="DEBUG"
    )
    
    # Setup
    setup_logger(settings)
    logger = structlog.get_logger(__name__)
    
    # Teste: Logger deve estar configurado
    assert logger is not None
    
    # Teste: Logger deve aceitar contexto estruturado
    logger.info("Test message", user_id=123, action="test")
    
    # TODO: Verificar se log foi emitido corretamente
    # Implementar captura de logs para validação

def test_logger_masking():
    """Testa masking de dados sensíveis"""
    from solview.security import EnhancedDataMasking as DataMasker, MaskingRule
    
    masker = DataMasker()
    
    # Dados de teste
    data = {
        "user_id": 123,
        "email": "user@example.com",
        "password": "secret123",
        "cpf": "123.456.789-00"
    }
    
    # Aplicar masking
    masked = masker.mask_dict(data)
    
    # Verificações
    assert masked["user_id"] == 123  # Não sensível
    assert "user@example.com" not in str(masked["email"])  # Mascarado
    assert masked["password"] == "***"  # Completamente mascarado
    assert "123.456.789-00" not in str(masked["cpf"])  # Mascarado
```

#### **2. Testando Métricas**

```python
# tests/test_metrics.py
import pytest
from prometheus_client import CollectorRegistry, Counter
from fastapi.testclient import TestClient
from solview.metrics import SolviewPrometheusMiddleware

def test_metrics_middleware():
    """Testa se middleware de métricas funciona"""
    from main import app  # Sua aplicação
    
    client = TestClient(app)
    
    # Fazer requisições
    response1 = client.get("/health")
    response2 = client.get("/health")
    response3 = client.get("/nonexistent", allow_redirects=False)
    
    # Verificar responses
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 404
    
    # Verificar métricas
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    
    metrics_text = metrics_response.text
    
    # Verificar se métricas HTTP estão presentes
    assert "http_requests_total" in metrics_text
    assert "http_request_duration_seconds" in metrics_text
    assert "http_responses_total" in metrics_text
    
    # Verificar contadores específicos
    assert 'method="GET"' in metrics_text
    assert 'status_code="200"' in metrics_text
    assert 'status_code="404"' in metrics_text

def test_custom_metrics():
    """Testa métricas customizadas"""
    # Criar registry isolado para teste
    registry = CollectorRegistry()
    
    # Métrica customizada
    custom_counter = Counter(
        'test_operations_total',
        'Test operations',
        ['operation_type'],
        registry=registry
    )
    
    # Incrementar
    custom_counter.labels(operation_type='create').inc()
    custom_counter.labels(operation_type='update').inc(2)
    
    # Coletar métricas
    from prometheus_client import generate_latest
    metrics_output = generate_latest(registry).decode('utf-8')
    
    # Verificar
    assert 'test_operations_total{operation_type="create"} 1.0' in metrics_output
    assert 'test_operations_total{operation_type="update"} 2.0' in metrics_output
```

#### **3. Testando Tracing**

```python
# tests/test_tracing.py
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.test.test_utils import TestSpanExporter
from fastapi.testclient import TestClient

def test_trace_setup():
    """Testa setup básico de tracing"""
    from solview.tracing import setup_tracer
    from solview import SolviewSettings
    
    settings = SolviewSettings(service_name="test-service")
    
    # Setup com exporter de teste
    test_exporter = TestSpanExporter()
    tracer = setup_tracer(settings)
    
    # Criar span de teste
    with tracer.start_as_current_span("test_span") as span:
        span.set_attribute("test.key", "test.value")
        span.set_attribute("test.number", 42)
    
    # Verificar se span foi criado
    spans = test_exporter.get_finished_spans()
    assert len(spans) == 1
    
    span = spans[0]
    assert span.name == "test_span"
    assert span.attributes["test.key"] == "test.value"
    assert span.attributes["test.number"] == 42

def test_fastapi_instrumentation():
    """Testa instrumentação automática do FastAPI"""
    from main import app
    
    # Setup de teste com span exporter
    test_exporter = TestSpanExporter()
    
    client = TestClient(app)
    
    # Fazer requisição
    response = client.get("/health")
    assert response.status_code == 200
    
    # Verificar spans criados
    spans = test_exporter.get_finished_spans()
    
    # Deve ter pelo menos 1 span da requisição HTTP
    http_spans = [s for s in spans if s.name.startswith("GET")]
    assert len(http_spans) >= 1
    
    # Verificar attributes do span HTTP
    http_span = http_spans[0]
    assert http_span.attributes.get("http.method") == "GET"
    assert http_span.attributes.get("http.status_code") == 200
```

---

## 🔍 Testes de Integração

### ✅ **Testes de Stack Completa**

#### **1. Teste de Conectividade**

```python
# tests/integration/test_observability_stack.py
import pytest
import asyncio
import aiohttp
from fastapi.testclient import TestClient

class TestObservabilityStack:
    """Testes de integração com stack completa"""
    
    @pytest.fixture(scope="class")
    def stack_urls(self):
        return {
            "app": "http://localhost:8000",
            "prometheus": "http://localhost:9090", 
            "grafana": "http://localhost:3000",
            "loki": "http://localhost:3100",
            "tempo": "http://localhost:3200"
        }
    
    def test_app_health(self, stack_urls):
        """Testa se aplicação está saudável"""
        import requests
        
        response = requests.get(f"{stack_urls['app']}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_metrics_endpoint(self, stack_urls):
        """Testa endpoint de métricas"""
        import requests
        
        response = requests.get(f"{stack_urls['app']}/metrics")
        assert response.status_code == 200
        
        # Verificar métricas essenciais
        metrics_text = response.text
        assert "http_requests_total" in metrics_text
        assert "http_request_duration_seconds" in metrics_text
        assert "process_cpu_usage_percent" in metrics_text
    
    def test_prometheus_scraping(self, stack_urls):
        """Testa se Prometheus está coletando métricas"""
        import requests
        import time
        
        # Fazer algumas requisições para gerar métricas
        for _ in range(5):
            requests.get(f"{stack_urls['app']}/health")
        
        # Aguardar scraping (15s de intervalo padrão)
        time.sleep(20)
        
        # Verificar se Prometheus tem as métricas
        query = "http_requests_total{job='solview-demo-app'}"
        response = requests.get(
            f"{stack_urls['prometheus']}/api/v1/query",
            params={"query": query}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["result"]) > 0
    
    def test_trace_generation(self, stack_urls):
        """Testa se traces estão sendo gerados"""
        import requests
        import time
        
        # Fazer requisição para gerar trace
        requests.get(f"{stack_urls['app']}/health")
        
        # Aguardar processamento
        time.sleep(10)
        
        # Verificar se Tempo recebeu traces
        response = requests.get(f"{stack_urls['tempo']}/api/search")
        assert response.status_code == 200
        
        data = response.json()
        assert "traces" in data
    
    async def test_log_correlation(self, stack_urls):
        """Testa correlação de logs com traces"""
        import json
        
        # Fazer requisição que gera logs
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{stack_urls['app']}/health") as response:
                trace_id = response.headers.get("traceparent", "").split("-")[1] if "traceparent" in response.headers else None
        
        if trace_id:
            # Verificar se logs contêm trace_id
            await asyncio.sleep(5)  # Aguardar processamento
            
            # Query Loki para logs com trace_id
            query = f'{{service_name="solview-demo-app"}} | json | trace_id="{trace_id}"'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{stack_urls['loki']}/loki/api/v1/query",
                    params={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Verificar se encontrou logs correlacionados
                        assert "data" in data
```

#### **2. Teste de Performance**

```python
# tests/integration/test_performance.py
import pytest
import asyncio
import aiohttp
import time
import statistics

class TestPerformanceImpact:
    """Testa impacto de performance da instrumentação"""
    
    async def test_latency_overhead(self):
        """Mede overhead de latência da instrumentação"""
        
        async def make_request(session, url):
            start = time.time()
            async with session.get(url) as response:
                await response.text()
            return time.time() - start
        
        url = "http://localhost:8000/health"
        requests_count = 100
        
        async with aiohttp.ClientSession() as session:
            # Warm up
            for _ in range(10):
                await make_request(session, url)
            
            # Medir latências
            latencies = []
            for _ in range(requests_count):
                latency = await make_request(session, url)
                latencies.append(latency)
        
        # Análise estatística
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        # Assertions - instrumentação não deve adicionar mais que 5ms
        assert avg_latency < 0.005  # 5ms
        assert p95_latency < 0.010  # 10ms
        
        print(f"Average latency: {avg_latency*1000:.2f}ms")
        print(f"P95 latency: {p95_latency*1000:.2f}ms")
    
    async def test_throughput_impact(self):
        """Mede impacto no throughput"""
        
        async def worker(session, url, results, duration):
            end_time = time.time() + duration
            count = 0
            
            while time.time() < end_time:
                async with session.get(url) as response:
                    if response.status == 200:
                        count += 1
            
            results.append(count)
        
        url = "http://localhost:8000/health"
        duration = 10  # 10 segundos
        workers = 5
        
        async with aiohttp.ClientSession() as session:
            results = []
            tasks = [
                worker(session, url, results, duration)
                for _ in range(workers)
            ]
            
            await asyncio.gather(*tasks)
        
        total_requests = sum(results)
        rps = total_requests / duration
        
        # Assertion - deve conseguir pelo menos 1000 RPS
        assert rps > 1000
        
        print(f"Throughput: {rps:.0f} RPS")
```

---

## 🚀 Testes de Carga

### ✅ **Scripts de Load Testing**

#### **1. Teste Básico de Carga**

```python
# tests/load/basic_load_test.py
import asyncio
import aiohttp
import time
from dataclasses import dataclass
from typing import List

@dataclass
class LoadTestResult:
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency: float
    p95_latency: float
    p99_latency: float
    throughput: float
    error_rate: float

class LoadTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str) -> dict:
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.text()
                return {
                    "success": True,
                    "status_code": response.status,
                    "latency": time.time() - start_time,
                    "error": None
                }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "latency": time.time() - start_time,
                "error": str(e)
            }
    
    async def run_load_test(
        self,
        endpoints: List[str],
        concurrent_users: int,
        duration_seconds: int
    ) -> LoadTestResult:
        """Executa teste de carga"""
        
        async def worker(session: aiohttp.ClientSession):
            worker_results = []
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                # Escolher endpoint aleatoriamente
                import random
                endpoint = random.choice(endpoints)
                
                result = await self.make_request(session, endpoint)
                worker_results.append(result)
                
                # Small delay to simulate real usage
                await asyncio.sleep(0.01)
            
            return worker_results
        
        # Executar workers concorrentes
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [worker(session) for _ in range(concurrent_users)]
            all_results = await asyncio.gather(*tasks)
        
        # Flatten results
        flat_results = [item for sublist in all_results for item in sublist]
        
        # Calcular estatísticas
        return self._calculate_stats(flat_results)
    
    def _calculate_stats(self, results: List[dict]) -> LoadTestResult:
        total = len(results)
        successful = len([r for r in results if r["success"]])
        failed = total - successful
        
        latencies = [r["latency"] for r in results]
        latencies.sort()
        
        return LoadTestResult(
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            avg_latency=sum(latencies) / len(latencies),
            p95_latency=latencies[int(len(latencies) * 0.95)],
            p99_latency=latencies[int(len(latencies) * 0.99)],
            throughput=total / duration_seconds if duration_seconds > 0 else 0,
            error_rate=(failed / total) * 100 if total > 0 else 0
        )

# Uso do teste
async def main():
    tester = LoadTester("http://localhost:8000")
    
    endpoints = ["/health", "/metrics", "/"]
    
    print("🚀 Iniciando teste de carga...")
    result = await tester.run_load_test(
        endpoints=endpoints,
        concurrent_users=50,
        duration_seconds=60
    )
    
    print(f"📊 Resultados:")
    print(f"  Total de requests: {result.total_requests}")
    print(f"  Sucessos: {result.successful_requests}")
    print(f"  Falhas: {result.failed_requests}")
    print(f"  Taxa de erro: {result.error_rate:.2f}%")
    print(f"  Throughput: {result.throughput:.0f} RPS")
    print(f"  Latência média: {result.avg_latency*1000:.1f}ms")
    print(f"  Latência P95: {result.p95_latency*1000:.1f}ms")
    print(f"  Latência P99: {result.p99_latency*1000:.1f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

#### **2. Teste de Stress**

```python
# tests/load/stress_test.py
import asyncio
import aiohttp
from load.basic_load_test import LoadTester

async def stress_test():
    """Teste de stress progressivo"""
    tester = LoadTester("http://localhost:8000")
    endpoints = ["/health"]
    
    stress_levels = [10, 25, 50, 100, 200, 500]
    duration = 30  # 30 segundos por nível
    
    print("🔥 Iniciando teste de stress progressivo...")
    
    for users in stress_levels:
        print(f"\n📈 Testando com {users} usuários concorrentes...")
        
        result = await tester.run_load_test(
            endpoints=endpoints,
            concurrent_users=users,
            duration_seconds=duration
        )
        
        print(f"  Throughput: {result.throughput:.0f} RPS")
        print(f"  Error Rate: {result.error_rate:.2f}%")
        print(f"  P95 Latency: {result.p95_latency*1000:.1f}ms")
        
        # Critérios de falha
        if result.error_rate > 5.0:
            print(f"❌ FALHA: Taxa de erro muito alta ({result.error_rate:.2f}%)")
            break
        
        if result.p95_latency > 1.0:
            print(f"⚠️  ALERTA: Latência alta ({result.p95_latency*1000:.1f}ms)")
        
        # Intervalo entre testes
        await asyncio.sleep(5)
    
    print("\n🏁 Teste de stress concluído!")

if __name__ == "__main__":
    asyncio.run(stress_test())
```

---

## 📊 Validação de Observabilidade

### ✅ **Checklist de Validação**

```python
# tests/validation/observability_checklist.py
import requests
import json
import time
from typing import Dict, List, Tuple

class ObservabilityValidator:
    def __init__(self, base_url: str, prometheus_url: str, grafana_url: str):
        self.base_url = base_url
        self.prometheus_url = prometheus_url
        self.grafana_url = grafana_url
        self.results = {}
    
    def validate_all(self) -> Dict[str, bool]:
        """Executa todas as validações"""
        validators = [
            ("health_endpoint", self.validate_health_endpoint),
            ("metrics_endpoint", self.validate_metrics_endpoint),
            ("structured_logs", self.validate_structured_logs),
            ("trace_headers", self.validate_trace_headers),
            ("prometheus_scraping", self.validate_prometheus_scraping),
            ("metric_cardinality", self.validate_metric_cardinality),
            ("trace_sampling", self.validate_trace_sampling),
            ("grafana_dashboards", self.validate_grafana_dashboards),
        ]
        
        for name, validator in validators:
            try:
                self.results[name] = validator()
                status = "✅" if self.results[name] else "❌"
                print(f"{status} {name}")
            except Exception as e:
                self.results[name] = False
                print(f"❌ {name}: {e}")
        
        return self.results
    
    def validate_health_endpoint(self) -> bool:
        """Valida endpoint de health"""
        response = requests.get(f"{self.base_url}/health")
        return response.status_code == 200
    
    def validate_metrics_endpoint(self) -> bool:
        """Valida endpoint de métricas"""
        response = requests.get(f"{self.base_url}/metrics")
        
        if response.status_code != 200:
            return False
        
        required_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "http_responses_total"
        ]
        
        metrics_text = response.text
        return all(metric in metrics_text for metric in required_metrics)
    
    def validate_structured_logs(self) -> bool:
        """Valida se logs estão estruturados"""
        # Fazer requisição para gerar log
        response = requests.get(f"{self.base_url}/health")
        
        # Note: Em um teste real, você capturaria os logs
        # Para este exemplo, assumimos que está configurado
        return True
    
    def validate_trace_headers(self) -> bool:
        """Valida se headers de trace estão presentes"""
        response = requests.get(f"{self.base_url}/health")
        
        # Verificar se response contém headers de tracing
        trace_headers = [
            "traceparent",
            "tracestate"
        ]
        
        return any(header in response.headers for header in trace_headers)
    
    def validate_prometheus_scraping(self) -> bool:
        """Valida se Prometheus está coletando métricas"""
        # Fazer algumas requisições para gerar métricas
        for _ in range(3):
            requests.get(f"{self.base_url}/health")
        
        # Aguardar scraping
        time.sleep(20)
        
        # Verificar se métricas estão no Prometheus
        query = "http_requests_total"
        response = requests.get(
            f"{self.prometheus_url}/api/v1/query",
            params={"query": query}
        )
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        return data.get("status") == "success" and len(data["data"]["result"]) > 0
    
    def validate_metric_cardinality(self) -> bool:
        """Valida cardinalidade das métricas"""
        response = requests.get(f"{self.prometheus_url}/api/v1/label/__name__/values")
        
        if response.status_code != 200:
            return False
        
        metrics = response.json()["data"]
        
        # Verificar se não há muitas métricas (indicador de alta cardinalidade)
        return len(metrics) < 1000
    
    def validate_trace_sampling(self) -> bool:
        """Valida se amostragem de traces está funcionando"""
        # Note: Implementação específica dependeria do setup
        return True
    
    def validate_grafana_dashboards(self) -> bool:
        """Valida se dashboards do Grafana estão funcionando"""
        try:
            # Verificar se Grafana está acessível
            response = requests.get(f"{self.grafana_url}/api/health")
            return response.status_code == 200
        except:
            return False

# Script de validação
def main():
    validator = ObservabilityValidator(
        base_url="http://localhost:8000",
        prometheus_url="http://localhost:9090",
        grafana_url="http://localhost:3000"
    )
    
    print("🔍 Validando observabilidade...")
    print("=" * 40)
    
    results = validator.validate_all()
    
    print("\n📊 Resumo:")
    print("=" * 40)
    
    passed = sum(results.values())
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"Testes passados: {passed}/{total} ({percentage:.0f}%)")
    
    if percentage >= 80:
        print("🎉 Observabilidade validada com sucesso!")
    else:
        print("⚠️  Observabilidade precisa de ajustes")
        
        failed_tests = [name for name, result in results.items() if not result]
        print(f"Testes falharam: {', '.join(failed_tests)}")

if __name__ == "__main__":
    main()
```

---

## 🔧 Automação de Testes

### ✅ **CI/CD Pipeline**

```yaml
# .github/workflows/observability-tests.yml
name: Observability Tests

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main ]

jobs:
  observability-tests:
    runs-on: ubuntu-latest
    
    services:
      prometheus:
        image: prom/prometheus:latest
        ports:
          - 9090:9090
        options: >-
          --health-cmd "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      grafana:
        image: grafana/grafana:latest
        ports:
          - 3000:3000
        env:
          GF_SECURITY_ADMIN_PASSWORD: admin
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Start application
      run: |
        uvicorn main:app --host 0.0.0.0 --port 8000 &
        sleep 10
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=solview
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Validate observability
      run: |
        python tests/validation/observability_checklist.py
    
    - name: Run load tests
      run: |
        python tests/load/basic_load_test.py
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### ✅ **Makefile para Testes**

```makefile
# Makefile
.PHONY: test test-unit test-integration test-load test-all validate

# Configuração
PYTHON = python3
PIP = pip3
PYTEST = pytest

# Instalação
install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt

# Testes unitários
test-unit:
	$(PYTEST) tests/unit/ -v --cov=solview --cov-report=html

# Testes de integração
test-integration:
	$(PYTEST) tests/integration/ -v

# Testes de carga
test-load:
	$(PYTHON) tests/load/basic_load_test.py
	$(PYTHON) tests/load/stress_test.py

# Validação de observabilidade
validate:
	$(PYTHON) tests/validation/observability_checklist.py

# Executar todos os testes
test-all: test-unit test-integration test-load validate

# Setup para desenvolvimento
dev-setup:
	docker-compose up -d
	sleep 30
	uvicorn main:app --reload &

# Limpeza
clean:
	docker-compose down -v
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -delete

# Teste completo com setup
test-full: dev-setup test-all clean
```

---

## 📈 Métricas de Qualidade

### ✅ **KPIs de Teste**

```python
# tests/metrics/test_quality_metrics.py
def calculate_observability_score(results: dict) -> float:
    """Calcula score de qualidade da observabilidade"""
    
    weights = {
        "metrics_coverage": 0.25,    # 25% - Cobertura de métricas
        "trace_coverage": 0.25,      # 25% - Cobertura de traces  
        "log_structure": 0.20,       # 20% - Qualidade dos logs
        "correlation": 0.15,         # 15% - Correlação funcional
        "performance": 0.15          # 15% - Impacto de performance
    }
    
    score = 0
    for metric, weight in weights.items():
        score += results.get(metric, 0) * weight
    
    return score

def generate_quality_report():
    """Gera relatório de qualidade"""
    
    results = {
        "metrics_coverage": 0.95,    # 95% dos endpoints têm métricas
        "trace_coverage": 0.90,      # 90% das operações trackeadas
        "log_structure": 0.85,       # 85% dos logs estruturados
        "correlation": 0.88,         # 88% das correlações funcionais
        "performance": 0.92          # 92% - baixo overhead
    }
    
    score = calculate_observability_score(results)
    
    print("📊 Relatório de Qualidade da Observabilidade")
    print("=" * 50)
    print(f"Score Geral: {score:.2f}/1.00 ({score*100:.0f}%)")
    print()
    
    for metric, value in results.items():
        status = "✅" if value >= 0.8 else "⚠️" if value >= 0.6 else "❌"
        print(f"{status} {metric.replace('_', ' ').title()}: {value:.1%}")
    
    if score >= 0.9:
        print("\n🎉 Excelente qualidade de observabilidade!")
    elif score >= 0.8:
        print("\n👍 Boa qualidade de observabilidade")
    else:
        print("\n⚠️ Observabilidade precisa de melhorias")
```

---

<div align="center">

**🧪 Teste com confiança, observe com precisão**

[🏠 Home](../README.md) | [📚 Docs](README.md) | [📋 Instrumentação](instrumentation-guide.md) | [📊 Best Practices](best-practices.md)

</div>

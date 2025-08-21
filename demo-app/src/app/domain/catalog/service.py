"""
🛍️ Catalog Domain Service - Integrado com Solview

Serviço de domínio para operações do catálogo usando Solview para observabilidade.
"""

import time
import random
from typing import List, Optional
from dataclasses import dataclass

from solview import get_logger
logger = get_logger(__name__)
from opentelemetry import trace
from opentelemetry.trace import get_current_span, format_trace_id, format_span_id


@dataclass
class Product:
    """Modelo de produto."""
    id: str
    name: str
    description: str
    price: float
    category: str
    stock: int
    available: bool = True


class CatalogService:
    """Serviço de catálogo integrado com Solview para observabilidade automática."""
    
    def __init__(self):
        """Inicializa o serviço de catálogo."""
        self._products = self._generate_sample_products()
        logger.info(
            "🛍️ CatalogService inicializado",
            products_count=len(self._products),
            event="catalog_service_init"
        )
    
    def _generate_sample_products(self) -> List[Product]:
        """Gera produtos de exemplo."""
        return [
            Product(
                id="prod-001",
                name="Smartphone Premium",
                description="Smartphone com 128GB de armazenamento",
                price=1299.99,
                category="eletrônicos",
                stock=50
            ),
            Product(
                id="prod-002", 
                name="Notebook Gamer",
                description="Notebook para jogos com placa de vídeo dedicada",
                price=2799.99,
                category="eletrônicos",
                stock=25
            ),
            Product(
                id="prod-003",
                name="Fones Bluetooth",
                description="Fones de ouvido sem fio com cancelamento de ruído",
                price=299.99,
                category="eletrônicos",
                stock=100
            ),
            Product(
                id="prod-004",
                name="Livro Python",
                description="Guia completo de programação Python",
                price=79.99,
                category="livros",
                stock=200
            ),
            Product(
                id="prod-005",
                name="Mesa de Escritório",
                description="Mesa ergonômica para home office",
                price=599.99,
                category="móveis",
                stock=15
            )
        ]
    
    async def list_products(
        self, 
        category: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Product]:
        """
        Lista produtos do catálogo.
        
        Args:
            category: Filtro por categoria
            limit: Limite de produtos
            offset: Offset para paginação
            
        Returns:
            List[Product]: Lista de produtos
        """
        # Usar tracer do OpenTelemetry se disponível (via Solview)
        current_tracer = trace.get_tracer(__name__)
        with current_tracer.start_as_current_span("catalog_list_products") as span:
            span.set_attribute("catalog.operation", "list")
            span.set_attribute("catalog.category", category or "all")
            span.set_attribute("catalog.limit", limit)
            span.set_attribute("catalog.offset", offset)
            
            start_time = time.time()
            
            try:
                # Simular latência de database
                await self._simulate_database_call("SELECT")
                
                # Filtrar por categoria se especificado
                products = self._products
                if category:
                    products = [p for p in products if p.category.lower() == category.lower()]
                
                # Aplicar paginação
                end_idx = offset + limit
                result = products[offset:end_idx]
                
                span.set_attribute("catalog.products_found", len(result))
                span.set_attribute("catalog.products_total", len(products))
                
                duration = time.time() - start_time
                
                # Obter trace context do Solview
                try:
                    span = get_current_span()
                    trace_id = format_trace_id(span.get_span_context().trace_id)
                    span_id = format_span_id(span.get_span_context().span_id)
                except Exception:
                    trace_id = "not-available"
                    span_id = "not-available"
                
                # Log estruturado via Solview
                logger.info(
                    "📋 Produtos listados com sucesso",
                    operation="list_products",
                    category=category or "all",
                    products_found=len(result),
                    duration_ms=duration * 1000,
                    trace_id=trace_id,
                    span_id=span_id,
                    event="catalog_list_success"
                )
                
                return result
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                # Log de erro via Solview
                logger.error(
                    "❌ Falha ao listar produtos",
                    operation="list_products",
                    error=str(e),
                    category=category,
                    event="catalog_list_error"
                )
                raise
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """
        Obtém um produto específico.
        
        Args:
            product_id: ID do produto
            
        Returns:
            Optional[Product]: Produto encontrado ou None
        """
        current_tracer = trace.get_tracer(__name__)
        with current_tracer.start_as_current_span("catalog_get_product") as span:
            span.set_attribute("catalog.operation", "get")
            span.set_attribute("catalog.product_id", product_id)
            
            start_time = time.time()
            
            try:
                # Simular consulta no cache
                await self._simulate_cache_lookup(product_id)
                
                # Buscar produto
                product = next((p for p in self._products if p.id == product_id), None)
                
                if product:
                    span.set_attribute("catalog.product_found", True)
                    span.set_attribute("catalog.product_name", product.name)
                    span.set_attribute("catalog.product_category", product.category)
                    # Métricas coletadas automaticamente pelo Solview middleware
                else:
                    span.set_attribute("catalog.product_found", False)
                    # Métricas coletadas automaticamente pelo Solview middleware
                
                duration = time.time() - start_time
                logger.info(
                    f"Product {'found' if product else 'not found'}",
                    extra={
                        "extra_fields": {
                            "operation": "get_product",
                            "product_id": product_id,
                            "found": product is not None,
                            "duration_ms": duration * 1000,
                            "event": "catalog_operation"
                        }
                    }
                )
                
                return product
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                # Erros rastreados automaticamente pelo Solview tracing
                
                logger.error(
                    f"Failed to get product {product_id}: {e}",
                    extra={
                        "extra_fields": {
                            "operation": "get_product",
                            "product_id": product_id,
                            "error": str(e),
                            "event": "catalog_error"
                        }
                    }
                )
                raise
    
    async def search_products(self, query: str) -> List[Product]:
        """
        Busca produtos por termo.
        
        Args:
            query: Termo de busca
            
        Returns:
            List[Product]: Produtos encontrados
        """
        current_tracer = trace.get_tracer(__name__)
        with current_tracer.start_as_current_span("catalog_search_products") as span:
            span.set_attribute("catalog.operation", "search")
            span.set_attribute("catalog.search_query", query)
            
            start_time = time.time()
            
            try:
                # Simular serviço de busca externa
                await self._simulate_external_search_service(query)
                
                # Buscar produtos (simulação simples)
                query_lower = query.lower()
                results = [
                    p for p in self._products 
                    if query_lower in p.name.lower() or query_lower in p.description.lower()
                ]
                
                span.set_attribute("catalog.results_found", len(results))
                span.set_attribute("catalog.search_query_length", len(query))
                
                self.metrics.record_catalog_operation("search", "success")
                
                duration = time.time() - start_time
                logger.info(
                    "Product search completed",
                    extra={
                        "extra_fields": {
                            "operation": "search_products",
                            "query": query,
                            "results_found": len(results),
                            "duration_ms": duration * 1000,
                            "event": "catalog_operation"
                        }
                    }
                )
                
                return results
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                # Erros de busca rastreados automaticamente pelo Solview
                
                logger.error(
                    f"Failed to search products with query '{query}': {e}",
                    extra={
                        "extra_fields": {
                            "operation": "search_products",
                            "query": query,
                            "error": str(e),
                            "event": "catalog_error"
                        }
                    }
                )
                raise
    
    async def _simulate_database_call(self, operation: str) -> None:
        """Simula chamada ao banco de dados."""
        current_tracer = trace.get_tracer(__name__)
        with current_tracer.start_as_current_span("database_query") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.operation", operation)
            span.set_attribute("db.table", "products")
            
            # Simular latência
            await self._sleep_random(0.01, 0.05)
    
    async def _simulate_cache_lookup(self, key: str) -> None:
        """Simula consulta no cache."""
        current_tracer = trace.get_tracer(__name__)
        with current_tracer.start_as_current_span("cache_lookup") as span:
            span.set_attribute("cache.system", "redis")
            span.set_attribute("cache.operation", "GET")
            span.set_attribute("cache.key", f"product:{key}")
            
            # Simular latência
            await self._sleep_random(0.001, 0.005)
    
    async def _simulate_external_search_service(self, query: str) -> None:
        """Simula chamada para serviço de busca externo."""
        current_tracer = trace.get_tracer(__name__)
        with current_tracer.start_as_current_span("external_search_api") as span:
            span.set_attribute("http.method", "POST")
            span.set_attribute("http.url", "https://search-api.company.com/search")
            span.set_attribute("search.query", query)
            span.set_attribute("search.service", "elasticsearch")
            
            # Simular latência de rede
            await self._sleep_random(0.05, 0.15)
            
            # Simular possível falha ocasional
            if random.random() < 0.05:  # 5% de chance de falha
                span.set_attribute("error", True)
                span.set_attribute("http.status_code", 503)
                raise Exception("Search service temporarily unavailable")
            
            span.set_attribute("http.status_code", 200)
    
    async def _sleep_random(self, min_time: float, max_time: float) -> None:
        """Simula latência aleatória."""
        import asyncio
        sleep_time = random.uniform(min_time, max_time)
        await asyncio.sleep(sleep_time)


# Instância global do serviço
_catalog_service: Optional[CatalogService] = None


def get_catalog_service() -> CatalogService:
    """
    Obtém instância do serviço de catálogo.
    
    Returns:
        CatalogService: Instância do serviço
    """
    global _catalog_service
    if _catalog_service is None:
        _catalog_service = CatalogService()
    return _catalog_service

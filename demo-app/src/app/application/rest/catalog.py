"""
🛍️ Catalog REST API

Endpoints REST para operações do catálogo de produtos.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from pydantic import BaseModel
from opentelemetry import trace

from app.domain.catalog.service import get_catalog_service, CatalogService, Product

router = APIRouter()
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ProductResponse(BaseModel):
    """Modelo de resposta para produto."""
    id: str
    name: str
    description: str
    price: float
    category: str
    stock: int
    available: bool


class ProductListResponse(BaseModel):
    """Modelo de resposta para lista de produtos."""
    products: List[ProductResponse]
    total: int
    limit: int
    offset: int


def product_to_response(product: Product) -> ProductResponse:
    """Converte Product para ProductResponse."""
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        category=product.category,
        stock=product.stock,
        available=product.available
    )


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    limit: int = Query(10, ge=1, le=100, description="Limite de produtos por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    catalog_service: CatalogService = Depends(get_catalog_service)
) -> ProductListResponse:
    """
    Lista produtos do catálogo.
    
    Args:
        category: Categoria para filtrar (opcional)
        limit: Número máximo de produtos por página
        offset: Offset para paginação
        catalog_service: Serviço de catálogo
        
    Returns:
        ProductListResponse: Lista de produtos
    """
    with tracer.start_as_current_span("api_list_products") as span:
        span.set_attribute("api.operation", "list_products")
        span.set_attribute("api.category", category or "all")
        span.set_attribute("api.limit", limit)
        span.set_attribute("api.offset", offset)
        
        try:
            products = await catalog_service.list_products(
                category=category,
                limit=limit,
                offset=offset
            )
            
            # Converter para modelos de resposta
            product_responses = [product_to_response(p) for p in products]
            
            response = ProductListResponse(
                products=product_responses,
                total=len(product_responses),  # Simplificado para demo
                limit=limit,
                offset=offset
            )
            
            span.set_attribute("api.products_returned", len(product_responses))
            
            logger.info(
                f"Listed {len(product_responses)} products",
                extra={
                    "extra_fields": {
                        "endpoint": "list_products",
                        "category": category,
                        "products_returned": len(product_responses),
                        "event": "api_success"
                    }
                }
            )
            
            return response
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                f"Failed to list products: {e}",
                extra={
                    "extra_fields": {
                        "endpoint": "list_products",
                        "error": str(e),
                        "event": "api_error"
                    }
                }
            )
            
            raise HTTPException(
                status_code=500,
                detail="Internal server error while listing products"
            )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(..., description="ID do produto"),
    catalog_service: CatalogService = Depends(get_catalog_service)
) -> ProductResponse:
    """
    Obtém um produto específico.
    
    Args:
        product_id: ID do produto
        catalog_service: Serviço de catálogo
        
    Returns:
        ProductResponse: Dados do produto
        
    Raises:
        HTTPException: 404 se produto não encontrado
    """
    with tracer.start_as_current_span("api_get_product") as span:
        span.set_attribute("api.operation", "get_product")
        span.set_attribute("api.product_id", product_id)
        
        try:
            product = await catalog_service.get_product(product_id)
            
            if not product:
                span.set_attribute("api.product_found", False)
                
                logger.warning(
                    f"Product not found: {product_id}",
                    extra={
                        "extra_fields": {
                            "endpoint": "get_product",
                            "product_id": product_id,
                            "event": "product_not_found"
                        }
                    }
                )
                
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {product_id} not found"
                )
            
            span.set_attribute("api.product_found", True)
            span.set_attribute("api.product_name", product.name)
            
            response = product_to_response(product)
            
            logger.info(
                f"Product retrieved: {product.name}",
                extra={
                    "extra_fields": {
                        "endpoint": "get_product",
                        "product_id": product_id,
                        "product_name": product.name,
                        "event": "api_success"
                    }
                }
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                f"Failed to get product {product_id}: {e}",
                extra={
                    "extra_fields": {
                        "endpoint": "get_product",
                        "product_id": product_id,
                        "error": str(e),
                        "event": "api_error"
                    }
                }
            )
            
            raise HTTPException(
                status_code=500,
                detail="Internal server error while retrieving product"
            )


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Termo de busca"),
    catalog_service: CatalogService = Depends(get_catalog_service)
) -> ProductListResponse:
    """
    Busca produtos por termo.
    
    Args:
        q: Termo de busca
        catalog_service: Serviço de catálogo
        
    Returns:
        ProductListResponse: Produtos encontrados
    """
    with tracer.start_as_current_span("api_search_products") as span:
        span.set_attribute("api.operation", "search_products")
        span.set_attribute("api.search_query", q)
        span.set_attribute("api.search_query_length", len(q))
        
        try:
            products = await catalog_service.search_products(q)
            
            # Converter para modelos de resposta
            product_responses = [product_to_response(p) for p in products]
            
            response = ProductListResponse(
                products=product_responses,
                total=len(product_responses),
                limit=len(product_responses),  # Sem paginação na busca para simplicidade
                offset=0
            )
            
            span.set_attribute("api.results_found", len(product_responses))
            
            logger.info(
                f"Search completed: '{q}' returned {len(product_responses)} results",
                extra={
                    "extra_fields": {
                        "endpoint": "search_products",
                        "query": q,
                        "results_found": len(product_responses),
                        "event": "api_success"
                    }
                }
            )
            
            return response
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                f"Failed to search products with query '{q}': {e}",
                extra={
                    "extra_fields": {
                        "endpoint": "search_products",
                        "query": q,
                        "error": str(e),
                        "event": "api_error"
                    }
                }
            )
            
            raise HTTPException(
                status_code=500,
                detail="Internal server error while searching products"
            )


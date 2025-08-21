"""
🔗 Demo App Client

HTTP client for communicating with the demo application.
Instrumented with OpenTelemetry for service graph generation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import httpx
from solview import get_logger
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.environment import Settings

# Instrument httpx for automatic tracing
HTTPXClientInstrumentor().instrument()

tracer = trace.get_tracer(__name__)
logger = get_logger(__name__)


class DemoAppClient:
    """
    HTTP client for Demo App communication with observability.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Demo App client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.demo_app_url
        self.timeout = settings.demo_app_timeout
        
        # Configure HTTP client with observability
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "User-Agent": f"backend-processor/{settings.version}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        )
    
    async def check_health(self) -> Optional[Dict[str, Any]]:
        """
        Check Demo App health status.
        
        Returns:
            Optional[Dict]: Health data or None if unavailable
        """
        with tracer.start_as_current_span("demo_app_health_check") as span:
            span.set_attribute("demo_app.url", self.base_url)
            span.set_attribute("demo_app.operation", "health_check")
            
            try:
                response = await self.client.get("/health")
                response.raise_for_status()
                
                health_data = response.json()
                span.set_attribute("demo_app.status", health_data.get("status", "unknown"))
                span.set_attribute("demo_app.version", health_data.get("version", "unknown"))
                
                logger.info(
                    "Demo App health check successful",
                    demo_app_status=health_data.get("status"),
                    demo_app_version=health_data.get("version"),
                    event="demo_app_health_check"
                )
                
                return health_data
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.warning(
                    "Demo App health check failed",
                    error=str(e),
                    demo_app_url=self.base_url,
                    event="demo_app_health_check_failed"
                )
                return None
    
    async def get_products(self, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch products from Demo App.
        
        Args:
            category: Product category filter
            limit: Maximum number of products
            
        Returns:
            List[Dict]: Product list
        """
        with tracer.start_as_current_span("demo_app_get_products") as span:
            span.set_attribute("demo_app.operation", "get_products")
            span.set_attribute("demo_app.category", category or "all")
            span.set_attribute("demo_app.limit", limit)
            
            try:
                params = {"limit": limit}
                if category:
                    params["category"] = category
                
                response = await self.client.get("/api/catalog/products", params=params)
                response.raise_for_status()
                
                data = response.json()
                products = data.get("products", [])
                
                span.set_attribute("demo_app.products_returned", len(products))
                
                logger.info(
                    "Fetched products from Demo App",
                    products_count=len(products),
                    category=category or "all",
                    event="demo_app_get_products"
                )
                
                return products
            
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to fetch products from Demo App",
                    error=str(e),
                    category=category,
                    event="demo_app_get_products_failed"
                )
                return []
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch specific product from Demo App.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Optional[Dict]: Product data or None if not found
        """
        with tracer.start_as_current_span("demo_app_get_product") as span:
            span.set_attribute("demo_app.operation", "get_product")
            span.set_attribute("demo_app.product_id", product_id)
            
            try:
                response = await self.client.get(f"/api/catalog/products/{product_id}")
                response.raise_for_status()
                
                product = response.json()
                span.set_attribute("demo_app.product_name", product.get("name", "unknown"))
                
                logger.info(
                    "Product fetched from Demo App",
                    product_id=product_id,
                    product_name=product.get("name"),
                    event="demo_app_get_product"
                )
                
                return product
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    span.set_attribute("demo_app.product_found", False)
                    logger.warning(
                        "Product not found in Demo App",
                        product_id=product_id,
                        event="demo_app_product_not_found"
                    )
                    return None
                raise
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to fetch product from Demo App",
                    error=str(e),
                    product_id=product_id,
                    event="demo_app_get_product_error"
                )
                raise
    
    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Search products in Demo App.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict]: Search results
        """
        with tracer.start_as_current_span("demo_app_search_products") as span:
            span.set_attribute("demo_app.operation", "search_products")
            span.set_attribute("demo_app.search_query", query)
            span.set_attribute("demo_app.search_query_length", len(query))
            
            try:
                response = await self.client.get("/api/catalog/search", params={"q": query})
                response.raise_for_status()
                
                data = response.json()
                products = data.get("products", [])
                
                span.set_attribute("demo_app.search_results", len(products))
                
                logger.info(
                    "Product search completed in Demo App",
                    query=query,
                    results_count=len(products),
                    event="demo_app_search_products"
                )
                
                return products
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to search products in Demo App",
                    error=str(e),
                    query=query,
                    event="demo_app_search_products_error"
                )
                raise
    
    async def create_order(self, cart_id: str) -> Dict[str, Any]:
        """
        Create order in Demo App.
        
        Args:
            cart_id: Cart identifier
            
        Returns:
            Dict: Created order data
        """
        with tracer.start_as_current_span("demo_app_create_order") as span:
            span.set_attribute("demo_app.operation", "create_order")
            span.set_attribute("demo_app.cart_id", cart_id)
            
            try:
                payload = {"cart_id": cart_id}
                response = await self.client.post("/api/orders/", json=payload)
                response.raise_for_status()
                
                order = response.json()
                span.set_attribute("demo_app.order_id", order.get("id", "unknown"))
                span.set_attribute("demo_app.order_total", order.get("total", 0))
                
                logger.info(
                    "Order created in Demo App",
                    cart_id=cart_id,
                    order_id=order.get("id"),
                    order_total=order.get("total"),
                    event="demo_app_create_order"
                )
                
                return order
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to create order in Demo App",
                    error=str(e),
                    cart_id=cart_id,
                    event="demo_app_create_order_error"
                )
                raise
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        """
        Fetch all orders from Demo App.
        
        Returns:
            List[Dict]: Orders list
        """
        with tracer.start_as_current_span("demo_app_get_orders") as span:
            span.set_attribute("demo_app.operation", "get_orders")
            
            try:
                response = await self.client.get("/api/orders/")
                response.raise_for_status()
                
                orders = response.json()
                span.set_attribute("demo_app.orders_count", len(orders))
                
                logger.info(
                    "Orders fetched from Demo App",
                    orders_count=len(orders),
                    event="demo_app_get_orders"
                )
                
                return orders
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                
                logger.error(
                    "Failed to fetch orders from Demo App",
                    error=str(e),
                    event="demo_app_get_orders_error"
                )
                raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

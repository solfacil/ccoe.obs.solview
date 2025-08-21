"""
📊 Analytics API

Endpoints for analytics and reporting that communicate with Demo App.
Generates rich service graph through inter-service communication.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from solview import get_logger
logger = get_logger(__name__)
from opentelemetry import trace

from app.environment import get_settings, Settings
from app.services.demo_client import DemoAppClient

router = APIRouter()
tracer = trace.get_tracer(__name__)


class ProductAnalytics(BaseModel):
    """Product analytics data model."""
    total_products: int
    categories: Dict[str, int]
    average_price: float
    top_products: List[Dict[str, Any]]
    analysis_timestamp: datetime


class OrderAnalytics(BaseModel):
    """Order analytics data model."""
    total_orders: int
    total_revenue: float
    average_order_value: float
    orders_by_status: Dict[str, int]
    analysis_timestamp: datetime


class SystemReport(BaseModel):
    """System-wide analytics report."""
    service_health: Dict[str, Any]
    product_analytics: ProductAnalytics
    order_analytics: OrderAnalytics
    processing_stats: Dict[str, Any]
    generated_at: datetime


@router.get("/products", response_model=ProductAnalytics)
async def analyze_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    settings: Settings = Depends(get_settings)
) -> ProductAnalytics:
    """
    Analyze products data from Demo App.
    
    Args:
        category: Optional category filter
        settings: Application settings
        
    Returns:
        ProductAnalytics: Product analysis results
    """
    with tracer.start_as_current_span("analytics_analyze_products") as span:
        span.set_attribute("analytics.operation", "analyze_products")
        span.set_attribute("analytics.category_filter", category or "all")
        
        try:
            demo_client = DemoAppClient(settings)
            
            # Fetch products from Demo App (creates service graph edge)
            products = await demo_client.get_products(category=category, limit=100)
            
            # Perform analytics processing
            total_products = len(products)
            categories = {}
            prices = []
            
            for product in products:
                product_category = product.get("category", "unknown")
                categories[product_category] = categories.get(product_category, 0) + 1
                
                price = product.get("price", 0)
                if price > 0:
                    prices.append(price)
            
            average_price = sum(prices) / len(prices) if prices else 0
            
            # Get top products by price
            top_products = sorted(
                products, 
                key=lambda x: x.get("price", 0), 
                reverse=True
            )[:5]
            
            span.set_attribute("analytics.products_processed", total_products)
            span.set_attribute("analytics.categories_found", len(categories))
            span.set_attribute("analytics.average_price", average_price)
            
            analytics_result = ProductAnalytics(
                total_products=total_products,
                categories=categories,
                average_price=round(average_price, 2),
                top_products=top_products,
                analysis_timestamp=datetime.now()
            )
            
            logger.info(
                "Product analytics completed",
                total_products=total_products,
                categories_count=len(categories),
                average_price=average_price,
                event="analytics_products_completed"
            )
            
            await demo_client.close()
            return analytics_result
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Product analytics failed",
                error=str(e),
                category=category,
                event="analytics_products_error"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze products: {str(e)}"
            )


@router.get("/orders", response_model=OrderAnalytics)
async def analyze_orders(
    settings: Settings = Depends(get_settings)
) -> OrderAnalytics:
    """
    Analyze orders data from Demo App.
    
    Args:
        settings: Application settings
        
    Returns:
        OrderAnalytics: Order analysis results
    """
    with tracer.start_as_current_span("analytics_analyze_orders") as span:
        span.set_attribute("analytics.operation", "analyze_orders")
        
        try:
            demo_client = DemoAppClient(settings)
            
            # Fetch orders from Demo App (creates service graph edge)
            orders = await demo_client.get_orders()
            
            # Perform analytics processing
            total_orders = len(orders)
            total_revenue = 0
            orders_by_status = {}
            
            for order in orders:
                status = order.get("status", "unknown")
                orders_by_status[status] = orders_by_status.get(status, 0) + 1
                
                order_total = order.get("total", 0)
                total_revenue += order_total
            
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            span.set_attribute("analytics.orders_processed", total_orders)
            span.set_attribute("analytics.total_revenue", total_revenue)
            span.set_attribute("analytics.average_order_value", average_order_value)
            
            analytics_result = OrderAnalytics(
                total_orders=total_orders,
                total_revenue=round(total_revenue, 2),
                average_order_value=round(average_order_value, 2),
                orders_by_status=orders_by_status,
                analysis_timestamp=datetime.now()
            )
            
            logger.info(
                "Order analytics completed",
                total_orders=total_orders,
                total_revenue=total_revenue,
                average_order_value=average_order_value,
                event="analytics_orders_completed"
            )
            
            await demo_client.close()
            return analytics_result
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Order analytics failed",
                error=str(e),
                event="analytics_orders_error"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze orders: {str(e)}"
            )


@router.get("/report", response_model=SystemReport)
async def generate_system_report(
    settings: Settings = Depends(get_settings)
) -> SystemReport:
    """
    Generate comprehensive system analytics report.
    
    This endpoint demonstrates complex service graph by making multiple
    calls to the Demo App and aggregating data.
    
    Args:
        settings: Application settings
        
    Returns:
        SystemReport: Complete system report
    """
    with tracer.start_as_current_span("analytics_generate_system_report") as span:
        span.set_attribute("analytics.operation", "generate_system_report")
        
        try:
            demo_client = DemoAppClient(settings)
            
            # Parallel execution to demonstrate concurrent service calls
            with tracer.start_as_current_span("analytics_parallel_data_fetch") as parallel_span:
                parallel_span.set_attribute("analytics.fetch_type", "parallel")
                
                # Fetch data in parallel for performance
                health_task = demo_client.check_health()
                products_task = demo_client.get_products(limit=50)
                orders_task = demo_client.get_orders()
                
                # Wait for all tasks to complete
                health_data, products, orders = await asyncio.gather(
                    health_task,
                    products_task,
                    orders_task,
                    return_exceptions=True
                )
            
            # Process health data
            if isinstance(health_data, Exception):
                service_health = {"status": "error", "error": str(health_data)}
            else:
                service_health = health_data or {"status": "unknown"}
            
            # Process products data
            if isinstance(products, Exception):
                logger.error(f"Failed to fetch products: {products}")
                products = []
            
            # Process orders data
            if isinstance(orders, Exception):
                logger.error(f"Failed to fetch orders: {orders}")
                orders = []
            
            # Generate product analytics
            product_categories = {}
            product_prices = []
            
            for product in products:
                category = product.get("category", "unknown")
                product_categories[category] = product_categories.get(category, 0) + 1
                
                price = product.get("price", 0)
                if price > 0:
                    product_prices.append(price)
            
            top_products = sorted(
                products, 
                key=lambda x: x.get("price", 0), 
                reverse=True
            )[:3]
            
            product_analytics = ProductAnalytics(
                total_products=len(products),
                categories=product_categories,
                average_price=round(sum(product_prices) / len(product_prices), 2) if product_prices else 0,
                top_products=top_products,
                analysis_timestamp=datetime.now()
            )
            
            # Generate order analytics
            order_revenue = sum(order.get("total", 0) for order in orders)
            order_statuses = {}
            
            for order in orders:
                status = order.get("status", "unknown")
                order_statuses[status] = order_statuses.get(status, 0) + 1
            
            order_analytics = OrderAnalytics(
                total_orders=len(orders),
                total_revenue=round(order_revenue, 2),
                average_order_value=round(order_revenue / len(orders), 2) if orders else 0,
                orders_by_status=order_statuses,
                analysis_timestamp=datetime.now()
            )
            
            # Processing statistics
            processing_stats = {
                "products_processed": len(products),
                "orders_processed": len(orders),
                "categories_analyzed": len(product_categories),
                "processing_time_ms": (datetime.now().timestamp() * 1000),
                "backend_processor_version": settings.version
            }
            
            span.set_attribute("analytics.products_processed", len(products))
            span.set_attribute("analytics.orders_processed", len(orders))
            span.set_attribute("analytics.categories_found", len(product_categories))
            
            system_report = SystemReport(
                service_health=service_health,
                product_analytics=product_analytics,
                order_analytics=order_analytics,
                processing_stats=processing_stats,
                generated_at=datetime.now()
            )
            
            logger.info(
                "System report generated successfully",
                products_processed=len(products),
                orders_processed=len(orders),
                service_health_status=service_health.get("status"),
                event="analytics_system_report_completed"
            )
            
            await demo_client.close()
            return system_report
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "System report generation failed",
                error=str(e),
                event="analytics_system_report_error"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate system report: {str(e)}"
            )


@router.post("/process-batch")
async def process_product_batch(
    category: Optional[str] = Query(None, description="Category to process"),
    batch_size: int = Query(10, ge=1, le=50, description="Batch size"),
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Process a batch of products for complex analytics.
    
    This endpoint demonstrates batch processing and multiple service calls.
    
    Args:
        category: Category to process
        batch_size: Number of products to process
        settings: Application settings
        
    Returns:
        Dict: Processing results
    """
    with tracer.start_as_current_span("analytics_process_batch") as span:
        span.set_attribute("analytics.operation", "process_batch")
        span.set_attribute("analytics.category", category or "all")
        span.set_attribute("analytics.batch_size", batch_size)
        
        try:
            demo_client = DemoAppClient(settings)
            
            # Fetch products
            products = await demo_client.get_products(category=category, limit=batch_size)
            
            processed_products = []
            total_processing_time = 0
            
            # Process each product individually (creates multiple service graph edges)
            for product in products:
                with tracer.start_as_current_span("analytics_process_single_product") as product_span:
                    product_id = product.get("id")
                    product_span.set_attribute("product.id", product_id)
                    
                    start_time = datetime.now()
                    
                    # Fetch detailed product info (additional service call)
                    detailed_product = await demo_client.get_product(product_id)
                    
                    if detailed_product:
                        # Simulate processing
                        processing_result = {
                            "id": product_id,
                            "name": detailed_product.get("name"),
                            "price": detailed_product.get("price"),
                            "category": detailed_product.get("category"),
                            "processed_at": datetime.now().isoformat(),
                            "processing_duration_ms": (datetime.now() - start_time).total_seconds() * 1000
                        }
                        
                        processed_products.append(processing_result)
                        total_processing_time += processing_result["processing_duration_ms"]
            
            span.set_attribute("analytics.products_processed", len(processed_products))
            span.set_attribute("analytics.total_processing_time_ms", total_processing_time)
            
            result = {
                "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "processed_products": processed_products,
                "total_processed": len(processed_products),
                "total_processing_time_ms": total_processing_time,
                "average_processing_time_ms": total_processing_time / len(processed_products) if processed_products else 0,
                "category": category,
                "batch_size": batch_size,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(
                "Batch processing completed",
                batch_size=batch_size,
                products_processed=len(processed_products),
                total_time_ms=total_processing_time,
                category=category,
                event="analytics_batch_processing_completed"
            )
            
            await demo_client.close()
            return result
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Batch processing failed",
                error=str(e),
                category=category,
                batch_size=batch_size,
                event="analytics_batch_processing_error"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process batch: {str(e)}"
            )

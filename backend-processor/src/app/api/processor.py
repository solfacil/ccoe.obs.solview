"""
⚙️ Processor API

Endpoints for data processing operations that create rich service graphs.
Demonstrates various patterns of inter-service communication.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel
from solview import get_logger
logger = get_logger(__name__)
from opentelemetry import trace

from app.environment import get_settings, Settings
from app.services.demo_client import DemoAppClient

router = APIRouter()
tracer = trace.get_tracer(__name__)


class ProcessingJob(BaseModel):
    """Processing job data model."""
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    parameters: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class OrderProcessingRequest(BaseModel):
    """Order processing request model."""
    cart_id: str
    customer_email: str
    priority: str = "normal"
    notify_customer: bool = True


class ProductEnrichmentRequest(BaseModel):
    """Product enrichment request model."""
    product_ids: List[str]
    enrichment_type: str = "full"
    include_analytics: bool = True


# In-memory job storage (in production, use Redis or database)
processing_jobs: Dict[str, ProcessingJob] = {}


@router.post("/orders/process", response_model=Dict[str, Any])
async def process_order_workflow(
    request: OrderProcessingRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Process order workflow with Demo App integration.
    
    This creates multiple service graph connections through order processing.
    
    Args:
        request: Order processing request
        background_tasks: FastAPI background tasks
        settings: Application settings
        
    Returns:
        Dict: Processing result
    """
    with tracer.start_as_current_span("processor_order_workflow") as span:
        span.set_attribute("processor.operation", "order_workflow")
        span.set_attribute("processor.cart_id", request.cart_id)
        span.set_attribute("processor.customer_email", request.customer_email)
        span.set_attribute("processor.priority", request.priority)
        
        job_id = str(uuid4())
        
        try:
            demo_client = DemoAppClient(settings)
            
            # Step 1: Create order in Demo App
            with tracer.start_as_current_span("processor_create_order") as create_span:
                create_span.set_attribute("step", "create_order")
                
                order = await demo_client.create_order(request.cart_id)
                order_id = order.get("id")
                order_total = order.get("total", 0)
                
                create_span.set_attribute("order.id", order_id)
                create_span.set_attribute("order.total", order_total)
            
            # Step 2: Fetch order details
            with tracer.start_as_current_span("processor_fetch_order_details") as fetch_span:
                fetch_span.set_attribute("step", "fetch_order_details")
                
                # Additional service call to get complete order data
                orders = await demo_client.get_orders()
                current_order = next((o for o in orders if o.get("id") == order_id), None)
                
                if not current_order:
                    raise HTTPException(status_code=404, detail="Order not found after creation")
            
            # Step 3: Process order items (fetch product details)
            order_items = current_order.get("items", [])
            enriched_items = []
            
            with tracer.start_as_current_span("processor_enrich_order_items") as enrich_span:
                enrich_span.set_attribute("step", "enrich_order_items")
                enrich_span.set_attribute("items_count", len(order_items))
                
                for item in order_items:
                    product_id = item.get("product_id")
                    if product_id:
                        # Fetch product details from Demo App
                        product_details = await demo_client.get_product(product_id)
                        if product_details:
                            enriched_item = {
                                **item,
                                "product_name": product_details.get("name"),
                                "product_category": product_details.get("category"),
                                "product_description": product_details.get("description")
                            }
                            enriched_items.append(enriched_item)
            
            # Create processing job record
            job = ProcessingJob(
                job_id=job_id,
                job_type="order_processing",
                status="completed",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parameters={
                    "cart_id": request.cart_id,
                    "customer_email": request.customer_email,
                    "priority": request.priority
                },
                results={
                    "order_id": order_id,
                    "order_total": order_total,
                    "enriched_items": enriched_items,
                    "items_processed": len(enriched_items)
                }
            )
            
            processing_jobs[job_id] = job
            
            # Schedule background notification if requested
            if request.notify_customer:
                background_tasks.add_task(
                    send_order_notification,
                    order_id,
                    request.customer_email,
                    settings
                )
            
            span.set_attribute("processor.job_id", job_id)
            span.set_attribute("processor.order_id", order_id)
            span.set_attribute("processor.items_processed", len(enriched_items))
            
            result = {
                "job_id": job_id,
                "status": "completed",
                "order_id": order_id,
                "order_total": order_total,
                "items_processed": len(enriched_items),
                "processing_timestamp": datetime.now().isoformat(),
                "notification_scheduled": request.notify_customer
            }
            
            logger.info(
                "Order processing workflow completed",
                job_id=job_id,
                order_id=order_id,
                items_processed=len(enriched_items),
                order_total=order_total,
                event="processor_order_workflow_completed"
            )
            
            await demo_client.close()
            return result
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            # Record failed job
            failed_job = ProcessingJob(
                job_id=job_id,
                job_type="order_processing",
                status="failed",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parameters={
                    "cart_id": request.cart_id,
                    "customer_email": request.customer_email,
                    "priority": request.priority
                },
                error_message=str(e)
            )
            
            processing_jobs[job_id] = failed_job
            
            logger.error(
                "Order processing workflow failed",
                job_id=job_id,
                error=str(e),
                cart_id=request.cart_id,
                event="processor_order_workflow_error"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Order processing failed: {str(e)}"
            )


@router.post("/products/enrich", response_model=Dict[str, Any])
async def enrich_products(
    request: ProductEnrichmentRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Enrich product data with additional information.
    
    This demonstrates parallel service calls and data aggregation.
    
    Args:
        request: Product enrichment request
        settings: Application settings
        
    Returns:
        Dict: Enrichment results
    """
    with tracer.start_as_current_span("processor_enrich_products") as span:
        span.set_attribute("processor.operation", "enrich_products")
        span.set_attribute("processor.product_count", len(request.product_ids))
        span.set_attribute("processor.enrichment_type", request.enrichment_type)
        
        job_id = str(uuid4())
        
        try:
            demo_client = DemoAppClient(settings)
            
            enriched_products = []
            
            # Process products in parallel for better performance
            with tracer.start_as_current_span("processor_parallel_product_fetch") as parallel_span:
                parallel_span.set_attribute("fetch_type", "parallel")
                
                # Create tasks for parallel execution
                product_tasks = [
                    demo_client.get_product(product_id) 
                    for product_id in request.product_ids
                ]
                
                # Execute all tasks in parallel
                product_results = await asyncio.gather(*product_tasks, return_exceptions=True)
            
            # Process results and enrich data
            for i, result in enumerate(product_results):
                product_id = request.product_ids[i]
                
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch product {product_id}: {result}")
                    continue
                
                if not result:
                    logger.warning(f"Product {product_id} not found")
                    continue
                
                # Base enrichment
                enriched_product = {
                    **result,
                    "enrichment_timestamp": datetime.now().isoformat(),
                    "enrichment_type": request.enrichment_type,
                    "processed_by": settings.service_name
                }
                
                # Additional enrichment based on type
                if request.enrichment_type == "full":
                    enriched_product.update({
                        "price_tier": classify_price_tier(result.get("price", 0)),
                        "availability_status": "in_stock" if result.get("stock", 0) > 0 else "out_of_stock",
                        "category_metadata": {
                            "category": result.get("category"),
                            "is_premium": result.get("price", 0) > 100
                        }
                    })
                
                # Include analytics if requested
                if request.include_analytics:
                    # Simulated analytics call (could be another service)
                    enriched_product["analytics"] = {
                        "view_count": 150,  # Mock data
                        "conversion_rate": 0.15,
                        "trending_score": calculate_trending_score(result)
                    }
                
                enriched_products.append(enriched_product)
            
            # Create job record
            job = ProcessingJob(
                job_id=job_id,
                job_type="product_enrichment",
                status="completed",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parameters={
                    "product_ids": request.product_ids,
                    "enrichment_type": request.enrichment_type,
                    "include_analytics": request.include_analytics
                },
                results={
                    "enriched_products": enriched_products,
                    "products_processed": len(enriched_products),
                    "success_rate": len(enriched_products) / len(request.product_ids)
                }
            )
            
            processing_jobs[job_id] = job
            
            span.set_attribute("processor.job_id", job_id)
            span.set_attribute("processor.products_enriched", len(enriched_products))
            span.set_attribute("processor.success_rate", len(enriched_products) / len(request.product_ids))
            
            result = {
                "job_id": job_id,
                "status": "completed",
                "products_requested": len(request.product_ids),
                "products_enriched": len(enriched_products),
                "success_rate": round(len(enriched_products) / len(request.product_ids), 2),
                "enrichment_type": request.enrichment_type,
                "processing_timestamp": datetime.now().isoformat(),
                "enriched_products": enriched_products
            }
            
            logger.info(
                "Product enrichment completed",
                job_id=job_id,
                products_requested=len(request.product_ids),
                products_enriched=len(enriched_products),
                success_rate=len(enriched_products) / len(request.product_ids),
                event="processor_product_enrichment_completed"
            )
            
            await demo_client.close()
            return result
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Product enrichment failed",
                job_id=job_id,
                error=str(e),
                product_count=len(request.product_ids),
                event="processor_product_enrichment_error"
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Product enrichment failed: {str(e)}"
            )


@router.get("/jobs/{job_id}", response_model=ProcessingJob)
async def get_processing_job(job_id: str) -> ProcessingJob:
    """
    Get processing job status and results.
    
    Args:
        job_id: Job identifier
        
    Returns:
        ProcessingJob: Job data
    """
    with tracer.start_as_current_span("processor_get_job") as span:
        span.set_attribute("processor.operation", "get_job")
        span.set_attribute("processor.job_id", job_id)
        
        if job_id not in processing_jobs:
            span.set_attribute("job.found", False)
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = processing_jobs[job_id]
        span.set_attribute("job.found", True)
        span.set_attribute("job.status", job.status)
        span.set_attribute("job.type", job.job_type)
        
        return job


@router.get("/jobs", response_model=List[ProcessingJob])
async def list_processing_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type")
) -> List[ProcessingJob]:
    """
    List processing jobs with optional filters.
    
    Args:
        status: Filter by job status
        job_type: Filter by job type
        
    Returns:
        List[ProcessingJob]: Filtered jobs list
    """
    with tracer.start_as_current_span("processor_list_jobs") as span:
        span.set_attribute("processor.operation", "list_jobs")
        span.set_attribute("processor.status_filter", status or "all")
        span.set_attribute("processor.type_filter", job_type or "all")
        
        jobs = list(processing_jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        if job_type:
            jobs = [job for job in jobs if job.job_type == job_type]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        span.set_attribute("processor.jobs_returned", len(jobs))
        
        logger.info(
            "Jobs list retrieved",
            total_jobs=len(jobs),
            status_filter=status,
            type_filter=job_type,
            event="processor_list_jobs"
        )
        
        return jobs


# Helper functions
def classify_price_tier(price: float) -> str:
    """Classify product price tier."""
    if price >= 500:
        return "premium"
    elif price >= 100:
        return "mid_tier"
    else:
        return "budget"


def calculate_trending_score(product: Dict[str, Any]) -> float:
    """Calculate product trending score (mock implementation)."""
    base_score = 0.5
    price_factor = min(product.get("price", 0) / 1000, 0.3)
    stock_factor = min(product.get("stock", 0) / 100, 0.2)
    
    return round(base_score + price_factor + stock_factor, 2)


async def send_order_notification(
    order_id: str,
    customer_email: str,
    settings: Settings
):
    """
    Background task to send order notification.
    
    Args:
        order_id: Order identifier
        customer_email: Customer email
        settings: Application settings
    """
    with tracer.start_as_current_span("processor_send_notification") as span:
        span.set_attribute("processor.operation", "send_notification")
        span.set_attribute("processor.order_id", order_id)
        span.set_attribute("processor.customer_email", customer_email)
        
        try:
            # Simulate notification sending delay
            await asyncio.sleep(2)
            
            logger.info(
                "Order notification sent",
                order_id=order_id,
                customer_email=customer_email,
                event="processor_notification_sent"
            )
            
            span.set_attribute("notification.sent", True)
            
        except Exception as e:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            
            logger.error(
                "Failed to send order notification",
                order_id=order_id,
                customer_email=customer_email,
                error=str(e),
                event="processor_notification_error"
            )

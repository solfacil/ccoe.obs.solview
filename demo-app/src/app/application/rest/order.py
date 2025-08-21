"""
📦 Order REST API

Endpoints REST para operações de pedidos.
"""

import logging
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from opentelemetry import trace

router = APIRouter()
logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class OrderItem(BaseModel):
    """Item do pedido."""
    product_id: str
    quantity: int
    price: float


class OrderResponse(BaseModel):
    """Resposta do pedido."""
    id: str
    items: List[OrderItem]
    total: float
    status: str


class CreateOrderRequest(BaseModel):
    """Requisição para criar pedido."""
    cart_id: str


# Simulação de armazenamento
_orders = {}


@router.post("/", response_model=OrderResponse)
async def create_order(request: CreateOrderRequest) -> OrderResponse:
    """
    Cria um novo pedido.
    
    Args:
        request: Dados do pedido
        
    Returns:
        OrderResponse: Pedido criado
    """
    with tracer.start_as_current_span("api_create_order") as span:
        span.set_attribute("api.operation", "create_order")
        span.set_attribute("api.cart_id", request.cart_id)
        
        order_id = str(uuid4())
        
        # Simular conversão de carrinho para pedido
        order = OrderResponse(
            id=order_id,
            items=[
                OrderItem(product_id="prod-001", quantity=1, price=99.99)
            ],
            total=99.99,
            status="confirmed"
        )
        
        _orders[order_id] = order
        
        span.set_attribute("api.order_id", order_id)
        span.set_attribute("api.order_total", order.total)
        
        logger.info(
            f"Order created: {order_id}",
            extra={
                "extra_fields": {
                    "endpoint": "create_order",
                    "order_id": order_id,
                    "cart_id": request.cart_id,
                    "total": order.total,
                    "event": "api_success"
                }
            }
        )
        
        return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str) -> OrderResponse:
    """
    Obtém pedido por ID.
    
    Args:
        order_id: ID do pedido
        
    Returns:
        OrderResponse: Dados do pedido
    """
    with tracer.start_as_current_span("api_get_order") as span:
        span.set_attribute("api.operation", "get_order")
        span.set_attribute("api.order_id", order_id)
        
        if order_id not in _orders:
            span.set_attribute("api.order_found", False)
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = _orders[order_id]
        span.set_attribute("api.order_found", True)
        span.set_attribute("api.order_status", order.status)
        
        return order


@router.get("/", response_model=List[OrderResponse])
async def list_orders() -> List[OrderResponse]:
    """
    Lista todos os pedidos.
    
    Returns:
        List[OrderResponse]: Lista de pedidos
    """
    with tracer.start_as_current_span("api_list_orders") as span:
        span.set_attribute("api.operation", "list_orders")
        
        orders = list(_orders.values())
        span.set_attribute("api.orders_count", len(orders))
        
        logger.info(
            f"Listed {len(orders)} orders",
            extra={
                "extra_fields": {
                    "endpoint": "list_orders",
                    "orders_count": len(orders),
                    "event": "api_success"
                }
            }
        )
        
        return orders




from datetime import datetime
from pydantic import BaseModel

from .schemas import OrderState


class OrderStateChangedEvent(BaseModel):
    event: str = "order.state_changed"
    order_id: int
    customer_id: int
    restaurant_id: int
    from_state: OrderState | None
    to_state: OrderState
    changed_at: datetime
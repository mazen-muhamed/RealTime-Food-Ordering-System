from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .events import OrderStateChangedEvent
from .message_bus import (
    publish_event,
    publish_order_update,
)

from .repository import (
    get_restaurant,
    create_order,
    get_order,
    get_orders,
    update_order_state,
    create_order_state_log,
    get_restaurants,
    get_restaurant_menu,
)

from .schemas import (
    OrderCreate,
    OrderState,
    OrderStateUpdate,
)


router = APIRouter()


# =========================
# Order State Transitions
# =========================

ALLOWED_TRANSITIONS = {

    OrderState.PLACED: [
        OrderState.CONFIRMED,
        OrderState.CANCELED,
    ],

    OrderState.CONFIRMED: [
        OrderState.PREPARING,
        OrderState.CANCELED,
    ],

    OrderState.PREPARING: [
        OrderState.OUT_OF_DELIVERY,
    ],

    OrderState.OUT_OF_DELIVERY: [
        OrderState.DELIVERED,
    ],

    OrderState.DELIVERED: [],

    OrderState.CANCELED: [],
}


def is_valid_transition(
    current_state: OrderState,
    new_state: OrderState,
) -> bool:

    return new_state in ALLOWED_TRANSITIONS.get(
        current_state,
        [],
    )


# =========================
# Create Order
# =========================

@router.post(
    "/orders",
    status_code=status.HTTP_201_CREATED,
)
async def create_order_endpoint(
    payload: OrderCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Get logged-in user's ID
    customer_id = current_user["id"]

    # Get restaurant
    restaurant = get_restaurant(
        db,
        payload.restaurant_id,
    )

    # Restaurant does not exist
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    # Restaurant is unavailable
    if not restaurant["is_available"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant is not available",
        )

    # Restaurant reached capacity
    if (
        restaurant["current_order_count"]
        >= restaurant["max_concurrent_orders"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant is at full capacity",
        )

    # Create order
    order = create_order(
        db,
        restaurant_id=payload.restaurant_id,
        customer_id=customer_id,
        state=OrderState.PLACED.value,
    )

    # Create initial state log
    create_order_state_log(
        db,
        order_id=order["id"],
        from_state=None,
        to_state=OrderState.PLACED.value,
    )

    return {
        "message": "Order created successfully",
        "order": order,
    }


# =========================
# Update Order State
# =========================

@router.patch("/order/{order_id}/state")
async def update_order_status(
    order_id: int,
    payload: OrderStateUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # Get order
    order = get_order(
        db,
        order_id,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Current state
    current_state = OrderState(
        order["state"]
    )

    # New state
    new_state = payload.state

    # Validate transition
    if not is_valid_transition(
        current_state,
        new_state,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid transition from "
                f"{current_state.value} "
                f"to "
                f"{new_state.value}"
            ),
        )

    # Update order state
    updated_order = update_order_state(
        db,
        order_id=order_id,
        new_state=new_state.value,
    )

    # Create state log
    create_order_state_log(
        db,
        order_id=order_id,
        from_state=current_state.value,
        to_state=new_state.value,
    )

    # Create event
    event = OrderStateChangedEvent(
        order_id=order_id,
        customer_id=order["customer_id"],
        restaurant_id=order["restaurant_id"],
        from_state=current_state,
        to_state=new_state,
        changed_at=datetime.now(timezone.utc),
    )

    # Convert event to dictionary
    event_data = event.model_dump(
        mode="json"
    )

    # Publish event to Redis Stream
    await publish_event(
        event_data
    )

    # Publish live update to Redis Pub/Sub
    await publish_order_update(
        order_id=order_id,
        event=event_data,
    )

    return {
        "message": "Order state updated successfully",
        "order": updated_order,
    }


# =========================
# Get Single Order
# =========================

@router.get("/order/{order_id}")
async def get_order_by_id(
    order_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    order = get_order(
        db,
        order_id,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return order


# =========================
# List Orders
# =========================

@router.get("/orders")
async def list_orders(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    orders = get_orders(
        db,
        limit=limit,
    )

    return orders


# =========================
# List Restaurants
# =========================

@router.get("/restaurants")
async def list_restaurants(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    restaurants = get_restaurants(
        db
    )

    return restaurants


# =========================
# Restaurant Availability
# =========================

@router.get(
    "/restaurants/{restaurant_id}/availability"
)
async def restaurant_availability(
    restaurant_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    restaurant = get_restaurant(
        db,
        restaurant_id,
    )

    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    available = (
        restaurant["is_available"]
        and
        restaurant["current_order_count"]
        < restaurant["max_concurrent_orders"]
    )

    return {
        "restaurant_id": restaurant["id"],
        "is_available": available,
        "current_order_count": (
            restaurant["current_order_count"]
        ),
        "max_concurrent_orders": (
            restaurant["max_concurrent_orders"]
        ),
    }


# =========================
# Restaurant Menu
# =========================

@router.get(
    "/restaurants/{restaurant_id}/menu"
)
async def restaurant_menu(
    restaurant_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    menu = get_restaurant_menu(
        db,
        restaurant_id,
    )

    if menu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    return menu


from pydantic import BaseModel, Field
from enum import Enum


class OrderState(str, Enum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_OF_DELIVERY = "out_of_delivery"
    DELIVERED = "delivered"
    CANCELED = "canceled"

class OrderCreate(BaseModel):
    restaurant_id: int

class OrderStateUpdate(BaseModel):
    state: OrderState

class SignupRequest(BaseModel):
    username: str
    email: str
    phone_number: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str
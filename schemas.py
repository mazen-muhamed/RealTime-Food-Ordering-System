from pydantic import BaseModel, Field

class SignupRequest(BaseModel):
    ## Database Columns Like name, email, password
    ...
    
class LoginRequest(BaseModel):
     ## Database Columns Like email, password
    ...

class UserRespone(BaseModel):
    ...
    
class MenuItems(BaseModel):
    ...

# don't touch this now 
class OrderItemInput(BaseModel):
    menu_item_id: int
    quantity: int = Field(ge=1, le=20)
    
# don't touch this now 
class CreateOrderRequest(BaseModel):
    items: list[OrderItemInput] = Field(min_length=1, max_length=20)
    
class OrderItemResponse(BaseModel):
    menu_item_id: int
    # Continue ya abdallah 
    
class OrderResponse(BaseModel):
    ... # Write the rest of code 
    items = list[OrderItemResponse]
    

class OrderStatusRequest(BaseModel):
    status: str
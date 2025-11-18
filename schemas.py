"""
Database Schemas for the Electronic Hardware Dealer app

Each Pydantic model represents a collection in MongoDB.
Collection name is the lowercase of the class name.

- User -> "user"
- Category -> "category"
- Product -> "product"
- Order -> "order"
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional

# Users
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    hashed_password: str = Field(..., description="Password hash")
    role: str = Field("customer", description="Role: customer or admin")
    is_active: bool = Field(True, description="Whether user is active")

# Categories (supports hierarchy via parent_id)
class Category(BaseModel):
    name: str = Field(..., description="Category name")
    parent_id: Optional[str] = Field(None, description="Parent category _id (for subcategories)")
    description: Optional[str] = Field(None, description="Optional description")

# Products
class Product(BaseModel):
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Unit price")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    image_url: Optional[str] = Field(None, description="Image URL")
    category_id: str = Field(..., description="Category _id")
    subcategory_id: Optional[str] = Field(None, description="Subcategory _id")
    in_stock: bool = Field(True, description="In stock flag")
    stock_qty: Optional[int] = Field(None, ge=0, description="Optional stock quantity")

# Orders
class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product _id")
    name: str = Field(..., description="Snapshot of product name at order time")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    unit_price: float = Field(..., ge=0, description="Unit price at order time")

class Order(BaseModel):
    user_id: str = Field(..., description="User _id placing the order")
    email: EmailStr = Field(..., description="Customer email for confirmations")
    items: List[OrderItem] = Field(..., description="Line items")
    subtotal: float = Field(..., ge=0)
    tax: float = Field(0, ge=0)
    total: float = Field(..., ge=0)
    status: str = Field("placed", description="Order status")
    notes: Optional[str] = Field(None, description="Optional notes from customer")
    shipping_name: Optional[str] = Field(None, description="Recipient name")
    shipping_address: Optional[str] = Field(None, description="Shipping address")
    shipping_phone: Optional[str] = Field(None, description="Phone number")

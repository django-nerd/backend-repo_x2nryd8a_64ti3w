import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Category, Product, Order, OrderItem

app = FastAPI(title="Electronic Hardware Dealer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class ProductFilters(BaseModel):
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    q: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Electronic Hardware Dealer API"}

# Auth (simple: store hashed_password = password for demo; prod should hash!)
@app.post("/auth/signup")
def signup(payload: SignupRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["user"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=payload.name, email=payload.email, hashed_password=payload.password)
    user_id = create_document("user", user)
    return {"user_id": user_id, "email": payload.email}

@app.post("/auth/login")
def login(payload: LoginRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    user = db["user"].find_one({"email": payload.email})
    if not user or user.get("hashed_password") != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": str(user.get("_id")), "name": user.get("name"), "email": user.get("email")}

# Categories
@app.get("/categories")
def list_categories():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    cats = get_documents("category")
    # Build hierarchy
    by_parent = {}
    for c in cats:
        c["_id"] = str(c["_id"])  # stringify
        parent = c.get("parent_id")
        by_parent.setdefault(parent, []).append(c)
    return by_parent

@app.post("/categories")
def create_category(cat: Category):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    new_id = create_document("category", cat)
    return {"id": new_id}

# Products
@app.post("/products")
def create_product(prod: Product):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Optional: verify category ids
    if prod.category_id:
        try:
            ObjectId(prod.category_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid category_id")
    doc_id = create_document("product", prod)
    return {"id": doc_id}

@app.get("/products")
def list_products(category_id: Optional[str] = None, subcategory_id: Optional[str] = None, q: Optional[str] = None, limit: int = 100):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict = {}
    if category_id:
        filter_dict["category_id"] = category_id
    if subcategory_id:
        filter_dict["subcategory_id"] = subcategory_id
    if q:
        filter_dict["name"] = {"$regex": q, "$options": "i"}
    prods = get_documents("product", filter_dict=filter_dict, limit=limit)
    for p in prods:
        p["_id"] = str(p["_id"])  # stringify id
    return prods

# Orders (email notification via simple console log; could integrate SMTP later)
class PlaceOrderRequest(BaseModel):
    user_id: str
    email: EmailStr
    items: List[OrderItem]
    notes: Optional[str] = None
    shipping_name: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None

@app.post("/orders")
def place_order(payload: PlaceOrderRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Compute totals
    subtotal = sum(i.quantity * i.unit_price for i in payload.items)
    tax = 0
    total = subtotal + tax
    order = Order(
        user_id=payload.user_id,
        email=payload.email,
        items=payload.items,
        subtotal=subtotal,
        tax=tax,
        total=total,
        notes=payload.notes,
        shipping_name=payload.shipping_name,
        shipping_address=payload.shipping_address,
        shipping_phone=payload.shipping_phone,
    )
    order_id = create_document("order", order)

    # Simulate email send (log)
    print("New order placed", {"order_id": order_id, "email": payload.email, "total": total})

    return {"order_id": order_id, "total": total}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

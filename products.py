# products.py
from fastapi import FastAPI, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Product Catalog API")

# Sample product catalog
PRODUCTS = [
    {"product_id": "P001", "product_name": "Smart Watch", "price": 199.99},
    {"product_id": "P002", "product_name": "Wireless Earbuds", "price": 89.99},
    {"product_id": "P003", "product_name": "Bluetooth Speaker", "price": 59.99},
    {"product_id": "P004", "product_name": "Laptop Backpack", "price": 49.99},
    {"product_id": "P005", "product_name": "Phone Charger", "price": 19.99},
    {"product_id": "P006", "product_name": "Fitness Tracker", "price": 79.99},
    {"product_id": "P007", "product_name": "External SSD", "price": 129.99},
    {"product_id": "P008", "product_name": "Gaming Mouse", "price": 39.99},
    {"product_id": "P009", "product_name": "Mechanical Keyboard", "price": 89.99},
    {"product_id": "P010", "product_name": "Noise Cancelling Headphones", "price": 149.99}
]

# Save products to JSON file
with open('products.json', 'w') as f:
    json.dump(PRODUCTS, f, indent=2)

class Product(BaseModel):
    product_id: str
    product_name: str
    price: float

@app.get("/products/search", response_model=List[Product])
async def search_products(name: str = Query(..., description="Product name search query")):
    if not name:
        raise HTTPException(status_code=400, detail="Please provide a search query using the 'name' parameter")
    
    name_lower = name.lower()
    matching_products = [
        product for product in PRODUCTS 
        if name_lower in product['product_name'].lower()
    ]
    
    return matching_products

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = next((p for p in PRODUCTS if p['product_id'] == product_id), None)
    
    if product:
        return product
    else:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

if __name__ == '__main__':
    uvicorn.run("products:app", host="0.0.0.0", port=3000, reload=True)
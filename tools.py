# tools.py
from langchain.tools import Tool
import os
import json
import requests
from typing import Dict, Any, List, Optional

# Base URL for the product service
PRODUCT_API_BASE_URL = os.environ.get('PRODUCT_API_BASE_URL', 'http://localhost:3000')

# Cart storage - using a dictionary to store carts per session
# In a real application, this would be a database
active_carts = {}

# Context storage - to remember products from searches
session_context = {}

class ProductCatalogAPI:
    def __init__(self, base_url=PRODUCT_API_BASE_URL):
        self.base_url = base_url
        
    def search_products(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for products by name"""
        try:
            response = requests.get(
                f"{self.base_url}/products/search",
                params={"name": product_name}
            )
            response.raise_for_status()
            
            products = response.json()
            
            # Store search results in context
            if products:
                self._update_search_context(product_name, products)
                
            return products
        except requests.exceptions.RequestException as e:
            print(f"Error searching products: {e}")
            return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by its ID"""
        try:
            response = requests.get(f"{self.base_url}/products/{product_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting product: {e}")
            return None
            
    def _update_search_context(self, query: str, products: List[Dict[str, Any]]):
        """Update the global search context with the results"""
        if "recent_searches" not in session_context:
            session_context["recent_searches"] = {}
            
        # Store the query and results
        session_context["recent_searches"][query.lower()] = products
        
        # Also store each product by name for easy lookup
        if "products_by_name" not in session_context:
            session_context["products_by_name"] = {}
            
        for product in products:
            name = product["product_name"].lower()
            session_context["products_by_name"][name] = product

class CartManager:
    @staticmethod
    def get_cart(session_id: str) -> List[Dict[str, Any]]:
        """Get the cart for a specific session"""
        # Return an empty list if the cart doesn't exist
        return active_carts.get(session_id, [])
    
    @staticmethod
    def add_to_cart(session_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a product to the cart"""
        # Initialize cart if it doesn't exist
        if session_id not in active_carts:
            active_carts[session_id] = []
        
        # Get product details
        product_api = ProductCatalogAPI()
        product = product_api.get_product_by_id(product_id)
        
        if not product:
            return {
                "success": False,
                "message": f"Product with ID {product_id} not found"
            }
        
        # Check if the product is already in the cart
        for item in active_carts[session_id]:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                item["total"] = round(item["price"] * item["quantity"], 2)
                return {
                    "success": True,
                    "message": f"Updated quantity of {product['product_name']} in your cart",
                    "cart": active_carts[session_id]
                }
        
        # Add the new product to the cart
        cart_item = {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "price": product["price"],
            "quantity": quantity,
            "total": round(product["price"] * quantity, 2)
        }
        
        active_carts[session_id].append(cart_item)
        
        return {
            "success": True,
            "message": f"Added {product['product_name']} to your cart",
            "cart": active_carts[session_id]
        }
    
    @staticmethod
    def add_to_cart_by_name(session_id: str, product_name: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a product to the cart using product name"""
        product_api = ProductCatalogAPI()
        
        # Try to find the product in the context first
        product = None
        name_lower = product_name.lower()
        
        # Check for exact or close matches in the context
        if "products_by_name" in session_context:
            # Try exact match first
            if name_lower in session_context["products_by_name"]:
                product = session_context["products_by_name"][name_lower]
            else:
                # Try partial matches
                for saved_name, saved_product in session_context["products_by_name"].items():
                    if name_lower in saved_name or saved_name in name_lower:
                        product = saved_product
                        break
        
        # If not found in context, search for it
        if not product:
            search_results = product_api.search_products(product_name)
            
            if search_results and len(search_results) > 0:
                # Use the first matching product
                product = search_results[0]
        
        if not product:
            return {
                "success": False,
                "message": f"No product found matching '{product_name}'"
            }
        
        # Now add the product to the cart
        return CartManager.add_to_cart(session_id, product["product_id"], quantity)
    
    @staticmethod
    def view_cart(session_id: str) -> Dict[str, Any]:
        """View the contents of the cart"""
        cart = active_carts.get(session_id, [])
        
        if not cart:
            return {
                "success": True,
                "message": "Your cart is empty",
                "cart": [],
                "cart_total": 0
            }
        
        # Calculate the total for the entire cart
        cart_total = sum(item["total"] for item in cart)
        
        return {
            "success": True,
            "message": f"Your cart has {len(cart)} items",
            "cart": cart,
            "cart_total": round(cart_total, 2)
        }
    
    @staticmethod
    def clear_cart(session_id: str) -> Dict[str, Any]:
        """Clear the cart"""
        if session_id in active_carts:
            del active_carts[session_id]
        
        return {
            "success": True,
            "message": "Your cart has been cleared"
        }
    
    @staticmethod
    def remove_from_cart_by_name(session_id: str, product_name: str) -> Dict[str, Any]:
        """Remove a product from the cart by name"""
        cart = active_carts.get(session_id, [])
        
        if not cart:
            return {
                "success": False,
                "message": "Your cart is already empty"
            }
        
        # Find the product by name (case-insensitive partial match)
        name_lower = product_name.lower()
        for i, item in enumerate(cart):
            if name_lower in item["product_name"].lower() or item["product_name"].lower() in name_lower:
                removed_item = cart.pop(i)
                return {
                    "success": True,
                    "message": f"Removed {removed_item['product_name']} from your cart",
                    "cart": cart
                }
        
        return {
            "success": False,
            "message": f"Product '{product_name}' not found in your cart"
        }
    
    @staticmethod
    def update_quantity(session_id: str, product_name: str, quantity: int) -> Dict[str, Any]:
        """Update the quantity of a product in the cart"""
        if quantity <= 0:
            return CartManager.remove_from_cart_by_name(session_id, product_name)
            
        cart = active_carts.get(session_id, [])
        
        if not cart:
            return {
                "success": False,
                "message": "Your cart is empty"
            }
        
        # Find the product by name (case-insensitive partial match)
        name_lower = product_name.lower()
        for item in cart:
            if name_lower in item["product_name"].lower() or item["product_name"].lower() in name_lower:
                item["quantity"] = quantity
                item["total"] = round(item["price"] * quantity, 2)
                return {
                    "success": True,
                    "message": f"Updated quantity of {item['product_name']} to {quantity}",
                    "cart": cart
                }
        
        return {
            "success": False,
            "message": f"Product '{product_name}' not found in your cart"
        }

# Function implementations for LangChain tools
def search_products(product_name: str) -> str:
    """Search for products by name"""
    product_api = ProductCatalogAPI()
    products = product_api.search_products(product_name)
    
    if not products:
        return f"I couldn't find any products matching '{product_name}'. Would you like to try a different search term?"
    
    # Format the results
    result = f"I found {len(products)} products matching '{product_name}':\n\n"
    for product in products:
        result += f"• {product['product_name']} - ${product['price']:.2f}\n"
    
    return result

def add_to_cart(session_id: str, product_name: str, quantity: int = 1) -> str:
    """Add a product to the cart by name"""
    cart_manager = CartManager()
    result = cart_manager.add_to_cart_by_name(session_id, product_name, quantity)
    
    return result["message"]

def view_cart(session_id: str) -> str:
    """View the contents of the cart"""
    cart_manager = CartManager()
    result = cart_manager.view_cart(session_id)
    
    if not result["cart"]:
        return "Your cart is empty"
    
    # Format the cart as a table
    cart_table = "| Product | Price | Quantity | Total |\n"
    cart_table += "|---------|-------|----------|-------|\n"
    
    for item in result["cart"]:
        cart_table += f"| {item['product_name']} | ${item['price']:.2f} | {item['quantity']} | ${item['total']:.2f} |\n"
    
    cart_table += f"\n**Total: ${result['cart_total']:.2f}**"
    
    return cart_table

def clear_cart(session_id: str) -> str:
    """Clear the cart"""
    cart_manager = CartManager()
    result = cart_manager.clear_cart(session_id)
    
    return result["message"]

def remove_from_cart(session_id: str, product_name: str) -> str:
    """Remove a product from the cart by name"""
    cart_manager = CartManager()
    result = cart_manager.remove_from_cart_by_name(session_id, product_name)
    
    return result["message"]

def update_quantity(session_id: str, product_name: str, quantity: int) -> str:
    """Update the quantity of a product in the cart"""
    cart_manager = CartManager()
    result = cart_manager.update_quantity(session_id, product_name, quantity)
    
    return result["message"]

# Create LangChain tools
search_products_tool = Tool(
    name="search_products",
    func=search_products,
    description="Search for products by name. Input should be the product name or a part of it."
)

add_to_cart_tool = Tool(
    name="add_to_cart",
    func=add_to_cart,
    description="Add a product to the cart by name. Input should include the product name and optionally the quantity."
)

view_cart_tool = Tool(
    name="view_cart",
    func=view_cart,
    description="View the contents of the cart. Shows all products, quantities, prices, and the total."
)

clear_cart_tool = Tool(
    name="clear_cart",
    func=clear_cart,
    description="Clear all items from the cart."
)

remove_from_cart_tool = Tool(
    name="remove_from_cart",
    func=remove_from_cart,
    description="Remove a product from the cart by name."
)

update_quantity_tool = Tool(
    name="update_quantity",
    func=update_quantity,
    description="Update the quantity of a product in the cart. Input should include the product name and the new quantity."
)
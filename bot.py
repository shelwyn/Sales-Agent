# Bot.py
import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Import tools from tools.py
from tools import (
    search_products_tool,
    add_to_cart_tool,
    view_cart_tool,
    clear_cart_tool,
    remove_from_cart_tool,
    update_quantity_tool
)

# Import Google's Generative AI library
import google.generativeai as genai

# Configure API key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class GeminiChatbot:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.model = genai.GenerativeModel(model_name)
        self.chat = self.model.start_chat(history=[])
        self.session_id = str(uuid.uuid4())  # Generate unique session ID for this chat
        self.tools = self._prepare_tools()
        
        # Print SDK version for debugging
        try:
            print(f"Using google-generativeai version: {genai.__version__}")
            print(f"Session ID: {self.session_id}")
        except AttributeError:
            print("Could not determine google-generativeai version")
        
    def _prepare_tools(self) -> Dict[str, Any]:
        """Convert LangChain tools to Gemini-compatible format."""
        # Dictionary to store our tools by name
        tools_dict = {}
        
        # Add search_products tool
        tools_dict["search_products"] = {
            "function": search_products_tool.func,
            "description": search_products_tool.description,
            "parameters": {
                "product_name": {
                    "type": "string",
                    "description": "Product name or search term"
                }
            },
            "required": ["product_name"]
        }
        
        # Add add_to_cart tool
        tools_dict["add_to_cart"] = {
            "function": add_to_cart_tool.func,
            "description": add_to_cart_tool.description,
            "parameters": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to identify the user's cart"
                },
                "product_name": {
                    "type": "string",
                    "description": "Name of the product to add to the cart"
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity of the product to add (default: 1)"
                }
            },
            "required": ["session_id", "product_name"]
        }
        
        # Add view_cart tool
        tools_dict["view_cart"] = {
            "function": view_cart_tool.func,
            "description": view_cart_tool.description,
            "parameters": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to identify the user's cart"
                }
            },
            "required": ["session_id"]
        }
        
        # Add clear_cart tool
        tools_dict["clear_cart"] = {
            "function": clear_cart_tool.func,
            "description": clear_cart_tool.description,
            "parameters": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to identify the user's cart"
                }
            },
            "required": ["session_id"]
        }
        
        # Add remove_from_cart tool
        tools_dict["remove_from_cart"] = {
            "function": remove_from_cart_tool.func,
            "description": remove_from_cart_tool.description,
            "parameters": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to identify the user's cart"
                },
                "product_name": {
                    "type": "string",
                    "description": "Name of the product to remove from the cart"
                }
            },
            "required": ["session_id", "product_name"]
        }
        
        # Add update_quantity tool
        tools_dict["update_quantity"] = {
            "function": update_quantity_tool.func,
            "description": update_quantity_tool.description,
            "parameters": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to identify the user's cart"
                },
                "product_name": {
                    "type": "string",
                    "description": "Name of the product to update quantity for"
                },
                "quantity": {
                    "type": "integer",
                    "description": "New quantity to set for the product"
                }
            },
            "required": ["session_id", "product_name", "quantity"]
        }
        
        return tools_dict
    
    def _format_tools_for_gemini(self) -> List[Dict[str, Any]]:
        """Format tools in the structure expected by Gemini."""
        formatted_tools = []
        
        for tool_name, tool_info in self.tools.items():
            formatted_tool = {
                "function_declarations": [{
                    "name": tool_name,
                    "description": tool_info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": tool_info.get("required", [])
                    }
                }]
            }
            
            # Add parameters
            for param_name, param_info in tool_info["parameters"].items():
                formatted_tool["function_declarations"][0]["parameters"]["properties"][param_name] = {
                    "type": param_info["type"],
                    "description": param_info["description"]
                }
            
            formatted_tools.append(formatted_tool)
            
        return formatted_tools
    
    def _extract_args_from_function_call(self, function_name, function_args):
        """Safely extract arguments from function_call.args, handling different types."""
        if isinstance(function_args, str):
            # If it's a string, try to parse as JSON
            try:
                return json.loads(function_args)
            except json.JSONDecodeError:
                # For simple string parameters
                if function_name == "search_products":
                    return {"product_name": function_args}
                return {}
        elif hasattr(function_args, '__getitem__') and hasattr(function_args, 'keys'):
            # If it's a dict-like object (including MapComposite)
            return {key: function_args[key] for key in function_args.keys()}
        else:
            # Fallback - convert to string representation if all else fails
            return {}
    
    def chat_with_function_calling(self, user_input: str) -> str:
        """Process user input, handle any function calls, and return a response."""
        try:
            # Step 1: Send user input with tools definition
            response = self.chat.send_message(
                user_input,
                tools=self._format_tools_for_gemini()
            )
            
            # Step 2: Check for function call in response
            if not hasattr(response, 'candidates') or len(response.candidates) == 0:
                return "I received an empty response. Please try again."
                
            candidate = response.candidates[0]
            if not hasattr(candidate, 'content') or not hasattr(candidate.content, 'parts'):
                return response.text
                
            # Step 3: Check each part for a function call
            function_call_detected = False
            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call_detected = True
                    function_call = part.function_call
                    
                    # Extract function name
                    function_name = function_call.name
                    
                    # Extract arguments safely
                    function_args = self._extract_args_from_function_call(function_name, function_call.args)
                    
                    print(f"Function call detected: {function_name} with args: {function_args}")
                    
                    # Step 4: Execute the function 
                    if function_name not in self.tools:
                        return f"Unknown function: {function_name}"
                    
                    tool = self.tools[function_name]
                    
                    # Handle arguments based on function type
                    if function_name == "search_products" and "product_name" in function_args:
                        function_result = tool["function"](function_args["product_name"])
                    elif function_name == "add_to_cart":
                        # Automatically use the session ID for this chat
                        quantity = function_args.get("quantity", 1)
                        function_result = tool["function"](
                            self.session_id, 
                            function_args.get("product_name", ""), 
                            quantity
                        )
                    elif function_name in ["view_cart", "clear_cart"]:
                        # Use the session ID for this chat
                        function_result = tool["function"](self.session_id)
                    elif function_name == "remove_from_cart":
                        # Use the session ID for this chat
                        function_result = tool["function"](
                            self.session_id,
                            function_args.get("product_name", "")
                        )
                    elif function_name == "update_quantity":
                        # Use the session ID for this chat
                        function_result = tool["function"](
                            self.session_id,
                            function_args.get("product_name", ""),
                            function_args.get("quantity", 1)
                        )
                    else:
                        # Generic fallback
                        function_result = tool["function"](**function_args)
                    
                    # Step 5: Send the result as a text message to get a response
                    result_message = f"FUNCTION_RESULT: {function_result}"
                    final_response = self.chat.send_message(result_message)
                    
                    return final_response.text
            
            # If no function call was detected
            if not function_call_detected:
                return response.text
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error details:\n{error_details}")
            return f"Error processing your request: {str(e)}"


def main():
    print("Starting Gemini Shopping Assistant")
    print("Type 'exit' to quit")
    
    chatbot = GeminiChatbot()
    
    # Initial system prompt to set up the bot's behavior
    system_prompt = """
    You are a helpful shopping assistant that helps users browse products, add items to their cart, and complete their purchase.

    Your capabilities:
    1. Search for products by name
    2. Add products to the user's cart by name
    3. Update quantities of products in the cart
    4. Remove products from the cart
    5. View the cart contents
    6. Clear the cart
    7. Complete the checkout process

    When a user asks about products, always search for products by name and present the options clearly.
    
    When a user wants to add a product to their cart:
    - If they mentioned a specific product by name that matches your catalog, add it directly
    - If their request is ambiguous, ask for clarification about which product they want
    
    When a user asks to check out:
    - Show their cart as a formatted table with products, prices, quantities, and totals
    - Calculate and display the final total
    - Offer information about shipping or payment options
    
    Be conversational and helpful throughout the shopping process. If users express preferences or ask questions about products, provide helpful information to guide their decisions.
    """
    
    chatbot.chat.send_message(system_prompt)
    
    print("\nWelcome to our Online Store! How can I help you today?")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            print("Thank you for shopping with us. Goodbye!")
            break
        
        response = chatbot.chat_with_function_calling(user_input)
        print(f"\nShopping Assistant: {response}")


if __name__ == "__main__":
    main()
# Sales Agent Chatbot

A smart shopping assistant powered by Google's Gemini LLM that helps users browse products, manage their cart, and complete purchases through natural language interactions.

## 🌟 Features

- **Natural language product search**: Find products by simply describing what you're looking for
- **Contextual understanding**: The bot remembers previous interactions and understands references to products
- **Shopping cart management**: Add, remove, update quantities, and view cart contents with simple commands
- **Checkout process**: Complete your purchase with a clear cart summary and total

## 🛠️ Architecture

The system consists of three main components:

1. **Product Catalog API** (`products.py`): A FastAPI server providing product information
2. **Tools Module** (`tools.py`): Implements product search and cart management functionality
3. **Chatbot Interface** (`bot.py`): The Gemini-powered conversational interface

## 📋 Requirements

- Python 3.8+
- Google Gemini API key
- Required Python packages (see `requirements.txt`)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/shelwyn/Sales-Agent.git
cd Sales-Agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory with the following content:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Start the Product API

```bash
python products.py
```

This will start the product catalog API on http://localhost:3000.

### 5. Start the Chatbot

In a new terminal window:

```bash
python bot.py
```

## 💬 Example Interactions

Here are some examples of how to interact with the Sales Agent:

- "Do you have any wireless headphones?"
- "Tell me about your phone accessories"
- "Add the noise cancelling headphones to my cart"
- "I'd like to buy 2 smart watches"
- "What's in my cart?"
- "Remove the Bluetooth speaker from my cart"
- "I'd like to check out now"

## 🧪 Testing the API

You can test the Product API using Postman with these sample requests:

### Search Products
- **GET** `http://localhost:3000/products/search?name=wireless`

### Get Product by ID
- **GET** `http://localhost:3000/products/P002`

### Browse API Documentation
You can access the interactive API documentation at http://localhost:3000/docs after starting the FastAPI server.

## 🔧 Customization

### Adding Products

Edit the `PRODUCTS` list in `products.py` to add, modify, or remove products.

### Extending Functionality

The modular design allows for easy extensions:
- Add new product fields in the `Product` model
- Create additional shopping tools in `tools.py`
- Modify the chatbot prompts in `bot.py` to highlight new features


## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues page](https://github.com/shelwyn/Sales-Agent/issues).

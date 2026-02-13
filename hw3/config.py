TARGET_SIZE_GB = 10
RECORD_SIZE_KB = 1
NUM_RECORDS = int((TARGET_SIZE_GB * 1024 * 1024) / RECORD_SIZE_KB)

OUTPUT_DIR = "test_data"

BATCH_SIZE = 100000

RANDOM_SEED = 42

PRODUCT_CATEGORIES = [
    "Electronics", "Clothing", "Home & Garden", "Sports", 
    "Books", "Toys", "Beauty", "Food", "Automotive"
]

PRODUCT_NAMES = {
    "Electronics": ["Laptop", "Smartphone", "Headphones", "Tablet", "Camera"],
    "Clothing": ["T-Shirt", "Jeans", "Dress", "Jacket", "Shoes"],
    "Home & Garden": ["Lamp", "Chair", "Table", "Cushion", "Vase"],
    "Sports": ["Ball", "Racket", "Weights", "Yoga Mat", "Bicycle"],
    "Books": ["Novel", "Textbook", "Comic", "Magazine", "Encyclopedia"],
    "Toys": ["Action Figure", "Puzzle", "Board Game", "Doll", "LEGO Set"],
    "Beauty": ["Lipstick", "Perfume", "Shampoo", "Cream", "Nail Polish"],
    "Food": ["Coffee", "Tea", "Chocolate", "Snacks", "Pasta"],
    "Automotive": ["Oil", "Tires", "Battery", "Filter", "Cleaner"]
}

COUNTRIES = ["USA", "UK", "Germany", "France", "Japan", "China", "Brazil", "India"]

CITIES = {
    "USA": ["New York", "Los Angeles", "Chicago", "Houston"],
    "UK": ["London", "Manchester", "Birmingham", "Liverpool"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
    "France": ["Paris", "Lyon", "Marseille", "Toulouse"],
    "Japan": ["Tokyo", "Osaka", "Kyoto", "Nagoya"],
    "China": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"],
    "Brazil": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador"],
    "India": ["Mumbai", "Delhi", "Bangalore", "Chennai"]
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "Cash on Delivery"]

ORDER_STATUSES = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]

START_DATE = "2020-01-01"
END_DATE = "2024-12-31"

AVRO_SCHEMA = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "customer_id", "type": "string"},
        {"name": "customer_name", "type": "string"},
        {"name": "customer_email", "type": "string"},
        {"name": "order_date", "type": "string"},
        {"name": "product_id", "type": "string"},
        {"name": "product_name", "type": "string"},
        {"name": "product_category", "type": "string"},
        {"name": "quantity", "type": "int"},
        {"name": "unit_price", "type": "double"},
        {"name": "total_price", "type": "double"},
        {"name": "discount_percent", "type": "double"},
        {"name": "tax_percent", "type": "double"},
        {"name": "shipping_cost", "type": "double"},
        {"name": "country", "type": "string"},
        {"name": "city", "type": "string"},
        {"name": "postal_code", "type": "string"},
        {"name": "payment_method", "type": "string"},
        {"name": "order_status", "type": "string"},
        {"name": "shipping_date", "type": ["null", "string"], "default": None},
        {"name": "delivery_date", "type": ["null", "string"], "default": None},
        {"name": "customer_rating", "type": ["null", "int"], "default": None},
        {"name": "customer_review", "type": ["null", "string"], "default": None},
    ]
}

import random
import string
from datetime import datetime, timedelta
from typing import Dict
import pandas as pd
import config


class EcommerceDataGenerator:
    
    def __init__(self, seed: int = config.RANDOM_SEED):
        random.seed(seed)
        self.start_date = datetime.fromisoformat(config.START_DATE)
        self.end_date = datetime.fromisoformat(config.END_DATE)
    
    def _random_string(self, length: int) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def _random_date(self) -> str:
        delta = self.end_date - self.start_date
        random_days = random.randint(0, delta.days)
        random_seconds = random.randint(0, 86400)
        date = self.start_date + timedelta(days=random_days, seconds=random_seconds)
        return date.isoformat()
    
    def generate_order(self, order_id: int) -> Dict:
        country = random.choice(config.COUNTRIES)
        category = random.choice(config.PRODUCT_CATEGORIES)
        product = random.choice(config.PRODUCT_NAMES[category])
        quantity = random.randint(1, 10)
        unit_price = round(random.uniform(5.0, 500.0), 2)
        
        order = {
            "order_id": f"ORD-{order_id:010d}",
            "customer_id": f"CUST-{random.randint(1, 1000000):08d}",
            "customer_name": self._random_string(8) + " " + self._random_string(10),
            "customer_email": f"{self._random_string(10).lower()}@email.com",
            "order_date": self._random_date(),
            "product_id": f"PROD-{random.randint(1, 50000):06d}",
            "product_name": product,
            "product_category": category,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": round(quantity * unit_price, 2),
            "discount_percent": round(random.uniform(0, 30), 2),
            "tax_percent": round(random.uniform(0, 20), 2),
            "shipping_cost": round(random.uniform(0, 50), 2),
            "country": country,
            "city": random.choice(config.CITIES[country]),
            "postal_code": self._random_string(6),
            "payment_method": random.choice(config.PAYMENT_METHODS),
            "order_status": random.choice(config.ORDER_STATUSES),
            "shipping_date": self._random_date() if random.random() > 0.2 else None,
            "delivery_date": self._random_date() if random.random() > 0.3 else None,
            "customer_rating": random.randint(1, 5) if random.random() > 0.3 else None,
            "customer_review": self._random_string(50) if random.random() > 0.7 else None,
        }
        
        return order
    
    def generate_batch(self, num_records: int, batch_size: int = config.BATCH_SIZE) -> pd.DataFrame:
        orders = []
        print(f"Generating {num_records:,} records...")
        
        for i in range(num_records):
            if i % batch_size == 0 and i > 0:
                print(f"  Generated {i:,} / {num_records:,} records ({i/num_records*100:.1f}%)")
            orders.append(self.generate_order(i))
        
        print(f"  Generated {num_records:,} / {num_records:,} records (100.0%)")
        return pd.DataFrame(orders)

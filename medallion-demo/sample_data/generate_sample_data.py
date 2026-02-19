"""Generate realistic sample data for the medallion architecture demo."""
import csv
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path(__file__).parent
CUSTOMERS = 500
PRODUCTS = 50
ORDERS = 3000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

# --- Customer Data ---
first_names = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
               "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
               "Lucas", "Harper", "Henry", "Evelyn", "Alexander"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Thomas", "Taylor",
              "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"]
domains = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "mail.com"]

customers = []
for i in range(1, CUSTOMERS + 1):
    first = random.choice(first_names)
    last = random.choice(last_names)
    signup = START_DATE + timedelta(days=random.randint(0, 365))
    customers.append({
        "customer_id": f"CUST-{i:05d}",
        "email": f"{first.lower()}.{last.lower()}{i}@{random.choice(domains)}",
        "first_name": first,
        "last_name": last,
        "city": random.choice(["New York", "LA", "Chicago", "Houston", "Phoenix",
                                "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]),
        "state": random.choice(["NY", "CA", "IL", "TX", "AZ", "PA", "FL", "OH", "GA", "NC"]),
        "signup_date": signup.strftime("%Y-%m-%d"),
        "is_active": random.choice(["true", "true", "true", "false"]),
    })

# Add some dirty data for quality testing
customers.append({"customer_id": "", "email": "invalid", "first_name": "",
                   "last_name": "", "city": "", "state": "", "signup_date": "not-a-date",
                   "is_active": "maybe"})
customers.append({"customer_id": "CUST-00001", "email": "DUPLICATE@gmail.com",
                   "first_name": "Dupe", "last_name": "Record", "city": "Nowhere",
                   "state": "XX", "signup_date": "2024-06-15", "is_active": "true"})

with open(OUTPUT_DIR / "customers.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=customers[0].keys())
    w.writeheader()
    w.writerows(customers)

# --- Product Data ---
categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Sports",
              "Beauty", "Toys", "Food & Drink"]
products = []
for i in range(1, PRODUCTS + 1):
    cat = random.choice(categories)
    products.append({
        "product_id": f"PROD-{i:04d}",
        "name": f"{cat} Item {i}",
        "category": cat,
        "price": round(random.uniform(5, 500), 2),
        "cost": round(random.uniform(2, 250), 2),
    })

with open(OUTPUT_DIR / "products.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=products[0].keys())
    w.writeheader()
    w.writerows(products)

# --- Orders & Items ---
orders = []
order_items = []
item_id = 0
for i in range(1, ORDERS + 1):
    cust = random.choice(customers[:CUSTOMERS])  # exclude dirty records
    order_date = START_DATE + timedelta(days=random.randint(0, 730))
    num_items = random.randint(1, 5)
    total = 0
    for j in range(num_items):
        item_id += 1
        prod = random.choice(products)
        qty = random.randint(1, 3)
        line_total = round(prod["price"] * qty, 2)
        total += line_total
        order_items.append({
            "order_item_id": f"ITEM-{item_id:06d}",
            "order_id": f"ORD-{i:06d}",
            "product_id": prod["product_id"],
            "quantity": qty,
            "unit_price": prod["price"],
            "line_total": line_total,
        })
    orders.append({
        "order_id": f"ORD-{i:06d}",
        "customer_id": cust["customer_id"],
        "order_date": order_date.strftime("%Y-%m-%d"),
        "status": random.choice(["completed", "completed", "completed", "shipped",
                                  "processing", "cancelled", "refunded"]),
        "total_amount": round(total, 2),
        "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
    })

with open(OUTPUT_DIR / "orders.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=orders[0].keys())
    w.writeheader()
    w.writerows(orders)

with open(OUTPUT_DIR / "order_items.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=order_items[0].keys())
    w.writeheader()
    w.writerows(order_items)

print(f"Generated: {len(customers)} customers, {len(products)} products, "
      f"{len(orders)} orders, {len(order_items)} order items")

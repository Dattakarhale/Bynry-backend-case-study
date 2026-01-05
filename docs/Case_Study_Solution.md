Inventory Management System – Case Study
 Name: Datta Karhale
 Role: Backend Engineering Intern
 Platform: StockFlow (B2B Inventory Management SaaS)

Introduction
This document contains my analysis and solution for the StockFlow case study.
The requirements were intentionally incomplete, so I have clearly stated assumptions wherever needed. My focus is on backend correctness, data consistency, scalability, and real-world business use cases rather than just writing code.

 Part 1: Code Review & Debugging
Given Scenario
An API endpoint is used to create a new product and initialize inventory.
 Although the code compiles, it does not behave correctly in production.

1️ Issues Identified, Impact, and Fixes

 Issue 1: No Input Validation
Problem:
 The code directly accesses request fields (data['name'], etc.) without validation.
Impact in Production:
API crashes if any field is missing


Returns 500 errors instead of meaningful messages


Fix:
 Validate required fields and return proper error responses.

 Issue 2: SKU Uniqueness Not Enforced
Problem:
 SKU must be unique across the platform, but no check exists.
Impact in Production:
Duplicate SKUs cause incorrect inventory tracking


Reporting and integrations break


Fix:
 Check SKU existence before insertion and enforce a database unique constraint.

 Issue 3: Incorrect Product–Warehouse Relationship
Problem:
 warehouse_id is stored inside the Product table, but products can exist in multiple warehouses.
Impact in Production:
Same product cannot be stored in multiple warehouses


Data model becomes inflexible and incorrect


Fix:
 Remove warehouse_id from Product and manage this relationship via the Inventory table.

 Issue 4: No Transaction Management
Problem:
 Product and inventory are committed separately.
Impact in Production:
Product may exist without inventory if second commit fails


Leads to inconsistent database state


Fix:
 Wrap both operations inside a single transaction.

Issue 5: Price Precision Issue
Problem:
 Price may be treated as float instead of decimal.
Impact in Production:
Rounding errors in financial calculations


Fix:
 Use Decimal type for price handling.

 Corrected Code (Improved Version)
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json

    required_fields = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity']
    for field in required_fields:
        if field not in data:
            return {"error": f"{field} is required"}, 400

    if Product.query.filter_by(sku=data['sku']).first():
        return {"error": "SKU already exists"}, 409

    try:
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=Decimal(data['price'])
        )

        inventory = Inventory(
            product=product,
            warehouse_id=data['warehouse_id'],
            quantity=data['initial_quantity']
        )

        db.session.add(product)
        db.session.add(inventory)
        db.session.commit()

        return {"message": "Product created", "product_id": product.id}, 201

    except IntegrityError:
        db.session.rollback()
        return {"error": "Database error occurred"}, 500


 Part 2: Database Design
Proposed Database Schema
Company
id (PK)


name



Warehouse
id (PK)


company_id (FK → Company)


name


location



Product
id (PK)


company_id (FK → Company)


name


sku (UNIQUE)


price (DECIMAL)



Inventory
id (PK)


product_id (FK → Product)


warehouse_id (FK → Warehouse)


quantity


updated_at



Inventory_History
id (PK)


inventory_id (FK → Inventory)


previous_quantity


new_quantity


changed_at



Supplier
id (PK)


name


contact_email



Product_Supplier (Many-to-Many)
product_id (FK → Product)


supplier_id (FK → Supplier)



Bundle
parent_product_id (FK → Product)


child_product_id (FK → Product)


quantity



Design Decisions
Inventory table handles multi-warehouse product storage


Inventory history enables audit and stock tracking


Unique SKU ensures platform-wide product identity


Indexes on sku, product_id, warehouse_id improve performance


Separate bundle table supports composite products



Missing Requirements / Questions to Ask
Can products be shared across companies?


How is “recent sales activity” defined (time window)?


Are bundles physical kits or virtual groupings?


Can a product have multiple suppliers with priority?


Should stock updates trigger real-time alerts?



 Part 3: Low Stock Alert API
Endpoint
GET /api/companies/{company_id}/alerts/low-stock


Assumptions
Recent sales = at least one sale in last 30 days


Average daily sales is pre-calculated


Low-stock threshold stored per product


One primary supplier per product



API Implementation (Flask Example)
@app.route('/api/companies/<int:company_id>/alerts/low-stock')
def low_stock_alerts(company_id):
    alerts = []

    inventories = (
        db.session.query(Inventory)
        .join(Product)
        .join(Warehouse)
        .filter(Warehouse.company_id == company_id)
        .all()
    )

    for inv in inventories:
        if not inv.product.has_recent_sales:
            continue

        threshold = inv.product.low_stock_threshold

        if inv.quantity < threshold:
            daily_sales = max(inv.product.avg_daily_sales, 1)
            days_until_stockout = inv.quantity // daily_sales

            supplier = inv.product.suppliers[0] if inv.product.suppliers else None

            alerts.append({
                "product_id": inv.product.id,
                "product_name": inv.product.name,
                "sku": inv.product.sku,
                "warehouse_id": inv.warehouse.id,
                "warehouse_name": inv.warehouse.name,
                "current_stock": inv.quantity,
                "threshold": threshold,
                "days_until_stockout": days_until_stockout,
                "supplier": {
                    "id": supplier.id,
                    "name": supplier.name,
                    "contact_email": supplier.contact_email
                } if supplier else None
            })

    return {
        "alerts": alerts,
        "total_alerts": len(alerts)
    }


Edge Cases Considered
No recent sales → no alert


Zero average sales → division handled safely


No supplier linked


Multiple warehouses per company


Empty alert response



Conclusion
This solution prioritizes data integrity, scalability, and real-world backend design.
 While assumptions were necessary, the system is flexible enough to adapt as requirements evolve. My approach focuses on writing maintainable backend systems rather than just passing test cases.


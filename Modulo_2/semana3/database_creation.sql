-- SQLite database for sales system

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    product_entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    brand TEXT,
    code TEXT UNIQUE NOT NULL
);

-- Shopping cart table
CREATE TABLE shopping_cart (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL
);

-- Shopping cart items table
CREATE TABLE shopping_cart_item (
    id INTEGER PRIMARY KEY,
    shopping_cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (shopping_cart_id) REFERENCES shopping_cart(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Invoice table (modified to include phone and employee code as requested)
CREATE TABLE invoice (
    id INTEGER PRIMARY KEY,
    purchase_date DATE NOT NULL DEFAULT CURRENT_DATE,
    shopping_cart_id INTEGER NOT NULL,
    buyer_email TEXT NOT NULL,
    buyer_phone TEXT, -- New column for buyer's phone number
    cashier_employee_code TEXT, -- New column for cashier employee code
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    invoice_number TEXT UNIQUE NOT NULL,
    FOREIGN KEY (shopping_cart_id) REFERENCES shopping_cart(id) ON DELETE RESTRICT
);

-- Purchased products table (invoice-products relationship)
CREATE TABLE purchase_product (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_purchased INTEGER NOT NULL CHECK (quantity_purchased > 0),
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

-- Comments about SQLite limitations and decisions made:
/*
SQLITE LIMITATIONS IDENTIFIED AND RESOLUTIONS:

1. DATA TYPES:
   - SQLite uses dynamic typing, but we maintained logical types (INTEGER, TEXT, REAL, DATE)
   - DATE is stored as TEXT in ISO format (YYYY-MM-DD)
   - BIGINT from the diagram is mapped to INTEGER (SQLite handles 64-bit integers automatically)

2. AUTO-INCREMENT:
   - Uses INTEGER PRIMARY KEY to generate PKs automatically
   - In SQLite, INTEGER PRIMARY KEY automatically provides auto-increment functionality

3. CONSTRAINTS:
   - Added CHECK constraints to validate positive values
   - UNIQUE constraints for product codes and invoice numbers
   - NOT NULL where appropriate

4. FOREIGN KEYS:
   - Defined all relationships with ON DELETE CASCADE or RESTRICT according to business logic
   - CASCADE to delete dependent records
   - RESTRICT to prevent deletion of referenced records

5. REQUESTED MODIFICATIONS:
   - Added buyer_phone and cashier_employee_code columns to the invoice table
*/ 
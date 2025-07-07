-- Transaction Database Creation Script

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    returned BOOLEAN DEFAULT 0,
    return_date DATETIME NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert sample data for testing
-- Users: 3 active users for testing transactions
INSERT INTO users (name, email, phone, address) VALUES 
('John Doe', 'john.doe@email.com', '555-1234', '123 Main St, City'),
('Jane Smith', 'jane.smith@email.com', '555-5678', '456 Oak Ave, City'),
('Mike Johnson', 'mike.johnson@email.com', '555-9012', '789 Pine Rd, City');

INSERT INTO products (name, description, price, stock) VALUES 
('HP Laptop', 'HP Pavilion 15-inch laptop', 899.99, 9),   -- 10 - 1 (John's purchase)
('Wireless Mouse', 'Logitech wireless mouse', 25.99, 51),  -- 50 - 2 (John's purchase) + 3 (Jane's return)
('Mechanical Keyboard', 'RGB mechanical keyboard', 79.99, 25), -- 25 - 1 (Jane's purchase) + 1 (Mike's return)
('24" Monitor', '24-inch Full HD LED monitor', 199.99, 7);  -- 8 - 1 (Mike's purchase)

-- Insert sample invoices for testing
INSERT INTO invoices (user_id, product_id, quantity, unit_price, total, purchase_date, returned, return_date) VALUES 
-- Active purchases (not returned) - These can be used to test return transactions
(1, 2, 2, 25.99, 51.98, '2024-01-15 10:30:00', 0, NULL),    -- John bought 2 mice
(2, 3, 1, 79.99, 79.99, '2024-01-16 14:45:00', 0, NULL),   -- Jane bought 1 keyboard
(3, 4, 1, 199.99, 199.99, '2024-01-17 09:15:00', 0, NULL), -- Mike bought 1 monitor
(1, 1, 1, 899.99, 899.99, '2024-01-18 16:20:00', 0, NULL), -- John bought 1 laptop
-- Returned purchases (for testing return validation failures)
(2, 2, 3, 25.99, 77.97, '2024-01-10 11:00:00', 1, '2024-01-12 15:30:00'), -- Jane returned 3 mice
(3, 3, 1, 79.99, 79.99, '2024-01-11 13:45:00', 1, '2024-01-13 10:15:00');  -- Mike returned 1 keyboard



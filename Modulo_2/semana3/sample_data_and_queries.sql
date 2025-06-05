-- Sample data insertion to perform the requested queries
-- NOTE: First execute database_creation.sql to create the tables

-- Enable foreign keys in SQLite
PRAGMA foreign_keys = ON;

-- Insert sample products
INSERT INTO products (name, price, product_entry_date, brand, code) VALUES
('Smartphone Samsung Galaxy', 85000.00, '2024-01-15', 'Samsung', 'SAM001'),
('Laptop Dell Inspiron', 120000.00, '2024-01-20', 'Dell', 'DEL001'),
('Tablet iPad Air', 95000.00, '2024-02-01', 'Apple', 'APP001'),
('Auriculares Sony', 45000.00, '2024-02-05', 'Sony', 'SON001'),
('Mouse Logitech', 25000.00, '2024-02-10', 'Logitech', 'LOG001'),
('Teclado mecánico', 75000.00, '2024-02-15', 'Razer', 'RAZ001'),
('Monitor LG 24"', 65000.00, '2024-02-20', 'LG', 'LG001'),
('Cámara Canon', 180000.00, '2024-03-01', 'Canon', 'CAN001');

-- Insert shopping carts
INSERT INTO shopping_cart (email) VALUES
('juan.perez@email.com'),
('maria.garcia@email.com'),
('carlos.rodriguez@email.com'),
('ana.martinez@email.com');

-- Insert shopping cart items
INSERT INTO shopping_cart_item (shopping_cart_id, product_id, quantity) VALUES
(1, 1, 2), -- Juan buys 2 Samsung Galaxy
(1, 4, 1), -- Juan buys 1 Sony Headphones
(2, 2, 1), -- María buys 1 Dell Laptop
(2, 5, 2), -- María buys 2 Logitech Mouse
(3, 3, 1), -- Carlos buys 1 iPad Air
(3, 6, 1), -- Carlos buys 1 Mechanical Keyboard
(4, 7, 1), -- Ana buys 1 LG Monitor
(4, 8, 1); -- Ana buys 1 Canon Camera

-- Insert invoices
INSERT INTO invoice (purchase_date, shopping_cart_id, buyer_email, buyer_phone, cashier_employee_code, total_amount, invoice_number) VALUES
('2024-03-15', 1, 'juan.perez@email.com', '+57-300-1234567', 'EMP001', 215000.00, 'INV-2024-001'),
('2024-03-16', 2, 'maria.garcia@email.com', '+57-301-2345678', 'EMP002', 170000.00, 'INV-2024-002'),
('2024-03-17', 3, 'carlos.rodriguez@email.com', '+57-302-3456789', 'EMP001', 170000.00, 'INV-2024-003'),
('2024-03-18', 4, 'ana.martinez@email.com', '+57-303-4567890', 'EMP003', 245000.00, 'INV-2024-004'),
-- Additional invoice for the same buyer (Juan)
('2024-03-20', 1, 'juan.perez@email.com', '+57-300-1234567', 'EMP002', 75000.00, 'INV-2024-005');

-- Insert purchased products (invoice details)
INSERT INTO purchase_product (invoice_id, product_id, quantity_purchased, total_amount) VALUES
-- Invoice 1 (Juan)
(1, 1, 2, 170000.00), -- 2 Samsung Galaxy
(1, 4, 1, 45000.00),  -- 1 Sony Headphones
-- Invoice 2 (María)
(2, 2, 1, 120000.00), -- 1 Dell Laptop
(2, 5, 2, 50000.00),  -- 2 Logitech Mouse
-- Invoice 3 (Carlos)
(3, 3, 1, 95000.00),  -- 1 iPad Air
(3, 6, 1, 75000.00),  -- 1 Mechanical Keyboard
-- Invoice 4 (Ana)
(4, 7, 1, 65000.00),  -- 1 LG Monitor
(4, 8, 1, 180000.00), -- 1 Canon Camera
-- Invoice 5 (Juan - second purchase)
(5, 6, 1, 75000.00);  -- 1 Mechanical Keyboard

-- ==================================================
-- REQUESTED SELECT QUERIES
-- ==================================================

-- 1. Get all stored products
SELECT 
    id,
    name,
    price,
    product_entry_date,
    brand,
    code
FROM products
ORDER BY name;

-- 2. Get all products with price greater than 50000
SELECT 
    id,
    name,
    price,
    brand,
    code
FROM products
WHERE price > 50000
ORDER BY price DESC;

-- 3. Get all purchases of the same product by id (example: product id = 1)
SELECT 
    pp.id as purchase_id,
    p.name as product_name,
    p.code as product_code,
    pp.quantity_purchased,
    pp.total_amount,
    i.invoice_number,
    i.purchase_date,
    i.buyer_email
FROM purchase_product pp
JOIN products p ON pp.product_id = p.id
JOIN invoice i ON pp.invoice_id = i.id
WHERE p.id = 1  -- Change this ID to query another product
ORDER BY i.purchase_date;

-- 4. Get all purchases grouped by product, showing the total purchased across all purchases
SELECT 
    p.id,
    p.name as product_name,
    p.code as product_code,
    p.price as unit_price,
    SUM(pp.quantity_purchased) as total_quantity_purchased,
    SUM(pp.total_amount) as total_revenue,
    COUNT(pp.id) as number_of_transactions
FROM products p
LEFT JOIN purchase_product pp ON p.id = pp.product_id
GROUP BY p.id, p.name, p.code, p.price
ORDER BY total_revenue DESC;

-- 5. Get all invoices made by the same buyer (example: juan.perez@email.com)
SELECT 
    i.id,
    i.invoice_number,
    i.purchase_date,
    i.buyer_email,
    i.buyer_phone,
    i.cashier_employee_code,
    i.total_amount
FROM invoice i
WHERE i.buyer_email = 'juan.perez@email.com'  -- Change email for another buyer
ORDER BY i.purchase_date;

-- 6. Get all invoices ordered by total amount in descending order
SELECT 
    i.id,
    i.invoice_number,
    i.purchase_date,
    i.buyer_email,
    i.buyer_phone,
    i.cashier_employee_code,
    i.total_amount
FROM invoice i
ORDER BY i.total_amount DESC;

-- 7. Get a single invoice by invoice number (example: INV-2024-001)
SELECT 
    i.id,
    i.invoice_number,
    i.purchase_date,
    i.buyer_email,
    i.buyer_phone,
    i.cashier_employee_code,
    i.total_amount,
    i.shopping_cart_id,
    -- Purchased product details
    p.name as product_name,
    p.code as product_code,
    pp.quantity_purchased,
    pp.total_amount as product_total
FROM invoice i
LEFT JOIN purchase_product pp ON i.id = pp.invoice_id
LEFT JOIN products p ON pp.product_id = p.id
WHERE i.invoice_number = 'INV-2024-001'  -- Change invoice number as needed
ORDER BY p.name; 
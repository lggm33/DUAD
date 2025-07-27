-- Transaction Scripts for Purchases and Returns
-- SQLite Transaction Scripts
-- 
-- IMPORTANT: These transactions use RAISE(ABORT) to fail immediately if validations don't pass
-- This ensures data integrity by preventing invalid operations from continuing

-- =====================================================
-- TRANSACTION 1: MAKE A PURCHASE
-- =====================================================

-- Example transaction to make a purchase
-- Parameters: user_id, product_id, quantity

BEGIN TRANSACTION;

-- Variables for the example (in practice these would be parameters)
-- User ID = 1, Product ID = 1, Quantity = 2

-- Step 1: Validate that the product has enough stock (FAIL if insufficient)
SELECT 
    CASE 
        WHEN stock >= 2 THEN stock
        ELSE RAISE(ABORT, 'ERROR: Insufficient stock. Available: ' || stock || ', Required: 2')
    END as validated_stock,
    name
FROM products 
WHERE id = 1 AND active = 1
UNION ALL
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN RAISE(ABORT, 'ERROR: Product not found or inactive')
        ELSE 0
    END,
    'Product validation'
FROM products 
WHERE id = 1 AND active = 1;

-- Step 2: Validate that the user exists (FAIL if not found)
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN COUNT(*)
        ELSE RAISE(ABORT, 'ERROR: User not found or inactive')
    END as validated_user,
    COALESCE(MAX(name), 'No user found') as user_name
FROM users 
WHERE id = 1 AND active = 1;

-- Step 3: Create the invoice with the related user
INSERT INTO invoices (user_id, product_id, quantity, unit_price, total)
SELECT 
    1 as user_id,
    1 as product_id,
    2 as quantity,
    price as unit_price,
    (price * 2) as total
FROM products 
WHERE id = 1 
    AND stock >= 2 
    AND EXISTS (SELECT 1 FROM users WHERE id = 1 AND active = 1);

-- Step 4: Reduce the product stock
UPDATE products 
SET stock = stock - 2 
WHERE id = 1 
    AND stock >= 2;

-- Verify that all operations were successful
SELECT 
    CASE 
        WHEN changes() > 0 THEN 'Purchase completed successfully - Stock updated'
        ELSE 'Warning: No changes made - Check validations'
    END as result;

COMMIT;

-- =====================================================
-- TRANSACTION 2: PROCESS A RETURN
-- =====================================================

-- Example transaction to process a return
-- Parameters: invoice_id

BEGIN TRANSACTION;

-- Variable for the example: invoice_id = 1

-- Step 1: Validate that the invoice exists in the DB and has not been returned (FAIL if not valid)
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN RAISE(ABORT, 'ERROR: Invoice not found or already returned')
        ELSE COUNT(*)
    END as validation_result
FROM invoices 
WHERE id = 1 AND returned = 0;

-- Get invoice details after validation passes
SELECT 
    i.id,
    i.user_id,
    i.product_id,
    i.quantity,
    i.total,
    i.returned,
    u.name as user_name,
    p.name as product_name
FROM invoices i
JOIN users u ON i.user_id = u.id
JOIN products p ON i.product_id = p.id
WHERE i.id = 1 AND i.returned = 0;

-- Step 2: Increase the product stock by the quantity that was purchased
UPDATE products 
SET stock = stock + (
    SELECT quantity 
    FROM invoices 
    WHERE id = 1 AND returned = 0
)
WHERE id = (
    SELECT product_id 
    FROM invoices 
    WHERE id = 1 AND returned = 0
);

-- Step 3: Update the invoice and mark it as returned
UPDATE invoices 
SET returned = 1,
    return_date = CURRENT_TIMESTAMP
WHERE id = 1 AND returned = 0;

-- Verify that the return was successful
SELECT 
    CASE 
        WHEN changes() > 0 THEN 'Return processed successfully - Stock restored'
        ELSE 'Warning: No changes made - Check validations'
    END as result;

COMMIT;


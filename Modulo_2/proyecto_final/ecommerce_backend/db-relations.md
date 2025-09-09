# 📊 Database Relations - Proyecto Final

Este documento describe las relaciones entre las entidades de la base de datos del sistema de e-commerce.

---

## 👥 Users (Usuarios)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Delivery Addresses:** Un usuario puede tener múltiples direcciones de entrega (`user_id` en `delivery_addresses`)
- **Carts:** Un usuario puede tener múltiples carritos (`user_id` en `carts`)
- **Sales:** Un usuario puede realizar múltiples ventas (`user_id` en `sales`)
- **Sessions:** Un usuario puede tener múltiples sesiones activas (`user_id` en `sessions`)

---

## 📍 Delivery Addresses (Direcciones de Entrega)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Users:** Cada dirección de entrega pertenece a un usuario (`user_id`)
- **Invoices:** Una dirección de entrega puede estar asociada a múltiples facturas (`delivery_address_id` en `invoices`)

---

## 📦 Products (Productos)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Cart Products:** Un producto puede estar en múltiples carritos (`product_id` en `cart_products`)
- **Sale Products:** Un producto puede estar en múltiples ventas (`product_id` en `sale_products`)

---

## 🛒 Carts (Carritos)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Users:** Cada carrito pertenece a un usuario (`user_id`)
- **Cart Products:** Un carrito puede contener múltiples productos (`cart_id` en `cart_products`)

---

## 🔗 Cart Products (Carritos_Productos)

**🔑 Primary Key:** Combinación de `cart_id` y `product_id` *(Composite Key)*

### 📋 Relaciones:
- **Carts:** Relaciona productos con carritos (`cart_id`)
- **Products:** Relaciona carritos con productos (`product_id`)

---

## 💰 Sales (Ventas)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Users:** Cada venta es realizada por un usuario (`user_id`)
- **Sale Products:** Una venta puede incluir múltiples productos (`sale_id` en `sale_products`)
- **Invoices:** Una venta puede generar múltiples facturas (`sale_id` en `invoices`)

---

## 🔗 Sale Products (Ventas_Productos)

**🔑 Primary Key:** Combinación de `sale_id` y `product_id` *(Composite Key)*

### 📋 Relaciones:
- **Sales:** Relaciona productos con ventas (`sale_id`)
- **Products:** Relaciona ventas con productos (`product_id`)

---

## 🧾 Invoices (Facturas)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Sales:** Cada factura está asociada a una venta (`sale_id`)
- **Delivery Addresses:** Cada factura puede tener una dirección de entrega (`delivery_address_id`)

---

## 🔐 Sessions (Sesiones)

**🔑 Primary Key:** `id`

### 📋 Relaciones:
- **Users:** Cada sesión pertenece a un usuario (`user_id`)

---

## 📈 Resumen de Cardinalidades

| Entidad | Relación | Cardinalidad |
|---------|----------|-------------|
| Users → Delivery Addresses | One-to-Many | 1:N |
| Users → Carts | One-to-Many | 1:N |
| Users → Sales | One-to-Many | 1:N |
| Users → Sessions | One-to-Many | 1:N |
| Products → Cart Products | One-to-Many | 1:N |
| Products → Sale Products | One-to-Many | 1:N |
| Carts → Cart Products | One-to-Many | 1:N |
| Sales → Sale Products | One-to-Many | 1:N |
| Sales → Invoices | One-to-Many | 1:N |
| Delivery Addresses → Invoices | One-to-Many | 1:N |
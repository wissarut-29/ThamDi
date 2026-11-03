CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name        VARCHAR NOT NULL,
    province    VARCHAR NOT NULL,
    segment     VARCHAR NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    category   VARCHAR NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date  DATE NOT NULL,
    channel     VARCHAR NOT NULL
);

CREATE TABLE order_items (
    order_id   INTEGER NOT NULL REFERENCES orders (order_id),
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    quantity   INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- data

INSERT INTO customers VALUES (1, 'ลูกค้า1', 'กรุงเทพมหานคร', 'องค์กร');
INSERT INTO customers VALUES (2, 'ลูกค้า2', 'ชลบุรี', 'ทั่วไป');
INSERT INTO customers VALUES (3, 'ลูกค้า3', 'เชียงใหม่', 'องค์กร');
INSERT INTO customers VALUES (4, 'ลูกค้า4', 'ขอนแก่น', 'สมาชิก');
INSERT INTO customers VALUES (5, 'ลูกค้า5', 'เชียงใหม่', 'สมาชิก');
INSERT INTO customers VALUES (6, 'ลูกค้า6', 'กรุงเทพมหานคร', 'สมาชิก');
INSERT INTO customers VALUES (7, 'ลูกค้า7', 'กรุงเทพมหานคร', 'ทั่วไป');
INSERT INTO customers VALUES (8, 'ลูกค้า8', 'ชลบุรี', 'ทั่วไป');
INSERT INTO customers VALUES (9, 'ลูกค้า9', 'เชียงใหม่', 'องค์กร');
INSERT INTO customers VALUES (10, 'ลูกค้า10', 'เชียงใหม่', 'สมาชิก');
INSERT INTO products VALUES (1, 'สินค้า1', 'ขนม', 30.67);
INSERT INTO products VALUES (2, 'สินค้า2', 'ของใช้', 58.82);
INSERT INTO products VALUES (3, 'สินค้า3', 'ขนม', 473.57);
INSERT INTO products VALUES (4, 'สินค้า4', 'เครื่องดื่ม', 363.72);
INSERT INTO products VALUES (5, 'สินค้า5', 'เครื่องดื่ม', 275.23);
INSERT INTO products VALUES (6, 'สินค้า6', 'ของใช้', 377.25);
INSERT INTO products VALUES (7, 'สินค้า7', 'ขนม', 338.32);
INSERT INTO orders VALUES (1, 9, '2025-12-14', 'หน้าร้าน');
INSERT INTO orders VALUES (2, 6, '2025-11-12', 'หน้าร้าน');
INSERT INTO orders VALUES (3, 10, '2025-08-09', 'หน้าร้าน');
INSERT INTO orders VALUES (4, 4, '2025-07-16', 'หน้าร้าน');
INSERT INTO orders VALUES (5, 9, '2025-12-26', 'หน้าร้าน');
INSERT INTO orders VALUES (6, 7, '2025-10-11', 'หน้าร้าน');
INSERT INTO orders VALUES (7, 4, '2025-09-28', 'หน้าร้าน');
INSERT INTO orders VALUES (8, 6, '2025-02-05', 'หน้าร้าน');
INSERT INTO orders VALUES (9, 2, '2025-04-04', 'หน้าร้าน');
INSERT INTO orders VALUES (10, 9, '2025-01-13', 'หน้าร้าน');
INSERT INTO orders VALUES (11, 4, '2025-04-01', 'หน้าร้าน');
INSERT INTO orders VALUES (12, 4, '2025-02-09', 'ออนไลน์');
INSERT INTO orders VALUES (13, 5, '2025-05-05', 'ออนไลน์');
INSERT INTO orders VALUES (14, 2, '2025-02-01', 'ออนไลน์');
INSERT INTO orders VALUES (15, 10, '2025-03-12', 'หน้าร้าน');
INSERT INTO orders VALUES (16, 1, '2025-02-16', 'หน้าร้าน');
INSERT INTO orders VALUES (17, 6, '2025-09-03', 'ออนไลน์');
INSERT INTO orders VALUES (18, 7, '2025-03-26', 'หน้าร้าน');
INSERT INTO orders VALUES (19, 7, '2025-04-11', 'ออนไลน์');
INSERT INTO order_items VALUES (17, 1, 1, 30.67);
INSERT INTO order_items VALUES (11, 3, 4, 473.57);
INSERT INTO order_items VALUES (18, 7, 4, 338.32);
INSERT INTO order_items VALUES (7, 4, 2, 363.72);
INSERT INTO order_items VALUES (16, 7, 4, 338.32);
INSERT INTO order_items VALUES (10, 6, 3, 377.25);
INSERT INTO order_items VALUES (17, 4, 1, 363.72);
INSERT INTO order_items VALUES (3, 3, 5, 473.57);
INSERT INTO order_items VALUES (6, 1, 2, 30.67);
INSERT INTO order_items VALUES (14, 5, 2, 275.23);
INSERT INTO order_items VALUES (17, 7, 2, 338.32);
INSERT INTO order_items VALUES (18, 7, 5, 338.32);
INSERT INTO order_items VALUES (4, 3, 2, 473.57);
INSERT INTO order_items VALUES (11, 3, 1, 473.57);
INSERT INTO order_items VALUES (18, 3, 5, 473.57);
INSERT INTO order_items VALUES (8, 5, 1, 275.23);
INSERT INTO order_items VALUES (11, 7, 4, 338.32);
INSERT INTO order_items VALUES (17, 6, 3, 377.25);
INSERT INTO order_items VALUES (3, 2, 5, 58.82);
INSERT INTO order_items VALUES (17, 6, 2, 377.25);
INSERT INTO order_items VALUES (11, 7, 3, 338.32);
INSERT INTO order_items VALUES (5, 5, 2, 275.23);
INSERT INTO order_items VALUES (6, 5, 1, 275.23);
INSERT INTO order_items VALUES (1, 3, 2, 473.57);
INSERT INTO order_items VALUES (17, 1, 3, 30.67);
INSERT INTO order_items VALUES (5, 1, 3, 30.67);
INSERT INTO order_items VALUES (7, 5, 4, 275.23);
INSERT INTO order_items VALUES (9, 3, 1, 473.57);
INSERT INTO order_items VALUES (18, 2, 2, 58.82);
INSERT INTO order_items VALUES (11, 1, 4, 30.67);
INSERT INTO order_items VALUES (7, 5, 4, 275.23);
INSERT INTO order_items VALUES (4, 3, 1, 473.57);
INSERT INTO order_items VALUES (5, 3, 5, 473.57);
INSERT INTO order_items VALUES (1, 2, 2, 58.82);
INSERT INTO order_items VALUES (4, 2, 5, 58.82);
INSERT INTO order_items VALUES (1, 6, 3, 377.25);
INSERT INTO order_items VALUES (3, 1, 3, 30.67);
INSERT INTO order_items VALUES (2, 1, 5, 30.67);
INSERT INTO order_items VALUES (3, 2, 3, 58.82);
INSERT INTO order_items VALUES (17, 1, 4, 30.67);

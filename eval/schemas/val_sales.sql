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

INSERT INTO customers VALUES (1, 'ลูกค้า1', 'ชลบุรี', 'สมาชิก');
INSERT INTO customers VALUES (2, 'ลูกค้า2', 'กรุงเทพมหานคร', 'องค์กร');
INSERT INTO customers VALUES (3, 'ลูกค้า3', 'ขอนแก่น', 'สมาชิก');
INSERT INTO customers VALUES (4, 'ลูกค้า4', 'กรุงเทพมหานคร', 'สมาชิก');
INSERT INTO customers VALUES (5, 'ลูกค้า5', 'เชียงใหม่', 'ทั่วไป');
INSERT INTO customers VALUES (6, 'ลูกค้า6', 'กรุงเทพมหานคร', 'สมาชิก');
INSERT INTO customers VALUES (7, 'ลูกค้า7', 'เชียงใหม่', 'ทั่วไป');
INSERT INTO customers VALUES (8, 'ลูกค้า8', 'ขอนแก่น', 'สมาชิก');
INSERT INTO customers VALUES (9, 'ลูกค้า9', 'ขอนแก่น', 'ทั่วไป');
INSERT INTO customers VALUES (10, 'ลูกค้า10', 'ขอนแก่น', 'สมาชิก');
INSERT INTO products VALUES (1, 'สินค้า1', 'ของใช้', 486.59);
INSERT INTO products VALUES (2, 'สินค้า2', 'ของใช้', 13.36);
INSERT INTO products VALUES (3, 'สินค้า3', 'เครื่องดื่ม', 302.64);
INSERT INTO products VALUES (4, 'สินค้า4', 'ของใช้', 354.9);
INSERT INTO products VALUES (5, 'สินค้า5', 'ขนม', 305.53);
INSERT INTO products VALUES (6, 'สินค้า6', 'ขนม', 293.27);
INSERT INTO products VALUES (7, 'สินค้า7', 'ขนม', 190.69);
INSERT INTO orders VALUES (1, 6, '2025-12-01', 'หน้าร้าน');
INSERT INTO orders VALUES (2, 7, '2025-09-02', 'หน้าร้าน');
INSERT INTO orders VALUES (3, 9, '2025-04-23', 'หน้าร้าน');
INSERT INTO orders VALUES (4, 4, '2025-09-22', 'หน้าร้าน');
INSERT INTO orders VALUES (5, 1, '2025-03-16', 'หน้าร้าน');
INSERT INTO orders VALUES (6, 4, '2025-07-04', 'ออนไลน์');
INSERT INTO orders VALUES (7, 2, '2025-05-08', 'ออนไลน์');
INSERT INTO orders VALUES (8, 1, '2025-06-04', 'ออนไลน์');
INSERT INTO orders VALUES (9, 3, '2025-04-05', 'ออนไลน์');
INSERT INTO orders VALUES (10, 10, '2025-07-18', 'หน้าร้าน');
INSERT INTO orders VALUES (11, 10, '2025-12-18', 'ออนไลน์');
INSERT INTO orders VALUES (12, 7, '2025-07-10', 'ออนไลน์');
INSERT INTO orders VALUES (13, 7, '2025-03-26', 'หน้าร้าน');
INSERT INTO orders VALUES (14, 8, '2025-02-18', 'หน้าร้าน');
INSERT INTO orders VALUES (15, 9, '2025-01-12', 'หน้าร้าน');
INSERT INTO orders VALUES (16, 7, '2025-07-25', 'ออนไลน์');
INSERT INTO orders VALUES (17, 2, '2025-11-06', 'หน้าร้าน');
INSERT INTO orders VALUES (18, 5, '2025-02-21', 'หน้าร้าน');
INSERT INTO orders VALUES (19, 7, '2025-06-13', 'ออนไลน์');
INSERT INTO order_items VALUES (6, 6, 5, 293.27);
INSERT INTO order_items VALUES (1, 7, 4, 190.69);
INSERT INTO order_items VALUES (10, 4, 2, 354.9);
INSERT INTO order_items VALUES (10, 3, 4, 302.64);
INSERT INTO order_items VALUES (6, 2, 1, 13.36);
INSERT INTO order_items VALUES (12, 2, 3, 13.36);
INSERT INTO order_items VALUES (2, 4, 5, 354.9);
INSERT INTO order_items VALUES (14, 7, 2, 190.69);
INSERT INTO order_items VALUES (6, 5, 4, 305.53);
INSERT INTO order_items VALUES (19, 1, 4, 486.59);
INSERT INTO order_items VALUES (16, 2, 2, 13.36);
INSERT INTO order_items VALUES (8, 1, 1, 486.59);
INSERT INTO order_items VALUES (17, 4, 3, 354.9);
INSERT INTO order_items VALUES (15, 2, 5, 13.36);
INSERT INTO order_items VALUES (15, 1, 5, 486.59);
INSERT INTO order_items VALUES (15, 1, 4, 486.59);
INSERT INTO order_items VALUES (13, 4, 5, 354.9);
INSERT INTO order_items VALUES (8, 5, 5, 305.53);
INSERT INTO order_items VALUES (3, 2, 3, 13.36);
INSERT INTO order_items VALUES (13, 2, 3, 13.36);
INSERT INTO order_items VALUES (16, 1, 3, 486.59);
INSERT INTO order_items VALUES (18, 2, 2, 13.36);
INSERT INTO order_items VALUES (2, 3, 4, 302.64);
INSERT INTO order_items VALUES (3, 2, 2, 13.36);
INSERT INTO order_items VALUES (14, 4, 2, 354.9);
INSERT INTO order_items VALUES (13, 5, 2, 305.53);
INSERT INTO order_items VALUES (10, 2, 2, 13.36);
INSERT INTO order_items VALUES (17, 4, 1, 354.9);
INSERT INTO order_items VALUES (10, 5, 3, 305.53);
INSERT INTO order_items VALUES (12, 6, 5, 293.27);
INSERT INTO order_items VALUES (8, 3, 2, 302.64);
INSERT INTO order_items VALUES (9, 5, 1, 305.53);
INSERT INTO order_items VALUES (7, 2, 2, 13.36);
INSERT INTO order_items VALUES (3, 2, 5, 13.36);
INSERT INTO order_items VALUES (10, 3, 1, 302.64);
INSERT INTO order_items VALUES (17, 5, 2, 305.53);
INSERT INTO order_items VALUES (19, 3, 5, 302.64);
INSERT INTO order_items VALUES (12, 4, 1, 354.9);
INSERT INTO order_items VALUES (19, 2, 4, 13.36);
INSERT INTO order_items VALUES (10, 4, 2, 354.9);

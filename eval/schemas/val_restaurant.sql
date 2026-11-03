CREATE TABLE staff (
    staff_id INTEGER PRIMARY KEY,
    name     VARCHAR NOT NULL,
    position VARCHAR NOT NULL,
    branch   VARCHAR NOT NULL
);

CREATE TABLE menu_items (
    menu_item_id INTEGER PRIMARY KEY,
    name         VARCHAR NOT NULL,
    category     VARCHAR NOT NULL,
    price        DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id   INTEGER PRIMARY KEY,
    staff_id   INTEGER NOT NULL REFERENCES staff (staff_id),
    order_date DATE NOT NULL,
    channel    VARCHAR NOT NULL
);

CREATE TABLE order_items (
    order_id     INTEGER NOT NULL REFERENCES orders (order_id),
    menu_item_id INTEGER NOT NULL REFERENCES menu_items (menu_item_id),
    quantity     INTEGER NOT NULL
);

-- data

INSERT INTO staff VALUES (1, 'พนักงาน1', 'กุ๊ก', 'สาขาลาดพร้าว');
INSERT INTO staff VALUES (2, 'พนักงาน2', 'แคชเชียร์', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (3, 'พนักงาน3', 'พนักงานเสิร์ฟ', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (4, 'พนักงาน4', 'แคชเชียร์', 'สาขาสุขุมวิท');
INSERT INTO staff VALUES (5, 'พนักงาน5', 'กุ๊ก', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (6, 'พนักงาน6', 'กุ๊ก', 'สาขาลาดพร้าว');
INSERT INTO staff VALUES (7, 'พนักงาน7', 'กุ๊ก', 'สาขาสุขุมวิท');
INSERT INTO staff VALUES (8, 'พนักงาน8', 'พนักงานเสิร์ฟ', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO menu_items VALUES (1, 'เมนู1', 'เครื่องดื่ม', 142.7);
INSERT INTO menu_items VALUES (2, 'เมนู2', 'เครื่องดื่ม', 143.98);
INSERT INTO menu_items VALUES (3, 'เมนู3', 'เครื่องดื่ม', 94.81);
INSERT INTO menu_items VALUES (4, 'เมนู4', 'เครื่องดื่ม', 231.89);
INSERT INTO menu_items VALUES (5, 'เมนู5', 'ของหวาน', 289.99);
INSERT INTO menu_items VALUES (6, 'เมนู6', 'ของหวาน', 260.99);
INSERT INTO menu_items VALUES (7, 'เมนู7', 'ของหวาน', 66.39);
INSERT INTO menu_items VALUES (8, 'เมนู8', 'ของหวาน', 240.57);
INSERT INTO menu_items VALUES (9, 'เมนู9', 'อาหารจานเดียว', 128.14);
INSERT INTO menu_items VALUES (10, 'เมนู10', 'อาหารจานเดียว', 37.83);
INSERT INTO menu_items VALUES (11, 'เมนู11', 'เครื่องดื่ม', 297.95);
INSERT INTO orders VALUES (1, 3, '2025-08-26', 'เดลิเวอรี');
INSERT INTO orders VALUES (2, 8, '2025-09-22', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (3, 3, '2025-08-17', 'เดลิเวอรี');
INSERT INTO orders VALUES (4, 1, '2025-05-11', 'นั่งทาน');
INSERT INTO orders VALUES (5, 2, '2025-12-24', 'นั่งทาน');
INSERT INTO orders VALUES (6, 8, '2025-06-16', 'เดลิเวอรี');
INSERT INTO orders VALUES (7, 7, '2025-05-26', 'นั่งทาน');
INSERT INTO orders VALUES (8, 2, '2025-07-04', 'เดลิเวอรี');
INSERT INTO orders VALUES (9, 4, '2025-03-25', 'เดลิเวอรี');
INSERT INTO orders VALUES (10, 5, '2025-07-22', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (11, 8, '2025-03-04', 'เดลิเวอรี');
INSERT INTO orders VALUES (12, 2, '2025-01-16', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (13, 4, '2025-09-22', 'นั่งทาน');
INSERT INTO orders VALUES (14, 6, '2025-12-08', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (15, 7, '2025-05-19', 'เดลิเวอรี');
INSERT INTO orders VALUES (16, 6, '2025-06-19', 'เดลิเวอรี');
INSERT INTO orders VALUES (17, 1, '2025-02-22', 'นั่งทาน');
INSERT INTO orders VALUES (18, 2, '2025-01-21', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (19, 2, '2025-11-17', 'สั่งกลับบ้าน');
INSERT INTO order_items VALUES (8, 8, 3);
INSERT INTO order_items VALUES (12, 1, 1);
INSERT INTO order_items VALUES (10, 2, 2);
INSERT INTO order_items VALUES (16, 3, 1);
INSERT INTO order_items VALUES (15, 9, 3);
INSERT INTO order_items VALUES (3, 3, 3);
INSERT INTO order_items VALUES (13, 1, 2);
INSERT INTO order_items VALUES (18, 7, 4);
INSERT INTO order_items VALUES (4, 3, 1);
INSERT INTO order_items VALUES (19, 10, 2);
INSERT INTO order_items VALUES (14, 4, 4);
INSERT INTO order_items VALUES (9, 4, 3);
INSERT INTO order_items VALUES (17, 5, 3);
INSERT INTO order_items VALUES (12, 6, 1);
INSERT INTO order_items VALUES (7, 2, 3);
INSERT INTO order_items VALUES (7, 1, 2);
INSERT INTO order_items VALUES (10, 1, 4);
INSERT INTO order_items VALUES (11, 8, 2);
INSERT INTO order_items VALUES (7, 4, 1);
INSERT INTO order_items VALUES (17, 1, 4);
INSERT INTO order_items VALUES (13, 6, 4);
INSERT INTO order_items VALUES (6, 2, 1);
INSERT INTO order_items VALUES (15, 11, 2);
INSERT INTO order_items VALUES (7, 9, 1);
INSERT INTO order_items VALUES (8, 2, 3);
INSERT INTO order_items VALUES (18, 3, 1);
INSERT INTO order_items VALUES (16, 2, 3);
INSERT INTO order_items VALUES (11, 5, 2);
INSERT INTO order_items VALUES (13, 4, 1);
INSERT INTO order_items VALUES (9, 8, 3);
INSERT INTO order_items VALUES (19, 5, 4);
INSERT INTO order_items VALUES (2, 4, 3);
INSERT INTO order_items VALUES (4, 7, 4);
INSERT INTO order_items VALUES (3, 3, 2);
INSERT INTO order_items VALUES (4, 10, 2);
INSERT INTO order_items VALUES (12, 5, 2);
INSERT INTO order_items VALUES (3, 1, 4);
INSERT INTO order_items VALUES (14, 9, 2);
INSERT INTO order_items VALUES (14, 4, 4);
INSERT INTO order_items VALUES (2, 3, 2);

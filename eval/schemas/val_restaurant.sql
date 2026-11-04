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

INSERT INTO staff VALUES (1, 'พนักงาน1', 'กุ๊ก', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (2, 'พนักงาน2', 'กุ๊ก', 'สาขาลาดพร้าว');
INSERT INTO staff VALUES (3, 'พนักงาน3', 'พนักงานเสิร์ฟ', 'สาขาลาดพร้าว');
INSERT INTO staff VALUES (4, 'พนักงาน4', 'พนักงานเสิร์ฟ', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (5, 'พนักงาน5', 'แคชเชียร์', 'สาขาสุขุมวิท');
INSERT INTO staff VALUES (6, 'พนักงาน6', 'กุ๊ก', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (7, 'พนักงาน7', 'แคชเชียร์', 'สาขาเซ็นทรัลเวิลด์');
INSERT INTO staff VALUES (8, 'พนักงาน8', 'กุ๊ก', 'สาขาลาดพร้าว');
INSERT INTO menu_items VALUES (1, 'เมนู1', 'เครื่องดื่ม', 282.72);
INSERT INTO menu_items VALUES (2, 'เมนู2', 'เครื่องดื่ม', 277.41);
INSERT INTO menu_items VALUES (3, 'เมนู3', 'อาหารจานเดียว', 288.14);
INSERT INTO menu_items VALUES (4, 'เมนู4', 'ของหวาน', 255.03);
INSERT INTO menu_items VALUES (5, 'เมนู5', 'เครื่องดื่ม', 78.57);
INSERT INTO menu_items VALUES (6, 'เมนู6', 'เครื่องดื่ม', 229.42);
INSERT INTO menu_items VALUES (7, 'เมนู7', 'ของหวาน', 187.68);
INSERT INTO menu_items VALUES (8, 'เมนู8', 'อาหารจานเดียว', 186.29);
INSERT INTO menu_items VALUES (9, 'เมนู9', 'เครื่องดื่ม', 234.21);
INSERT INTO menu_items VALUES (10, 'เมนู10', 'เครื่องดื่ม', 57.44);
INSERT INTO menu_items VALUES (11, 'เมนู11', 'ของหวาน', 220.03);
INSERT INTO orders VALUES (1, 6, '2025-07-08', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (2, 6, '2025-12-13', 'เดลิเวอรี');
INSERT INTO orders VALUES (3, 2, '2025-07-01', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (4, 7, '2025-07-17', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (5, 5, '2025-07-01', 'เดลิเวอรี');
INSERT INTO orders VALUES (6, 1, '2025-02-21', 'เดลิเวอรี');
INSERT INTO orders VALUES (7, 8, '2025-04-15', 'นั่งทาน');
INSERT INTO orders VALUES (8, 4, '2025-01-05', 'นั่งทาน');
INSERT INTO orders VALUES (9, 8, '2025-10-13', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (10, 3, '2025-06-28', 'นั่งทาน');
INSERT INTO orders VALUES (11, 8, '2025-10-14', 'เดลิเวอรี');
INSERT INTO orders VALUES (12, 2, '2025-03-02', 'เดลิเวอรี');
INSERT INTO orders VALUES (13, 7, '2025-07-04', 'นั่งทาน');
INSERT INTO orders VALUES (14, 3, '2025-07-19', 'เดลิเวอรี');
INSERT INTO orders VALUES (15, 2, '2025-03-10', 'เดลิเวอรี');
INSERT INTO orders VALUES (16, 6, '2025-02-12', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (17, 3, '2025-05-09', 'สั่งกลับบ้าน');
INSERT INTO orders VALUES (18, 7, '2025-10-05', 'นั่งทาน');
INSERT INTO orders VALUES (19, 4, '2025-09-25', 'สั่งกลับบ้าน');
INSERT INTO order_items VALUES (2, 9, 1);
INSERT INTO order_items VALUES (17, 5, 3);
INSERT INTO order_items VALUES (7, 5, 2);
INSERT INTO order_items VALUES (3, 9, 4);
INSERT INTO order_items VALUES (4, 4, 3);
INSERT INTO order_items VALUES (13, 7, 2);
INSERT INTO order_items VALUES (17, 3, 4);
INSERT INTO order_items VALUES (13, 4, 2);
INSERT INTO order_items VALUES (12, 7, 2);
INSERT INTO order_items VALUES (19, 8, 3);
INSERT INTO order_items VALUES (9, 11, 4);
INSERT INTO order_items VALUES (18, 6, 2);
INSERT INTO order_items VALUES (13, 9, 3);
INSERT INTO order_items VALUES (16, 10, 1);
INSERT INTO order_items VALUES (15, 9, 4);
INSERT INTO order_items VALUES (17, 8, 2);
INSERT INTO order_items VALUES (1, 1, 1);
INSERT INTO order_items VALUES (8, 1, 3);
INSERT INTO order_items VALUES (10, 11, 1);
INSERT INTO order_items VALUES (13, 10, 1);
INSERT INTO order_items VALUES (13, 7, 4);
INSERT INTO order_items VALUES (19, 11, 3);
INSERT INTO order_items VALUES (13, 1, 1);
INSERT INTO order_items VALUES (15, 8, 4);
INSERT INTO order_items VALUES (5, 8, 3);
INSERT INTO order_items VALUES (13, 3, 4);
INSERT INTO order_items VALUES (18, 6, 4);
INSERT INTO order_items VALUES (6, 11, 2);
INSERT INTO order_items VALUES (10, 3, 3);
INSERT INTO order_items VALUES (15, 1, 2);
INSERT INTO order_items VALUES (18, 2, 1);
INSERT INTO order_items VALUES (15, 4, 3);
INSERT INTO order_items VALUES (14, 11, 3);
INSERT INTO order_items VALUES (7, 10, 2);
INSERT INTO order_items VALUES (4, 11, 1);
INSERT INTO order_items VALUES (15, 9, 2);
INSERT INTO order_items VALUES (14, 1, 4);
INSERT INTO order_items VALUES (14, 9, 1);
INSERT INTO order_items VALUES (6, 3, 3);
INSERT INTO order_items VALUES (10, 7, 1);

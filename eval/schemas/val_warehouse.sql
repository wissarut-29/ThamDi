CREATE TABLE warehouses (
    warehouse_id INTEGER PRIMARY KEY,
    name         VARCHAR NOT NULL,
    city         VARCHAR NOT NULL
);

CREATE TABLE items (
    item_id    INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    category   VARCHAR NOT NULL,
    unit_cost  DECIMAL(10, 2) NOT NULL
);

CREATE TABLE shipments (
    shipment_id   INTEGER PRIMARY KEY,
    warehouse_id  INTEGER NOT NULL REFERENCES warehouses (warehouse_id),
    shipment_date DATE NOT NULL,
    shipment_type VARCHAR NOT NULL
);

CREATE TABLE shipment_items (
    shipment_id INTEGER NOT NULL REFERENCES shipments (shipment_id),
    item_id     INTEGER NOT NULL REFERENCES items (item_id),
    quantity    INTEGER NOT NULL
);

-- data

INSERT INTO warehouses VALUES (1, 'คลัง1', 'กรุงเทพมหานคร');
INSERT INTO warehouses VALUES (2, 'คลัง2', 'สมุทรปราการ');
INSERT INTO warehouses VALUES (3, 'คลัง3', 'กรุงเทพมหานคร');
INSERT INTO warehouses VALUES (4, 'คลัง4', 'สมุทรปราการ');
INSERT INTO warehouses VALUES (5, 'คลัง5', 'กรุงเทพมหานคร');
INSERT INTO items VALUES (1, 'สินค้า1', 'เครื่องใช้ไฟฟ้า', 743.44);
INSERT INTO items VALUES (2, 'สินค้า2', 'อิเล็กทรอนิกส์', 909.83);
INSERT INTO items VALUES (3, 'สินค้า3', 'อิเล็กทรอนิกส์', 571.64);
INSERT INTO items VALUES (4, 'สินค้า4', 'วัสดุก่อสร้าง', 235.18);
INSERT INTO items VALUES (5, 'สินค้า5', 'เครื่องใช้ไฟฟ้า', 648.69);
INSERT INTO items VALUES (6, 'สินค้า6', 'วัสดุก่อสร้าง', 955.62);
INSERT INTO items VALUES (7, 'สินค้า7', 'อิเล็กทรอนิกส์', 681.62);
INSERT INTO items VALUES (8, 'สินค้า8', 'วัสดุก่อสร้าง', 591.98);
INSERT INTO items VALUES (9, 'สินค้า9', 'เครื่องใช้ไฟฟ้า', 840.47);
INSERT INTO items VALUES (10, 'สินค้า10', 'วัสดุก่อสร้าง', 134.51);
INSERT INTO items VALUES (11, 'สินค้า11', 'อิเล็กทรอนิกส์', 160.41);
INSERT INTO shipments VALUES (1, 1, '2025-12-26', 'รับเข้า');
INSERT INTO shipments VALUES (2, 1, '2025-02-08', 'จ่ายออก');
INSERT INTO shipments VALUES (3, 2, '2025-06-13', 'รับเข้า');
INSERT INTO shipments VALUES (4, 3, '2025-04-07', 'จ่ายออก');
INSERT INTO shipments VALUES (5, 2, '2025-02-14', 'จ่ายออก');
INSERT INTO shipments VALUES (6, 4, '2025-05-17', 'รับเข้า');
INSERT INTO shipments VALUES (7, 4, '2025-06-14', 'จ่ายออก');
INSERT INTO shipments VALUES (8, 4, '2025-07-18', 'รับเข้า');
INSERT INTO shipments VALUES (9, 3, '2025-01-27', 'จ่ายออก');
INSERT INTO shipments VALUES (10, 1, '2025-05-18', 'รับเข้า');
INSERT INTO shipments VALUES (11, 1, '2025-08-12', 'รับเข้า');
INSERT INTO shipments VALUES (12, 2, '2025-06-17', 'รับเข้า');
INSERT INTO shipments VALUES (13, 4, '2025-02-08', 'รับเข้า');
INSERT INTO shipments VALUES (14, 1, '2025-10-04', 'จ่ายออก');
INSERT INTO shipments VALUES (15, 5, '2025-01-28', 'รับเข้า');
INSERT INTO shipments VALUES (16, 1, '2025-12-03', 'จ่ายออก');
INSERT INTO shipments VALUES (17, 5, '2025-06-02', 'จ่ายออก');
INSERT INTO shipments VALUES (18, 3, '2025-08-09', 'รับเข้า');
INSERT INTO shipments VALUES (19, 5, '2025-03-13', 'รับเข้า');
INSERT INTO shipment_items VALUES (19, 9, 86);
INSERT INTO shipment_items VALUES (12, 10, 83);
INSERT INTO shipment_items VALUES (8, 6, 48);
INSERT INTO shipment_items VALUES (19, 2, 36);
INSERT INTO shipment_items VALUES (9, 7, 98);
INSERT INTO shipment_items VALUES (16, 9, 50);
INSERT INTO shipment_items VALUES (8, 4, 75);
INSERT INTO shipment_items VALUES (16, 11, 28);
INSERT INTO shipment_items VALUES (13, 5, 22);
INSERT INTO shipment_items VALUES (16, 11, 25);
INSERT INTO shipment_items VALUES (7, 1, 83);
INSERT INTO shipment_items VALUES (3, 10, 47);
INSERT INTO shipment_items VALUES (9, 7, 26);
INSERT INTO shipment_items VALUES (18, 3, 43);
INSERT INTO shipment_items VALUES (19, 9, 78);
INSERT INTO shipment_items VALUES (8, 11, 10);
INSERT INTO shipment_items VALUES (2, 4, 7);
INSERT INTO shipment_items VALUES (2, 11, 3);
INSERT INTO shipment_items VALUES (2, 11, 15);
INSERT INTO shipment_items VALUES (6, 2, 5);
INSERT INTO shipment_items VALUES (8, 4, 20);
INSERT INTO shipment_items VALUES (11, 3, 36);
INSERT INTO shipment_items VALUES (17, 8, 94);
INSERT INTO shipment_items VALUES (8, 5, 60);
INSERT INTO shipment_items VALUES (9, 4, 88);
INSERT INTO shipment_items VALUES (10, 11, 82);
INSERT INTO shipment_items VALUES (18, 6, 96);
INSERT INTO shipment_items VALUES (13, 8, 61);
INSERT INTO shipment_items VALUES (19, 11, 70);
INSERT INTO shipment_items VALUES (4, 6, 83);
INSERT INTO shipment_items VALUES (12, 2, 21);
INSERT INTO shipment_items VALUES (19, 4, 15);
INSERT INTO shipment_items VALUES (15, 11, 83);
INSERT INTO shipment_items VALUES (17, 2, 35);
INSERT INTO shipment_items VALUES (12, 1, 56);
INSERT INTO shipment_items VALUES (14, 7, 35);
INSERT INTO shipment_items VALUES (11, 9, 78);
INSERT INTO shipment_items VALUES (9, 9, 63);
INSERT INTO shipment_items VALUES (6, 2, 97);
INSERT INTO shipment_items VALUES (16, 3, 49);

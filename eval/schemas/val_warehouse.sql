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

INSERT INTO warehouses VALUES (1, 'คลัง1', 'สมุทรปราการ');
INSERT INTO warehouses VALUES (2, 'คลัง2', 'สมุทรปราการ');
INSERT INTO warehouses VALUES (3, 'คลัง3', 'กรุงเทพมหานคร');
INSERT INTO warehouses VALUES (4, 'คลัง4', 'สมุทรปราการ');
INSERT INTO warehouses VALUES (5, 'คลัง5', 'สมุทรปราการ');
INSERT INTO items VALUES (1, 'สินค้า1', 'วัสดุก่อสร้าง', 821.56);
INSERT INTO items VALUES (2, 'สินค้า2', 'อิเล็กทรอนิกส์', 602.38);
INSERT INTO items VALUES (3, 'สินค้า3', 'เครื่องใช้ไฟฟ้า', 248.81);
INSERT INTO items VALUES (4, 'สินค้า4', 'อิเล็กทรอนิกส์', 524.24);
INSERT INTO items VALUES (5, 'สินค้า5', 'เครื่องใช้ไฟฟ้า', 581.49);
INSERT INTO items VALUES (6, 'สินค้า6', 'เครื่องใช้ไฟฟ้า', 324.19);
INSERT INTO items VALUES (7, 'สินค้า7', 'อิเล็กทรอนิกส์', 865.71);
INSERT INTO items VALUES (8, 'สินค้า8', 'วัสดุก่อสร้าง', 796.74);
INSERT INTO items VALUES (9, 'สินค้า9', 'วัสดุก่อสร้าง', 236.06);
INSERT INTO items VALUES (10, 'สินค้า10', 'วัสดุก่อสร้าง', 635.24);
INSERT INTO items VALUES (11, 'สินค้า11', 'วัสดุก่อสร้าง', 278.52);
INSERT INTO shipments VALUES (1, 4, '2025-01-11', 'จ่ายออก');
INSERT INTO shipments VALUES (2, 3, '2025-06-12', 'จ่ายออก');
INSERT INTO shipments VALUES (3, 3, '2025-03-18', 'รับเข้า');
INSERT INTO shipments VALUES (4, 3, '2025-06-20', 'จ่ายออก');
INSERT INTO shipments VALUES (5, 3, '2025-04-21', 'จ่ายออก');
INSERT INTO shipments VALUES (6, 4, '2025-02-26', 'จ่ายออก');
INSERT INTO shipments VALUES (7, 1, '2025-07-03', 'รับเข้า');
INSERT INTO shipments VALUES (8, 3, '2025-08-28', 'จ่ายออก');
INSERT INTO shipments VALUES (9, 5, '2025-06-11', 'จ่ายออก');
INSERT INTO shipments VALUES (10, 1, '2025-02-24', 'จ่ายออก');
INSERT INTO shipments VALUES (11, 2, '2025-12-23', 'รับเข้า');
INSERT INTO shipments VALUES (12, 2, '2025-01-09', 'รับเข้า');
INSERT INTO shipments VALUES (13, 1, '2025-03-08', 'จ่ายออก');
INSERT INTO shipments VALUES (14, 5, '2025-10-19', 'จ่ายออก');
INSERT INTO shipments VALUES (15, 1, '2025-11-06', 'รับเข้า');
INSERT INTO shipments VALUES (16, 1, '2025-01-09', 'รับเข้า');
INSERT INTO shipments VALUES (17, 4, '2025-11-18', 'จ่ายออก');
INSERT INTO shipments VALUES (18, 5, '2025-08-06', 'จ่ายออก');
INSERT INTO shipments VALUES (19, 4, '2025-02-26', 'จ่ายออก');
INSERT INTO shipment_items VALUES (13, 9, 79);
INSERT INTO shipment_items VALUES (9, 10, 96);
INSERT INTO shipment_items VALUES (18, 1, 73);
INSERT INTO shipment_items VALUES (12, 3, 79);
INSERT INTO shipment_items VALUES (12, 1, 27);
INSERT INTO shipment_items VALUES (8, 4, 79);
INSERT INTO shipment_items VALUES (3, 8, 49);
INSERT INTO shipment_items VALUES (3, 4, 61);
INSERT INTO shipment_items VALUES (14, 2, 20);
INSERT INTO shipment_items VALUES (3, 7, 33);
INSERT INTO shipment_items VALUES (7, 1, 59);
INSERT INTO shipment_items VALUES (3, 5, 14);
INSERT INTO shipment_items VALUES (14, 3, 2);
INSERT INTO shipment_items VALUES (7, 10, 95);
INSERT INTO shipment_items VALUES (8, 10, 75);
INSERT INTO shipment_items VALUES (4, 2, 48);
INSERT INTO shipment_items VALUES (11, 10, 76);
INSERT INTO shipment_items VALUES (19, 4, 20);
INSERT INTO shipment_items VALUES (1, 2, 81);
INSERT INTO shipment_items VALUES (15, 3, 30);
INSERT INTO shipment_items VALUES (9, 9, 85);
INSERT INTO shipment_items VALUES (10, 4, 95);
INSERT INTO shipment_items VALUES (19, 6, 18);
INSERT INTO shipment_items VALUES (13, 9, 96);
INSERT INTO shipment_items VALUES (17, 5, 86);
INSERT INTO shipment_items VALUES (4, 6, 23);
INSERT INTO shipment_items VALUES (12, 2, 16);
INSERT INTO shipment_items VALUES (12, 9, 37);
INSERT INTO shipment_items VALUES (8, 8, 12);
INSERT INTO shipment_items VALUES (17, 11, 91);
INSERT INTO shipment_items VALUES (2, 2, 50);
INSERT INTO shipment_items VALUES (15, 9, 82);
INSERT INTO shipment_items VALUES (1, 1, 77);
INSERT INTO shipment_items VALUES (18, 4, 93);
INSERT INTO shipment_items VALUES (4, 10, 34);
INSERT INTO shipment_items VALUES (16, 6, 68);
INSERT INTO shipment_items VALUES (16, 9, 59);
INSERT INTO shipment_items VALUES (12, 2, 34);
INSERT INTO shipment_items VALUES (5, 2, 73);
INSERT INTO shipment_items VALUES (18, 4, 68);

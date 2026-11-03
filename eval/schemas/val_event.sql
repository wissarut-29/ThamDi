CREATE TABLE events (
    event_id   INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    city       VARCHAR NOT NULL,
    event_date DATE NOT NULL
);

CREATE TABLE tickets (
    ticket_id      INTEGER PRIMARY KEY,
    event_id       INTEGER NOT NULL REFERENCES events (event_id),
    ticket_type    VARCHAR NOT NULL,
    price          DECIMAL(10, 2) NOT NULL,
    purchase_date  DATE NOT NULL
);

-- data

INSERT INTO events VALUES (1, 'งานอีเวนต์1', 'กรุงเทพมหานคร', '2025-12-25');
INSERT INTO events VALUES (2, 'งานอีเวนต์2', 'ภูเก็ต', '2025-03-24');
INSERT INTO events VALUES (3, 'งานอีเวนต์3', 'เชียงใหม่', '2025-08-28');
INSERT INTO events VALUES (4, 'งานอีเวนต์4', 'ภูเก็ต', '2025-10-02');
INSERT INTO events VALUES (5, 'งานอีเวนต์5', 'ภูเก็ต', '2025-06-19');
INSERT INTO events VALUES (6, 'งานอีเวนต์6', 'กรุงเทพมหานคร', '2025-04-20');
INSERT INTO events VALUES (7, 'งานอีเวนต์7', 'กรุงเทพมหานคร', '2025-05-16');
INSERT INTO tickets VALUES (1, 4, 'ทั่วไป', 519.89, '2025-03-11');
INSERT INTO tickets VALUES (2, 2, 'VIP', 283.81, '2025-12-20');
INSERT INTO tickets VALUES (3, 4, 'ทั่วไป', 1607.71, '2025-01-16');
INSERT INTO tickets VALUES (4, 4, 'VIP', 399.43, '2025-11-09');
INSERT INTO tickets VALUES (5, 6, 'นักเรียน', 1053.15, '2025-11-26');
INSERT INTO tickets VALUES (6, 7, 'ทั่วไป', 739.54, '2025-06-19');
INSERT INTO tickets VALUES (7, 5, 'ทั่วไป', 2677.25, '2025-04-02');
INSERT INTO tickets VALUES (8, 4, 'VIP', 1737.4, '2025-02-18');
INSERT INTO tickets VALUES (9, 6, 'ทั่วไป', 1781.11, '2025-11-02');
INSERT INTO tickets VALUES (10, 1, 'ทั่วไป', 1841.35, '2025-01-01');
INSERT INTO tickets VALUES (11, 5, 'VIP', 468.79, '2025-06-27');
INSERT INTO tickets VALUES (12, 1, 'VIP', 2660.67, '2025-04-02');
INSERT INTO tickets VALUES (13, 7, 'VIP', 1798.98, '2025-07-21');
INSERT INTO tickets VALUES (14, 1, 'VIP', 2970.79, '2025-12-04');
INSERT INTO tickets VALUES (15, 3, 'ทั่วไป', 1275.82, '2025-04-13');
INSERT INTO tickets VALUES (16, 1, 'ทั่วไป', 728.1, '2025-02-07');
INSERT INTO tickets VALUES (17, 3, 'ทั่วไป', 496.38, '2025-04-28');
INSERT INTO tickets VALUES (18, 3, 'นักเรียน', 2490.74, '2025-02-01');
INSERT INTO tickets VALUES (19, 7, 'ทั่วไป', 1223.11, '2025-05-14');
INSERT INTO tickets VALUES (20, 4, 'ทั่วไป', 1860.09, '2025-04-11');
INSERT INTO tickets VALUES (21, 5, 'VIP', 2400.94, '2025-11-22');
INSERT INTO tickets VALUES (22, 4, 'นักเรียน', 1857.47, '2025-10-20');
INSERT INTO tickets VALUES (23, 6, 'ทั่วไป', 2842.83, '2025-05-26');
INSERT INTO tickets VALUES (24, 1, 'VIP', 1301.04, '2025-03-04');
INSERT INTO tickets VALUES (25, 3, 'นักเรียน', 2508.46, '2025-01-10');
INSERT INTO tickets VALUES (26, 4, 'VIP', 2892.02, '2025-08-02');
INSERT INTO tickets VALUES (27, 3, 'VIP', 2610.67, '2025-07-07');
INSERT INTO tickets VALUES (28, 2, 'นักเรียน', 2780.96, '2025-11-01');
INSERT INTO tickets VALUES (29, 6, 'VIP', 740.14, '2025-07-10');

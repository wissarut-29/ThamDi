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

INSERT INTO events VALUES (1, 'งานอีเวนต์1', 'ภูเก็ต', '2025-03-05');
INSERT INTO events VALUES (2, 'งานอีเวนต์2', 'กรุงเทพมหานคร', '2025-12-15');
INSERT INTO events VALUES (3, 'งานอีเวนต์3', 'เชียงใหม่', '2025-11-08');
INSERT INTO events VALUES (4, 'งานอีเวนต์4', 'ภูเก็ต', '2025-05-02');
INSERT INTO events VALUES (5, 'งานอีเวนต์5', 'ภูเก็ต', '2025-01-04');
INSERT INTO events VALUES (6, 'งานอีเวนต์6', 'กรุงเทพมหานคร', '2025-02-09');
INSERT INTO events VALUES (7, 'งานอีเวนต์7', 'เชียงใหม่', '2025-04-18');
INSERT INTO tickets VALUES (1, 3, 'ทั่วไป', 2870.77, '2025-08-22');
INSERT INTO tickets VALUES (2, 6, 'นักเรียน', 2604.29, '2025-02-22');
INSERT INTO tickets VALUES (3, 6, 'VIP', 827.47, '2025-03-02');
INSERT INTO tickets VALUES (4, 5, 'ทั่วไป', 2185.1, '2025-06-12');
INSERT INTO tickets VALUES (5, 7, 'นักเรียน', 1714.26, '2025-09-06');
INSERT INTO tickets VALUES (6, 4, 'VIP', 519.17, '2025-03-02');
INSERT INTO tickets VALUES (7, 5, 'VIP', 2614.14, '2025-07-26');
INSERT INTO tickets VALUES (8, 7, 'ทั่วไป', 2418.52, '2025-12-05');
INSERT INTO tickets VALUES (9, 1, 'VIP', 1817.34, '2025-06-20');
INSERT INTO tickets VALUES (10, 1, 'นักเรียน', 2236.59, '2025-11-17');
INSERT INTO tickets VALUES (11, 1, 'VIP', 2596.51, '2025-12-21');
INSERT INTO tickets VALUES (12, 7, 'นักเรียน', 942.08, '2025-03-09');
INSERT INTO tickets VALUES (13, 2, 'VIP', 1803.0, '2025-02-25');
INSERT INTO tickets VALUES (14, 6, 'ทั่วไป', 1796.92, '2025-12-13');
INSERT INTO tickets VALUES (15, 6, 'ทั่วไป', 510.76, '2025-10-03');
INSERT INTO tickets VALUES (16, 6, 'ทั่วไป', 1256.33, '2025-05-03');
INSERT INTO tickets VALUES (17, 6, 'ทั่วไป', 523.79, '2025-10-12');
INSERT INTO tickets VALUES (18, 4, 'ทั่วไป', 1802.86, '2025-04-16');
INSERT INTO tickets VALUES (19, 6, 'ทั่วไป', 1363.03, '2025-04-28');
INSERT INTO tickets VALUES (20, 3, 'นักเรียน', 867.0, '2025-12-27');
INSERT INTO tickets VALUES (21, 3, 'VIP', 1088.46, '2025-12-13');
INSERT INTO tickets VALUES (22, 1, 'VIP', 1158.89, '2025-04-22');
INSERT INTO tickets VALUES (23, 3, 'VIP', 2918.12, '2025-09-16');
INSERT INTO tickets VALUES (24, 2, 'นักเรียน', 1106.37, '2025-01-16');
INSERT INTO tickets VALUES (25, 1, 'นักเรียน', 1052.27, '2025-04-12');
INSERT INTO tickets VALUES (26, 2, 'นักเรียน', 1016.48, '2025-03-16');
INSERT INTO tickets VALUES (27, 5, 'ทั่วไป', 493.45, '2025-05-15');
INSERT INTO tickets VALUES (28, 4, 'ทั่วไป', 598.66, '2025-11-23');
INSERT INTO tickets VALUES (29, 6, 'นักเรียน', 1157.12, '2025-02-10');

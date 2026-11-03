CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    location      VARCHAR NOT NULL
);

CREATE TABLE employees (
    employee_id   INTEGER PRIMARY KEY,
    name          VARCHAR NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments (department_id),
    position      VARCHAR NOT NULL,
    hire_date     DATE NOT NULL,
    salary        DECIMAL(10, 2) NOT NULL
);

-- data

INSERT INTO departments VALUES (1, 'แผนก1', 'กรุงเทพมหานคร');
INSERT INTO departments VALUES (2, 'แผนก2', 'เชียงใหม่');
INSERT INTO departments VALUES (3, 'แผนก3', 'กรุงเทพมหานคร');
INSERT INTO departments VALUES (4, 'แผนก4', 'กรุงเทพมหานคร');
INSERT INTO departments VALUES (5, 'แผนก5', 'ขอนแก่น');
INSERT INTO employees VALUES (1, 'พนักงาน1', 2, 'ฝ่ายขาย', '2025-01-23', 63877.59);
INSERT INTO employees VALUES (2, 'พนักงาน2', 4, 'ฝ่ายขาย', '2021-05-18', 74995.61);
INSERT INTO employees VALUES (3, 'พนักงาน3', 4, 'วิศวกร', '2024-02-28', 48562.18);
INSERT INTO employees VALUES (4, 'พนักงาน4', 2, 'วิศวกร', '2023-05-27', 68154.42);
INSERT INTO employees VALUES (5, 'พนักงาน5', 2, 'นักบัญชี', '2024-12-21', 18005.51);
INSERT INTO employees VALUES (6, 'พนักงาน6', 4, 'วิศวกร', '2023-12-22', 41490.78);
INSERT INTO employees VALUES (7, 'พนักงาน7', 1, 'นักบัญชี', '2022-04-12', 48899.9);
INSERT INTO employees VALUES (8, 'พนักงาน8', 2, 'วิศวกร', '2023-05-14', 19727.88);
INSERT INTO employees VALUES (9, 'พนักงาน9', 2, 'ฝ่ายบุคคล', '2022-06-08', 68912.75);
INSERT INTO employees VALUES (10, 'พนักงาน10', 2, 'ฝ่ายขาย', '2023-04-18', 43427.77);
INSERT INTO employees VALUES (11, 'พนักงาน11', 5, 'ฝ่ายขาย', '2021-02-13', 72016.98);
INSERT INTO employees VALUES (12, 'พนักงาน12', 1, 'ฝ่ายบุคคล', '2025-02-10', 62234.04);
INSERT INTO employees VALUES (13, 'พนักงาน13', 1, 'ฝ่ายขาย', '2021-01-16', 63522.94);
INSERT INTO employees VALUES (14, 'พนักงาน14', 2, 'วิศวกร', '2025-06-21', 85725.58);
INSERT INTO employees VALUES (15, 'พนักงาน15', 2, 'นักบัญชี', '2023-02-11', 33834.16);
INSERT INTO employees VALUES (16, 'พนักงาน16', 1, 'ฝ่ายขาย', '2021-08-19', 71617.01);
INSERT INTO employees VALUES (17, 'พนักงาน17', 1, 'วิศวกร', '2022-05-23', 41519.61);
INSERT INTO employees VALUES (18, 'พนักงาน18', 5, 'ฝ่ายขาย', '2021-09-06', 81231.96);
INSERT INTO employees VALUES (19, 'พนักงาน19', 2, 'นักบัญชี', '2023-12-04', 35804.52);
INSERT INTO employees VALUES (20, 'พนักงาน20', 4, 'นักบัญชี', '2021-12-15', 19795.37);
INSERT INTO employees VALUES (21, 'พนักงาน21', 5, 'นักบัญชี', '2022-07-20', 37426.57);
INSERT INTO employees VALUES (22, 'พนักงาน22', 3, 'ฝ่ายขาย', '2024-03-26', 85781.21);
INSERT INTO employees VALUES (23, 'พนักงาน23', 4, 'ฝ่ายบุคคล', '2025-01-20', 52191.78);
INSERT INTO employees VALUES (24, 'พนักงาน24', 2, 'นักบัญชี', '2020-09-06', 82705.86);
INSERT INTO employees VALUES (25, 'พนักงาน25', 1, 'นักบัญชี', '2020-08-10', 70842.79);
INSERT INTO employees VALUES (26, 'พนักงาน26', 4, 'ฝ่ายบุคคล', '2022-07-06', 52851.85);
INSERT INTO employees VALUES (27, 'พนักงาน27', 1, 'วิศวกร', '2020-03-17', 88368.61);
INSERT INTO employees VALUES (28, 'พนักงาน28', 1, 'ฝ่ายบุคคล', '2023-02-10', 60719.23);
INSERT INTO employees VALUES (29, 'พนักงาน29', 3, 'วิศวกร', '2025-07-05', 69866.26);

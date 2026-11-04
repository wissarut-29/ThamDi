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

INSERT INTO departments VALUES (1, 'แผนก1', 'ขอนแก่น');
INSERT INTO departments VALUES (2, 'แผนก2', 'เชียงใหม่');
INSERT INTO departments VALUES (3, 'แผนก3', 'กรุงเทพมหานคร');
INSERT INTO departments VALUES (4, 'แผนก4', 'เชียงใหม่');
INSERT INTO departments VALUES (5, 'แผนก5', 'กรุงเทพมหานคร');
INSERT INTO employees VALUES (1, 'พนักงาน1', 4, 'ฝ่ายขาย', '2024-01-14', 29329.62);
INSERT INTO employees VALUES (2, 'พนักงาน2', 5, 'วิศวกร', '2020-07-24', 35031.57);
INSERT INTO employees VALUES (3, 'พนักงาน3', 2, 'ฝ่ายบุคคล', '2022-09-15', 57784.85);
INSERT INTO employees VALUES (4, 'พนักงาน4', 4, 'ฝ่ายบุคคล', '2022-07-20', 42971.47);
INSERT INTO employees VALUES (5, 'พนักงาน5', 1, 'ฝ่ายบุคคล', '2024-11-07', 88493.61);
INSERT INTO employees VALUES (6, 'พนักงาน6', 3, 'นักบัญชี', '2020-04-04', 21461.95);
INSERT INTO employees VALUES (7, 'พนักงาน7', 2, 'นักบัญชี', '2020-11-01', 64822.12);
INSERT INTO employees VALUES (8, 'พนักงาน8', 3, 'นักบัญชี', '2021-05-01', 70452.96);
INSERT INTO employees VALUES (9, 'พนักงาน9', 5, 'นักบัญชี', '2021-08-04', 41692.99);
INSERT INTO employees VALUES (10, 'พนักงาน10', 5, 'ฝ่ายบุคคล', '2021-06-03', 18853.33);
INSERT INTO employees VALUES (11, 'พนักงาน11', 3, 'ฝ่ายบุคคล', '2021-10-14', 54286.83);
INSERT INTO employees VALUES (12, 'พนักงาน12', 1, 'ฝ่ายบุคคล', '2023-08-23', 89928.81);
INSERT INTO employees VALUES (13, 'พนักงาน13', 4, 'ฝ่ายบุคคล', '2021-03-13', 69591.16);
INSERT INTO employees VALUES (14, 'พนักงาน14', 2, 'นักบัญชี', '2024-11-23', 35429.67);
INSERT INTO employees VALUES (15, 'พนักงาน15', 1, 'นักบัญชี', '2020-04-09', 24324.81);
INSERT INTO employees VALUES (16, 'พนักงาน16', 3, 'ฝ่ายบุคคล', '2021-10-13', 48634.45);
INSERT INTO employees VALUES (17, 'พนักงาน17', 1, 'ฝ่ายบุคคล', '2023-02-02', 50438.71);
INSERT INTO employees VALUES (18, 'พนักงาน18', 5, 'ฝ่ายบุคคล', '2023-05-04', 82675.92);
INSERT INTO employees VALUES (19, 'พนักงาน19', 5, 'ฝ่ายขาย', '2023-07-24', 89681.86);
INSERT INTO employees VALUES (20, 'พนักงาน20', 3, 'นักบัญชี', '2020-05-20', 66411.1);
INSERT INTO employees VALUES (21, 'พนักงาน21', 3, 'วิศวกร', '2022-05-15', 37115.23);
INSERT INTO employees VALUES (22, 'พนักงาน22', 2, 'ฝ่ายบุคคล', '2020-01-11', 22090.17);
INSERT INTO employees VALUES (23, 'พนักงาน23', 5, 'นักบัญชี', '2020-01-11', 85656.15);
INSERT INTO employees VALUES (24, 'พนักงาน24', 1, 'ฝ่ายขาย', '2022-03-21', 22946.98);
INSERT INTO employees VALUES (25, 'พนักงาน25', 2, 'ฝ่ายขาย', '2022-01-06', 59150.43);
INSERT INTO employees VALUES (26, 'พนักงาน26', 4, 'นักบัญชี', '2023-02-15', 19984.99);
INSERT INTO employees VALUES (27, 'พนักงาน27', 2, 'นักบัญชี', '2021-04-09', 28048.21);
INSERT INTO employees VALUES (28, 'พนักงาน28', 1, 'วิศวกร', '2021-04-06', 29962.48);
INSERT INTO employees VALUES (29, 'พนักงาน29', 3, 'ฝ่ายบุคคล', '2020-11-22', 62689.0);

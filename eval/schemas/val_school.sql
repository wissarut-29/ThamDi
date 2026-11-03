CREATE TABLE teachers (
    teacher_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    subject    VARCHAR NOT NULL
);

CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name       VARCHAR NOT NULL,
    grade_level VARCHAR NOT NULL
);

CREATE TABLE enrollments (
    enrollment_id INTEGER PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students (student_id),
    teacher_id    INTEGER NOT NULL REFERENCES teachers (teacher_id),
    enroll_date   DATE NOT NULL,
    score         DECIMAL(5, 1) NOT NULL
);

-- data

INSERT INTO teachers VALUES (1, 'ครู1', 'คณิตศาสตร์');
INSERT INTO teachers VALUES (2, 'ครู2', 'คณิตศาสตร์');
INSERT INTO teachers VALUES (3, 'ครู3', 'ภาษาไทย');
INSERT INTO teachers VALUES (4, 'ครู4', 'ภาษาไทย');
INSERT INTO teachers VALUES (5, 'ครู5', 'ภาษาไทย');
INSERT INTO teachers VALUES (6, 'ครู6', 'ภาษาอังกฤษ');
INSERT INTO students VALUES (1, 'นักเรียน1', 'ม.2');
INSERT INTO students VALUES (2, 'นักเรียน2', 'ป.4');
INSERT INTO students VALUES (3, 'นักเรียน3', 'ม.2');
INSERT INTO students VALUES (4, 'นักเรียน4', 'ม.1');
INSERT INTO students VALUES (5, 'นักเรียน5', 'ป.5');
INSERT INTO students VALUES (6, 'นักเรียน6', 'ม.2');
INSERT INTO students VALUES (7, 'นักเรียน7', 'ป.4');
INSERT INTO students VALUES (8, 'นักเรียน8', 'ป.4');
INSERT INTO students VALUES (9, 'นักเรียน9', 'ม.2');
INSERT INTO students VALUES (10, 'นักเรียน10', 'ม.1');
INSERT INTO students VALUES (11, 'นักเรียน11', 'ม.1');
INSERT INTO students VALUES (12, 'นักเรียน12', 'ม.2');
INSERT INTO students VALUES (13, 'นักเรียน13', 'ม.2');
INSERT INTO students VALUES (14, 'นักเรียน14', 'ป.4');
INSERT INTO students VALUES (15, 'นักเรียน15', 'ม.1');
INSERT INTO students VALUES (16, 'นักเรียน16', 'ป.6');
INSERT INTO students VALUES (17, 'นักเรียน17', 'ป.5');
INSERT INTO students VALUES (18, 'นักเรียน18', 'ป.6');
INSERT INTO students VALUES (19, 'นักเรียน19', 'ป.4');
INSERT INTO students VALUES (20, 'นักเรียน20', 'ป.5');
INSERT INTO students VALUES (21, 'นักเรียน21', 'ม.1');
INSERT INTO students VALUES (22, 'นักเรียน22', 'ม.2');
INSERT INTO students VALUES (23, 'นักเรียน23', 'ม.2');
INSERT INTO students VALUES (24, 'นักเรียน24', 'ป.6');
INSERT INTO enrollments VALUES (1, 24, 3, '2025-02-11', 81.6);
INSERT INTO enrollments VALUES (2, 17, 2, '2025-06-12', 92.0);
INSERT INTO enrollments VALUES (3, 16, 5, '2025-08-06', 64.9);
INSERT INTO enrollments VALUES (4, 18, 1, '2025-09-16', 55.1);
INSERT INTO enrollments VALUES (5, 6, 4, '2025-11-05', 93.9);
INSERT INTO enrollments VALUES (6, 2, 4, '2025-01-01', 50.6);
INSERT INTO enrollments VALUES (7, 10, 6, '2025-11-15', 42.0);
INSERT INTO enrollments VALUES (8, 20, 1, '2025-05-19', 86.9);
INSERT INTO enrollments VALUES (9, 20, 3, '2025-01-28', 97.1);
INSERT INTO enrollments VALUES (10, 22, 1, '2025-04-24', 75.8);
INSERT INTO enrollments VALUES (11, 4, 2, '2025-10-07', 73.3);
INSERT INTO enrollments VALUES (12, 21, 2, '2025-05-06', 78.0);
INSERT INTO enrollments VALUES (13, 4, 3, '2025-01-15', 56.5);
INSERT INTO enrollments VALUES (14, 18, 5, '2025-09-03', 64.0);
INSERT INTO enrollments VALUES (15, 16, 3, '2025-07-02', 73.4);
INSERT INTO enrollments VALUES (16, 18, 3, '2025-01-06', 40.2);
INSERT INTO enrollments VALUES (17, 4, 5, '2025-07-25', 42.5);
INSERT INTO enrollments VALUES (18, 11, 5, '2025-11-02', 74.3);
INSERT INTO enrollments VALUES (19, 14, 2, '2025-04-21', 54.9);
INSERT INTO enrollments VALUES (20, 11, 2, '2025-07-27', 76.5);
INSERT INTO enrollments VALUES (21, 20, 2, '2025-04-17', 97.1);
INSERT INTO enrollments VALUES (22, 11, 4, '2025-10-13', 89.6);
INSERT INTO enrollments VALUES (23, 5, 6, '2025-09-27', 59.8);
INSERT INTO enrollments VALUES (24, 19, 6, '2025-12-25', 92.9);
INSERT INTO enrollments VALUES (25, 21, 5, '2025-05-13', 74.2);
INSERT INTO enrollments VALUES (26, 13, 6, '2025-10-05', 74.8);
INSERT INTO enrollments VALUES (27, 7, 5, '2025-09-06', 43.9);
INSERT INTO enrollments VALUES (28, 10, 4, '2025-05-24', 95.9);
INSERT INTO enrollments VALUES (29, 23, 6, '2025-02-04', 43.8);

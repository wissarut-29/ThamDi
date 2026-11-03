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

INSERT INTO teachers VALUES (1, 'ครู1', 'ภาษาไทย');
INSERT INTO teachers VALUES (2, 'ครู2', 'วิทยาศาสตร์');
INSERT INTO teachers VALUES (3, 'ครู3', 'ภาษาไทย');
INSERT INTO teachers VALUES (4, 'ครู4', 'ภาษาไทย');
INSERT INTO teachers VALUES (5, 'ครู5', 'คณิตศาสตร์');
INSERT INTO teachers VALUES (6, 'ครู6', 'วิทยาศาสตร์');
INSERT INTO students VALUES (1, 'นักเรียน1', 'ม.2');
INSERT INTO students VALUES (2, 'นักเรียน2', 'ป.4');
INSERT INTO students VALUES (3, 'นักเรียน3', 'ม.2');
INSERT INTO students VALUES (4, 'นักเรียน4', 'ป.5');
INSERT INTO students VALUES (5, 'นักเรียน5', 'ป.5');
INSERT INTO students VALUES (6, 'นักเรียน6', 'ป.4');
INSERT INTO students VALUES (7, 'นักเรียน7', 'ม.2');
INSERT INTO students VALUES (8, 'นักเรียน8', 'ป.6');
INSERT INTO students VALUES (9, 'นักเรียน9', 'ม.1');
INSERT INTO students VALUES (10, 'นักเรียน10', 'ม.1');
INSERT INTO students VALUES (11, 'นักเรียน11', 'ป.4');
INSERT INTO students VALUES (12, 'นักเรียน12', 'ป.5');
INSERT INTO students VALUES (13, 'นักเรียน13', 'ป.6');
INSERT INTO students VALUES (14, 'นักเรียน14', 'ม.2');
INSERT INTO students VALUES (15, 'นักเรียน15', 'ป.4');
INSERT INTO students VALUES (16, 'นักเรียน16', 'ม.2');
INSERT INTO students VALUES (17, 'นักเรียน17', 'ม.1');
INSERT INTO students VALUES (18, 'นักเรียน18', 'ป.6');
INSERT INTO students VALUES (19, 'นักเรียน19', 'ป.6');
INSERT INTO students VALUES (20, 'นักเรียน20', 'ม.2');
INSERT INTO students VALUES (21, 'นักเรียน21', 'ม.1');
INSERT INTO students VALUES (22, 'นักเรียน22', 'ป.4');
INSERT INTO students VALUES (23, 'นักเรียน23', 'ม.1');
INSERT INTO students VALUES (24, 'นักเรียน24', 'ป.6');
INSERT INTO enrollments VALUES (1, 11, 1, '2025-01-06', 59.3);
INSERT INTO enrollments VALUES (2, 22, 4, '2025-01-21', 45.3);
INSERT INTO enrollments VALUES (3, 9, 5, '2025-03-05', 57.6);
INSERT INTO enrollments VALUES (4, 22, 1, '2025-11-21', 78.1);
INSERT INTO enrollments VALUES (5, 11, 2, '2025-01-17', 50.1);
INSERT INTO enrollments VALUES (6, 16, 3, '2025-06-20', 68.1);
INSERT INTO enrollments VALUES (7, 15, 1, '2025-04-28', 92.2);
INSERT INTO enrollments VALUES (8, 7, 1, '2025-10-05', 47.6);
INSERT INTO enrollments VALUES (9, 14, 3, '2025-10-27', 46.9);
INSERT INTO enrollments VALUES (10, 18, 1, '2025-11-11', 72.9);
INSERT INTO enrollments VALUES (11, 6, 6, '2025-01-15', 80.3);
INSERT INTO enrollments VALUES (12, 6, 2, '2025-10-15', 64.1);
INSERT INTO enrollments VALUES (13, 3, 3, '2025-08-04', 76.7);
INSERT INTO enrollments VALUES (14, 14, 5, '2025-07-09', 44.8);
INSERT INTO enrollments VALUES (15, 20, 3, '2025-11-07', 43.5);
INSERT INTO enrollments VALUES (16, 9, 5, '2025-01-02', 57.8);
INSERT INTO enrollments VALUES (17, 7, 1, '2025-02-05', 47.0);
INSERT INTO enrollments VALUES (18, 3, 5, '2025-04-19', 66.5);
INSERT INTO enrollments VALUES (19, 1, 3, '2025-09-10', 51.3);
INSERT INTO enrollments VALUES (20, 2, 3, '2025-09-05', 86.0);
INSERT INTO enrollments VALUES (21, 16, 1, '2025-09-08', 90.5);
INSERT INTO enrollments VALUES (22, 9, 4, '2025-05-19', 75.6);
INSERT INTO enrollments VALUES (23, 9, 5, '2025-07-05', 96.7);
INSERT INTO enrollments VALUES (24, 7, 5, '2025-12-03', 79.5);
INSERT INTO enrollments VALUES (25, 24, 1, '2025-02-13', 76.4);
INSERT INTO enrollments VALUES (26, 9, 6, '2025-01-21', 53.0);
INSERT INTO enrollments VALUES (27, 23, 1, '2025-01-22', 95.1);
INSERT INTO enrollments VALUES (28, 14, 4, '2025-08-18', 84.7);
INSERT INTO enrollments VALUES (29, 22, 5, '2025-09-24', 98.5);

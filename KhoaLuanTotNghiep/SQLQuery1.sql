create database HeThongCDTL

CREATE TABLE Admin (
    id_admin INT  PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(255) UNIQUE NOT NULL,
    password NVARCHAR(255) NOT NULL
);

CREATE TABLE Teacher (
    id_teacher INT PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(255) UNIQUE NOT NULL,
    password NVARCHAR(255) NOT NULL,
    subject NVARCHAR(100) NOT NULL
);

CREATE TABLE Student (
    id_student INT  PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(255) UNIQUE NOT NULL,
    password NVARCHAR(255) NOT NULL,
    class NVARCHAR(50) NOT NULL
);

CREATE TABLE Essay (
    id_essay INT  PRIMARY KEY,
    id_student INT NOT NULL,
    id_teacher INT NOT NULL,
    title NVARCHAR(255) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    submission_date DATETIME DEFAULT GETDATE(),
    status NVARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (id_student) REFERENCES Student(id_student) ,
    FOREIGN KEY (id_teacher) REFERENCES Teacher(id_teacher)
);

CREATE TABLE Grading (
    id_grading INT IDENTITY(1,1) PRIMARY KEY,
    id_essay INT NOT NULL,
    id_teacher INT NOT NULL,
    AI_score FLOAT CHECK (AI_score BETWEEN 0 AND 10),
    final_score FLOAT CHECK (final_score BETWEEN 0 AND 10),
    feedback NVARCHAR(MAX),
    grading_date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_essay) REFERENCES Essay(id_essay),
    FOREIGN KEY (id_teacher) REFERENCES Teacher(id_teacher) 
);

CREATE TABLE GradingCriteria (
    id_gradingCriteria INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    maxScore FLOAT CHECK (maxScore > 0),
    description NVARCHAR(MAX)
);

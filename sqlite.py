import sqlite3

## connect to sqlite database
connection = sqlite3.connect('student.db')

## create a cursor object to insert record ,create table
cursor = connection.cursor()

## create table
table_info="""
create table if not exists student(
    id integer primary key,
    name text,
    age integer,
    grade text
)
"""
cursor.execute(table_info)
## insert records
cursor.execute("insert into student(name,age,grade) values('Alice',20,'A')")
cursor.execute("insert into student(name,age,grade) values('Bob',22,'B')")
cursor.execute("insert into student(name,age,grade) values('Charlie',21,'A-')")
cursor.execute("insert into student(name,age,grade) values('David',23,'B+')")
cursor.execute("insert into student(name,age,grade) values('Eve',20,'A')")

## display all records
print("recorded students are:")
data = cursor.execute("select * from student")
for row in data:
    print(row)

## commit changes and close connection
connection.commit()
connection.close()
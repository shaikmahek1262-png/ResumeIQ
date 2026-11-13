import os
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="resumeiq"
)

cursor = db.cursor()

print("Connected to ResumeIQ database successfully!")

cursor.close()
db.close()
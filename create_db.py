import mysql.connector

# Connect to MySQL server
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port=3307    # <-- YOUR REAL PASSWORD
)

cursor = conn.cursor()

# 1. Create database
cursor.execute("CREATE DATABASE IF NOT EXISTS library_project")
print("Database created or already exists.")

# 2. Select database
cursor.execute("USE library_project")

# 3. Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100),
    status VARCHAR(20) DEFAULT 'available'
)
""")

print("Tables created or already exist.")

cursor.close()
conn.close()
print("Database setup complete.")

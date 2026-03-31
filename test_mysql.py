import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Manoj982134"   # <-- your password
    )
    print("Connected successfully!")
    conn.close()

except Exception as e:
    print("Error:", e)

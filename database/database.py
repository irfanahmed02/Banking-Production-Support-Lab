import psycopg2

try:

    conn = psycopg2.connect(
        host = "localhost",
        database = "BankDB",
        user = "postgres",
        password = "1234"
    )

    print("Connected to BankDB Successfully")

    conn.close()

except Exception as e:
    print("Connection Failed")
    print(e)
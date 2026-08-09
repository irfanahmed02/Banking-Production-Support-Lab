import psycopg2

try:

    conn = psycopg2.connect(
        host = "localhost",
        dbname = "BankDB",
        user = "postgres",
        password = "1234"
    )

    cursor = conn.cursor()

    query = """
            INSERT INTO transactions(pan,merchant_id,terminal_id,amount,stan,rrn,response_code,status) VALUES(
            %s,%s,%s,%s,%s,%s,%s,%s)
            """

    transactions = ("12345******67890","MM001","TT001",100.000,"000001","123456789012","00","Approved")

    cursor.execute(query=query, vars=transactions)

    conn.commit()

    print("The transaction successfully completed")

    conn.close()

except  Exception as e:
    print("Transaction failed")
    print(e)
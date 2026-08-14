import psycopg2

def get_connection():
    try:

        conn = psycopg2.connect(
            host = "localhost",
            database = "BankDB",
            user = "postgres",
            password = "1234"
        )

        print("Connected to BankDB Successfully")
        return conn, conn.cursor()

    except Exception as e:
        print("Database Connection Failed")
        raise e

def get_last_stan(cursor):

    try:

        query = """
                select max(stan) from transactions
                """
        
        cursor.execute(query=query)
        stan = cursor.fetchone()[0]
        return 0 if stan is None else stan

    except Exception as e:
        print("Retrieving STAN failed")
        print(e)

def get_last_rrn(cursor):
    
    try:
            query = """
                    select max(rrn) from transactions
                    """
            
            cursor.execute(query=query)
            rrn = cursor.fetchone()[0]
            return 0 if rrn is None else rrn
    
    except Exception as e:
        print("Retrieving RRN failed")
        print(e)

def close_connection(conn):
    try:
        conn.close()
        print("Database connecion closed successfully")
    except Exception as e:
        print("Database connection failed to be closed")
        print(e)

def insert_one_transaction(conn,cursor, values: tuple):

    query = """
                INSERT INTO transactions(pan,merchant_id,terminal_id,amount,currency,stan,rrn,response_code,status) VALUES(
                %s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
    cursor.execute(query,values)
    conn.commit()

def insert_many_transactions(cursor,values: list):
    query = """
                INSERT INTO transactions(pan, merchant_id, terminal_id, amount, currency, stan, rrn, response_code, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
    cursor.executemany(query=query, vars_list=values)

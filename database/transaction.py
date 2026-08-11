import database

conn, cursor = database.get_connection()

last_stan = database.get_last_stan(cursor)
last_rrn = database.get_last_rrn(cursor)
    
try:

    transactions = ("42222*******2222","M1004","T001",100.000,"BHD",str(int(last_stan)+1).zfill(6),str(int(last_rrn)+1).zfill(12),"00","Approved")
    database.insert_one_transaction(conn,cursor,transactions)
    print("The transaction successfully completed")

except  Exception as e:
    print("Transaction failed")
    print(e)

finally:
    database.close_connection(conn)
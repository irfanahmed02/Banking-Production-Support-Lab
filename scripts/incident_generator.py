import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
import random
from datetime import datetime,timedelta
import database
import constant

conn, cursor = database.get_connection()
transactions = []
starting_time = datetime(2026,8,11,00,41,00)
stan = database.get_last_stan(cursor)
rrn = database.get_last_rrn(cursor)

for i in range(15):
    transaction_time = starting_time + timedelta(minutes=i)
    if i < 2 or i == 14:
        respose_code = "00"
    else:
        respose_code = "96"

    pan = random.choice(constant.MASKED_PANS)
    merchant_id = random.choice(constant.MERCHANT_IDS)
    terminal_id = constant.TERMINAL_IDS[3]
    amount = round(random.uniform(0.1,1000),3)
    currency =  "BHD"
    stan = str(int(stan) + 1).zfill(6)
    rrn = str(int(rrn) + 1).zfill(12)
    status = constant.RESPONSE_CODES[respose_code]
    transactions.append((pan, merchant_id, terminal_id, amount, currency, stan, rrn, respose_code, status,transaction_time))

try:


    query = """
            INSERT INTO transactions(pan, merchant_id, terminal_id, amount, currency, stan, rrn, response_code, status, time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
    cursor.executemany(query=query, vars_list=transactions)

    conn.commit()
    print("Incident transactions posted successfully")

except Exception as e:
    print("Posting unsuccessfull")
    print(e)

finally:
    database.close_connection(conn)

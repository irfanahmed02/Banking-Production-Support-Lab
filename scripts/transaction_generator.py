import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
import database
import random
import constant

conn, cursor = database.get_connection()
transactions = []
stan = database.get_last_stan(cursor)
rrn = database.get_last_rrn(cursor)

for _ in range(10):
    pan = random.choice(constant.MASKED_PANS)
    merchant_id = random.choice(constant.MERCHANT_IDS)
    terminal_id = random.choice(constant.TERMINAL_IDS)
    amount = round(random.uniform(0.1,1000),3)
    currency =  "BHD"
    stan = str(int(stan) + 1).zfill(6)
    rrn = str(int(rrn) + 1).zfill(12)
    respose_code = random.choices(list(constant.RESPONSE_CODES.keys()),weights=constant.WEIGHTS,k=1)[0]
    status = constant.RESPONSE_CODES[respose_code]

    transactions.append((pan, merchant_id, terminal_id, amount, currency, stan, rrn, respose_code, status))

try:
    database.insert_many_transactions(cursor,transactions)
    conn.commit()
    print("10 transactions posted successfully")

except Exception as e:
    print("Posting unsuccessfull")
    print(e)

finally:
    database.close_connection(conn)
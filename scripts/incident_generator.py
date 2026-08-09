import random
import psycopg2
from datetime import datetime,timedelta

MASKED_PANS = ["41111*******1111","51111*******1111","42222*******2222","52222*******2222","43333******33333"]
merchant_ids = ["M1001","M1002","M1003","M1004","M1005"]
terminal_ids = ["T001","T002","T003","T004","T005","T006","T007","T008","T009","T010"]
response_codes = {"00": "Approved",
                    "05": "Declined",
                    "51": "Insufficient_Funds",
                    "54": "Expired_Card",
                    "91": "Issuer_Unavailable",
                    "96": "System_Error"
                  }
stan = "001001"
rrn = "000000001001"

transactions = []
starting_time = datetime(2026,8,9,20,15,00)

for i in range(15):
    transaction_time = starting_time + timedelta(minutes=i)
    if i < 2 or i == 14:
        respose_code = "00"
    else:
        respose_code = "96"

    pan = random.choice(MASKED_PANS)
    merchant_id = random.choice(merchant_ids)
    terminal_id = terminal_ids[3]
    amount = round(random.uniform(0.1,1000),3)
    currency =  "BHD"
    stan = str(int(stan) + 1).zfill(6)
    rrn = str(int(rrn) + 1).zfill(12)
    status = response_codes[respose_code]
    transactions.append((pan, merchant_id, terminal_id, amount, currency, stan, rrn, respose_code, status,transaction_time))

try:

    conn = psycopg2.connect(
        host = "localhost",
        dbname = "BankDB",
        user = "postgres",
        password = "1234"
    )
    cursor = conn.cursor()

    query = """
            INSERT INTO transactions(pan, merchant_id, terminal_id, amount, currency, stan, rrn, response_code, status, time)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
    cursor.executemany(query=query, vars_list=transactions)

    conn.commit()
    conn.close()
    print("Incident transactions posted successfully")

except Exception as e:
    print("Posting unsuccessfull")
    print(e)
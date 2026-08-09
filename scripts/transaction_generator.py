import random
import psycopg2

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
stan = "000001"
rrn = "000000000001"
weights= [0.85,0.07,0.04,0.02,0.01,0.01]

transactions = []

for _ in range(1000):
    pan = random.choice(MASKED_PANS)
    merchant_id = random.choice(merchant_ids)
    terminal_id = random.choice(terminal_ids)
    amount = round(random.uniform(0.1,1000),3)
    currency =  "BHD"
    stan = str(int(stan) + 1).zfill(6)
    rrn = str(int(rrn) + 1).zfill(12)
    respose_code = random.choices(list(response_codes.keys()),weights=weights,k=1000)[0]
    status = response_codes[respose_code]

    transactions.append((pan, merchant_id, terminal_id, amount, currency, stan, rrn, respose_code, status))

try:

    conn = psycopg2.connect(
        host = "localhost",
        dbname = "BankDB",
        user = "postgres",
        password = "1234"
    )
    cursor = conn.cursor()

    query = """
            INSERT INTO transactions(pan, merchant_id, terminal_id, amount, currency, stan, rrn, response_code, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
    cursor.executemany(query=query, vars_list=transactions)

    conn.commit()
    conn.close()
    print("1000 transactions posted successfully")

except Exception as e:
    print("Posting unsuccessfull")
    print(e)
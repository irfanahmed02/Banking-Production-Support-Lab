from fastapi import FastAPI, Response, status
from pydantic import BaseModel
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))
import database
import constant
import random

class TransactionRequest(BaseModel):
    pan: str
    merchant_id: str
    terminal_id: str
    amount: float
    currency: str

app = FastAPI()

def format_transaction(result):
    transaction = {"transaction_id": result[0], 
                               "pan": result[1], 
                               "merchant_id": result[2], 
                               "terminal_id": result[3], 
                               "amount": result[4],
                               "currency": result[5],
                               "stan": result[6],
                               "rrn": result[7],
                               "response_code": result[8],
                               "status_code": result[9],
                               "authorization_time": result[10]
                               }
    return transaction

@app.get("/health")
def health_check(response: Response):

    try:
        conn, cursor = database.get_connection()
        query = """select 1"""
        cursor.execute(query)
        database.close_connection(conn)
        return {"status":"ok", "database":"connected"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        print(e)
        return {"status":"failed","Database":"unavailable"}

@app.get("/transactions/{id}")
def get_transaction_by_id(id: int,response: Response):
    conn = None
    try:
        conn, cursor = database.get_connection()
        query = """select * from transactions where transaction_id = %s"""
        cursor.execute(query,(id,))
        result = cursor.fetchone()
        if result is None:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"status":"not found"}
        else:
            return format_transaction(result)
    except Exception as e:
        print(e)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status":"failed","Database":"unavailable"}
    finally:
        if conn:
            database.close_connection(conn)
    
@app.get("/transactions/rrn/{rrn}")
def get_transaction_by_rrn(rrn: str, response: Response):
    conn = None
    try:
        conn, cursor = database.get_connection()
        query = """select * from transactions where rrn = %s"""
        cursor.execute(query,(rrn,))
        result = cursor.fetchone()
        if result is None:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"status":"not found"}
        else:
            return format_transaction(result)
    except Exception as e:
        print(e)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status":"failed","Database":"unavailable"}
    finally:
        if conn:
            database.close_connection(conn)

@app.get("/terminals/{id}/transactions")
def get_all_transactions_by_terminal(id: str, response: Response):
    conn = None
    try:
        if id not in constant.TERMINAL_IDS:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"status":"not found"}
        conn,cursor = database.get_connection()
        query = """select * from transactions where terminal_id = %s"""
        cursor.execute(query,(id,))
        result = cursor.fetchall()
        transactions=[]
        for transaction in result:
            transactions.append(format_transaction(transaction))
        return transactions
    except Exception as e:
            print(e)
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status":"failed","Database":"unavailable"}
    finally:
            if conn:
                database.close_connection(conn)

@app.post("/transactions")
def post_transaction(request: TransactionRequest, response: Response):
    conn = None
    try:
        conn, cursor = database.get_connection()
        if request.pan not in constant.MASKED_PANS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","pan":"not found"}
        elif request.merchant_id not in constant.MERCHANT_IDS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","merchant_id":"not found"}
        elif request.terminal_id not in constant.TERMINAL_IDS:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","terminal_id":"not found"}
        elif request.currency.upper() != "BHD":
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","currency":"invalid"}

        stan = str(int(database.get_last_stan(cursor)) + 1).zfill(6)
        rrn = str(int(database.get_last_rrn(cursor)) + 1).zfill(12)
        response_code = random.choices(list(constant.RESPONSE_CODES.keys()),weights=constant.WEIGHTS,k=1)[0]
        trn_status = constant.RESPONSE_CODES[response_code]

        transaction = (request.pan,request.merchant_id,request.terminal_id,request.amount,request.currency,stan,rrn,response_code,trn_status)

        database.insert_one_transaction(conn,cursor,transaction)
        query = """select * from transactions where stan = %s"""
        cursor.execute(query,(stan,))
        result = cursor.fetchone()
        response.status_code = status.HTTP_201_CREATED
        return format_transaction(result)
    except Exception as e:
            print(e)
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status":"failed","Database":"unavailable"}
    finally:
        if conn:
            database.close_connection(conn)
    
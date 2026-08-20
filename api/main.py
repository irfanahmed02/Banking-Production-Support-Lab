from fastapi import FastAPI, Response, status, Request
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'database'))

import database
import constant
import random
import logging

log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'api.log')
logging.basicConfig(
    filename= log_path,
    level= logging.INFO,
    format= "%(asctime)s - %(levelname)s - %(message)s"
)

class TransactionRequest(BaseModel):
    pan: str
    merchant_id: str
    terminal_id: str
    amount: float
    currency: str

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for err in exc.errors():
        field = err["loc"][-1] if err["loc"] else "unknown"
        logging.warning(f'path={request.url.path}, issue_field={field}, message={err["msg"]}')
    return JSONResponse(
    status_code=422,
    content={"detail": exc.errors()},
)

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
                               "authorizer_response": result[9],
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
        logging.info("Health check passed")
        return {"status":"ok", "database":"connected"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logging.critical(e)
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
            logging.warning(f"Transaction not found: ID={id}")
            return {"status": "not found", "detail": f"Transaction with ID {id} not found"}
        else:
            logging.info(f"Transaction retrieved: ID={id}")
            return format_transaction(result)
    except Exception as e:
        logging.critical(e)
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
            logging.warning(f"Transaction not found: RRN={rrn}")
            return {"status": "not found", "detail": f"Transaction with RRN {rrn} not found"}
        else:
            logging.info(f"Transaction retrieved: RRN={rrn}")
            return format_transaction(result)
    except Exception as e:
        logging.critical(e)
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
            logging.warning(f"Terminal not found: TERMINALID={id}")
            return {"status": "not found", "detail": f"Terminal {id} not found"}
        conn,cursor = database.get_connection()
        query = """select * from transactions where terminal_id = %s"""
        cursor.execute(query,(id,))
        result = cursor.fetchall()
        transactions=[]
        for transaction in result:
            transactions.append(format_transaction(transaction))
        logging.info(f"Transactions retrieved: TERMINALID={id}, COUNT={len(transactions)}")
        return transactions
    except Exception as e:
            logging.critical(e)
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
            logging.warning(f"PAN not found: PAN={request.pan}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","pan":"not found"}
        elif request.merchant_id not in constant.MERCHANT_IDS:
            logging.warning(f"Merchant not found: MERCHANTID={request.merchant_id}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","merchant_id":"not found"}
        elif request.terminal_id not in constant.TERMINAL_IDS:
            logging.warning(f"Terminal not found: TERMINALID={request.terminal_id}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","terminal_id":"not found"}
        elif request.currency.upper() != "BHD":
            logging.warning(f"Invalid currency: CURRENCY={request.currency}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"status":"failed","currency":"invalid"}

        stan = str(int(database.get_last_stan(cursor)) + 1).zfill(6)
        rrn = str(int(database.get_last_rrn(cursor)) + 1).zfill(12)
        response_code = random.choices(list(constant.RESPONSE_CODES.keys()),weights=constant.WEIGHTS,k=1)[0]
        trn_status = constant.RESPONSE_CODES[response_code]

        transaction = (request.pan,request.merchant_id,request.terminal_id,request.amount,request.currency.upper(),stan,rrn,response_code,trn_status)

        database.insert_one_transaction(conn,cursor,transaction)
        query = """select * from transactions where stan = %s"""
        cursor.execute(query,(stan,))
        result = cursor.fetchone()
        response.status_code = status.HTTP_201_CREATED
        if result[8] == "00":
            logging.info(f"Transaction approved: ID={result[0]}, STAN={result[6]}, RRN={result[7]}, RESPONSE={result[9]}")
        elif result[8] in ("05","51","54"):
            logging.info(f"Transaction declined: ID={result[0]}, STAN={result[6]}, RRN={result[7]}, RESPONSE={result[9]}")
        else:
            logging.warning(f"Transaction failed: ID={result[0]}, STAN={result[6]}, RRN={result[7]}, RESPONSE={result[9]}")
        return format_transaction(result)
    except Exception as e:
        logging.critical(e)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status":"failed","Database":"unavailable"}
    finally:
        if conn:
            database.close_connection(conn)
    
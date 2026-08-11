MASKED_PANS = ["41111*******1111","51111*******1111","42222*******2222","52222*******2222","43333******33333"]
MERCHANT_IDS = ["M1001","M1002","M1003","M1004","M1005"]
TERMINAL_IDS = ["T001","T002","T003","T004","T005","T006","T007","T008","T009","T010"]
RESPONSE_CODES = {"00": "Approved",
                    "05": "Declined",
                    "51": "Insufficient_Funds",
                    "54": "Expired_Card",
                    "91": "Issuer_Unavailable",
                    "96": "System_Error"
                  }
WEIGHTS= [0.85,0.07,0.04,0.02,0.01,0.01]
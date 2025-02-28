import requests, jwt, json
from datetime import datetime

API_URL = "https://api.freedompay.kg/v5/merchant/invoice/init"
MERCHANT_ID = "YOUR_MERCHANT_ID"
SECRET_KEY = "YOUR_SECRET_KEY"

# Prepare the invoice request data
invoice_request = {
    "order_id": "ORDER12345",           # your unique order ID
    "merchant_id": MERCHANT_ID,
    "amount": 100.50,                  # e.g. 100.50 KZT (adjust currency as needed)
    "description": "Service payment for Order12345",
    "invoice_method": "qr",            # requesting a QR code payment link
    "currency": "KZT",
    "result_url": "https://yourdomain.com/api/payment/notify",  # your callback URL
    "request_method": "POST"
}

# Generate HS512 signature for the request
# Create JWT token with header, payload, and sign with SECRET_KEY
headers = {
    "uri": "/v5/merchant/invoice/init",
    "merchant_id": str(MERCHANT_ID),
    "method": "POST",
    "params": "",
    "alg": "HS512"
}
token = jwt.encode(invoice_request, SECRET_KEY, algorithm="HS512", headers=headers)
# jwt.encode returns the full JWT "header.payload.signature"
token_parts = token.split('.')
jws_signature = token_parts[0] + '..' + token_parts[2]  # header..signature

# Send the request with the X-JWS-Signature header
response = requests.post(API_URL, json=invoice_request, headers={"X-JWS-Signature": jws_signature})
res_data = response.json()
print(res_data)

# If the request is successful, FreedomPay will return a JSON response indicating an invoice was created. Key fields in the response include:
# status            – "ok" if the request was successful​
# invoice_status    – initial status of the invoice (usually "new" meaning waiting for payment)​
# invoice_id        – FreedomPay’s transaction ID for this invoice​
# invoice_methods   – an object containing payment method details requested. For QR codes, look at invoice_methods.qr​

# invoice_methods.qr    - field contains the payment URL encoded as a QR code (in base64 format

# If invoice_methods.qr is a base64-encoded image: You can send it directly to the frontend. For instance, if res_data["invoice_methods"]["qr"] returns a long base64 string, prefix it with data:image/png;base64, and embed in an <img> tag.
# If it’s a base64-encoded URL token: Decode it to get the actual URL, then generate a QR code image from that URL.

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/create_payment")
async def create_payment():
    # ... (prepare invoice_request and X-JWS-Signature as above) ...
    response = requests.post(API_URL, json=invoice_request, headers={"X-JWS-Signature": jws_signature})
    data = response.json()
    if data.get("status") != "ok":
        return JSONResponse({"error": data.get("error_description", "Unknown error")}, status_code=400)
    # Extract the QR code (base64 string)
    qr_base64 = data["invoice_methods"]["qr"]
    # Optionally, we can form a data URL for convenience
    qr_image_data_url = f"data:image/png;base64,{qr_base64}"
    # Return the data needed to display the QR (could also return other info like invoice_id)
    return {"order_id": invoice_request["order_id"], "qr_image": qr_image_data_url}


# result_url : HTTP request (POST by default) to the URL
    # pg_order_id – the order ID you originally sent​
    # pg_payment_id – the transaction ID in FreedomPay system​
    # pg_amount and pg_currency – amount and currency paid​
    # pg_result – 1 for success, 0 for failure​
    # pg_payment_date – timestamp of payment.
    # pg_card_pan – masked card number (if paid by card).
    # ... (other details like payment method, customer contact, etc.)
    # pg_sig – a signature string to verify the authenticity of this callback.

from fastapi import Request
from fastapi.responses import Response
import hashlib

@app.post("/payment/notify")
async def payment_notify(request: Request):
    # Parse the incoming form data
    form = await request.form()
    data = { key: form.get(key) for key in form.keys() }
    # Log or use the data as needed
    order_id = data.get("pg_order_id")
    payment_id = data.get("pg_payment_id")
    result = data.get("pg_result")  # "1" for success
    signature = data.get("pg_sig")
    
    # Verify the signature using FreedomPay's signature algorithm
    # (Typically, concatenate certain fields with your SECRET_KEY and compare MD5 hashes as per docs)
    def verify_signature(data: dict, secret: str) -> bool:
        if not data.get("pg_sig"):
            return False
        # FreedomPay signature generation (for callbacks) usually involves:
        # 1. Sorting all received pg_* keys except pg_sig alphabetically.
        # 2. Concatenating the script name and all values, separated by semicolons, and append secret.
        # 3. Taking an MD5 hash of that string (case-insensitive comparison).
        # Example (from docs) for request signature: 'init_payment.php;...;{secret_key}'&#8203;:contentReference[oaicite:31]{index=31}.
        keys = sorted(k for k in data.keys() if k != "pg_sig")
        signature_base = ";".join(["payment.php"] + [data[k] or "" for k in keys] + [secret])
        # Note: using "payment.php" or appropriate script name as per docs for result_url signature
        calc_sig = hashlib.md5(signature_base.encode()).hexdigest()
        return calc_sig == data.get("pg_sig")
    
    if not verify_signature(data, SECRET_KEY):
        # Signature mismatch – respond with an error (HTTP 400 or a "rejected" XML response)
        return Response(
            content='<?xml version="1.0"?><response><pg_status>rejected</pg_status><pg_description>Invalid signature</pg_description></response>', 
            media_type="application/xml"
        )
    
    # Signature is valid; process the payment result
    if result == "1":
        # Payment was successful
        # TODO: mark order as paid in your system, fulfill order, etc.
        status_description = "Order paid"
        pg_status = "ok"
    else:
        # Payment failed or was canceled
        status_description = "Payment failed or canceled"
        pg_status = "rejected"  # you could also use "ok" and handle failure in your system logic
    
    # Respond to FreedomPay with an XML acknowledgment
    # FreedomPay expects an XML with pg_status (ok/rejected) and a signature.
    # We will generate a signature for our response similarly.
    response_salt = "random string"  # or generate a random salt for the response
    response_sig_base = f"payment.php;{pg_status};{status_description};{response_salt};{SECRET_KEY}"
    response_sig = hashlib.md5(response_sig_base.encode()).hexdigest()
    xml_response = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<response>'
        f'<pg_status>{pg_status}</pg_status>'
        f'<pg_description>{status_description}</pg_description>'
        f'<pg_salt>{response_salt}</pg_salt>'
        f'<pg_sig>{response_sig}</pg_sig>'
        '</response>'
    )
    return Response(content=xml_response, media_type="application/xml")


# Important Details:
    # The result_url must be accessible publicly (no auth) so FreedomPay can reach it​
    # Ensure the path is correct and uses HTTPS.
    # Always verify pg_sig in the callback. This ensures the notification is genuinely from FreedomPay and not altered. Use your secret key to compute the expected signature. (The algorithm shown is an example; refer to official docs for exact procedure.)
    # After verification, update your order/payment status in your database accordingly.
    



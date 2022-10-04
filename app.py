from flask import Flask, redirect, request, jsonify
import os

import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = "whsec_fbd4303b3eb759f55fc3644a8b0a1502fc4938f5dccd1d58b346bc497ad99aa9"

WIN_DISPUTE = True

app = Flask(__name__)

@app.route("/")
def index():
  checkout_session = stripe.checkout.Session.create(
    line_items=[
      {
        "price": "price_1L2iJFF5HVVmwe4SYQXZq1dO",
        "quantity": 1,
      },
    ],
    mode="payment",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
  )

  return redirect(checkout_session.url, code=303)

@app.route("/tokenize", methods=["POST"])
def tokenize_card():
  customer = stripe.Customer.create(
    name="Test Customer",
    email="test.customer@example.com",
  )

  setup_intent = stripe.SetupIntent.create(
    customer=customer.id,
    confirm=True,
    usage="off_session",
    payment_method_data={
      "type": "card",
      "card": {
        "number": "4242424242424242",
        "exp_month": 1,
        "exp_year": 2023,
        "cvc": "123",
      },
      "billing_details": {
        "address": {
          "postal_code": "12345",
        },
      },
    },
  )

  print("[+] Tokenized card!")

  return jsonify(success=True)

@app.route("/webhooks", methods=["POST"])
def handle_webhooks():
  event = None
  stripe_payload = request.data
  sig_header = request.headers["STRIPE_SIGNATURE"]

  try:
    event = stripe.Webhook.construct_event(
      stripe_payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    raise e
  except stripe.error.SignatureVerificationError as e:
    raise e


  # Dispute events
  if event.type == "charge.dispute.created":
    dispute = event.data.object
    with open("./example-receipt.pdf", "rb") as fp:
      file_response = stripe.File.create(
        file=fp,
        purpose="dispute_evidence",
      )

    if WIN_DISPUTE:
      uncategorized_text = "winning_evidence"
    else:
      uncategorized_text = "losing_evidence"

    dispute_response = stripe.Dispute.modify(
      dispute.id,
      evidence={
        "billing_address": "123 Main St City, State 12345",
        "customer_email_address": "test@example.com",
        "customer_name": "Test Customer",
        "customer_purchase_ip": "123.123.123.123",
        "uncategorized_text": uncategorized_text,
        "receipt": file_response.id,
      },
    )

  elif event.type == "charge.dispute.updated":
    dispute = event.data.object
    print("[+] Dispute has been updated. Status is now [{}]".format(dispute.status))

  elif event.type == "charge.dispute.closed":
    dispute = event.data.object
    print("[+] Dispute has been closed. Status is [{}]".format(dispute.status))

  elif event.type == "charge.dispute.funds_reinstated":
    print("[+] Dispute fees reinstated")

  elif event.type == "charge.dispute.funds_withdrawn":
    dispute = event.data.object
    print("[+] Dispute fee has been withdrawn from your account")


  # Early fraud warning events
  elif event.type == "radar.early_fraud_warning.created":
    efw = event.data.object
    payment_intent_id = efw.payment_intent

    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

    # If PaymentIntent amount is < $20, just issue a refund
    if payment_intent.amount < 2000:
      print("[+] Proactively refunding payment")
      stripe.Refund.create(
        payment_intent=payment_intent_id,
      )
    else:
      print("[+] Not proactively refunding payment")


  # Refund events
  elif event.type == "charged.refunded":
    print("[+] Refund processed successfully")


  # Unexpected events
  else:
    print("[!] Got unexpected webhook event: {}".format(event.type))

  return jsonify(success=True)

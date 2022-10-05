# Overview

A simple app to demonstrate how to handle webhooks and collect/submit evidence for disputes.

## Install dependencies

To run the app: 
```
python3 -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt
```

## Stripe CLI

You'll want to use the [Stripe CLI](https://stripe.com/docs/stripe-cli) in order for this app to receive webhooks (if running locally).

You can also use something like [flask-ngrok][https://pypi.org/project/flask-ngrok/] to deploy this with a publicly accessible URL over HTTPS and use Stripe webhooks configured via the [Dashboard](https://stripe.com/docs/development/dashboard/register-webhook) as opposed to using the Stripe CLI.

Download and install the Stripe CLI and follow [this guide](https://stripe.com/docs/webhooks/test) to get the CLI set up.

Once the CLI is setup and you've run the `stripe login` command, run this command:
```
stripe listen --events charge.dispute.created,charge.dispute.updated,charge.dispute.closed,charge.dispute.funds_reinstated,charge.dispute.funds_withdrawn,radar.early_fraud_warning.created,charge.refunded --forward-to 127.0.0.1:5000/webhooks
```

You'll see a printout with a webhook secret key. Update line #6 with your endpoint secret.

## Run the app

Make sure you set your Stripe [secret test API key](https://dashboard.stripe.com/test/apikeys) via `export STRIPE_SECRET_KEY=<secret_api_key>`.

At this point you should have everything setup and ready to go. Run the app with:
```
flask run
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser and enter in a test card from [this page](https://stripe.com/docs/testing) (maybe one of the [dispute](https://stripe.com/docs/testing#disputes) ones).

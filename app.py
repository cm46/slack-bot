import os
import re

from dotenv import load_dotenv
load_dotenv()

from slack_bolt import App
import requests

alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_KEY")
slack_bot_token = os.getenv("BOT_OAUTH_TOKEN")
slack_bot_signing_secret = os.getenv("BOT_SIGNIN_SECRET")

# initializes your app with your bot token and signing secret
app = App(
    token=os.getenv("BOT_OAUTH_TOKEN"),
    signing_secret=os.getenv("BOT_SIGNIN_SECRET")
)

# collects crypto ticker for crypto requests
def handle_crypto_req(rest_of_message, event):
  if len(rest_of_message) < 1:
    return "Please specify a cryptocurrency ticker."
  
  [ticker] = rest_of_message

  response = requests.get(f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={ticker}&to_currency=USD&apikey={alpha_vantage_api_key}")
  response_json = response.json()

  if "Realtime Currency Exchange Rate" not in response_json:
    return f"{ticker} is not a valid ticker."
  currency_exchange_rate_data = response_json["Realtime Currency Exchange Rate"]
  
  bid_price = currency_exchange_rate_data["8. Bid Price"]
  ask_price = currency_exchange_rate_data["9. Ask Price"]

  bid_price_formatted = "{:,.2f}".format(float(bid_price))
  ask_price_formatted = "{:,.2f}".format(float(ask_price))

  return f"{ticker.upper()}\nBid Price: ${bid_price_formatted}\nAsk Price: ${ask_price_formatted}"

# collects user name for greeting requests
def handle_greeting_req(rest_of_message, event):
  user = event["user"]
  return (f"Hello <@{user}>!")

# collects ticker for quote requests 
def handle_quote_req(rest_of_message, event):
  if len(rest_of_message) < 1:
    return "Please specify a ticker."

  ticker = rest_of_message[0]

  response = requests.get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={alpha_vantage_api_key}")
  response_json = response.json()
  global_quote_data = response_json["Global Quote"]

  if "05. price" not in global_quote_data:
    return f"{ticker} is not a valid ticker."

  price = global_quote_data["05. price"]
  high = global_quote_data["03. high"]
  low = global_quote_data["04. low"]
  change = global_quote_data["10. change percent"]

  return f"{ticker.upper()}\nCurrent price: {price}\nHigh: {high}\nLow: {low}\nChange: {change}"

# collects ticker for info requests
def handle_info_req(rest_of_message, event):
  if len(rest_of_message) < 1:
    return "Please specify a ticker."

  [ticker] = rest_of_message

  response = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={alpha_vantage_api_key}")
  response_json = response.json()

  if "Name" not in response_json:
    return f"{ticker} is not a valid ticker."

  name = response_json["Name"]
  description = response_json["Description"]

  return f"{ticker.upper()}\nCompany: {name}\nDescription: {description}"

# list of commands that our Slack bot can understand
command_handlers = {}
command_handlers["quote"] = handle_quote_req
command_handlers["info"] = handle_info_req
command_handlers["hello"] = handle_greeting_req
command_handlers["crypto"] = handle_crypto_req

# Slack bot responses
@app.event("app_mention")
def respond(event, say):
  user = event["user"]
  message = event["text"].strip()
  parsed = message.replace("\xa0", ",").replace(" ", ",").split(",")

  if len(parsed) == 1:
    say(f"What do you want <@{user}>?")

  command = parsed[1]

  if command not in command_handlers:
    say(f"{command} is not a supported command.")
  
  handler = command_handlers[command]
  rest_of_messages = parsed[2:]
  what_to_say = handler(rest_of_messages, event)
  say(what_to_say)

# start the app
if __name__ == "__main__":
  app.start(port=int(os.environ.get("PORT", 3000)))
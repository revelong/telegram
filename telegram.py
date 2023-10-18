from telebot import types
import telebot, requests
import threading
import random


BOT_TOKEN="6646591548:AAEw1qDAQxJfOE_5jRrWqVPp4AOdQI6QeSQ"
BASE = "https://collector-ps-142293b20427.herokuapp.com/"
POOF_TOKEN = "Rn0KT5RQP9l99D-XfqkNJg"
POOF_BASE = "https://www.poof.io/api/v2/"
POOF_HEADERS = {"Content-Type": "application/json", "Authorization": POOF_TOKEN}
BITCOIN_ADDRESS =  "bc1q7d5sw9yksd03hsmpjjt34slt8f0rac38dreq4p"

support = "@BBunny323"
bot = telebot.TeleBot(BOT_TOKEN)

# Format card number
def format_card(number_string):
    modified_string = ' '.join(number_string[i:i+4] for i in range(0, len(number_string), 4))
    return modified_string

# Format date
def format_date(date_string):
    day, month, year = date_string.split("/")
    day = day.zfill(2)
    formatted_date = f"{day}/{year}"
    return formatted_date

# Get all the card information through pid
def provide_card(pidCard):
    info = requests.post(BASE + "pid", json = {"pid": pidCard})
    return info.json()

# Register Transaction
def register_transaction(pid, btc_addr, btc_amount, delivery_balance, invoice_id):
    resp = requests.post(BASE + "registertransaction", json = {"pid": pid, "btc_addr":btc_addr, "btc_amount":btc_amount, "delivery_balance": delivery_balance, "invoice_id": invoice_id})
    return resp.json()

# Round the number down
def roundNum(number):
    rounded = (number // 10) * 10
    return float("{:.2f}".format(rounded))

# Get available cards in the database
def obtain_available_cards():
    balances = requests.get(BASE + "available")
    return balances.json();

# Check transaction
def check_transaction(addr):
    data = {"filter": "crypto_address", "search": addr}
    r = requests.post(POOF_BASE + "transaction_query", json = data, headers = POOF_HEADERS)
    return r.json()

# Update all the cards balances
def update_cards():
    print("updating balance of cards")
    t = threading.Timer(600.0, update_cards)
    t.start()
    available_cards = obtain_available_cards()
    for available_card in available_cards:
        c = provide_card(available_card["pid"])
        maindigits = c["rows"][0]["maindigits"]
        last4 = "{}{}{}{}".format(maindigits[12], maindigits[13], maindigits[14], maindigits[15])
        requests.post(BASE + "balance", json = {"last4": last4})
update_cards()

# Create a bitcoin charge - when a user requests to pay for a card
def create_charge(amount):
    data = {"amount": amount, "crypto": "bitcoin"}
    r = requests.post(POOF_BASE + "create_charge", json = data, headers = POOF_HEADERS)
    return r.json()

# Check card status and balance
@bot.message_handler(commands=['check'])
def send_check(msg):
    msg = bot.reply_to(msg, "🤵 Please provide the last 4 digits of the card you have. 🤵")
    bot.register_next_step_handler(msg, define)
def define(message):
    chat_id = message.chat.id
    last4 = message.text
    r = requests.post(BASE + "balance", json = {"last4": last4})
    r = r.json()
    print(r)
    if r:
        if (r['status']):
            bot.send_message(chat_id, """
Status: Active
Balance: {}
            """.format(r['balance']))
        else:
            bot.send_message(chat_id, """
Status: Suspended
            """)
    else:

        bot.send_message(chat_id, """Card not in system""")



@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(message, """
✴️ Welcome to our organization currently working at a financial institution exporting card information and providing valid and live debit cards with full information and balance. We are not only selling the cards, but working with distributors worldwide. ✴️
    """)

@bot.message_handler(commands=["deposit"])
def send_deposit(message):
    bot.reply_to(message, """
🧑‍💻  Congratulations! 🧑‍💻️
If you've successfully finished cashing out a card, send us our cut to the address below and send our support team a screenshot as proof of payment and your Distributor ID.

{}

Thank you!
    """.format(BITCOIN_ADDRESS))







@bot.message_handler(commands=["support"])
def send_support(message):
    bot.reply_to(message, """
Support Team: {}
    """.format(support))


def generate_random_digits():
    random_digits = [str(random.randint(0, 9)) for _ in range(8)]
    return ''.join(random_digits)

# Request a card
@bot.message_handler(commands=["requestcard"])
def send_requested_card(msg):
    card = ""
    message = ""
    username = msg.chat.username
    print("username", username)
    profile_json = requests.post(BASE + "getdistributor", json = {"username": username}, headers = {"Content-Type": "application/json"})
    print("response")
    print(profile_json)
    profile = profile_json.json()
    print(profile)

    if (len(profile) > 0):
        if (not profile[0]["locked"]):
            profile_id = profile[0]["id"]
            ranking = profile[0]["ranking"]
            cards = obtain_available_cards()
            for c in cards:
                balance = roundNum(float(c["balance"]))
                if (ranking == 1):
                    if (float(balance) < 300.0 and float(balance) > 100.00):
                        card = c
                        break
                elif (ranking == 2):
                    if (float(balance) < 500.0 and float(balance) > 300.00):
                        card = c
                        break
                elif (ranking == 3):
                    if (float(balance) < 800.0 and float(balance) > 500.00):
                        card = c
                        break
                else:
                    if (float(balance) > 800.00):
                        card = c
                        break
            if (card):
                pid = card["pid"]
                card = provide_card(pid)
                card = card["rows"][0]
                realid = card["realid"]
                print("pid", pid)
                requests.post(BASE + "distributed", json = {"distributed": True, "pid": pid, "realid":realid}, headers = {"Content-Type": "application/json"})
                requests.post(BASE + "setdistributor", json = {"distributor": username, "pid": pid}, headers = {"Content-Type": "application/json"})
                message = """
First Name: {}
Middle Name: {}
Last Name: {}
Card Number: {}
Expiration Date: {}
CVV: {}
Address: {}
Second Address: {}
City: {}
State: {}
Zip: {}
Balance: {}
            """.format(card["firstname"], card["middlename"], card["lastname"], format_card(card["maindigits"]), format_date(card["exp"]), card["cvv"], card["address"], card["secondaddress"], card["city"], card["state"], card["zip"], card["balance"])
                requests.post(BASE + "updatedistributor", json = {"id": profile_id, "locked": True}, headers = {"Content-Type": "application/json"})
        else:
            message = """
You already are a distributor and have a pending card for cashout, contact support if you have finished cashing out.
Thank you
"""
    else:
        message = "You are not a distributor, please apply if you are interested"

    bot.send_message(msg.chat.id, message)

# # Distribute a card
# @bot.message_handler(commands=["distribute"])
# def send_distribution(message):
#     markup = types.InlineKeyboardMarkup(row_width=2)

#     desc = """
# ⚠️ Please read the terms and requirements before proceeding. ⚠️

# 📌 The division of funds and profit will be 50/50.
# 📌 So you can have an understanding in how these cards work, go into the menu and click on purchase a new card before applying please.
# 📌 We receive ONLY as payment form, bitcoin.
# 📌 You have 7 business days deposit our cut after cashing out.
# 📌 If there is no response of progress after a card has been provided for 7 business days, and/or slow and short responses are being given by the recipient, will result in termination.
# 📌 You will be provided cards $100 balance and scaling upwards depending on performance.
# 📌 Join here  https://t.me/+PPxfJ6285542ZDlh  or you will be terminated due to lack of organization.

# There are absolutely NO EXCEPTIONS to these terms. Once agreeing to these terms, please click YES to begin.
#     """
#     agreement = types.InlineKeyboardButton("YES", callback_data="YES")
#     markup.add(agreement)
#     bot.send_message(message.chat.id, desc, reply_markup=markup)

# Purchase a card - Provide a card
@bot.message_handler(commands=["purchase"])
def send_catalog(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    available_cards = obtain_available_cards()
    desc = """
✴️ ALL ISSUES WITH ITEMS ARE RESOLVING WITH OUR SUPPORT AS SOON AS POSSIBLE ({})

✴️ OUR SUPPORT DOESN'T ADVISE HOW TO USE CARDS BUT THEY WILL PROVIDE PLATFORMS WHERE THE CARDS MAY GO THROUGH

✴️ YOU CAN ALWAYS CHECK WITH THE SUPPORT FOR GENERAL QUESTIONS ABOUT THE CARDS

✴️ ALL THE CARDS ARE CHECKED AND LIVE UPON DELIVERY

✴️ WE DO NOT PROVIDE DISCOUNTS, REFUNDS OR PARTIAL PAYMENTS BEFORE DELIVERY

✴️ BY USING OUR PRODUCT YOU AGREE WITH ITEMS REFUND POLICY AND WON'T HAVE ANY COMPLAINS

📌 These are the cards we currently have available. They are sold for 20% of the available balance.
📌 They do not have an AI fraud detection system, therefore can only get burnt manually, and they go through payment gateways such as Cash App, Paypal, Remitly, Western Union, etc.
📌 The main issue with these cards is not so much the card getting suspended, but them going through the payment gateway. As many payment gateways reject transactions due to fraud, it is recommended to use the cards on accounts that are old and have a history.
📌 Just as with any other card, they do run the risk of being suspended nonetheless. The only ways of suspension are the fraud department which goes through each individual card and suspends it, or the card holder recognizing their card is being used and calling in to suspend it.
📌 The best hours to cash out these cards are outside business days Monday - Friday, and if you are cashing out the cards during such hours, then attempt to avoid using the cards between 8am - 5pm PST as the fraud department may suspend the card - very unlikely.
📌 You can check these cards through the menu, but they will not burn or suspend the cards as with common checkers, reason being this is internal programming and the balance checking is automated, no third parties involved.
📌 As these cards to pertain to real people, the balance can change, therefore the server will update the most recent balance every 10 minutes.
📌 We receive only Bitcoin as form of payment.
📌 These are visa prepaid debit cards and the bin for all of these cards is 407535.
📌 The card does have an external transfer fee of $1.00, this is when you want to add funds to a third party platform such as Cashapp or Paypal. Take that into consideration when cashing out.
📌 There is a 20 daily transaction limit and $2,000 transaction limit with platforms such as Paypal or Cashapp.

INSTRUCTIONS
1. Click on the card you would like to purchase.
2. Send the amount of bitcoin stated below to the address below.
3. Bot will provide you the card upon payment.

The format is the catalog is presented: Balance of the card - Price at which the card will be sold at
    """.format(support)
    for card in available_cards:
        balance_price = roundNum(float(card["balance"]))
        price = 20/100 * balance_price
        price = roundNum(price)
        if price <= 10 or card["realid"] == None or str(balance_price) == "1000.0" or str(balance_price) == "1000" or str(balance_price) == "1000.00":
            continue
        price = str(round(price, 2))
        card = types.InlineKeyboardButton("💵 " + str(balance_price) + " - " + str(price) + " 💳", callback_data="card_"+card["pid"])
        markup.add(card)

    bot.send_message(message.chat.id, desc, reply_markup=markup)

@bot.callback_query_handler(func=lambda call:True)
def answer_distribution(callback):
    if (callback.message):
        if "card_" in callback.data:
            pid = callback.data.split("_")[1]
            card = provide_card(pid)
            card = card["rows"][0]
            balance_price = float(card["balance"])
            price = 20/100 * balance_price
            price = roundNum(price)
            expiration_secs10 = 720
            cardMessage = """
First Name: {}
Middle Name: {}
Last Name: {}
Card Number: {}
Expiration Date: {}
CVV: {}
Address: {}
Second Address: {}
City: {}
State: {}
Zip: {}
Balance: {}
            """.format(card["firstname"], card["middlename"], card["lastname"], format_card(card["maindigits"]), format_date(card["exp"]), card["cvv"], card["address"], card["secondaddress"], card["city"], card["state"], card["zip"], card["balance"])
            charge = create_charge(price)
            print("Created a charge")
            message = """
Send exactly this amount of bitcoin {} to below address

Bitcoin Address: {}
Price of Card - Purchase Amount: {}
Rate: {}

⚠️ WARNING ⚠️
📌 Within 15 minutes the transaction will expire, sending funds to provided bitcoin address will result in a loss of funds, please send bitcoin within timeframe and when ready.
📌 The card will be provided immediately upon payment.
            """.format(charge["charge"], charge["address"], charge["amount"], charge["rate"])
            register_transaction(pid, charge["address"], charge["charge"], card["balance"], charge["uuid"])

            timers = []
            def check(c,addr):
                trx = check_transaction(addr)
                print("Got the transaction")
                trx = trx.values()
                if card["sold"] == False and c == expiration_secs10:
                    for t in timers:
                        try:
                            t.cancel()
                            print("Expired, terminating process")
                        except Exception as e:
                            print(e)
                            pass

                if card["sold"] == False and c != expiration_secs10:
                    print("The card is not marked as sold")
                    t = threading.Timer(10.0, check, [c+1,addr])
                    t.start()
                    timers.append(t)
                    print("Started the timer")
                    for obj in trx:
                        print("Object found in the transaction that was located")
                        print(obj)
                        print("Has the object been paid")
                        print(obj["paid"])
                        print("Checking if the card is marked as paid")
                        if obj['paid'] != "no":
                            print("The card is marked as paid")
                            r = requests.post(BASE + "sold", json = {"sold": True, "pid": pid}, headers = {"Content-Type": "application/json"})
                            r = r.json()
                            print(r)
                            if r:
                                print("Sending over the card")
                                bot.send_message(callback.message.chat.id, """
Payment Successful!

{}

Thank you for your purchase, if you have any questions, please contact us!
                                    """.format(cardMessage))
                                t.cancel()
                        else:
                            print("The card has not been paid, no card provided")
                            print("Current count")
                            print(c)
            check(0,charge["address"])

            bot.send_message(callback.message.chat.id, message)
        else:
            card = ""
            message = ""
            username = callback.message.chat.username
            print("username", username)
            if (username):
                profile_json = requests.post(BASE + "getdistributor", json = {"username": username}, headers = {"Content-Type": "application/json"})
                print("response")
                print(profile_json)
                profile = profile_json.json()
                print(profile)
                ranking = 1


                if (len(profile) > 0):
                    if (profile[0]["locked"]):
                        message = """
You already are a distributor and have a pending card for cashout, contact support if you have finished cashing out.
Thank you
"""
                    else:
                        ranking = profile[0]["ranking"]
                else:
                    cards = obtain_available_cards()
                    for c in cards:
                        balance = roundNum(float(c["balance"]))
                        if (ranking == 1):
                            if (float(balance) < 300.0 and float(balance) > 100.00):
                                card = c
                                break
                        elif (ranking == 2):
                            if (float(balance) < 500.0 and float(balance) > 300.00):
                                card = c
                                break
                        elif (ranking == 3):
                            if (float(balance) < 800.0 and float(balance) > 500.00):
                                card = c
                                break
                        else:
                            if (float(balance) > 800.00):
                                card = c
                                break

                    if (card):
                        profile_id = generate_random_digits()
                        pid = card["pid"]
                        card = provide_card(pid)
                        card = card["rows"][0]
                        print("pid", pid)
                        realid = card["realid"]
                        requests.post(BASE + "createdistributor", json = {"username": username, "id": profile_id}, headers = {"Content-Type": "application/json"})
                        requests.post(BASE + "distributed", json = {"distributed": True, "pid": pid, "realid":realid}, headers = {"Content-Type": "application/json"})
                        requests.post(BASE + "setdistributor", json = {"distributor": username, "pid": pid}, headers = {"Content-Type": "application/json"})
                        message = """
----------------------------------------------
Distributor ID: {}

This is a unique ID you will have to keep in order to continue working with us, you will provide this to customer support after cashing out.
----------------------------------------------

Card Information

First Name: {}
Middle Name: {}
Last Name: {}
Card Number: {}
Expiration Date: {}
CVV: {}
Address: {}
Second Address: {}
City: {}
State: {}
Zip: {}
Balance: {}

----------------------------------------------

Thank you for doing business with us! We hope hearing from you soon.
                        """.format(profile_id, card["firstname"], card["middlename"], card["lastname"], format_card(card["maindigits"]), format_date(card["exp"]), card["cvv"], card["address"], card["secondaddress"], card["city"], card["state"], card["zip"], card["balance"])
                        requests.post(BASE + "updatedistributor", json = {"id": profile_id, "locked": True}, headers = {"Content-Type": "application/json"})
                    else:
                        message = "According to the ranking, no cards available for distribution, please try again later."
            else:
                message = "Sadly, until further notice your username must be public or you must have set a username in order for the bot to function. Thank you for your interest."

            bot.send_message(callback.message.chat.id, message)

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

# Start the bot
bot.infinity_polling()



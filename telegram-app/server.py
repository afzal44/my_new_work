from bot import telegram_chatbot
import gizoogle

bot = telegram_chatbot("config.cfg")

update_id = None

def make_reply(msg):
    reply = None
    if msg is not None:
        reply = gizoogle.text(msg)
    return reply

while True:
    updates = bot.get_updates(offset=update_id)
    print(updates)
    updates = updates.get("result",None)
    if updates:
        for item in updates:
            update_id = item["update_id"]
            try:
                message = item["message"]["text"]
            except:
                message = None
            from_ = item["message"]["from"]["id"]
            reply = make_reply(message)
            bot.send_message(reply, from_)


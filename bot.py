import telebot
import requests
import os
from flask import Flask
from threading import Thread
from telebot import types

# --- ၁။ Render အတွက် အသေးစား Web Server ပိုင်း (အပေါ်ဆုံးမှာ ထားပါ) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ၂။ Bot Setting ပိုင်း ---
BOT_TOKEN = '8772824284:AAHq3om8lFd4QhoJW_ortNc3Hu8VVCs4FLc' # ဒီနေရာမှာ သင့် Token ထည့်ပါ
bot = telebot.TeleBot(BOT_TOKEN)

RAPIDAPI_KEY = "81af0e4596msh99a544721cd6043p12ea14jsn9e95af1e2351"
RAPIDAPI_HOST = "universal-social-media-downloader-api.p.rapidapi.com"

user_data = {}

# --- ၃။ Bot ရဲ့ လုပ်ဆောင်ချက် Logic များ ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Link ပို့ပေးပါ၊ Quality ရွေးချယ်နိုင်အောင် ပြင်ဆင်ပေးပါမည်။ ✨")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "http" in url:
        msg = bot.reply_to(message, "⏳ အချက်အလက်များကို စစ်ဆေးနေသည်...")
        api_url = "https://universal-social-media-downloader-api.p.rapidapi.com/parse"
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }
        try:
            response = requests.post(api_url, json={"url": url}, headers=headers)
            result = response.json()
            if result.get('success') and 'data' in result:
                medias = result['data'].get('medias', [])
                markup = types.InlineKeyboardMarkup()
                valid_links = {}
                for index, item in enumerate(medias):
                    if item.get('format') == 'mp4':
                        quality = item.get('quality', 'Normal')
                        label = f"Video - {quality}"
                        callback_val = f"dl_{index}_{message.chat.id}"
                        markup.add(types.InlineKeyboardButton(text=label, callback_data=callback_val))
                        valid_links[index] = item.get('url')
                user_data[message.chat.id] = valid_links
                if valid_links:
                    bot.edit_message_text("Video Quality ရွေးချယ်ပါ -", message.chat.id, msg.message_id, reply_markup=markup)
                else:
                    bot.edit_message_text("❌ Download link များ ရှာမတွေ့ပါ။", message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ API မှ အချက်အလက် မရရှိနိုင်ပါ။", message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def callback_download(call):
    _, index, chat_id = call.data.split('_')
    index = int(index)
    chat_id = int(chat_id)
    if chat_id in user_data and index in user_data[chat_id]:
        video_url = user_data[chat_id][index]
        bot.answer_callback_query(call.id, "ဗီဒီယို ပို့ပေးနေပြီ...")
        bot.send_video(chat_id, video_url, caption="ရပါပြီခင်ဗျာ! ✅")
    else:
        bot.answer_callback_query(call.id, "Error: Link သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)

# --- ၄။ Bot ကို Run တဲ့အပိုင်း (အောက်ဆုံးမှာ ထားပါ) ---
if __name__ == "__main__":
    keep_alive() # Web server ကို အရင်နှိုးမယ်
    print("Bot is starting...")
    bot.polling(none_stop=True)

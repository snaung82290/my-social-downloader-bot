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

# API အဟောင်း (TikTok, Rednote အတွက်)
UNIVERSAL_HOST = "universal-social-media-downloader-api.p.rapidapi.com"

# API အသစ် (Pinterest အတွက် - သင်ယူထားတဲ့ Host နဲ့ လဲပါ)
PINTEREST_HOST = "pinterest-video-and-image-downloader.p.rapidapi.com" 

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # ၁။ Pinterest ဖြစ်ခဲ့လျှင်
    if "pinterest.com" in url or "pin.it" in url:
        msg = bot.reply_to(message, "⏳ Pinterest Video ကို ရှာဖွေနေပါတယ်...")
        
        # Pinterest API Endpoint (API အလိုက် ပြောင်းလဲနိုင်သည်)
        api_url = f"https://{PINTEREST_HOST}/download" 
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY, # Key ကတော့ အတူတူပဲ ဖြစ်နိုင်ပါတယ်
            "x-rapidapi-host": PINTEREST_HOST
        }
        params = {"url": url}

        try:
            response = requests.get(api_url, headers=headers, params=params)
            result = response.json()
            
            # API အသစ်ရဲ့ JSON structure အတိုင်း link ကို ယူရပါမယ်
            # ဥပမာ - result['data']['url']
            video_url = result.get('data', {}).get('url') 

            if video_url:
                bot.send_video(message.chat.id, video_url, caption="Pinterest Video ရပါပြီ! ✅")
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Pinterest Video ရှာမတွေ့ပါ။", message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Pinterest Error: {str(e)}", message.chat.id, msg.message_id)

    # ၂။ TikTok သို့မဟုတ် Rednote ဖြစ်ခဲ့လျှင် (Code အဟောင်းအတိုင်း)
    elif any(domain in url for domain in ["tiktok.com", "rednote.com", "xhslink.com"]):
        # ... သင်အရင်သုံးနေကျ Universal API code များကို ဒီမှာ ဆက်ရေးပါ ...
        msg = bot.reply_to(message, "⏳ Link ကို စစ်ဆေးနေပါတယ်...")
        
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
                # Video link တွေအပြင် ပုံ (Images) တွေကိုပါ download ဆွဲနိုင်အောင် logic ထပ်ဖြည့်ထားပါတယ်
                medias = result['data'].get('medias', [])
                markup = types.InlineKeyboardMarkup()
                valid_links = {}

                for index, item in enumerate(medias):
                    # Video ရော Image ရော link အကုန်ထုတ်ပေးမယ်
                    format_type = item.get('format', 'media').upper()
                    quality = item.get('quality', 'Standard')
                    label = f"{format_type} - {quality}"
                    
                    callback_val = f"dl_{index}_{message.chat.id}"
                    markup.add(types.InlineKeyboardButton(text=label, callback_data=callback_val))
                    valid_links[index] = {
                        "url": item.get('url'),
                        "type": item.get('format')
                    }

                user_data[message.chat.id] = valid_links

                if valid_links:
                    bot.edit_message_text("ရရှိနိုင်သော Media များ -", message.chat.id, msg.message_id, reply_markup=markup)
                else:
                    bot.edit_message_text("❌ Media link များ ရှာမတွေ့ပါ။", message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ API မှ အချက်အလက် မရရှိနိုင်ပါ။", message.chat.id, msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "TikTok, Pinterest သို့မဟုတ် Rednote link ပို့ပေးပါ။")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def callback_download(call):
    _, index, chat_id = call.data.split('_')
    index = int(index)
    chat_id = int(chat_id)

    if chat_id in user_data and index in user_data[chat_id]:
        media_info = user_data[chat_id][index]
        media_url = media_info["url"]
        media_type = media_info["type"]

        bot.answer_callback_query(call.id, "ပို့ပေးနေပြီ...")
        
        try:
            if media_type == 'mp4':
                bot.send_video(chat_id, media_url, caption="Done! ✅")
            else:
                bot.send_photo(chat_id, media_url, caption="Done! ✅")
        except Exception as e:
            bot.send_message(chat_id, f"❌ ပို့လို့မရပါ: {str(e)}")
    else:
        bot.answer_callback_query(call.id, "Error: Link သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)

# --- ၄။ Bot ကို Run တဲ့အပိုင်း (အောက်ဆုံးမှာ ထားပါ) ---
if __name__ == "__main__":
    keep_alive() # Web server ကို အရင်နှိုးမယ်
    print("Bot is starting...")
    bot.polling(none_stop=True)

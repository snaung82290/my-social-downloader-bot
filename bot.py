import telebot
import requests
import os
from flask import Flask
from threading import Thread
from telebot import types

# --- ၁။ Render အတွက် Web Server ပိုင်း ---
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
BOT_TOKEN = '8772824284:AAHq3om8lFd4QhoJW_ortNc3Hu8VVCs4FLc'
bot = telebot.TeleBot(BOT_TOKEN)

RAPIDAPI_KEY = "81af0e4596msh99a544721cd6043p12ea14jsn9e95af1e2351"
UNIVERSAL_HOST = "universal-social-media-downloader-api.p.rapidapi.com"
PINTEREST_HOST = "pinterest-video-and-image-downloader.p.rapidapi.com" 

user_data = {}

# --- ၃။ Bot ရဲ့ လုပ်ဆောင်ချက် Logic များ ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "TikTok, Pinterest သို့မဟုတ် Rednote link ပို့ပေးပါ။ Quality ရွေးချယ်နိုင်အောင် ပြင်ဆင်ပေးပါမည်။ ✨")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # ၁။ Pinterest ဖြစ်ခဲ့လျှင်
    if "pinterest.com" in url or "pin.it" in url:
        msg = bot.reply_to(message, "⏳ Pinterest Media ကို ရှာဖွေနေပါတယ်...")
        api_url = f"https://{PINTEREST_HOST}/pinterest" # ဒီ Endpoint ကို တစ်ချက်ပြန်စစ်ပါ (API dashboard မှာကြည့်ရန်)
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": PINTEREST_HOST
        }
        params = {"url": url}

        try:
            response = requests.get(api_url, headers=headers, params=params)
            result = response.json()
            
            # Pinterest API က ပေးတဲ့ data structure ကို စစ်ဆေးခြင်း
            # ဥပမာ result['url'] သို့မဟုတ် result['data']['url'] ဖြစ်နိုင်သည်
            video_url = result.get('url') or result.get('data', {}).get('url')

            if video_url:
                # Pinterest က ဗီဒီယိုဆိုရင် send_video၊ ပုံဆိုရင် send_photo
                if ".mp4" in video_url or "video" in video_url.lower():
                    bot.send_video(message.chat.id, video_url, caption="Pinterest Video ✅")
                else:
                    bot.send_photo(message.chat.id, video_url, caption="Pinterest Image ✅")
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Pinterest Media ရှာမတွေ့ပါ။ API Dashboard မှာ test လုပ်ကြည့်ပါ။", message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Pinterest Error: {str(e)}", message.chat.id, msg.message_id)

    # ၂။ TikTok သို့မဟုတ် Rednote ဖြစ်ခဲ့လျှင်
    elif any(domain in url for domain in ["tiktok.com", "rednote.com", "xhslink.com"]):
        msg = bot.reply_to(message, "⏳ Link ကို စစ်ဆေးနေပါတယ်...")
        api_url = f"https://{UNIVERSAL_HOST}/parse"
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": UNIVERSAL_HOST
        }

        try:
            response = requests.post(api_url, json={"url": url}, headers=headers)
            result = response.json()

            if result.get('success') and 'data' in result:
                medias = result['data'].get('medias', [])
                markup = types.InlineKeyboardMarkup()
                valid_links = {}

                for index, item in enumerate(medias):
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
    # (Callback code အပိုင်းကတော့ အိုကေပါတယ်၊ အရင်အတိုင်းထားနိုင်သည်)
    try:
        _, index, chat_id = call.data.split('_')
        index, chat_id = int(index), int(chat_id)
        if chat_id in user_data and index in user_data[chat_id]:
            media_info = user_data[chat_id][index]
            bot.answer_callback_query(call.id, "ပို့ပေးနေပြီ...")
            if media_info["type"] == 'mp4':
                bot.send_video(chat_id, media_info["url"], caption="Done! ✅")
            else:
                bot.send_photo(chat_id, media_info["url"], caption="Done! ✅")
    except:
        bot.answer_callback_query(call.id, "Error: Link သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)

# --- ၄။ Bot ကို Run တဲ့အပိုင်း ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is starting...")
    bot.polling(none_stop=True)

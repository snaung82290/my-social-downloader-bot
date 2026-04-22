import telebot
import requests
import os
import re
from flask import Flask
from threading import Thread
from telebot import types

# --- ၁။ Render အတွက် Web Server ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and serving multiple users!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ၂။ Bot Setting ---
BOT_TOKEN = '8772824284:AAHq3om8lFd4QhoJW_ortNc3Hu8VVCs4FLc'
bot = telebot.TeleBot(BOT_TOKEN)

RAPIDAPI_KEY = "81af0e4596msh99a544721cd6043p12ea14jsn9e95af1e2351"
UNIVERSAL_HOST = "universal-social-media-downloader-api.p.rapidapi.com"
PINTEREST_HOST = "pinterest-video-and-image-downloader.p.rapidapi.com"
YT_HOST = "youtube-media-downloader.p.rapidapi.com"

# User အသီးသီးရဲ့ Data တွေကို သိမ်းဖို့ Dictionary (Memory)
user_data_storage = {}

def get_url(text):
    """စာသားထဲကနေ URL သီးသန့်ကို ဆွဲထုတ်ပေးတဲ့ function"""
    urls = re.findall(r'(https?://\S+)', text)
    return urls[0] if urls else None

# --- ၃။ Bot Logic ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "မင်္ဂလာပါ! TikTok, IG, Pinterest, YouTube, Rednote လင့်များ ပို့နိုင်ပါပြီ။ ✨")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    raw_text = message.text
    url = get_url(raw_text)
    chat_id = message.chat.id

    if not url:
        bot.reply_to(message, "ကျေးဇူးပြု၍ Link တစ်ခု ပို့ပေးပါခင်ဗျာ။")
        return

    # ၁။ Instagram Logic
    if "instagram.com" in url:
        msg = bot.reply_to(message, "⏳ Instagram Media ကို စစ်ဆေးနေပါတယ်...")
        try:
            response = requests.post(f"https://{UNIVERSAL_HOST}/parse", json={"url": url}, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": UNIVERSAL_HOST, "content-type": "application/json"})
            result = response.json()
            if result.get('success'):
                medias = result['data'].get('medias', [])
                markup = types.InlineKeyboardMarkup()
                valid_links = {}
                for index, item in enumerate(medias):
                    markup.add(types.InlineKeyboardButton(text=f"Download {item.get('quality', 'HD')}", callback_data=f"dl_{index}_{chat_id}"))
                    valid_links[index] = {"url": item.get('url'), "type": item.get('format')}
                user_data_storage[chat_id] = valid_links
                bot.edit_message_text("Instagram Media ရွေးချယ်ပါ -", chat_id, msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ Media ရှာမတွေ့ပါ။", chat_id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", chat_id, msg.message_id)

    # ၂။ YouTube Logic
    elif "youtube.com" in url or "youtu.be" in url:
        msg = bot.reply_to(message, "⏳ YouTube Video ရှာနေပါတယ်...")
        try:
            response = requests.get(f"https://{YT_HOST}/v2/video/details", headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": YT_HOST}, params={"url": url})
            result = response.json()
            video_url = result.get('videos', {}).get('items', [{}])[0].get('url')
            if video_url:
                bot.send_video(chat_id, video_url, caption="YouTube ✅")
                bot.delete_message(chat_id, msg.message_id)
            else:
                bot.edit_message_text("❌ YouTube Link ရှာမတွေ့ပါ။", chat_id, msg.message_id)
        except:
            bot.edit_message_text("❌ YouTube API Error!", chat_id, msg.message_id)

    # ၃။ Pinterest Logic
    elif "pinterest.com" in url or "pin.it" in url:
        msg = bot.reply_to(message, "⏳ Pinterest Media ရှာနေပါတယ်...")
        try:
            response = requests.get(f"https://{PINTEREST_HOST}/pinterest", headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": PINTEREST_HOST}, params={"url": url})
            result = response.json()
            video_url = result.get('url') or result.get('data', {}).get('url')
            if video_url:
                if ".mp4" in video_url:
                    bot.send_video(chat_id, video_url, caption="Pinterest Video ✅")
                else:
                    bot.send_photo(chat_id, video_url, caption="Pinterest Image ✅")
                bot.delete_message(chat_id, msg.message_id)
            else:
                bot.edit_message_text("❌ Pinterest ရှာမတွေ့ပါ။", chat_id, msg.message_id)
        except:
            bot.edit_message_text("❌ Pinterest Error!", chat_id, msg.message_id)

    # ၄။ TikTok/Rednote Logic
    elif any(domain in url for domain in ["tiktok.com", "rednote.com", "xhslink.com", "xiaohongshu.com"]):
        msg = bot.reply_to(message, "⏳ Processing TikTok/Rednote...")
        try:
            response = requests.post(f"https://{UNIVERSAL_HOST}/parse", json={"url": url}, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": UNIVERSAL_HOST, "content-type": "application/json"})
            result = response.json()
            if result.get('success'):
                medias = result['data'].get('medias', [])
                markup = types.InlineKeyboardMarkup()
                valid_links = {}
                for index, item in enumerate(medias):
                    markup.add(types.InlineKeyboardButton(text=f"Download {item.get('quality', 'HD')}", callback_data=f"dl_{index}_{chat_id}"))
                    valid_links[index] = {"url": item.get('url'), "type": item.get('format')}
                user_data_storage[chat_id] = valid_links
                bot.edit_message_text("Quality ရွေးချယ်ပါ -", chat_id, msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ API Error!", chat_id, msg.message_id)
        except:
            bot.edit_message_text("❌ Connection Error!", chat_id, msg.message_id)
    
    else:
        bot.reply_to(message, "ဒီ Link ကို Bot က နားမလည်ပါဘူး။ (TikTok, IG, Pinterest, YouTube) ပဲ ပို့ပေးပါ။")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def callback_download(call):
    try:
        # callback_data: dl_{index}_{chat_id}
        data_parts = call.data.split('_')
        index = int(data_parts[1])
        chat_id = int(data_parts[2])

        if chat_id in user_data_storage and index in user_data_storage[chat_id]:
            media = user_data_storage[chat_id][index]
            bot.answer_callback_query(call.id, "ပို့ပေးနေပြီ...")
            if media["type"] == 'mp4':
                bot.send_video(chat_id, media["url"], caption="Done! ✅")
            else:
                bot.send_photo(chat_id, media["url"], caption="Done! ✅")
        else:
            bot.answer_callback_query(call.id, "Error: Link Expired! ကျေးဇူးပြု၍ လင့်ပြန်ပို့ပါ။", show_alert=True)
    except Exception as e:
        print(f"Callback Error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

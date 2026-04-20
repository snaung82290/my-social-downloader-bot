import telebot
import requests
import os
import yt_dlp
from flask import Flask
from threading import Thread
from telebot import types

# --- ၁။ Render အတွက် Web Server ---
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

# --- ၂။ Bot Setting ---
BOT_TOKEN = '8772824284:AAHq3om8lFd4QhoJW_ortNc3Hu8VVCs4FLc'
bot = telebot.TeleBot(BOT_TOKEN)

RAPIDAPI_KEY = "81af0e4596msh99a544721cd6043p12ea14jsn9e95af1e2351"
UNIVERSAL_HOST = "universal-social-media-downloader-api.p.rapidapi.com"
PINTEREST_HOST = "pinterest-video-and-image-downloader.p.rapidapi.com" 

user_data = {}

# --- ၃။ Bot Logic ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "TikTok, Pinterest, YouTube သို့မဟုတ် Rednote link ပို့ပေးပါ။ ✨")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    
    # YouTube Logic
    if "youtube.com" in url or "youtu.be" in url:
        msg = bot.reply_to(message, "⏳ YouTube Video ကို စစ်ဆေးနေပါတယ်...")
        try:
            ydl_opts = {'format': 'best', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                title = info.get('title', 'YouTube Video')
            if video_url:
                bot.send_video(message.chat.id, video_url, caption=f"{title} ✅")
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ YouTube Link ရှာမတွေ့ပါ။", message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ YouTube Error: {str(e)}", message.chat.id, msg.message_id)

    # Pinterest Logic
    elif "pinterest.com" in url or "pin.it" in url:
        msg = bot.reply_to(message, "⏳ Pinterest Media ကို ရှာဖွေနေပါတယ်...")
        api_url = f"https://{PINTEREST_HOST}/pinterest"
        try:
            response = requests.get(api_url, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": PINTEREST_HOST}, params={"url": url})
            result = response.json()
            video_url = result.get('url') or result.get('data', {}).get('url')
            if video_url:
                if ".mp4" in video_url:
                    bot.send_video(message.chat.id, video_url, caption="Pinterest Video ✅")
                else:
                    bot.send_photo(message.chat.id, video_url, caption="Pinterest Image ✅")
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Pinterest Media ရှာမတွေ့ပါ။", message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Pinterest Error: {str(e)}", message.chat.id, msg.message_id)

    # TikTok/Rednote Logic
    elif any(domain in url for domain in ["tiktok.com", "rednote.com", "xhslink.com"]):
        msg = bot.reply_to(message, "⏳ Link ကို စစ်ဆေးနေပါတယ်...")
        try:
            response = requests.post(f"https://{UNIVERSAL_HOST}/parse", json={"url": url}, headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": UNIVERSAL_HOST, "content-type": "application/json"})
            result = response.json()
            if result.get('success') and 'data' in result:
                medias = result['data'].get('medias', [])
                markup = types.InlineKeyboardMarkup()
                valid_links = {}
                for index, item in enumerate(medias):
                    label = f"{item.get('format', 'media').upper()} - {item.get('quality', 'HD')}"
                    markup.add(types.InlineKeyboardButton(text=label, callback_data=f"dl_{index}_{message.chat.id}"))
                    valid_links[index] = {"url": item.get('url'), "type": item.get('format')}
                user_data[message.chat.id] = valid_links
                bot.edit_message_text("Media Quality ရွေးချယ်ပါ -", message.chat.id, msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ အချက်အလက် မရရှိနိုင်ပါ။", message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def callback_download(call):
    try:
        _, index, chat_id = call.data.split('_')
        index, chat_id = int(index), int(chat_id)
        if chat_id in user_data and index in user_data[chat_id]:
            media = user_data[chat_id][index]
            bot.answer_callback_query(call.id, "ပို့ပေးနေပြီ...")
            if media["type"] == 'mp4':
                bot.send_video(chat_id, media["url"], caption="Done! ✅")
            else:
                bot.send_photo(chat_id, media["url"], caption="Done! ✅")
    except:
        bot.answer_callback_query(call.id, "Link သက်တမ်းကုန်သွားပါပြီ။", show_alert=True)

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)

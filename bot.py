import telebot
import requests

# သင်၏ Bot Token ကို ထည့်ပါ
BOT_TOKEN = '8772824284:AAHq3om8lFd4QhoJW_ortNc3Hu8VVCs4FLc' 
bot = telebot.TeleBot(BOT_TOKEN)

RAPIDAPI_KEY = "81af0e4596msh99a544721cd6043p12ea14jsn9e95af1e2351"
RAPIDAPI_HOST = "universal-social-media-downloader-api.p.rapidapi.com"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "TikTok, Pinterest, Rednote link များ ပို့ပေးနိုင်ပါပြီ။ 🤖")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "http" in url:
        msg = bot.reply_to(message, "⏳ Video ကို ပြင်ဆင်နေပါတယ်...")
        
        api_url = "https://universal-social-media-downloader-api.p.rapidapi.com/parse"
        payload = { "url": url }
        headers = {
            "content-type": "application/json",
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            result = response.json()

            # Screenshot အရ ဗီဒီယို link ကို ရှာပုံဖော်ခြင်း
            video_url = None
            if result.get('success') and 'data' in result:
                medias = result['data'].get('medias', [])
                for item in medias:
                    # format က mp4 ဖြစ်တဲ့ link ကို ရှာယူမယ်
                    if item.get('format') == 'mp4':
                        video_url = item.get('url')
                        break

            if video_url:
                bot.send_video(message.chat.id, video_url, caption="Done! ✅")
                bot.delete_message(message.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Video link ကို ရှာမတွေ့ပါ။", message.chat.id, msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ Error ဖြစ်သွားပါတယ်: {str(e)}", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "ကျေးဇူးပြု၍ Link အမှန် ပို့ပေးပါ။")

print("Bot is running...")
bot.polling(none_stop=True)
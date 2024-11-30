from pyrogram import filters
from devgagan import app
from devgagan.core import script
from devgagan.core.func import subscribe
from config import OWNER_ID
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ------------------- Start-Buttons ------------------- #

buttons = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("🎯 Join Channel", url="https://t.me/targetallcourse")],
        [InlineKeyboardButton("💎 Buy Premium", url="https://t.me/Free_course2_bot")]
    ]
)

@app.on_message(filters.command("start"))
async def start(_, message):
    try:
        # Check subscription status before proceeding
        join = await subscribe(_, message)
        if join == 1:
            return

        # Stylish Caption with emojis and formatting
        caption = f"""
        👋 **Hello {message.from_user.mention}, welcome to our bot!** 🎉

        🚀 **What can I do for you?** 
        - Join our amazing channel to access exclusive content! 🎯
        - Buy Premium for extra benefits and features! 💎

        📩 Click the buttons below to get started! ⬇️
        """

        # Send a welcome message with a photo and inline buttons
        await message.reply_photo(
            photo="https://iili.io/2B1dGlR.md.jpg",  # Ensure the URL works
            caption=caption, 
            reply_markup=buttons
        )
    except Exception as e:
        # Handle any errors that occur during the process
        await message.reply_text(f"Oops! Something went wrong. Error: {str(e)} 😞")

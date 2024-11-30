from pyrogram import filters, Client
from devgagan import app
from devgagan.core import script
from devgagan.core.func import subscribe, chk_user
from config import API_ID as api_id, API_HASH as api_hash
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait
)
import os
import random
import string
from devgagan.core.mongo import db
from pyrogram.types import Message


# -------------------- Helper Functions ------------------- #
def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


async def delete_session_files(user_id):
    session_file = f"session_{user_id}.session"
    memory_file = f"session_{user_id}.session-journal"

    # Check if the session or memory file exists
    session_file_exists = os.path.exists(session_file)
    memory_file_exists = os.path.exists(memory_file)

    # Delete the session files from disk and database if they exist
    if session_file_exists:
        os.remove(session_file)
    
    if memory_file_exists:
        os.remove(memory_file)

    # Remove session from database
    if session_file_exists or memory_file_exists:
        await db.delete_session(user_id)
        return True  # Files were deleted
    return False  # No files found


# -------------------- Commands ---------------------------- #
@app.on_message(filters.command("logout"))
async def clear_db(client, message: Message):
    user_id = message.chat.id
    files_deleted = await delete_session_files(user_id)

    # Notify user whether their session was cleared
    if files_deleted:
        await message.reply("✅ Your session data and files have been cleared from memory and disk.")
    else:
        await message.reply("⚠️ You are not logged in, no session data found.")


@app.on_message(filters.command("login"))
async def generate_session(_, message: Message):
    # Ensure the user is subscribed before logging in
    joined = await subscribe(_, message)
    if joined == 1:
        return

    # Generate session if user is not logged in
    user_id = message.chat.id   

    # Ask for phone number input from the user
    number = await _.ask(user_id, 'Please enter your phone number along with the country code. \nExample: +19876543210', filters=filters.text)   
    phone_number = number.text

    try:
        # Send OTP to the provided phone number
        await message.reply("📲 Sending OTP...")
        client = Client(f"session_{user_id}", api_id, api_hash)
        await client.connect()
    except Exception as e:
        await message.reply(f"❌ Failed to send OTP: {e}. Please try again later.")
        return

    try:
        # Sending the OTP code to the user
        code = await client.send_code(phone_number)
    except ApiIdInvalid:
        await message.reply('❌ Invalid combination of API ID and API HASH. Please restart the session.')
        return
    except PhoneNumberInvalid:
        await message.reply('❌ Invalid phone number. Please restart the session.')
        return

    try:
        # Ask for the OTP input from the user
        otp_code = await _.ask(user_id, "Please enter the OTP you received in your Telegram account.", filters=filters.text, timeout=600)
    except TimeoutError:
        await message.reply('⏰ Time limit of 10 minutes exceeded. Please restart the session.')
        return

    phone_code = otp_code.text.replace(" ", "")

    try:
        # Try signing in with the OTP
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await message.reply('❌ Invalid OTP. Please restart the session.')
        return
    except PhoneCodeExpired:
        await message.reply('❌ OTP expired. Please restart the session.')
        return
    except SessionPasswordNeeded:
        # Handle two-step verification if enabled
        try:
            two_step_msg = await _.ask(user_id, 'Your account has two-step verification enabled. Please enter your password.', filters=filters.text, timeout=300)
        except TimeoutError:
            await message.reply('⏰ Time limit of 5 minutes exceeded. Please restart the session.')
            return
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply('❌ Invalid password. Please restart the session.')
            return

    # Successfully logged in, export session string
    string_session = await client.export_session_string()

    # Save session in the database
    await db.set_session(user_id, string_session)

    # Disconnect the client
    await client.disconnect()

    # Notify the user of successful login
    await otp_code.reply("✅ Login successful! ab process kro /batch")

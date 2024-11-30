from pyrogram import filters, Client
from devgagan import app
from pyromod import listen
import random
import os
import string
from devgagan.core.mongo import db
from devgagan.core.func import subscribe
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

# Generate a random name (utility function)
def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Function to delete session files and database entries
async def delete_session_files(user_id):
    session_file = f"session_{user_id}.session"
    memory_file = f"session_{user_id}.session-journal"

    session_file_exists = os.path.exists(session_file)
    memory_file_exists = os.path.exists(memory_file)

    if session_file_exists:
        os.remove(session_file)
        print(f"🗑️ Deleted session file for user: {user_id}")
    
    if memory_file_exists:
        os.remove(memory_file)
        print(f"🗑️ Deleted memory file for user: {user_id}")

    # Delete session from the database
    if session_file_exists or memory_file_exists:
        try:
            await db.delete_session(user_id)
            print(f"✅ Session deleted from database for user: {user_id}")
        except Exception as e:
            print(f"❌ Failed to delete session from database for user: {user_id}, Error: {e}")
        return True
    return False

# Logout command handler
@app.on_message(filters.command("logout"))
async def clear_db(client, message):
    user_id = message.chat.id
    files_deleted = await delete_session_files(user_id)

    if files_deleted:
        await message.reply("✅ You have been logged out. Your session data and files have been cleared.")
    else:
        await message.reply("⚠️ You are not logged in, no session data found.")

# Login command handler
@app.on_message(filters.command("login"))
async def generate_session(_, message):
    joined = await subscribe(_, message)
    if joined == 1:
        return

    user_id = message.chat.id

    # Check if session already exists
    try:
        existing_session = await db.get_session(user_id)
        if existing_session:
            await message.reply("✅ You are already logged in. Use /logout if you want to end the session.")
            return
    except Exception as e:
        await message.reply(f"❌ Error checking existing session: {e}")
        return

    # Ask for phone number
    number = await _.ask(
        user_id,
        "Please enter your phone number along with the country code.\nExample: +19876543210",
        filters=filters.text
    )
    phone_number = number.text.strip()

    try:
        await message.reply("📲 Sending OTP...")
        client = Client(f"session_{user_id}", api_id, api_hash)
        await client.connect()
        code = await client.send_code(phone_number)
    except ApiIdInvalid:
        await message.reply("❌ Invalid API ID/API HASH. Please restart the session.")
        return
    except PhoneNumberInvalid:
        await message.reply("❌ Invalid phone number. Please restart the session.")
        return
    except Exception as e:
        await message.reply(f"❌ Failed to send OTP: {e}. Please try again later.")
        return

    # Ask for OTP
    try:
        otp_code = await _.ask(
            user_id,
            "Please enter the OTP received on your Telegram account. Format: `1 2 3 4 5`.",
            filters=filters.text,
            timeout=600
        )
    except TimeoutError:
        await message.reply("⏰ Time limit of 10 minutes exceeded. Please restart the session.")
        return

    phone_code = otp_code.text.replace(" ", "")

    # Verify OTP
    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await message.reply("❌ Invalid OTP. Please restart the session.")
        return
    except PhoneCodeExpired:
        await message.reply("❌ Expired OTP. Please restart the session.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_msg = await _.ask(
                user_id,
                "Your account has two-step verification enabled. Please enter your password.",
                filters=filters.text,
                timeout=300
            )
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply("❌ Invalid password. Please restart the session.")
            return
        except TimeoutError:
            await message.reply("⏰ Time limit of 5 minutes exceeded. Please restart the session.")
            return

    # Export session string
    try:
        string_session = await client.export_session_string()
        await db.set_session(user_id, string_session)
        await otp_code.reply("✅ Login successful! Your session is now active.")
    except Exception as e:
        await message.reply(f"❌ Failed to save session: {e}")
    finally:
        await client.disconnect()

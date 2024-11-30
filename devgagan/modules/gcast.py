import asyncio
from pyrogram import filters
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid,
)
from config import OWNER_ID
from devgagan import app
from devgagan.core.mongo.users_db import get_users


async def send_msg(user_id, message):
    """
    Sends a message to a user and handles common exceptions.
    """
    try:
        await message.copy(chat_id=user_id)
        return 200, f"{user_id} : success\n"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception as e:
        return 500, f"{user_id} : {str(e)}\n"


@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(_, message):
    """
    Broadcasts a message to all users in the database.
    """
    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to broadcast it.")
        return
    
    exmsg = await message.reply_text("Broadcasting started...")
    all_users = await get_users() or []
    done_users, failed_users = 0, 0
    failed_logs = []

    for user in all_users:
        status, log = await send_msg(user, message.reply_to_message)
        if status == 200:
            done_users += 1
        else:
            failed_users += 1
            failed_logs.append(log)
        await asyncio.sleep(0.1)  # To avoid hitting rate limits

    # Final report
    report = (
        f"**Broadcast Complete ✅**\n\n"
        f"**Successful:** `{done_users}` users\n"
        f"**Failed:** `{failed_users}` users"
    )
    await exmsg.edit_text(report)

    # Log failed users to a file
    if failed_logs:
        with open("failed_users.txt", "w") as f:
            f.writelines(failed_logs)


@app.on_message(filters.command("announce") & filters.user(OWNER_ID))
async def announced(_, message):
    """
    Forwards a message to all users in the database.
    """
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to broadcast it.")
        return
    
    to_send = message.reply_to_message.id
    users = await get_users() or []
    failed_users = 0
    success_users = 0
    failed_logs = []

    for user in users:
        try:
            await _.forward_messages(chat_id=int(user), from_chat_id=message.chat.id, message_ids=to_send)
            success_users += 1
        except Exception as e:
            failed_users += 1
            failed_logs.append(f"{user}: {str(e)}\n")
        await asyncio.sleep(1)  # To avoid hitting rate limits

    # Final report
    report = (
        f"**Announcement Complete ✅**\n\n"
        f"**Successful:** `{success_users}` users\n"
        f"**Failed:** `{failed_users}` users"
    )
    await message.reply_text(report)

    # Log failed users to a file
    if failed_logs:
        with open("announce_failed_users.txt", "w") as f:
            f.writelines(failed_logs)

import asyncio
import re
import ast
import math
import random

import datetime 
import psutil
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import LANGUAGES, IMDB_DLT_TIME, BOT_START_TIME, MAX_BTN, ADMINS, AUTH_CHANNEL, AUTH_USERS, SUPPORT_CHAT_ID, CUSTOM_FILE_CAPTION, MSG_ALRT, PICS, AUTH_GROUPS, P_TTI_SHOW_OFF, NOR_IMG, LOG_CHANNEL, MAX_B_TN, IMDB, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, NO_RESULTS_MSG, REQ_CHANNEL, MAIN_CHANNEL, FILE_CHANNEL, CLOSE_IMG, DELETE_TIME, LOGIN_CHANNEL, SP, FILE_FORWARD
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatPermissions
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, get_shortlink, mute_login
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results, get_bad_files
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import (
    find_gfilter,
    get_gfilters,
    del_allg
)
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}

#@Client.on_message(filters.private & filters.text & filters.incoming & filters.user(AUTH_USERS) if AUTH_USERS else filters.private & filters.text & filters.incoming)
#async def pv_filter(client, message):
    #kd = await global_filters(client, message)
    #if kd == False:
        #await auto_filter(client, message)

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    content = message.text
    settings = await get_settings(message.chat.id)        
    if settings["auto_ffilter"]:
        userid = message.from_user.id if message.from_user else None
        if not userid:
            search = message.text
            k = await message.reply(f"You'r anonymous admin! Sorry you can't get '{search}' from here.\nYou can get '{search}' from bot inline search.")
            await asyncio.sleep(30)
            await k.delete()
            try:
                await message.delete()
            except:
                pass
            return

        if AUTH_CHANNEL and not await is_subscribed(client, message):
            try:
                invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
            except ChatAdminRequired:
                logger.error("Make sure Bot is admin in Forcesub channel")
                return
            buttons = [[
                InlineKeyboardButton("📢 𝐉𝐨𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 📢", url=invite_link.invite_link)
            ],[
                InlineKeyboardButton("🔁 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐀𝐠𝐚𝐢𝐧 🔁", callback_data="grp_checksub")
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
#            try:
#                await client.restrict_chat_member(message.chat.id, message.from_user.id, ChatPermissions(), datetime.now() + timedelta(minutes=1))
#            except:
#                pass
            k = await message.reply_photo(
                photo=random.choice(SP),
                caption=f"👋 𝐇𝐞𝐥𝐥𝐨 {message.from_user.mention},\n\n{content} 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞..!!\n\n𝐏𝐥𝐞𝐚𝐬𝐞 𝐉𝐨𝐢𝐧 𝐌𝐲 '𝐔𝐩𝐝𝐚𝐭𝐞𝐬 𝐂𝐡𝐚𝐧𝐧𝐞𝐥' 𝐀𝐧𝐝 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐀𝐠𝐚𝐢𝐧. 😇",
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
            await asyncio.sleep(300)
            await k.delete()
            try:
                await message.delete()
            except:
                pass
        else:
            await auto_filter(client, message)
    else:
        k = await message.reply_text(f"𝐇𝐞𝐥𝐥𝐨 {message.from_user.mention},\n\n{content} 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞..!! \n\n❌️𝐀𝐮𝐭𝐨 𝐅𝐢𝐥𝐭𝐞𝐫 𝐎𝐟𝐟..!!!❌️ \n𝐏𝐥𝐞𝐚𝐬𝐞 𝐖𝐚𝐢𝐭..")
        await asyncio.sleep(5)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
            return
        if message.chat.id != SUPPORT_CHAT_ID:
            await global_filters(client, message)
        manual = await manual_filters(client, message)
        if manual == False:
            settings = await get_settings(message.chat.id)
            try:
                if settings['auto_ffilter']:
                    await auto_filter(client, message)
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_ffilter', False)
                settings = await get_settings(message.chat.id)
                if settings['auto_ffilter']:
                    await auto_filter(client, message) 
                    try:
                        await message.delete()
                    except:
                        pass

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if content.startswith("/") or content.startswith("#"): return  # ignore commands and hashtags
    if user_id in ADMINS: return # ignore admins
    await message.reply_text(
         text="<b>ʜᴇʏ ᴅᴜᴅᴇ 😍 ,\n\nʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ᴍᴏᴠɪᴇs ꜰʀᴏᴍ ʜᴇʀᴇ. ʀᴇǫᴜᴇsᴛ ᴏɴ ᴏᴜʀ <a href=https://t.me/CinemaKovilakam_Group>ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ</a> ᴏʀ ᴄʟɪᴄᴋ ʀᴇǫᴜᴇsᴛ ʜᴇʀᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ​👇</b>",   
         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 ʀᴇǫᴜᴇsᴛ ʜᴇʀᴇ​ ", url=f"t.me/at3movies")]])
    )

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total = await get_search_results(query.message.chat.id, search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(query.message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    if ENABLE_SHORTLINK == True:
        if settings['button']:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"🔖 {get_size(file.file_size)}--💠--{file.file_name}", url=await get_shortlink(query.message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}", url=await get_shortlink(query.message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        url=await get_shortlink(query.message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
    else:
        if settings['button']:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"🔖 {get_size(file.file_size)}--💠--{file.file_name}", callback_data=f'files#{file.file_id}'
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        callback_data=f'files_#{file.file_id}',
                    ),
                ]
                for file in files
            ]
    try:
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )
                
    except KeyError:
        grpid = await active_connection(str(query.message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(query.message.chat.id)
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )
    try:
        settings = await get_settings(query.message.chat.id)
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
    except KeyError:
        await save_group_settings(query.message.chat.id, 'max_btn', False)
        settings = await get_settings(query.message.chat.id)
        if settings['max_btn']:
            if 0 < offset <= 10:
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - 10
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
        else:
            if 0 < offset <= int(MAX_B_TN):
                off_set = 0
            elif offset == 0:
                off_set = None
            else:
                off_set = offset - int(MAX_B_TN)
            if n_offset == 0:
                btn.append(
                    [InlineKeyboardButton("⇚ ʙᴀᴄᴋ​", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages")]
                )
            elif off_set is None:
                btn.append([InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"), InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")])
            else:
                btn.append(
                    [
                        InlineKeyboardButton("⇚ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                        InlineKeyboardButton(f"{math.ceil(int(offset)/int(MAX_B_TN))+1} / {math.ceil(total/int(MAX_B_TN))}", callback_data="pages"),
                        InlineKeyboardButton("ɴᴇxᴛ​⇛", callback_data=f"next_{req}_{key}_{n_offset}")
                    ],
                )
    btn.insert(0, [
        InlineKeyboardButton(f'🔍 {search} 🔎', 'reqst1')
    ])
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movie = movies[(int(movie_))]
    await query.answer(script.TOP_ALRT_MSG, show_alert=True)
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
        if files:
            await query.message.delete()
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:         
            reqstr1 = query.from_user.id if query.from_user else 0
            reqstr = await bot.get_users(reqstr1)
            if NO_RESULTS_MSG:
                await bot.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, movie)))
            k = await query.message.edit(script.MVE_NT_FND)
            await asyncio.sleep(10)
            await k.delete()

#languages

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):

    if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
        return await query.answer(
            f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
            show_alert=True,
        )
    
    _, search, key = query.data.split("#")

    btn = [
        [
            InlineKeyboardButton(
                text=lang.title(),
                callback_data=f"fl#{lang.lower()}#{search}#{key}"
                ),
        ]
        for lang in LANGUAGES
    ]

    btn.insert(
        0,
        [
            InlineKeyboardButton(
                text="👇 𝖲𝖾𝗅𝖾𝖼𝗍 𝖸𝗈𝗎𝗋 𝖫𝖺𝗇𝗀𝗎𝖺𝗀𝖾𝗌 👇", callback_data="ident"
            )
        ],
    )
    req = query.from_user.id
    offset = 0
    btn.append([InlineKeyboardButton(text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ​↭", callback_data=f"next_{req}_{key}_{offset}")])

    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    _, lang, search, key = query.data.split("#")

    search = search.replace("_", " ")
    req = query.from_user.id
    chat_id = query.message.chat.id
    message = query.message
    if int(req) not in [query.message.reply_to_message.from_user.id, 0]:
        return await query.answer(
            f"⚠️ ʜᴇʟʟᴏ{query.from_user.first_name},\nᴛʜɪꜱ ɪꜱ ɴᴏᴛ ʏᴏᴜʀ ᴍᴏᴠɪᴇ ʀᴇQᴜᴇꜱᴛ,\nʀᴇQᴜᴇꜱᴛ ʏᴏᴜʀ'ꜱ...",
            show_alert=True,
        )

    search = f"{search} {lang}" 

    files, _, _ = await get_search_results(chat_id, search, max_results=10)
    files = [file for file in files if re.search(lang, file.file_name, re.IGNORECASE)]
    if not files:
        await query.answer("🚫 𝗡𝗼 𝗙𝗶𝗹𝗲 𝗪𝗲𝗿𝗲 𝗙𝗼𝘂𝗻𝗱 🚫", show_alert=1)
        return

    settings = await get_settings(message.chat.id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    pre = 'filep' if settings['file_secure'] else 'file'
    if ENABLE_SHORTLINK == True:
        btn = (
            [
                [
                    InlineKeyboardButton(
                        text=f"🔖 {get_size(file.file_size)}--💠--{file.file_name}",
                        url=await get_shortlink(
                            message.chat.id,
                            f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}",
                        ),
                    ),
                ]
                for file in files
            ]
            if settings["button"]
            else [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}",
                        url=await get_shortlink(
                            message.chat.id,
                            f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}",
                        ),
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        url=await get_shortlink(
                            message.chat.id,
                            f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}",
                        ),
                    ),
                ]
                for file in files
            ]
        )
    elif settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🔖 {get_size(file.file_size)}--💠--{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'{pre}#{file.file_id}',
                ),
            ]
            for file in files
        ]
    try:
        if settings['auto_delete']:
            btn.insert(
                0,
                [
                    InlineKeyboardButton(f'♻️ ɪɴꜰᴏ', 'info'),
                    InlineKeyboardButton("ꜰᴏʀᴍᴀᴛ​", 'format'),
                    InlineKeyboardButton(f'ᴛɪᴘs​ ⚜', 'tips'),
                ],
            )

        else:
            btn.insert(
                0,
                [
                    InlineKeyboardButton(f'♻️ ɪɴꜰᴏ', 'info'),
                    InlineKeyboardButton("ꜰᴏʀᴍᴀᴛ​", 'format'),
                    InlineKeyboardButton(f'ᴛɪᴘs​ ⚜', 'tips'),
                ],
            )

    except KeyError:
        grpid = await active_connection(str(message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(message.chat.id)
        if settings['auto_delete']:
            btn.insert(
                0,
                [
                    InlineKeyboardButton(f'♻️ ɪɴꜰᴏ', 'info'),
                    InlineKeyboardButton("ꜰᴏʀᴍᴀᴛ​", 'format'),
                    InlineKeyboardButton(f'ᴛɪᴘs​ ⚜', 'tips'),
                ],
            )

        else:
            btn.insert(
                0,
                [
                    InlineKeyboardButton(f'♻️ ɪɴꜰᴏ', 'info'),
                    InlineKeyboardButton("ꜰᴏʀᴍᴀᴛ​", 'format'),
                    InlineKeyboardButton(f'ᴛɪᴘs​ ⚜', 'tips'),
                ],
            )

    btn.insert(0, [
        InlineKeyboardButton("💢 𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐆𝐫𝐨𝐮𝐩𝐬 💢", url=f'http://t.me/{temp.U_NAME}?startgroup=true')
    ])
    offset = 0

    btn.append(        [
            InlineKeyboardButton(
                text="↭ ʙᴀᴄᴋ ᴛᴏ ꜰɪʟᴇs ​↭",
                callback_data=f"next_{req}_{key}_{offset}"
                ),
        ])


    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))




#languages


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "gfiltersdeleteallconfirm":
        await del_allg(query.message, 'gfilters')
        await query.answer("Done !")
        return
    elif query.data == "gfiltersdeleteallcancel": 
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("Process Cancelled !")
        return
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Mᴀᴋᴇ sᴜʀᴇ I'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ!!", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text(
                    "I'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs!\nCʜᴇᴄᴋ /connections ᴏʀ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs",
                    quote=True
                )
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer(MSG_ALRT)

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("Yᴏᴜ ɴᴇᴇᴅ ᴛᴏ ʙᴇ Gʀᴏᴜᴘ Oᴡɴᴇʀ ᴏʀ ᴀɴ Aᴜᴛʜ Usᴇʀ ᴛᴏ ᴅᴏ ᴛʜᴀᴛ!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Tʜᴀᴛ's ɴᴏᴛ ғᴏʀ ʏᴏᴜ!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Gʀᴏᴜᴘ Nᴀᴍᴇ : **{title}**\nGʀᴏᴜᴘ ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Cᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Dɪsᴄᴏɴɴᴇᴄᴛᴇᴅ ғʀᴏᴍ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴄᴏɴɴᴇᴄᴛɪᴏɴ !"
            )
        else:
            await query.message.edit_text(
                f"Sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs!! Cᴏɴɴᴇᴄᴛ ᴛᴏ sᴏᴍᴇ ɢʀᴏᴜᴘs ғɪʀsᴛ.",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Yᴏᴜʀ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ᴅᴇᴛᴀɪʟs ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "gfilteralert" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        clicked = query.from_user.id #fetching the ID of the user who clicked the button
        try:
            typed = query.message.reply_to_message.from_user.id #fetching user ID of the user who sent the movie request
        except:
            typed = clicked #if failed, uses the clicked user's ID as requested user ID
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        username = query.message.from_user.first_name
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(temp.B_NAME,
                                                       user_name= '' if username is None else username,
                                                       file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            elif settings['botpm']:
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            else:
                if clicked == typed:
                    file_send=await client.send_cached_media(
                        chat_id=FILE_CHANNEL,
                        file_id=file_id,
                        caption=script.CHANNEL_CAP.format(query.from_user.mention, title, query.message.chat.title),
                        protect_content=True if ident == "filep" else False,
                        reply_markup=InlineKeyboardMarkup(
                             [
                                [
                                     InlineKeyboardButton('📤𝐉𝐨𝐢𝐧📤', url="https://t.me/+7oxSIxY4X0c2ZGVl")
                                 ],
                                 [
                                 InlineKeyboardButton('🧩𝐔𝐩𝐝𝐚𝐭𝐞🧩', url="https://t.me/bigmoviesworld"),
                                 InlineKeyboardButton('☘𝐒𝐮𝐩𝐩𝐨𝐫𝐭☘', url="https://t.me/NasraniChatGroup")
                                 ]                            
                             ]
                         )
                     )
                    Joel_tgx = await query.message.reply_text(
                        script.FILE_MSG.format(query.from_user.mention, title, size),
                        parse_mode=enums.ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(
                            [
                             [
                              InlineKeyboardButton('📥 𝖣𝗈𝗐𝗇𝗅𝗈𝖺𝖽 𝖫𝗂𝗇𝗄 📥 ', url = file_send.link)
                           ],[
                              InlineKeyboardButton("⚠️ 𝖢𝖺𝗇'𝗍 𝖠𝖼𝖼𝖾𝗌𝗌 ❓ 𝖢𝗅𝗂𝖼𝗄 𝖧𝖾𝗋𝖾 ⚠️", url=(FILE_FORWARD))
                             ]
                            ]
                        )
                    )
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await Joel_tgx.delete()
                        await file_send.delete()

                    k = await client.send_message(
                        chat_id=FILE_CHANNEL,                        
                        text=script.DONE_MSG.format(query.from_user.mention, title, size),
                        parse_mode=enums.ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton("🔥 ᴄʜᴀɴɴᴇʟ 🔥", url=(MAIN_CHANNEL))
                                ]
                            ]
                        )
                    )
                    await asyncio.sleep(180)
                    await k.delete()
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
                await query.answer('Cʜᴇᴄᴋ PM, I ʜᴀᴠᴇ sᴇɴᴛ ғɪʟᴇs ɪɴ PM', show_alert=True)
        except UserIsBlocked:
            await query.answer('𝐔𝐧𝐛𝐥𝐨𝐜𝐤 𝐭𝐡𝐞 𝐛𝐨𝐭 𝐦𝐚𝐡𝐧 !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("𝑰 𝑳𝒊𝒌𝒆 𝒀𝒐𝒖𝒓 𝑺𝒎𝒂𝒓𝒕𝒏𝒆𝒔𝒔, 𝑩𝒖𝒕 𝑫𝒐𝒏'𝒕 𝑩𝒆 𝑶𝒗𝒆𝒓𝒔𝒎𝒂𝒓𝒕 😒\n@𝒄𝒊𝒏𝒆𝒎𝒂𝒍𝒂.𝒄𝒐𝒎", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        username = query.message.from_user.first_name
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(temp.B_NAME,
                                                       user_name= '' if username is None else username,
                                                       file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )


    elif query.data.startswith("grp_checksub"):
        userid = query.message.reply_to_message.from_user.id
        if int(userid) not in [query.from_user.id, 0]:
            return await query.answer("This Is Not For You!", show_alert=True)
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Please join first my Updates Channel", show_alert=True)
            return
        await client.unban_chat_member(query.message.chat.id, query.from_user.id)
        await query.answer("Can You Request Now!", show_alert=True)
        await query.message.delete()
        await query.message.reply_to_message.delete()
                                                        



    elif query.data == "pages":
        await query.answer()

    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Tʜᴇ Rɪɢʜᴛs Tᴏ Dᴏ Tʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons =  [
            [
                InlineKeyboardButton(
                    'Fɪʟᴛᴇʀ Bᴜᴛᴛᴏɴ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Sɪɴɢʟᴇ' if settings["button"] else 'Dᴏᴜʙʟᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Fɪʟᴇ Mᴏᴅᴇ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Sᴛᴀʀᴛ' if settings["botpm"] else 'Cʜᴀɴɴᴇʟ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Fɪʟᴇ Sᴇᴄᴜʀᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["file_secure"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Iᴍᴅʙ Pᴏsᴛᴇʀ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["imdb"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Sᴘᴇʟʟ Cʜᴇᴄᴋ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["spell_check"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Wᴇʟᴄᴏᴍᴇ Msɢ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["welcome"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Aᴜᴛᴏ Fɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["auto_ffilter"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Aᴜᴛᴏ Dᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["auto_delete"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Mᴀx Bᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'SʜᴏʀᴛLɪɴᴋ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["is_shortlink"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('✘ Cʟᴏsᴇ ✘', callback_data='close_data')
            ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>Cᴜʀʀᴇɴᴛ Sᴇᴛᴛɪɴɢs Fᴏʀ {title}\n\nYᴏᴜ Cᴀɴ Cʜᴀɴɢᴇ Sᴇᴛᴛɪɴɢs As Yᴏᴜʀ Wɪsʜ Bʏ Usɪɴɢ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴs.</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)
        
    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Tʜᴇ Rɪɢʜᴛs Tᴏ Dᴏ Tʜɪs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("‼️ Go To The Chat ‼️", url=f"t.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>Sᴇᴛᴛɪɴɢꜱ Mᴇɴᴜ Sᴇɴᴛ Iɴ Pʀɪᴠᴀᴛᴇ Cʜᴀᴛ ✅</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons =  [
            [
                InlineKeyboardButton(
                    'Fɪʟᴛᴇʀ Bᴜᴛᴛᴏɴ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Sɪɴɢʟᴇ' if settings["button"] else 'Dᴏᴜʙʟᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Fɪʟᴇ Mᴏᴅᴇ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Sᴛᴀʀᴛ' if settings["botpm"] else 'Cʜᴀɴɴᴇʟ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Fɪʟᴇ Sᴇᴄᴜʀᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["file_secure"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Iᴍᴅʙ Pᴏsᴛᴇʀ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["imdb"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Sᴘᴇʟʟ Cʜᴇᴄᴋ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["spell_check"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Wᴇʟᴄᴏᴍᴇ Msɢ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["welcome"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Aᴜᴛᴏ Fɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["auto_ffilter"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Aᴜᴛᴏ Dᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["auto_delete"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Mᴀx Bᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'SʜᴏʀᴛLɪɴᴋ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["is_shortlink"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('✘ Cʟᴏsᴇ ✘', callback_data='close_data')
            ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>Cᴜʀʀᴇɴᴛ Sᴇᴛᴛɪɴɢs Fᴏʀ {title}\n\nYᴏᴜ Cᴀɴ Cʜᴀɴɢᴇ Sᴇᴛᴛɪɴɢs As Yᴏᴜʀ Wɪsʜ Bʏ Usɪɴɢ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴs.</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("Uɴᴀᴠᴀɪʟᴀʙʟᴇ", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("Uᴘʟᴏᴀᴅᴇᴅ", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ", callback_data=f"already_available#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Hᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴs !")
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("⚠️ Uɴᴀᴠᴀɪʟᴀʙʟᴇ ⚠️", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uɴᴀᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Hᴇʏ {user.mention}, Sᴏʀʀʏ Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Hᴇʏ {user.mention}, Sᴏʀʀʏ Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ. Sᴏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴄᴀɴ'ᴛ ᴜᴘʟᴏᴀᴅ ɪᴛ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("✅ Uᴘʟᴏᴀᴅᴇᴅ ✅", callback_data=f"upalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Uᴘʟᴏᴀᴅᴇᴅ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ʜᴀs ʙᴇᴇɴ ᴜᴘʟᴏᴀᴅᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("🟢 Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ 🟢", callback_data=f"alalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("Vɪᴇᴡ Sᴛᴀᴛᴜs", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sᴇᴛ ᴛᴏ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴏᴜʀ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Hᴇʏ {user.mention}, Yᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴏᴜʀ ʙᴏᴛ's ᴅᴀᴛᴀʙᴀsᴇ. Kɪɴᴅʟʏ sᴇᴀʀᴄʜ ᴀɢᴀɪɴ.\n\nNᴏᴛᴇ: Tʜɪs ᴍᴇssᴀɢᴇ ɪs sᴇɴᴛ ᴛᴏ ᴛʜɪs ɢʀᴏᴜᴘ ʙᴇᴄᴀᴜsᴇ ʏᴏᴜ'ᴠᴇ ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ. Tᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ʏᴏᴜʀ PM, Mᴜsᴛ ᴜɴʙʟᴏᴄᴋ ᴛʜᴇ ʙᴏᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Uᴘʟᴏᴀᴅᴇᴅ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)
        
    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hᴇʏ {user.first_name}, Yᴏᴜʀ Rᴇᴏ̨ᴜᴇsᴛ ɪs Uɴᴀᴠᴀɪʟᴀʙʟᴇ !", show_alert=True)
        else:
            await query.answer("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ sᴜғғɪᴄɪᴀɴᴛ ʀɪɢᴛs ᴛᴏ ᴅᴏ ᴛʜɪs !", show_alert=True)

    elif query.data == "info":
        await query.answer(text=script.INFO, show_alert=True)

    elif query.data == "format":
        await query.answer(text=script.FORMAT, show_alert=True)
        
    elif query.data == "rendering_info":
        await query.answer(text=script.RENDERING_TXT, show_alert=True)

    elif query.data == "tips":
        await query.answer(text=script.TIPS, show_alert=True)

    elif query.data == "whyjoin":
        await query.answer(text=script.WHYJOIN, show_alert=True)

    elif query.data == "delf":
        await query.answer(text=script.DELF, show_alert=True)
        
    elif query.data == "help":
        await query.answer(text=script.HELP_TXT, show_alert=True)
     
    elif query.data == "malayalam":
        await query.answer(text=script.MALAYALAM_TXT, show_alert=True)

    elif query.data == "hindi":
        await query.answer(text=script.HINDI_TXT, show_alert=True)

    elif query.data == "tamil":
        await query.answer(text=script.TAMIL_TXT, show_alert=True)

    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('〆 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ 〆', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],[
            InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ​', switch_inline_query_current_chat=''),
            InlineKeyboardButton('👨‍💻 ᴅᴇᴠ​', callback_data='owner_info')
            ],[      
            InlineKeyboardButton('🎭 ʜᴇʟᴘ 🎭', callback_data='help2'),
            InlineKeyboardButton('♻️ ᴀʙᴏᴜᴛ ♻️', callback_data='about')
            ],[
            InlineKeyboardButton('💰 ᴇᴀʀɴ ᴍᴏɴᴇʏ ᴡɪᴛʜ ʙᴏᴛ 💸', callback_data='money_bot')
        ]] 
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer(MSG_ALRT)
        
    elif query.data == "filters":
        buttons = [[
            InlineKeyboardButton('ᴍᴀɴᴜᴀʟ ꜰɪʟᴛᴇʀ', callback_data='manuelfilter'),
            InlineKeyboardButton('ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ', callback_data='autofilter')
        ],[
            InlineKeyboardButton('⇍ʙᴀᴄᴋ', callback_data='help2'),
            InlineKeyboardButton('ɢʟᴏʙᴀʟ ꜰɪʟᴛᴇʀs​', callback_data='global_filters')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ALL_FILTERS.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "global_filters":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "owner_info":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('✧ ᴄᴏɴᴛᴀᴄᴛ​', url='t.me/af_x_su')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.OWNER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "money_bot":
        buttons = [[
            InlineKeyboardButton('ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ', url='https://t.me/MLZ_BOTZ_SUPPORT')
        ],[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ', callback_data='start'),
            InlineKeyboardButton('ᴄʟᴏsᴇ ⊝', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.EARN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "dics_btn":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.DISC_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "setting_btn":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help2')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SETTING_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rule_btn":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help2')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.RULE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "help2":
        buttons = [[
            InlineKeyboardButton('🍷 ᴄʟᴏɴᴇ 🍷', callback_data='help')
        ], [
            InlineKeyboardButton('∙ ꜰɪʟᴛᴇʀs ∙', callback_data='filters'),
            InlineKeyboardButton('∙ ꜰɪʟᴇ sᴛᴏʀᴇ ∙', callback_data='store_file')
        ], [
            InlineKeyboardButton('∙ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ∙', callback_data='coct'),
            InlineKeyboardButton('∙ ᴇxᴛʀᴀ ᴍᴏᴅs ∙', callback_data='extra')
        ], [
            InlineKeyboardButton('∙ ʀᴜʟᴇs ∙', callback_data='rule_btn'),
            InlineKeyboardButton('∙ sᴇᴛᴛɪɴɢs ∙', callback_data='setting_btn')
        ], [
            InlineKeyboardButton('⇌ ʙᴀᴄᴋ ⇌', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.HELPER_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('sᴛᴀᴛᴜs​', callback_data='stats'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ​', callback_data='source')
        ],[
            InlineKeyboardButton('🛰 ʀᴇɴᴅᴇʀɪɴɢ ɪɴꜰᴏ ☁️', callback_data='rendering_info')
        ],[            
            InlineKeyboardButton('© ᴅɪsᴄʟᴀɪᴍᴇʀ​ ©', callback_data='dics_btn')
        ],[
            InlineKeyboardButton('♙ ʜᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('ᴄʟᴏsᴇ ⊝', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('⇍ʙᴀᴄᴋ', callback_data='filters'),
            InlineKeyboardButton('Bᴜᴛᴛᴏɴs', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='manuelfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help2')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help2')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "store_file":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='help2')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILE_STORE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('⇍ ʙᴀᴄᴋ ⇏', callback_data='owner_info')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        if query.from_user.id in ADMINS:
            await query.message.edit_text(text=script.ADMIN_TXT, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            await query.answer("⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nIᴛꜱ ᴏɴʟʏ ғᴏʀ ᴍʏ ADMINS\n\n©ᴍʟᴢ ʙᴏᴛᴢ", show_alert=True)

    elif query.data == "stats":
        buttons = [[           
            InlineKeyboardButton('⇍Bᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('⟲ Rᴇғʀᴇsʜ', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons) 
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )    
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[            
            InlineKeyboardButton('⇍Bᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('⟲ Rᴇғʀᴇsʜ', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons) 
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        ) 
        
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "predvd":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'predvd',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('PreDVD File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} PʀᴇDVD Fɪʟᴇs.</b>")

    elif query.data == "camrip":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'camrip',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('CamRip File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} CᴀᴍRɪᴘ Fɪʟᴇs.</b>")

    elif query.data == "predvdrip":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'Predvdrip',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('PreDVDRip File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} PʀᴇDVDRɪᴘ Fɪʟᴇs.</b>")

    elif query.data == "hdcam":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'HDCam',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('HDCams File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} HDCᴀᴍ Fɪʟᴇs.</b>")

    elif query.data == "hdcams":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'HD-Cam',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('HD-Cams File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} HD-Cᴀᴍ Fɪʟᴇs.</b>")

    elif query.data == "sprint":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'S-print',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('S-Print File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} S-Pʀɪɴᴛ Fɪʟᴇs.</b>")

    elif query.data == "hdts":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'HDTS',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('HDTS File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} HDTS Fɪʟᴇs.</b>")

    elif query.data == "hdtss":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Dᴇʟᴇᴛɪɴɢ...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'HD-TS',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('HD-TS File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ Dᴇʟᴇᴛᴇᴅ {deleted} HD-TS Fɪʟᴇs.</b>")
        
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Yᴏᴜʀ Aᴄᴛɪᴠᴇ Cᴏɴɴᴇᴄᴛɪᴏɴ Hᴀs Bᴇᴇɴ Cʜᴀɴɢᴇᴅ. Gᴏ Tᴏ /connections ᴀɴᴅ ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ.")
            return await query.answer(MSG_ALRT)

        #"if set_type == 'is_shortlink' and query.from_user.id not in ADMINS:
            #"return await query.answer(text=f"Hey {query.from_user.first_name}, You can't change shortlink settings for your group !\n\nIt's an admin only setting !", show_alert=True)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons =  [
            [
                InlineKeyboardButton(
                    'Fɪʟᴛᴇʀ Bᴜᴛᴛᴏɴ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Sɪɴɢʟᴇ' if settings["button"] else 'Dᴏᴜʙʟᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Fɪʟᴇ Mᴏᴅᴇ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Sᴛᴀʀᴛ' if settings["botpm"] else 'Cʜᴀɴɴᴇʟ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Fɪʟᴇ Sᴇᴄᴜʀᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["file_secure"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Iᴍᴅʙ Pᴏsᴛᴇʀ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["imdb"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Sᴘᴇʟʟ Cʜᴇᴄᴋ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["spell_check"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Wᴇʟᴄᴏᴍᴇ Msɢ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["welcome"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Aᴜᴛᴏ Fɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["auto_ffilter"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Aᴜᴛᴏ Dᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["auto_delete"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Mᴀx Bᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'SʜᴏʀᴛLɪɴᴋ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Eɴᴀʙʟᴇ' if settings["is_shortlink"] else 'Dɪsᴀʙʟᴇ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('✘ Cʟᴏsᴇ ✘', callback_data='close_data')
            ]
        ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)

    
async def auto_filter(client, msg, spoll=False):
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)

    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(message.chat.id ,search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    if NO_RESULTS_MSG:
                        await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, search)))
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    settings = await get_settings(message.chat.id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    pre = 'filep' if settings['file_secure'] else 'file'
    if ENABLE_SHORTLINK == True:
        if settings["button"]:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"🔖 {get_size(file.file_size)}--💠--{file.file_name}", url=await get_shortlink(message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}",
                        url=await get_shortlink(message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        url=await get_shortlink(message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
    else:
        if settings["button"]:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"🔖 {get_size(file.file_size)}--💠--{file.file_name}", callback_data=f'{pre}#{file.file_id}'
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}",
                        callback_data=f'{pre}#{file.file_id}',
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        callback_data=f'{pre}#{file.file_id}',
                    ),
                ]
                for file in files
            ]

    try:
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )
                
    except KeyError:
        grpid = await active_connection(str(message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(message.chat.id)
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'🗂 ꜰɪʟᴇs: {len(files)}', 'dupe'),
                    InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇs", callback_data=f"languages#{search.replace(' ', '_')}#{key}"),
                    InlineKeyboardButton(f'🔮 ᴛɪᴘs', 'tips')
                ]
            )

    btn.insert(0, [
        InlineKeyboardButton(f'🔍 {search} 🔎', 'reqst1')
    ])
    await message.delete()
    m=await message.reply_text("🔍") 
    await asyncio.sleep(1)
    await m.delete()
   


     
    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        try:
            settings = await get_settings(message.chat.id)
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ​⇛",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ​⇛",callback_data=f"next_{req}_{key}_{offset}")]
                )
        except KeyError:
            await save_group_settings(message.chat.id, 'max_btn', False)
            settings = await get_settings(message.chat.id)
            if settings['max_btn']:
                btn.append(
                    [InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ​⇛",callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton("📚 ᴘᴀɢᴇ​", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/int(MAX_B_TN))}",callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ​⇛",callback_data=f"next_{req}_{key}_{offset}")]
                )
    else:
        btn.append(
            [InlineKeyboardButton(text="♨️ ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs ᴀᴠᴀɪʟᴀʙʟᴇ ♨️",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>🎪 ᴛɪᴛɪʟᴇ {search}\n\n┏ 🤴 ᴀsᴋᴇᴅ ʙʏ : {message.from_user.mention}\n┣ ⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : <a href='https://t.me/nasrani_update'>ᴛᴏᴍ</a></b>"
    if imdb and imdb.get('poster'):
        try:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(
                    text=f"<b>Hᴇʏ {message.from_user.mention}\n\n{str(total_results)} Rᴇsᴜʟᴛs Aʀᴇ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ Bᴜᴛ I Cᴀɴ'ᴛ Gɪᴠᴇ Fɪʟᴇꜱ,\nBᴇᴄᴀᴜꜱᴇ Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ\nPʟᴇᴀꜱᴇ Rᴇǫᴜᴇꜱᴛ Oɴ Oᴜʀ Mᴏᴠɪᴇ Gʀᴏᴜᴘ</b>",
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton('📌 Rᴇǫᴜᴇꜱᴛ Hᴇʀᴇ', url ='https://t.me/NasraniChatGroup')
                        ]]
                    )
                )
            else:
                hehe = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(IMDB_DLT_TIME)
                        await hehe.delete()
                        thega=await message.reply_photo(
                            photo=random.choice(CLOSE_IMG),
                            caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                        await asyncio.sleep(37)                   
                        await thega.delete()                        
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(IMDB_DLT_TIME)
                        await hehe.delete()
                        thega=await message.reply_photo(
                            photo=random.choice(CLOSE_IMG),
                            caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                        await asyncio.sleep(37)                   
                        await thega.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(
                    text=f"<b>Hᴇʏ {message.from_user.mention}\n\n{str(total_results)} Rᴇsᴜʟᴛs Aʀᴇ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ Bᴜᴛ I Cᴀɴ'ᴛ Gɪᴠᴇ Fɪʟᴇꜱ,\nBᴇᴄᴀᴜꜱᴇ Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ\nPʟᴇᴀꜱᴇ Rᴇǫᴜᴇꜱᴛ Oɴ Oᴜʀ Mᴏᴠɪᴇ Gʀᴏᴜᴘ</b>",
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton('📌 Rᴇǫᴜᴇꜱᴛ Hᴇʀᴇ', url ='https://t.me/NasraniChatGroup')
                        ]]
                    )
                )
            else:
                pic = imdb.get('poster')
                poster = pic.replace('.jpg', "._V1_UX360.jpg")
                hmm = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(IMDB_DLT_TIME)
                        await hmm.delete()
                        thega=await message.reply_photo(
                            photo=random.choice(CLOSE_IMG),
                            caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                        await asyncio.sleep(37)                   
                        await thega.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(IMDB_DLT_TIME)
                        await hmm.delete()
                        thega=await message.reply_photo(
                            photo=random.choice(CLOSE_IMG),
                            caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                        await asyncio.sleep(37)                   
                        await thega.delete()                         
        except Exception as e:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(
                    text=f"<b>Hᴇʏ {message.from_user.mention}\n\n{str(total_results)} Rᴇsᴜʟᴛs Aʀᴇ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ Bᴜᴛ I Cᴀɴ'ᴛ Gɪᴠᴇ Fɪʟᴇꜱ,\nBᴇᴄᴀᴜꜱᴇ Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ\nPʟᴇᴀꜱᴇ Rᴇǫᴜᴇꜱᴛ Oɴ Oᴜʀ Mᴏᴠɪᴇ Gʀᴏᴜᴘ</b>",
                    reply_markup=InlineKeyboardMarkup(
                        [[
                           InlineKeyboardButton('📌 Rᴇǫᴜᴇꜱᴛ Hᴇʀᴇ', url ='https://t.me/NasraniChatGroup')
                        ]]
                    )
                )
            else:                
                logger.exception(e)
                fek = await message.reply_photo(photo=random.choice(NOR_IMG), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(IMDB_DLT_TIME)
                        await fek.delete()
                        thega=await message.reply_photo(
                            photo=random.choice(CLOSE_IMG),
                            caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                        await asyncio.sleep(37)                   
                        await thega.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(IMDB_DLT_TIME)
                        await fek.delete()
                        thega=await message.reply_photo(
                            photo=random.choice(CLOSE_IMG),
                            caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                        await asyncio.sleep(37)                   
                        await thega.delete()                 
    else:
        if message.chat.id == SUPPORT_CHAT_ID:
            await message.reply_text(
                text=f"<b>Hᴇʏ {message.from_user.mention}\n\n{str(total_results)} Rᴇsᴜʟᴛs Aʀᴇ Aʟʀᴇᴀᴅʏ Aᴠᴀɪʟᴀʙʟᴇ Bᴜᴛ I Cᴀɴ'ᴛ Gɪᴠᴇ Fɪʟᴇꜱ,\nBᴇᴄᴀᴜꜱᴇ Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ\nPʟᴇᴀꜱᴇ Rᴇǫᴜᴇꜱᴛ Oɴ Oᴜʀ Mᴏᴠɪᴇ Gʀᴏᴜᴘ</b>",
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton('📌 Rᴇǫᴜᴇꜱᴛ Hᴇʀᴇ', url ='https://t.me/NasraniChatGroup')
                    ]]
                )
            )
        else:
            fuk = await message.reply_photo(photo=random.choice(NOR_IMG), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(IMDB_DLT_TIME)
                    await fuk.delete()
                    thega=await message.reply_photo(
                        photo=random.choice(CLOSE_IMG),
                        caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                    await asyncio.sleep(37)                   
                    await thega.delete()  
                    
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(IMDB_DLT_TIME)
                    await fuk.delete()
                    thega=await message.reply_photo(
                        photo=random.choice(CLOSE_IMG),
                        caption=f"⚙️ {message.from_user.mention} Fɪʟᴛᴇʀ Fᴏʀ {search} Cʟᴏꜱᴇᴅ 🗑️")
                    await asyncio.sleep(37)                   
                    await thega.delete()
                                       
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(client, msg):
    mv_id = msg.id
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    settings = await get_settings(msg.chat.id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    try:
        movies = await get_poster(mv_rqst, bulk=True)
    except Exception as e:
        logger.exception(e)
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
        InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ ᴏɴ ɢᴏᴏɢʟᴇ​ 🔎', url=f"https://www.google.com/search?q={reqst_gle}")            
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
  
        k = await msg.reply_text(
            text=("<b>sᴏʀʀʏ ɴᴏ ꜰɪʟᴇs ᴡᴇʀᴇ ꜰᴏᴜɴᴅ\n\nᴄʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪɴ ɢᴏᴏɢʟᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ !!</b>"),
            reply_markup=InlineKeyboardMarkup(button),
            reply_to_message_id=msg.id
        )
        await asyncio.sleep(60)
        await k.delete()
        await msg.delete()  
        return
    movielist = []
    if not movies:
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
        InlineKeyboardButton('🔍 sᴇᴀʀᴄʜ ᴏɴ ɢᴏᴏɢʟᴇ​ 🔎', url=f"https://www.google.com/search?q={reqst_gle}")   
        ]]
        if NO_RESULTS_MSG:
            await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply_text(
            text=("<b>sᴏʀʀʏ ɴᴏ ꜰɪʟᴇs ᴡᴇʀᴇ ꜰᴏᴜɴᴅ\n\nᴄʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪɴ ɢᴏᴏɢʟᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ !!</b>"),
            reply_markup=InlineKeyboardMarkup(button),
            reply_to_message_id=msg.id
        )
        await asyncio.sleep(60)
        await k.delete()
        await msg.delete()
        return
    movielist = [movie.get('title') for movie in movies]
    SPELL_CHECK[mv_id] = movielist
    btn = [
        [
            InlineKeyboardButton(
                text=movie_name.strip(),
                callback_data=f"spol#{reqstr1}#{k}",
            )
        ]
        for k, movie_name in enumerate(movielist)
    ]
    btn.append([InlineKeyboardButton(text="✘ ᴄʟᴏsᴇ ✘", callback_data=f'spol#{reqstr1}#close_spellcheck')])
    spell_check_del = await msg.reply_text(
        text=(script.CUDNT_FND.format(mv_rqst)),
        reply_markup=InlineKeyboardMarkup(btn),
        reply_to_message_id=msg.id
    )
    await msg.delete()
    try:
        if settings['auto_delete']:
            await asyncio.sleep(60)
            await spell_check_del.delete()
    except KeyError:
            grpid = await active_connection(str(message.from_user.id))
            await save_group_settings(grpid, 'auto_delete', True)
            settings = await get_settings(message.chat.id)
            if settings['auto_delete']:
                await asyncio.sleep(60)
                await spell_check_del.delete()


async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            try:
                                if settings['auto_delete']:
                                    await joelkb.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await joelkb.delete()

                        else:
                            button = eval(btn)
                            hmm = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            try:
                                if settings['auto_delete']:
                                    await hmm.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await hmm.delete()

                    elif btn == "[]":
                        oto = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            protect_content=True if settings["file_secure"] else False,
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        try:
                            if settings['auto_delete']:
                                await oto.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_delete', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_delete']:
                                await oto.delete()

                    else:
                        button = eval(btn)
                        dlt = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        try:
                            if settings['auto_delete']:
                                await dlt.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_delete', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_delete']:
                                await dlt.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            
                        else:
                            button = eval(btn)
                            hmm = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )

                    elif btn == "[]":
                        oto = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )

                    else:
                        button = eval(btn)
                        dlt = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

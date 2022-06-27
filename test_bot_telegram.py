from telethon.sync import TelegramClient
from telethon import functions, types

api_id = "13440456"
api_hash = "516a1deb18a0663eb808fb8d1909bb79"

with TelegramClient("create_channels", api_id, api_hash) as client:
    result = client(functions.channels.CreateChannelRequest(
        title="SN000",
        about="Info robot SN000"
    ))
    result2 = client(functions.channels.InviteToChannelRequest(
        channel=result.chats[0],
        users=['+33620359732']
    ))
    chat_id = result.chats[0].id
    

import os
import json
import asyncio
import aiohttp

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

SERVERS_API = 'https://api.cs2kz.org/servers'
REPO = 'vap222222/nonglobalmaps'
REPORTED_FILE = 'reported_maps.json'

async def fetch_servers(session):
    async with session.get(SERVERS_API) as resp:
        data = await resp.json()
        return data.get('values', [])

async def image_exists_in_repo(session, map_name):
    url = f'https://api.github.com/repos/{REPO}/contents/{map_name}.jpg'
    headers = {'Authorization': f'Bearer {GITHUB_TOKEN}'}
    async with session.get(url, headers=headers) as resp:
        return resp.status == 200

async def send_telegram(session, message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    async with session.post(url, data=payload) as resp:
        if resp.status != 200:
            print(f'Telegram error: {await resp.text()}')

def load_reported():
    try:
        with open(REPORTED_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_reported(reported: set):
    with open(REPORTED_FILE, 'w') as f:
        json.dump(list(reported), f)

async def main():
    reported = load_reported()
    newly_missing = []

    async with aiohttp.ClientSession() as session:
        servers = await fetch_servers(session)

        # Collect unique non-global maps that are actually running
        non_global_maps = {}  # map_name -> server address
        for server in servers:
            a2s = server.get('a2s_info')
            if not a2s:
                continue
            current_map = a2s.get('current_map', '')
            map_info = a2s.get('current_map_info')
            if current_map and map_info is None:
                host = server.get('host', '')
                port = server.get('port', '')
                non_global_maps[current_map] = f'{host}:{port}'

        print(f'Non-global maps currently running: {non_global_maps}')

        # Check each one against the repo
        for map_name in non_global_maps:
            if map_name in reported:
                print(f'Already reported: {map_name}, skipping')
                continue
            exists = await image_exists_in_repo(session, map_name)
            if not exists:
                print(f'Missing image for: {map_name}')
                newly_missing.append(map_name)
            else:
                print(f'Image exists for: {map_name}')

        # Send telegram if anything new is missing
        if newly_missing:
            if len(newly_missing) == 1:
                map_name = newly_missing[0]
                msg = f'{map_name}, {non_global_maps[map_name]}'
            else:
                maps_list = '\n'.join(f'{m}, {non_global_maps[m]}' for m in newly_missing)
                msg = maps_list
            await send_telegram(session, msg)
            reported.update(newly_missing)
            save_reported(reported)
            print(f'Reported {len(newly_missing)} new missing maps')
        else:
            print('No new missing maps found')

if __name__ == '__main__':
    asyncio.run(main())

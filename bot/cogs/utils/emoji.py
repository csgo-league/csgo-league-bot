ABS_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
EMOJI_FILE = os.path.join(ABS_ROOT_DIR, 'emojis.json')

def create_emojis(client, guild):
    """"""

    icon_dir = os.path.join(ABS_ROOT_DIR, 'assets', 'maps', 'icons')
    reason = 'Used by the CS:GO League Bot'
    existing_emojis = {emoji.name: emoji for emoji in guild.emojis}

    if os.path.exists(EMOJI_FILE):
        with open(EMOJI_FILE) as f:
            emoji_dict = json.load(f)
    else:
        emoji_dict = {}

    for item in os.listdir(icon_dir):
        if item.endswith('.png'):
            emoji_name = item.split('.')[0]  # Remove file extension for emoji name

            # Check if emoji already exists and if it was made by this bot
            if emoji_name in existing_emojis:
                # Emoji user attribute only accessible with fetch_emoji()
                existing_emoji = await guild.fetch_emoji(existing_emojis[emoji_name].id)

                if existing_emoji.user == client.user:
                    BOT_LOGGER.info(
                        f'Emoji :{existing_emoji.name}: has already been created in the server, updating'
                    )
                    emoji_dict[existing_emoji.name] = f'<:{existing_emoji.name}:{existing_emoji.id}>'
                    continue

            # Attempt to create emoji
            try:
                with open(os.path.join(icon_dir, item), 'rb') as file:
                    new_emoji = await guild.create_custom_emoji(name=emoji_name, image=file.read(), reason=reason)
            except discord.Forbidden:
                BOT_LOGGER.error('Bot does not have permission to create custom emojis in the specified server')
                break
            except discord.HTTPException as e:
                BOT_LOGGER.error(f'HTTP exception raised when creating emoji for "{item}": {e.text} ({e.code})')
            except Exception as e:
                BOT_LOGGER.error(f'Exception {e} occurred')
            else:
                BOT_LOGGER.info(f'Emoji :{emoji_name}: created successfully')
                emoji_dict[new_emoji.name] = f'<:{new_emoji.name}:{new_emoji.id}>'

    with open(EMOJI_FILE, 'w+') as f:
        json.dump(emoji_dict, f)

EMOJI_DICT =

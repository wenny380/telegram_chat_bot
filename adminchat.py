import env
import requests


TOKEN = env.BOT_TOKEN
ADMIN_CHAT_ID = env.ADMIN_ID
API_URL = f'https://api.telegram.org/bot{TOKEN}/'

def send_message(chat_id, text):
    """Send a text message to a specific chat ID."""
    url = API_URL + 'sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, json=payload)

def send_media(chat_id, media_type, file_id, caption=None):
    url = API_URL + f'send{media_type.capitalize()}'
    payload = {'chat_id': chat_id, media_type.lower(): file_id}
    if caption:
        payload['caption'] = caption
    requests.post(url, json=payload)

def get_file_url(file_id):
    # Retrieve file path
    file_info = requests.get(API_URL + f'getFile?file_id={file_id}').json()
    file_path = file_info['result']['file_path']
    return f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'

def get_updates(offset=None):
    """Fetch updates from the Telegram API."""
    url = API_URL + 'getUpdates'
    payload = {'offset': offset, 'timeout': 100}
    response = requests.get(url, params=payload)
    return response.json()

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates.get('result', []):
            offset = update['update_id'] + 1
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                message_text = update['message'].get('text')
                document = update['message'].get('document')
                photo = update['message'].get('photo')
                voice = update['message'].get('voice')
                caption = update['message'].get('caption', '')  # Get the caption
                reply_to_message = update['message'].get('reply_to_message')

                # Handle /start command
                if message_text == '/start':
                    send_message(chat_id, 'Welcome! How can I assist you today?')
                    continue

                # Forward user messages and media to admin
                if chat_id != int(ADMIN_CHAT_ID):
                    if message_text:
                        send_message(
                            ADMIN_CHAT_ID, f"User {chat_id}: {message_text}"
                        )
                    if document:
                        file_id = document['file_id']
                        send_media(
                            ADMIN_CHAT_ID,
                            "Document",
                            file_id,
                            f"User {chat_id} sent a document. {caption}" if caption else f"User {chat_id} sent a document."
                        )
                    if photo:
                        file_id = photo[-1]['file_id']  # Highest resolution photo
                        send_media(
                            ADMIN_CHAT_ID,
                            "Photo",
                            file_id,
                            f"User {chat_id} sent a photo. {caption}" if caption else f"User {chat_id} sent a photo."
                        )
                    if voice:
                        file_id = voice['file_id']
                        send_media(
                            ADMIN_CHAT_ID,
                            "Voice",
                            file_id,
                            f"User {chat_id} sent a voice message. {caption}" if caption else f"User {chat_id} sent a voice message."
                        )
                    continue

                # Handle admin's replies with text or media
                if chat_id == int(ADMIN_CHAT_ID) and reply_to_message:
                    # Extract user ID from the replied message text or media caption
                    original_text = reply_to_message.get('text', '')
                    reply_caption = reply_to_message.get('caption', '')
                    reference_text = original_text or reply_caption

                    if reference_text.startswith('User '):
                        try:
                            user_chat_id = int(reference_text.split(' ')[1].split(':')[0])

                            # Send admin's text reply to the user
                            if message_text:
                                send_message(user_chat_id, message_text)
                            # Send admin's media reply to the user with caption
                            if document:
                                send_media(user_chat_id, "Document", document['file_id'], caption)
                            if photo:
                                file_id = photo[-1]['file_id']
                                send_media(user_chat_id, "Photo", file_id, caption)
                            if voice:
                                send_media(user_chat_id, "Voice", voice['file_id'], caption)
                        except (ValueError, IndexError):
                            print("Failed to extract user_chat_id from reference text.")
                    else:
                        print("Reply does not reference a user message.")



if __name__ == '__main__':
    main()

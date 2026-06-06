import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
import time

TOKEN = 'YOUR_BOT_TOKEN'
ADMIN_ID = 1945305616
POST_CHANNEL = '@Englishmovieswithsubb'
FORCE_JOIN = '@Englishmovieswithsubb'
MOVIE_STORAGE = -1002626990546
SERIES_STORAGE = -1002462921353

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
movies = {}
serials = {}
users = set()
join_cache = {}
CACHE_TIME = 600


def make_key(text):
    if not text:
        return ''
    text = text.lower().strip()
    text = re.sub(r'(19|20)[0-9][0-9]', '', text)
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = re.sub(r'[ ]+', ' ', text)
    return text.strip()


def key_to_param(key):
    return key.replace(' ', '_')


def param_to_key(param):
    return param.replace('_', ' ')


def load_users():
    try:
        f = open('users.txt', 'r')
        for line in f:
            uid = line.strip()
            if uid:
                users.add(int(uid))
        f.close()
    except:
        pass


def load_movies():
    try:
        f = open('movies.txt', 'r', encoding='utf-8')
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) == 4:
                name = parts[0]
                dtype = parts[1]
                chat_id = parts[2]
                msg_id = parts[3]
                if name not in movies:
                    movies[name] = {'files': []}
                if dtype == 'photo':
                    movies[name]['photo'] = (int(chat_id), int(msg_id))
                elif dtype == 'file':
                    movies[name]['files'].append((int(chat_id), int(msg_id)))
        f.close()
    except:
        pass


def load_serials():
    try:
        f = open('serials.txt', 'r', encoding='utf-8')
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) == 3:
                name = parts[0]
                chat_id = parts[1]
                msg_id = parts[2]
                if name not in serials:
                    serials[name] = {'info': {}, 'seasons': {}}
                serials[name]['info'] = {
                    'title': name,
                    'chat_id': int(chat_id),
                    'msg_id': int(msg_id),
                    'file_id': None
                }
            elif len(parts) == 4:
                name = parts[0]
                chat_id = parts[1]
                msg_id = parts[2]
                file_id = parts[3]
                if name not in serials:
                    serials[name] = {'info': {}, 'seasons': {}}
                serials[name]['info'] = {
                    'title': name,
                    'chat_id': int(chat_id),
                    'msg_id': int(msg_id),
                    'file_id': file_id
                }
            elif len(parts) == 5:
                name = parts[0]
                season = parts[1]
                episode = parts[2]
                chat_id = parts[3]
                msg_id = parts[4]
                if name not in serials:
                    serials[name] = {'info': {}, 'seasons': {}}
                if season not in serials[name]['seasons']:
                    serials[name]['seasons'][season] = {}
                serials[name]['seasons'][season][episode] = (int(chat_id), int(msg_id))
        f.close()
    except:
        pass


load_users()
load_movies()
load_serials()


def save_movie_db(name, dtype, chat_id, msg_id):
    f = open('movies.txt', 'a', encoding='utf-8')
    f.write(name + '|' + dtype + '|' + str(chat_id) + '|' + str(msg_id) + '\n')
    f.close()


def save_serial_info_db(name, chat_id, msg_id, file_id):
    f = open('serials.txt', 'a', encoding='utf-8')
    f.write(name + '|' + str(chat_id) + '|' + str(msg_id) + '|' + str(file_id) + '\n')
    f.close()


def save_serial_episode_db(name, season, episode, chat_id, msg_id):
    f = open('serials.txt', 'a', encoding='utf-8')
    f.write(name + '|' + season + '|' + episode + '|' + str(chat_id) + '|' + str(msg_id) + '\n')
    f.close()


def add_user(user_id):
    if user_id not in users:
        users.add(user_id)
        f = open('users.txt', 'a')
        f.write(str(user_id) + '\n')
        f.close()


def parse_episode_caption(caption):
    match = re.match(r'^(.+?)\s+[Ss]([0-9]+)[Ee]([0-9]+)', caption.strip())
    if match:
        name = make_key(match.group(1).strip())
        season = str(int(match.group(2)))
        episode = str(int(match.group(3)))
        return name, season, episode
    return None, None, None


def check_joined(user_id):
    now = time.time()
    if user_id in join_cache:
        if now - join_cache[user_id] < CACHE_TIME:
            return True
    for i in range(3):
        try:
            member = bot.get_chat_member(FORCE_JOIN, user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
            if is_member:
                join_cache[user_id] = now
            return is_member
        except:
            time.sleep(1)
    return False


def join_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Join Channel', url='https://t.me/' + FORCE_JOIN[1:]))
    return markup


def season_markup(name, seasons):
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for season in sorted(seasons.keys(), key=lambda x: int(x)):
        param = key_to_param(name) + '__season__' + season
        btn = InlineKeyboardButton('Season ' + season, url='https://t.me/' + bot.get_me().username + '?start=' + param)
        buttons.append(btn)
    if buttons:
        markup.add(*buttons)
    return markup


@bot.channel_post_handler(content_types=['photo'])
def channel_photo(message):
    if message.chat.id != SERIES_STORAGE:
        return
    if not message.caption:
        return
    name = make_key(message.caption.splitlines()[0])
    if not name:
        return
    file_id = message.photo[-1].file_id
    if name not in serials:
        serials[name] = {'info': {}, 'seasons': {}}
    serials[name]['info'] = {
        'title': message.caption.splitlines()[0].strip(),
        'chat_id': message.chat.id,
        'msg_id': message.message_id,
        'file_id': file_id
    }
    save_serial_info_db(name, message.chat.id, message.message_id, file_id)


@bot.channel_post_handler(content_types=['video', 'document'])
def channel_video(message):
    if not message.caption:
        return
    if message.chat.id == MOVIE_STORAGE:
        name = make_key(message.caption.splitlines()[0])
        if not name:
            return
        if name not in movies:
            movies[name] = {'files': []}
        movies[name]['files'].append((message.chat.id, message.message_id))
        save_movie_db(name, 'file', message.chat.id, message.message_id)
        return
    if message.chat.id == SERIES_STORAGE:
        name, season, episode = parse_episode_caption(message.caption)
        if not name or not season or not episode:
            return
        if name not in serials:
            serials[name] = {'info': {}, 'seasons': {}}
        if season not in serials[name]['seasons']:
            serials[name]['seasons'][season] = {}
        serials[name]['seasons'][season][episode] = (message.chat.id, message.message_id)
        save_serial_episode_db(name, season, episode, message.chat.id, message.message_id)


@bot.message_handler(content_types=['photo'])
def admin_photo(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.caption:
        return
    caption = message.caption.strip()
    title = caption.splitlines()[0].strip()
    name = make_key(title)
    seasons = serials.get(name, {}).get('seasons', {})
    if seasons:
        markup = season_markup(name, seasons)
        bot.send_photo(POST_CHANNEL, message.photo[-1].file_id, caption='<b>' + title + '</b>', reply_markup=markup)
    else:
        param = key_to_param(name)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Download Here', url='https://t.me/' + bot.get_me().username + '?start=' + param))
        if name not in movies:
            movies[name] = {'files': []}
        bot.send_photo(POST_CHANNEL, message.photo[-1].file_id, caption=caption + '\n\nShare and Support Us!', reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    add_user(user_id)
    param = message.text.replace('/start', '').strip()
    if not check_joined(user_id):
        bot.send_message(message.chat.id, 'Please join our channel first!', reply_markup=join_markup())
        return
    if param:
        if '__season__' in param:
            parts = param.split('__season__')
            serial_name = param_to_key(parts[0])
            season = parts[1]
            send_season(message.chat.id, serial_name, season)
            return
        name = param_to_key(param)
        if name in movies:
            send_movie(message.chat.id, name)
            return
        bot.send_message(message.chat.id, 'Not found.')
        return
    bot.send_message(message.chat.id, 'Welcome!\n\nSend a movie or series name.\n\nExample: Avatar or Breaking Bad')


def send_movie(chat_id, name):
    data = movies.get(name)
    if not data or not data.get('files'):
        bot.send_message(chat_id, 'Movie not found.')
        return
    bot.send_message(chat_id, 'Sending movie...')
    by_channel = {}
    for ch, mid in data['files']:
        if ch not in by_channel:
            by_channel[ch] = []
        by_channel[ch].append(mid)
    for ch in by_channel:
        mids = by_channel[ch]
        try:
            bot.copy_messages(chat_id, ch, mids)
        except:
            for mid in mids:
                try:
                    bot.copy_message(chat_id, ch, mid)
                    time.sleep(0.3)
                except:
                    pass


def send_season(chat_id, serial_name, season):
    if serial_name not in serials:
        bot.send_message(chat_id, 'Episodes not found.')
        return
    if season not in serials[serial_name]['seasons']:
        bot.send_message(chat_id, 'Episodes not found.')
        return
    episodes = serials[serial_name]['seasons'][season]
    sorted_eps = sorted(episodes.items(), key=lambda x: int(x[0]))
    title = serials[serial_name]['info'].get('title', serial_name)
    bot.send_message(chat_id, title + ' Season ' + season + '\nSending ' + str(len(sorted_eps)) + ' episodes...')
    for ep_num, ep_data in sorted_eps:
        ch = ep_data[0]
        mid = ep_data[1]
        try:
            bot.copy_message(chat_id, ch, mid)
            time.sleep(0.3)
        except:
            try:
                bot.forward_message(chat_id, ch, mid)
                time.sleep(0.3)
            except:
                pass


@bot.message_handler(content_types=['text'])
def group_search(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        return
    add_user(user_id)
    if not check_joined(user_id):
        bot.reply_to(message, 'Please join our channel first!', reply_markup=join_markup())
        return
    text = make_key(message.text)
    if not text:
        return
    movie_results = [n for n in movies if text in n]
    serial_results = [n for n in serials if text in n and serials[n].get('info')]
    if not movie_results and not serial_results:
        return
    if movie_results:
        name = movie_results[0]
        data = movies[name]
        by_channel = {}
        for ch, mid in data.get('files', []):
            if ch not in by_channel:
                by_channel[ch] = []
            by_channel[ch].append(mid)
        for ch in by_channel:
            mids = by_channel[ch]
            try:
                bot.copy_messages(message.chat.id, ch, mids)
            except:
                for mid in mids:
                    try:
                        bot.copy_message(message.chat.id, ch, mid)
                        time.sleep(0.3)
                    except:
                        pass
        return
    if serial_results:
        name = serial_results[0]
        info = serials[name]['info']
        seasons = serials[name].get('seasons', {})
        markup = season_markup(name, seasons)
        file_id = info.get('file_id')
        if file_id:
            bot.send_photo(message.chat.id, file_id, caption='<b>' + info['title'] + '</b>', reply_markup=markup)
        else:
            try:
                bot.copy_message(message.chat.id, info['chat_id'], info['msg_id'], reply_markup=markup)
            except:
                bot.send_message(message.chat.id, '<b>' + info['title'] + '</b>', reply_markup=markup)


@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, 'Statistics\n\nUsers: ' + str(len(users)) + '\nMovies: ' + str(len(movies)) + '\nSeries: ' + str(len(serials)))


@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast ', '', 1)
    success = 0
    for user in users:
        try:
            bot.send_message(user, text)
            success += 1
            time.sleep(0.05)
        except:
            pass
    bot.reply_to(message, 'Sent to ' + str(success) + ' users.')


@bot.message_handler(commands=['delete'])
def delete(message):
    if message.from_user.id != ADMIN_ID:
        return
    name = make_key(message.text.replace('/delete ', '', 1))
    if name in movies:
        del movies[name]
        bot.reply_to(message, 'Movie deleted.')
    elif name in serials:
        del serials[name]
        bot.reply_to(message, 'Series deleted.')
    else:
        bot.reply_to(message, 'Not found.')


while True:
    try:
        bot.infinity_polling(timeout=60)
    except:
        time.sleep(5)
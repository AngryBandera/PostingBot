from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text
import logging, time, threading, json
from datetime import datetime
from telegram import InputMediaPhoto, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from app import create_markup
from db_handler import DB

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

db_uri = 'sqlite:///db.db'  
polling = True
TOKEN = "1714618330:AAE8zVajugM5_WFcvkU8LKUQ0BFYTWjDXTI"
timeout = 5

def db_update():
    sended = 0
    strt_time = datetime.now()
    msgs = DB().get_delayed_msgs()

    for msg in msgs:
        delay_time = datetime.strptime(msg.dateTime, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()

        cond1 = (delay_time.date()==now.date() and delay_time.hour==now.hour and delay_time.minute==now.minute)
        cond2 = (delay_time.date()<=now.date())
        cond3 = (delay_time.date()==now.date() and delay_time.hour<=now.hour)
        cond4 = (delay_time.date()==now.date() and delay_time.hour==now.hour and delay_time.minute<=now.minute)

        if cond1 or cond2 or cond3 or cond4:
            # flood control (30 msgs in second)
            if sended >= 25:
                wasted = datetime.now() - strt_time
                wait_time=60-wasted.seconds
                if wait_time>0:time.sleep(wait_time)
                strt_time=datetime.now()
                sended=0

            print('sending')
            x = threading.Thread(target=send_message, args=(msg,))
            x.start()
            sended+=1
    print('checked for messages')
    print(datetime.now())

def send_message(msg):
    data = json.loads(msg.data)
    chat_id = data['chat_id']
    text = data['text_parsed']
    media = data['media']
    group = data['group']
    sended_msg = None
    reply_markup = None 

    if data.get('reply_markup', True) != True:
        reply_markup = create_markup(data['reply_markup'])

    if not media:
        sended_msg = Bot(TOKEN).send_message(chat_id=chat_id, text=text, parse_mode='html', reply_markup=reply_markup)
        print('sended text')
    elif media and not group:
        print('sended image')
        photo = data['photo'][-1]['file_id']
        sended_msg = Bot(TOKEN).send_photo(chat_id=chat_id, caption=text, parse_mode='html', reply_markup=reply_markup, photo=photo)
    elif media and group:
        media_group = []
        first = True
        for photo in data['photo']:
            photo = photo['file_id']
            media_group.append(InputMediaPhoto(photo, caption=text if first else '', parse_mode='HTML'))
            first = False

        sended_msg = Bot(TOKEN).send_media_group(chat_id, media_group)
    
    if group:
        #in case of multiple img sending
        new_msg_list = []
        for element in sended_msg:
            new_msg_list.append(element.to_dict()['photo'][-1])
        sended_msg = sended_msg[0]
        data['photo'] = new_msg_list

    sended_msg = sended_msg.to_dict()

    sended_msg['photo'] = data['photo']
    sended_msg['text_parsed'] = data['text_parsed']
    sended_msg['media'] = data['media']
    sended_msg['group'] = data['group']
    
    DB().from_delayed_to_sended(msg, sended_msg)

    print('sended')

if __name__ == "__main__":
    x = threading.Thread(target=db_update)
    x.start()

    print(60-datetime.now().second)
    time.sleep(60-datetime.now().second)

    while polling:
        x = threading.Thread(target=db_update)
        x.start()
        time.sleep(60-datetime.now().second)

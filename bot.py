from atexit import register
import telegram
from tkinter.messagebox import NO
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Chat, ChatMember, ChatMemberUpdated, constants
from telegram.ext import Updater, CallbackContext, CallbackQueryHandler, CommandHandler, MessageHandler, Filters, ConversationHandler, ContextTypes,ChatMemberHandler
import logging, bcrypt
from datetime import datetime

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

engine = create_engine('sqlite:///db.db', echo = True)
meta = MetaData()

user = Table('User', meta, Column('id', Integer, primary_key=True),
    Column('chat_id', Integer, nullable=False, unique=True),
    Column('username', String(20), nullable=False, unique=True),
    Column('password', String(80), nullable=False))

channel = Table('channel', meta, Column('id', Integer, primary_key=True),
    Column('chat_id', Integer, nullable=False, unique=True),
    Column('owner_id', Integer, nullable=False),
    Column('title', String, nullable=False))

# meta.create_all(engine)

TOKEN = ""

updater = None

STATE1, STATE2, STATE3, STATE4 = range(4)

###############################SERVICE#####################################
def deleteMessage(update, context):
    try:
        updater.bot.delete_message(update.message.chat_id, context.user_data["last_msg"])
    except Exception as e:pass

def processError(error):
    updater.bot.sendMessage(729560932, error)

###############################channel add listener#################################
def extract_status_change(chat_member_update: ChatMemberUpdated):
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
    if status_change is None:
        return None
    old_status, new_status = status_change
    was_member = old_status in [
        constants.CHATMEMBER_MEMBER,
        constants.CHATMEMBER_CREATOR,
        constants.CHATMEMBER_ADMINISTRATOR
    ] or (old_status == constants.CHATMEMBER_RESTRICTED and old_is_member is True)
    is_member = new_status in [
        constants.CHATMEMBER_MEMBER,
        constants.CHATMEMBER_CREATOR,
        constants.CHATMEMBER_ADMINISTRATOR
    ] or (new_status == constants.CHATMEMBER_RESTRICTED and new_is_member is True)
    return was_member, is_member

def track_chats(update: Update, context) -> None:
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    cause_name = update.effective_user.full_name
    effective_user = update.effective_user

    chat = update.effective_chat
    resp = None
    added=True
    if chat.type != Chat.PRIVATE:
        if not was_member and is_member:
            ins = user.select().where(user.c.chat_id==effective_user.id)
            conn = engine.connect()
            result = conn.execute(ins).first()
            ins = channel.insert().values(chat_id = chat.id, owner_id = result[0], title = chat.title)
            result = conn.execute(ins)
        elif was_member and not is_member:
            added = False
            ins = channel.delete().where(channel.c.chat_id == chat.id)
            conn = engine.connect()
            result = conn.execute(ins)
        reply_text=f"Канал {chat.title} успішно вилучено!"
        log_text=f"{cause_name} removed the bot from the channel {chat.title}"
        if added:
            reply_text=f"Канал {chat.title} успішно додано!"
            log_text=f"{cause_name} added bot to the channel {chat.title}"
        updater.bot.send_message(effective_user.id, reply_text)
        logger.info(log_text)

def start(update: Update, context: CallbackContext, get=False):

    keyboard = [[InlineKeyboardButton("Зареєструватися", callback_data="register")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = "Привіт це бот ________, нажми <i>Зареєструватися</i>, щоб створити аккаунт"
    if get:
        return reply_text, reply_markup
    msg = update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode="HTML")
    if msg.chat_id<0:
        msg.delete()
        update.message.reply_text("Цим ботом неможна користуватися в групах😔. Перейди в особисті повідомлення і продовжи роботу!")
        return
    context.user_data['last_msg'] = msg.message_id 

###############################Register funcs#######################################
def regStart(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    reply_text = "Введи логін:"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("В головне меню", callback_data="cancel")]])

    s = user.select().where(user.c.chat_id==query.message.chat_id)
    conn = engine.connect()
    result = conn.execute(s).first()
    if result != None:
        query.edit_message_text(text="В тебе вже є аккаунт!", reply_markup=reply_markup)
        return ConversationHandler.END

    query.edit_message_text(text=reply_text, reply_markup=reply_markup)
    return STATE1

def loginEntered(update: Update, context: CallbackContext):
    context.user_data['login'] = update.message.text
    reply_text = "Введи пароль:"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("В головне меню", callback_data="cancel")]])

    s = user.select().where(user.c.username==update.message.text)
    conn = engine.connect()
    result = conn.execute(s).first()
    if result != None:
        text="Це ім'я вже зайняте!"
        update.message.reply_text(text)
    elif len(update.message.text)<4:
        text="Логін має містити щонайменше 4 символи!"
        update.message.reply_text(text)
    else:
        deleteMessage(update, context)
        msg = update.message.reply_text(text=reply_text, reply_markup=reply_markup)
        context.user_data['last_msg'] = msg.message_id 
        return STATE2

def passwordEntered(update: Update, context: CallbackContext):
    
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("В головне меню", callback_data="cancel")]])
    if len(update.message.text)<8:
        text="Пароль має містити щонайменше 8 символів!"
        update.message.reply_text(text)
        return STATE2

    passwd = update.message.text.encode('UTF-8')

    passwd = bcrypt.hashpw(passwd, bcrypt.gensalt())

    try:
        ins = user.insert().values(username = context.user_data['login'], password = passwd, chat_id = update.message.chat_id)
        conn = engine.connect()
        result = conn.execute(ins)
    except Exception as err:
        logging.error(err)

    reply_text = "Тебе успішно зареєстровано!"


    msg = update.message.reply_text(text=reply_text, reply_markup=reply_markup)

    deleteMessage(update, context)

    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    reply_text, reply_markup = start(None, None, get=True)

    query.edit_message_text(text=reply_text, reply_markup=reply_markup, parse_mode="HTML")

    return ConversationHandler.END

###############################Native comments###############################
def updateStats(update: Update, context: CallbackContext):
    logger.info("##############Entered updateStats()")
    query = update.callback_query
    row, collumn, num, text, messageId, emojiId = query.data.split("|")
    row, collumn, num, messageId, emojiId = (int(row), int(collumn), int(num), int(messageId), int(emojiId))
    
    last_user_data = None
    if context.bot_data.get('comments', []) == []:
        context.bot_data['comments'] = []

    if messageId==-1:
        messageId = len(context.bot_data['comments'])
        context.bot_data['comments'].append({})
        logger.info("Created userdata")
    decreaseEmoji = None

    if update.effective_user in context.bot_data['comments'][messageId]:
        user_data = context.bot_data['comments'][messageId][update.effective_user]

        if (datetime.now() - user_data['time']).seconds < 0.2:
            query.answer()
            logger.info(f"##############Exited updateStats()")
            return
        
        last_user_data = user_data.copy()
        logger.info("User commented before")
        decreaseEmoji = user_data.copy()
        user_data = {'text':text,'id':emojiId,'row':row,'collumn':collumn, 'num': num, 'time': datetime.now()}
        context.bot_data['comments'][messageId][update.effective_user] = user_data
    else:
        logger.info("User haven't commented before")
        context.bot_data['comments'][messageId][update.effective_user] = {'text':text,'id':emojiId,'row':row,'collumn':collumn, 'num': num, 'time': datetime.now()}

    query.answer(f"Ти вибрав {text}")

    oldKeyboard = query.message.reply_markup.to_dict()["inline_keyboard"].copy()

    print(row, collumn)
    oldKeyboard[row][collumn] = {"callback_data":f"{row}|{collumn}|{num+1}|{text}|{messageId}|{emojiId}","text":f"{text} {num+1}"}
    logger.info(f"Added emoji {text} num")

    if decreaseEmoji!=None:
        row, collumn = decreaseEmoji['row'], decreaseEmoji['collumn']
        text, emojiId = decreaseEmoji['text'], decreaseEmoji['id']
        num = int(oldKeyboard[row][collumn]['callback_data'].split('|')[2])

        oldKeyboard[row][collumn] = {"callback_data":f"{row}|{collumn}|{num-1}|{text}|{messageId}|{emojiId}","text":f"{text} {num-1}"}
        logger.info(f"Decreased emoji {text} num")

    keyboard = []
    for row in oldKeyboard:
        btns = []
        for collumn in row:
            btns.append(InlineKeyboardButton(collumn["text"], callback_data=collumn["callback_data"].replace("-1", str(messageId))))
        keyboard.append(btns)


    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = query.message.text
    
    try:
        query.edit_message_reply_markup(reply_markup=reply_markup)
    except telegram.error.BadRequest as err:
        logger.info("message isn't modified")
        context.bot_data['comments'][messageId][update.effective_user] = last_user_data
    except telegram.error.RetryAfter as err:
        logger.info("Flood control restrict")
        context.bot_data['comments'][messageId][update.effective_user] = last_user_data

    logger.info(f"##############Exited updateStats()")

def photo(update: Update, context: CallbackContext):
    update.message.reply_text(update.message.to_json())

if __name__ == "__main__":

    updater = Updater(TOKEN, use_context=True)

    registerHandler = ConversationHandler(
        entry_points=[CallbackQueryHandler(regStart, pattern='register')],
        states={
            STATE1: [MessageHandler(Filters.text, loginEntered)],
            STATE2: [MessageHandler(Filters.text, passwordEntered)]
            },
        fallbacks=[CallbackQueryHandler(cancel, pattern='cancel')])

    dp = updater.dispatcher
    dp.add_handler(registerHandler)
    dp.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(cancel, pattern='cancel'))
    dp.add_handler(CallbackQueryHandler(updateStats, pattern='\d+\|\d+\|\d+\|.+\|(-1|\d+)\|\d+'))

    dp.add_handler(MessageHandler(Filters.photo, photo))

    updater.start_polling()

    updater.idle()

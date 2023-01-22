from flask import Flask, render_template, url_for, redirect, request, abort
from urllib.parse import urlparse, urljoin
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import json, os, logging, random, string, re
from werkzeug.utils import secure_filename
from telegram import InputMediaPhoto, Bot, InlineKeyboardMarkup, InlineKeyboardButton, Message
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


IP = '185.237.206.40'
PORT = 1234
IP = '127.0.0.1'
SERVICE_ID = '729560932'
TOKEN = "1714618330:AAE8zVajugM5_WFcvkU8LKUQ0BFYTWjDXTI"

app = Flask(__name__)
db = SQLAlchemy(app)
# app.config['SQLALCHEMY_ECHO'] = True
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config["imgFolder"] = "static"

logging.basicConfig(format='%(asctime)s - %(process)d-%(levelname)s-%(message)s')

logger = logging.getLogger(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

content_type = {'ContentType':'application/json'}


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, nullable=False, unique=True)
    owner_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, nullable=False)
    chat_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=False)

    def to_json(self):
        return json.dumps({"id": self.id, "owner_id": self.owner_id, "chat_id": self.chat_id})

class delayed_message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, nullable=False)
    chat_id = db.Column(db.Integer, nullable=False)
    dateTime = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text, nullable=False)

    def to_json(self):
        return json.dumps({"id": self.id, "owner_id": self.owner_id, "chat_id": self.chat_id})

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Логін"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Пароль"})

    submit = SubmitField('Увійти')

db.create_all()
db.session.commit()

home_page = 'messages_list'

def is_safe_url(target):
    ref_url = urlparse(request.host_url) 
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@app.route('/')
def home():
    return redirect(url_for(home_page))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)

                next_page = request.args.get('next')
                if not is_safe_url(next_page):
                    return abort(400)

                return redirect(next_page or url_for(home_page))
    if request.method == 'POST':
        errs = list(form.password.errors)
        errs.append('Неправильний логін чи пароль')
        form.password.errors = tuple(errs)
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    now = datetime.now().replace(microsecond=0)
    dates = [now, now + timedelta(days=3)]

    return render_template('dashboard.html', dates=dates)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/sendMessage", methods=["POST"])
@login_required
def send_message():
    data = request.form
    imgs = request.files
    token = data['token']
    is_delayed = data['is_delayed']=='true'
    disable_web_preview = data['disable_web_preview']
    chat_id = data['chat_id']
    if is_delayed: 
        chat_id=SERVICE_ID
        date = [ int(x) for x in data['date'].split(',') ]
        time = [ int(x) for x in data['time'].split(',') ]

    text = html_to_markdown(data['text'])

    msg = None
    filenames = []
    files_id = []
    message_key = get_random_string()
    if len(imgs)==1:
        print('Single image')
        f = imgs[list(imgs.keys())[0]]
        filename = f"{message_key}_single"
        filenames.append(filename)
        f.save(os.path.join(app.config["imgFolder"], secure_filename(filename)))
        msg = Bot(token).send_photo(chat_id, photo=open(f'static/{filename}', 'rb')
        , caption=text, reply_markup=data['reply_markup'] if data['keyboard'] else None, parse_mode='HTML')
        files_id.append(msg.photo[-1]['file_id'])
    elif len(imgs)>1:   
        print('Multiple images')
        first = True
        media_group = []
        i = 0
        for img in imgs:
            img = imgs[img]
            filename = f"{message_key}_{i}"
            filenames.append(filename)
            img.save(os.path.join(app.config["imgFolder"], secure_filename(filename)))

            media_group.append(InputMediaPhoto(open(f'static/{filename}', 'rb'), caption=text if first else '', parse_mode='HTML'))
            first = False
            i+=1
            if i == 10:
                break

        msg = Bot(token).send_media_group(chat_id, media_group)
        for photo in msg:
            files_id.append(photo.photo[-1]['file_id'])
    else:
        print('No image')
        msg = Bot(token).send_message(chat_id, text, reply_markup=data['reply_markup'] if data['keyboard'] else None, parse_mode='HTML', disable_web_page_preview=disable_web_preview)

    for name in filenames:
        if os.path.exists(os.path.join(app.config["imgFolder"], name)):
            os.remove(os.path.join(app.config["imgFolder"], name))
        
    if msg!=None:
        
        if type(msg) == list:
            #in case of multiple img sending

            new_msg = {'chat_id' : msg[0].chat_id, 'text' : data['text'], 'text_parsed': msg[0].caption_html, 'media' : True, 'group' : True, 'message_id': msg[0].message_id}

            msg_list = []
            for element in msg:
                msg_list.append(element.to_dict()['photo'][-1])
            msg = msg_list

            new_msg['photo'] = msg
            msg = new_msg
                    
            msg['media'] = True
            msg['group'] = True

        else:
            text_parsed = msg.text_html
            media = False
            if msg.photo != []:
                media = True
                text_parsed = msg.caption_html
            msg = msg.to_dict()
            msg['media'] = False
            msg['group'] = False

            if media:
                msg['text'] = msg.get('caption', '')
                msg['media'] = True
        
            msg['text_parsed'] = text_parsed
            msg['text'] = data['text']

        if is_delayed:
            print('delayed')
            msg['chat_id'] = data['chat_id']
            delay_time = datetime(date[0], date[1], date[2], time[0], time[1])
            msg_entry = delayed_message(owner_id=current_user.id, chat_id=chat_id, data=json.dumps(msg, ensure_ascii=False), dateTime=str(delay_time))
            db.session.add(msg_entry)
            db.session.commit()
        else:
            msg_entry = Message(owner_id=current_user.id, chat_id=chat_id, data=json.dumps(msg, ensure_ascii=False))
            db.session.add(msg_entry)
            db.session.commit()

        return json.dumps({'success':True}), 200, content_type
    else:
        return json.dumps({'success':False}), 500, content_type

@app.route("/getChannels", methods=["GET"])
@login_required
def get_channels():
    s = channel.query.filter_by(owner_id=current_user.id)
    channs = []
    is_empty = True
    for row in s:
        is_empty = False
        channs.append({'title': row.title, 'chat_id': row.chat_id})
    return json.dumps({'is_empty': is_empty, 'channels': channs})

@app.route('/messagesList', methods=['GET', 'POST'])
@app.route('/messagesList/<mode>', methods=['GET', 'POST'])
@login_required
def messages_list(mode = 'sended'):
    sended = mode=='sended'
    messages_data = None
    
    if sended:
        messages_data = Message.query.filter_by(owner_id=current_user.id)
    else:
        messages_data = delayed_message.query.filter_by(owner_id=current_user.id)

    messages = []
    for message in messages_data:
        data = json.loads(message.data)

        data['db_id'] = message.id
        if data['media']:
            if data['group']:
                photos_ids = []
                for photo in data['photo']: 
                    photos_ids.append(photo['file_id'])
                data['photos_ids'] = photos_ids
            else:
                data['photos_ids'] = [data['photo'][-1]['file_id']]    
                
        messages.append(data)

    messages.reverse()
    return render_template('messagesList.html', messages=messages, mode=mode)

@app.route('/editMessagePage/<message_id>/<mode>', methods=['GET'])
@login_required
def edit_message_page(message_id, mode): 
    sended = mode=='sended'
    if sended:
        message = Message.query.filter_by(id=int(message_id)).first()
    else:
        message = delayed_message.query.filter_by(id=int(message_id)).first()

    if message==None:
        return redirect(url_for('messages_list'))

    data = json.loads(message.data)

    data['db_id'] = message.id
    
    data['photos_ids'] = []
    if data['media']:
        if data['group']:
            photos_ids = []
            for photo in data['photo']: 
                photos_ids.append(photo['file_id'])
            data['photos_ids'] = photos_ids
        else:
            data['photos_ids'] = [data['photo'][1]['file_id']]    

    now = datetime.now()
    dates = [now.replace(microsecond=0), now.replace(day=now.day+7)]

    disable_preview = data.get('disable_web_page_preview', False) == 'true'
    page = 'editMessage.html'
    if not sended:
        page = 'editUnsendedMessage.html'
    return render_template(page, message=message.to_json(), data=json.dumps(data), media=data['media'], photos_ids=data['photos_ids'], dates=dates, disable_preview=disable_preview)

@app.route('/editMessage', methods=['POST', 'GET'])
@login_required
def edit_message():
    error = ''
    data = request.form
    imgs = request.files
    text = data['text']
    token = data['token']
    chat_id = data['chat_id']
    media = data['media'] == 'true'
    group = data['group'] == 'true'
    disable_web_preview = data['disable_web_preview']
    msg, msg = None, None

    text = html_to_markdown(data['text'])

    msg_entry = Message().query.filter_by(id=data['db_id']).first()

    db_data = json.loads(msg_entry.data)
    filenames = []

    update_text = True if db_data['text']!=text else False

    reply_markup = None 
    if db_data.get('reply_markup', True) != True:
        reply_markup = create_markup(db_data['reply_markup'])

    msg_text = None
    message_key = get_random_string()
    if media == True:
        if len(imgs)==1 and not group:
            f = imgs[list(imgs.keys())[0]]
            filename = f"{message_key}_single_edit"
            filenames.append(filename)
            f.save(os.path.join(app.config["imgFolder"], secure_filename(filename)))
            img = InputMediaPhoto(media=open(f'static/{filename}', 'rb'))

            msg = Bot(token).edit_message_media(media=img, chat_id=chat_id, message_id=data['message_id'])
            db_data['photo'] = msg.to_dict()['photo']
            try:
                msg_text = Bot(token).edit_message_caption(chat_id=chat_id, message_id=data['message_id'], caption=text, reply_markup=reply_markup, parse_mode="html")
                if msg_text!=None:
                    db_data['text_parsed'] = msg_text.caption_html
                    db_data['text'] = msg_text.caption
            except Exception as err:
                print(err, " :single photo caption")

        elif len(imgs)==0:
            try:
                msg_text = Bot(token).edit_message_caption(chat_id=chat_id, message_id=data['message_id'], caption=text, reply_markup=reply_markup, parse_mode="html")
                if msg_text!=None:
                    db_data['text_parsed'] = msg_text.caption_html
                    db_data['text'] = msg_text.caption
            except Exception as err:
                print(err, " :no photo caption")

        for name in filenames:
            if os.path.exists(os.path.join(app.config["imgFolder"], name)):
                os.remove(os.path.join(app.config["imgFolder"], name))
                
    elif update_text:
        try:
            msg_text = Bot(token).edit_message_text(chat_id=chat_id, message_id=data['message_id'], text=text, reply_markup=reply_markup, parse_mode="html", disable_web_page_preview=disable_web_preview)
            if msg_text!=None:
                db_data['text_parsed'] = msg_text.text_html
                db_data['text'] = msg_text.text
        except Exception as err:
            print(err, " : text")

    if msg!=None or msg_text!=None:
        msg_entry.data = json.dumps(db_data, ensure_ascii=False)
        db.session.commit()
        return json.dumps({'success':True, 'error':error}), 200, content_type
    else:
        error = "Message is not modified"
        print(error)
        return json.dumps({'success':False, 'error':error}), 500, content_type

@app.route('/editUnsendedMessage', methods=['POST', 'GET'])
@login_required
def edit_unsended_message():
    data = request.form
    imgs = request.files
    text = html_to_markdown(data['text'])
    db_id = data['db_id']
    is_delay_changed = data['isDelayChanged']=='true'
    disable_web_preview = data['disable_web_preview']
    media, group = False, False
    if len(imgs) > 0:
        media = True
        if len(imgs) > 1:
            group = True

    msg_entry = delayed_message().query.filter_by(id=db_id).first()

    db_data = json.loads(msg_entry.data)

    msg = None

    if media:
        filenames = []
        message_key = get_random_string()
        if group:
            print('Multiple images')
            media_group = []
            i = 0
            for img in imgs:
                img_key = img
                img = imgs[img]
                filename = f"{message_key}_{i}"
                filenames.append(filename)
                if 'local' in img_key:
                    img.save(os.path.join(app.config["imgFolder"], secure_filename(filename)))
                    media_group.append(InputMediaPhoto(open(f'static/{filename}', 'rb')))
                else:
                    media_group.append(InputMediaPhoto(img_key))

                i+=1
                if i == 10:
                    break

                msg = Bot(TOKEN).send_media_group(SERVICE_ID, media_group)

                photos = []
                for element in msg:
                    photos.append(element.to_dict()['photo'][-1])
                db_data['photo'] = photos
        else:
            print('Single image')
            f = imgs[list(imgs.keys())[0]]
            filename = f"{get_random_string()}_single_edit_unsended"
            filenames.append(filename)
            f.save(os.path.join(app.config["imgFolder"], secure_filename(filename)))

            msg = Bot(TOKEN).send_photo(SERVICE_ID, photo=open(f'static/{filename}', 'rb'))

            msg = msg.to_dict()

            db_data['photo'] = msg['photo']

        for name in filenames:
            if os.path.exists(os.path.join(app.config["imgFolder"], name)):
                os.remove(os.path.join(app.config["imgFolder"], name))

    if data['text'] != db_data['text']:
        msg = Bot(TOKEN).send_message(chat_id=SERVICE_ID, text=text, parse_mode="html")
        db_data['text'] = data['text']
        db_data['text_parsed'] = msg.text_html

    if is_delay_changed:
        time = datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S')
        msg_entry.dateTime = str(time)

    db_data['reply_markup'] = json.loads(data['reply_markup'])


    db_data['media'], db_data['group'], db_data['disable_web_page_preview'] = media, group, disable_web_preview

    msg_entry.data = json.dumps(db_data, ensure_ascii=False)
    db.session.commit()
    # if not is_delay_changed and msg==None:
    #     print("Message is not modified")
    #     return json.dumps({'success':False}), 500, content_type

    return json.dumps({'success':True}), 200, content_type

def create_markup(arr):
    markup = []
    for row in arr['inline_keyboard']:
        row_t = []
        for collumn in row:
            row_t.append(InlineKeyboardButton(text=collumn.get('text', "."), 
                callback_data=collumn.get('callback_data', None), url=collumn.get('url', None)))

        markup.append(row_t)

    return InlineKeyboardMarkup(markup)

def html_to_markdown(text):

    tags = ['strong', 'em', 'u', 's']
    # for tag in tags:
    tags_re = re.findall('<\/?(strong|s|em|u)>', text)

    for tag in tags_re[::-1]: 
        if tag in tags:
            tags.remove(tag)
            tags_num = len(re.findall('<\/{0,1}'+tag+'>', text))
            if tags_num%2!=0:
                text+=f'</{tag}>'

    text = text.replace("</p>", "\n")

    text = text.replace("<strong>", "(bold_open)")
    text = text.replace("</strong>", "(bold_close)")

    text = text.replace("<em>", "(italic_open)")
    text = text.replace("</em>", "(italic_close)")

    text = text.replace("<u>", "(underline_open)")
    text = text.replace("</u>", "(underline_close)")

    text = text.replace("<s>", "(strike_open)")
    text = text.replace("</s>", "(strike_close)")

    start_index = text.find("<a")
    while start_index != -1:
        end_index = text.find(">", start_index)
        link_text_start_index = text.find(">", end_index)
        text = text[:link_text_start_index] + '|endLinkOpening|' + text[link_text_start_index+1:]
        link_text_start_index+=1
        link_text_end_index = text.find("</a>", link_text_start_index)
        start_index = text.find("<a", link_text_end_index+4)

    text = text.replace("<a", "|(openLink)|")
    text = text.replace("</a>", "|(closeLink)|")

    soup = BeautifulSoup(text, 'html.parser')
    for tag in soup.find_all():
        tag.unwrap()
    text = str(soup)

    text = text.replace("(bold_open)", "<strong>")
    text = text.replace("(bold_close)", "</strong>")

    text = text.replace("(italic_open)", "<em>")
    text = text.replace("(italic_close)", "</em>")

    text = text.replace("(underline_open)", "<u>")
    text = text.replace("(underline_close)", "</u>")

    text = text.replace("(strike_open)", "<s>")
    text = text.replace("(strike_close)", "</s>")

    text = text.replace("|(openLink)|", "<a")
    text = text.replace("|(closeLink)|", "</a>")
    text = text.replace("|endLinkOpening|", ">")

    return text

def get_random_string():
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for _ in range(10))
    return(result_str)

if __name__ == "__main__":
    app.run(host=IP, port=PORT, debug=True)

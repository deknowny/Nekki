# vim: set fileencoding=utf-8 :
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import vk_api, sqlite3, traceback, random, time, datetime, re, operator, wikipedia

# Подключение
vk = vk_api.VkApi(token="7059080e6d4b5959bae233a596872518ba23b6f4a0dcdd2359198e3c96af23335f2b1d8c3861ffc9529cb")
vk._auth_token()
vk.get_api()
longpoll = VkBotLongPoll(vk, 187017444, wait = 86400)

# Подключение к .bd
conn = sqlite3.connect("./Nekki_database/Nekki.bd")
cursor = conn.cursor()

# Регулярные шаблоны
pr_pat = r"[!/&^.,\"\\'$~:#%].+"
word_tuple = ("офи", "некки", "nekki", "ofi")
id_searcher = r"\d{2,}"

# Словари 
pe = None # Словарь с пользователями
rp = None # Словарь с рпшками
pe_ic = None # Словарь с участниками в беседе

# Список с пользователями, от которых ждется согласие на брак
pe_m = {}

# Списки
mr_pe = [] # Для пользвоателей, от которых ждут ответ
mr_from_pe = []
mr_date = [] # Для время ожиданий

# wiki
wikipedia.set_lang("RU")

# Простые ответы
simple_answers = {
    "комиксы": "➾ Комиксы ЛоА/ЛоК\nhttps://vk.com/@aang_plus_korra-comics",
    "comics": "➾ Комиксы ЛоА/ЛоК\nhttps://vk.com/@aang_plus_korra-comics",
    "карты": "➾ Разбор карты мира Аватара (LoA/LoK).\n■ Здесь собранна информация об объектах и достопримечательностях:\nhttps://vk.com/topic-187166361_39795174\n■ Разбор карты:\nhttps://vk.com/topic-187166361_39795172",
    "maps": "➾ Разбор карты мира Аватара (LoA/LoK).\n■ Здесь собранна информация об объектах и достопримечательностях:\nhttps://vk.com/topic-187166361_39795174\n■ Разбор карты:\nhttps://vk.com/topic-187166361_39795172",
    "правила": "➾ Правила беседы:\nhttps://vk.com/topic-187166361_39809806",
    "rules": "➾ Правила беседы:\nhttps://vk.com/topic-187166361_39809806",
    "помощь": "➾ Статья-документация по командам и функционалу бота:\nvk.com/@waiter_bot-nekki",
    "help": "➾ Статья-документация по командам и функционалу бота:\nvk.com/@waiter_bot-nekki",
    "книга" : "➾ Книга жалоб и предложений\nhttps://vk.com/topic-187166361_39814620",
    "book" : "➾ Книга жалоб и предложений\nhttps://vk.com/topic-187166361_39814620"
}


def bd(request, *args):
    '''Выделяет данные из базы данных'''
    get_sql = request
    cursor.execute(get_sql, args)
    return cursor.fetchall()

class Chat:
    gs = None
    atts = None
    swears = None
    all_smb = None
    all_msg = None

    def __init__(self):

        sql = bd("SELECT all_smb, all_msg, gs, swears, atts FROM persons;")

        all_smb = sum([i[0] for i in sql])
        all_msg = sum([i[1] for i in sql])
        gs = sum([i[2] for i in sql])
        swears = sum([i[3] for i in sql])
        atts = sum([i[4] for i in sql])


        self.all_smb = all_smb
        self.all_msg = all_msg
        self.gs = gs
        self.swears = swears
        self.atts = atts

class User:

    last_active = 0
    gs = 0
    atts = 0
    swears = 0
    all_smb = 0
    all_msg = 0

    def __init__(self, user_id, first_name, last_name, scope, softmute, nickname, badge, gender, in_chat, marriage, marriage_date, ban, bl):

        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.scope = scope
        self.softmute = softmute
        self.nickname = nickname
        self.badge = badge
        self.gender = gender
        self.in_chat = in_chat
        self.marriage = marriage
        self.marriage_date = marriage_date
        self.ban = ban
        self.bl = bl

    def setSummary(self):
        sql = bd("SELECT all_smb, all_msg, last_active, gs, swears, atts FROM persons WHERE user_id = ?;", self.user_id)

        self.all_smb = sql[0][0]
        self.all_msg = sql[0][1]
        self.last_active = sql[0][2]
        self.gs = sql[0][3]
        self.swears = sql[0][4]
        self.atts = sql[0][5]

    def men(self, first_last = 1, *args):
        if first_last:
            return "[id{}|{} {}]".format(self.user_id, self.first_name, self.last_name)
        else:
            return "[id{}|{}]".format(self.user_id, ' '.join(args))

class Admin:
    def __init__(self, user_id, scope):
        self.user_id = user_id
        self.scope = scope


class RP:
    def __init__(self, action_1, action_2, emoji):
        self.action_1 = action_1
        self.action_2 = action_2
        self.emoji = emoji

def toFixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"

def rp_update():
    global rp
    sql = bd("SELECT action_1, action_2, emoji, assoc FROM role_play")
    assco_list = [i[3] for i in sql]
    obj_list = [RP(i[0], i[1], i[2]) for i in sql]
    rp = dict(zip(assco_list, obj_list))




def up_bd(request, *args):
    '''Обновляет данные в базе данных'''
    sql = request
    cursor.execute(sql, args)
    conn.commit()


def mention(us_id, value):
    return "[id{}|{}]".format(us_id, value)


def date(pattern='%d_%m_%Y', h=3):
    '''Возвращает дату по шаблону'''
    dt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=h)))
    value = datetime.datetime.fromtimestamp(time.mktime(dt.timetuple()))
    return value.strftime(pattern) # '%Y-%m-%d %H:%M:%S'

def pe_update():
    '''Заполняет словарь данным из базы данных'''
    global pe
    global pe_ic
    sql = bd("SELECT user_id, first_name, last_name, scope, softmute, nickname, badge, gender, in_chat, marriage, marriage_date, ban, bl FROM persons;")
    id_list = [i[0] for i in sql]
    id_list_in_chat = [i[0] for i in sql if i[8]]
    obj_list = [User(i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12]) for i in sql]

    obj_list_ic = [User(i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12]) for i in sql if i[8]]

    pe_ic = dict(zip(id_list_in_chat, obj_list_ic))
    pe = dict(zip(id_list, obj_list))


def get_id(value):
    return int(re.search(id_searcher, value)[0]) if (int(re.search(id_searcher, value)[0]) if re.search(id_searcher, value) else 0) and int(re.search(id_searcher, value)[0]) in pe else 0

def simpleDiffirentTime(t_max, t_min):
    dif = t_max - t_min
    if dif // 86400 == 0:

        if dif % 86400 // 3600 == 0:

            if dif % 86400 % 3600 // 60 == 0:

                return "{}с".format(dif % 86400 % 3600 % 60)

            else:
                return "{}м {}с".format(dif % 86400 % 3600 // 60, dif % 86400 % 3600 % 60)

        else:
            return "{}ч {}м".format(dif % 86400 // 3600, dif % 86400 % 3600 // 60)

    else:
        return "{}д {}ч".format(dif // 86400, dif % 86400 // 3600)

# Вызов функции для заполнения словарей
pe_update()
rp_update()

# Ныняшняя дата
date_now = date()

# Проверка
print("✓ Ready")

# Основной цикл

for event in longpoll.listen():

    

    def kick(us_id, peer_id = event.object.peer_id - 2000000000):
        vk.method("messages.removeChatUser", {
                "chat_id": peer_id,
                "user_id": us_id,
            })
        up_bd("UPDATE persons SET in_chat = ? WHERE user_id = ?", 0, us_id)
        pe_update()

    def ms(text="❕Неправильный формат команды", dm = 1, peer_id = 2000000001):
        '''Отправляет сообщение'''
        vk.method("messages.send", {
            "peer_id": peer_id,
            "message": text,
            "random_id": 0,
            "disable_mentions": dm
            })
        

    def users_get(us_id):
        return vk.method("users.get", {
                "user_ids": us_id,
                "fields": "sex"
            })

    def get_conversation_members():
        return vk.method("messages.getConversationMembers", {
            "peer_id": 2000000001
        })

    def adminsPusher(ev, person, *person_action):
        '''Обработка событий в беседе'''
        ms("#JasmineDragon\nСобытие: #{}\nИнициатор: {}\nЗадействован: {}\nДата: {}".format
            (
            ev,
            person if type(person) is str else person.men(),
            (' ,'.join([i.men() for i in person_action[0]])) if len(person_action) else "-",
            date('%H:%M %d.%m.%Y')
            ),
            peer_id = 2000000003)
    

    try:

        if event.type == VkBotEventType.MESSAGE_NEW: 
            
            if event.object.peer_id != event.object.from_id:

                if event.object.peer_id == 2000000001:

                    if date_now != date():

                        up_bd("ALTER TABLE pers_stats ADD COLUMN {} INTEGER DEFAULT 0;".format('s' + date()))
                        up_bd("ALTER TABLE pers_stats ADD COLUMN {} INTEGER DEFAULT 0;".format('m' + date()))
                        date_now = date()

                    if event.object.from_id > 0:


                    # Обрабатывает action
                        if 'action' in event.object and event.object.action.get('type') == 'chat_invite_user':


                            if event.object.action.get('member_id') in pe:

                                if pe[event.object.action.get('member_id')].ban:

                                    if pe[event.object.from_id].scope != 'Владелец':

                                        if pe[event.object.action.get('member_id')].ban < 0 :
                                            ms("❕Пользоватлель находится в перманентном бане, поэтому будет исключен")
                                            kick(event.object.action.get('member_id'))

                                        else:
                                            ms("❕Пользователь находится в бане до [{}], поэтому будет исключен".format(date("%d.%m.%Y %H:%M")))
                                            kick(event.object.action.get('member_id'))

                                    else:

                                        ms("❕Пользователь добавлен Владельцем, поэтому бан снят автоматически")
                                        up_bd("UPDATE persons SET in_chat = ?, ban = ? WHERE user_id = ?", 1, 0, event.object.action.get('member_id'))

                                else:

                                    ms("{}, Добро пожаловать в чайную Жасминовый Дракон. 🐉\nНе желаете ли чашечку нашего прекрасного жасминового чая?🍵🐲\n\nПредлагаем вам ознакомиться с правилами:\nhttps://vk.com/topic-187166361_39809806\nИ функционалом бота:\nvk.com/@waiter_bot-nekki".format(mention(event.object.action.get('member_id'), users_get(event.object.action.get('member_id'))[0]["first_name"])), 0)
                                    up_bd("UPDATE persons SET in_chat = ? WHERE user_id = ?", 1, event.object.action.get('member_id'))
                                
                            elif event.object.action.get('member_id') > 0:

                                b = users_get(event.object.action.get('member_id'))
                                ms("{}, Добро пожаловать в чайную Жасминовый Дракон. 🐉\nНе желаете ли чашечку нашего прекрасного жасминового чая?🍵🐲\n\nПредлагаем вам ознакомиться с правилами:\nhttps://vk.com/topic-187166361_39809806\nИ функционалом бота:\nvk.com/@waiter_bot-nekki".format(mention(event.object.action.get('member_id'), b[0]["first_name"])), 0)
                                up_bd("INSERT INTO persons (user_id, first_name, last_name, scope, softmute, nickname, badge, all_msg, all_smb, gender, in_chat, marriage, marriage_date, ban, bl, join_date, last_active, gs, atts, swears) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", event.object.action.get('member_id'), b[0]["first_name"], b[0]["last_name"], "Прохожий", 0, '', '', 0, 0, b[0]['sex'], 1, 0, 0, 0, 0, event.object.date, 0, 0, 0, 0)
                                up_bd("INSERT INTO pers_stats (user_id) VALUES (?)", event.object.action.get('member_id'))

                                

                            pe_update()
                            ###ADMINS###
                            if event.object.action.get('member_id') == event.object.from_id:
                                adminsPusher("chat_return_user", pe[event.object.from_id])
                            else:
                                adminsPusher("chat_invite_user", pe[event.object.from_id], [pe[event.object.action.get('member_id')]])
                            ###ADMINS###
                            continue

                        elif 'action' in event.object and event.object.action.get('type') == 'chat_kick_user':

                            up_bd("UPDATE persons SET in_chat = ? WHERE user_id = ?", 0, event.object.from_id)
                            pe_update()

                            ###ADMINS###
                            if event.object.from_id == event.object.action.get('member_id'):
                                adminsPusher("chat_leave_user", pe[event.object.from_id])
                            ###ADMINS###
                            continue

                        elif 'action' in event.object and event.object.action.get('type') == 'chat_invite_user_by_link':

                            b = users_get(event.object.from_id)
                            ms("{}, Добро пожаловать в чайную Жасминовый Дракон. 🐉\nНе желаете ли чашечку нашего прекрасного жасминового чая?🍵🐲\n\nПредлагаем вам ознакомиться с правилами:\nhttps://vk.com/topic-187166361_39809806\nИ функционалом бота:\nvk.com/@waiter_bot-nekki".format(mention(event.object.from_id, b[0]["first_name"])), 0)
                            up_bd("INSERT INTO persons (user_id, first_name, last_name, scope, softmute, nickname, badge, all_msg, all_smb, gender, in_chat, marriage, marriage_date, ban, bl, join_date, last_active, gs, atts, swears) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", event.object.from_id, b[0]["first_name"], b[0]["last_name"], "Прохожий", 0, '', '', 0, 0, b[0]['sex'], 1, 0, 0, 0, 0, event.object.date, 0, 0, 0, 0)
                            up_bd("INSERT INTO pers_stats (user_id) VALUES (?)", event.object.from_id)
                            pe_update()

                            ###ADMINS###
                            adminsPusher("chat_invite_user_by_link", pe[event.object.from_id])
                            ###ADMINS###
                            continue


                        if pe[event.object.from_id].scope == 'Прохожий':

                            sql = bd("SELECT all_msg, all_smb FROM persons WHERE user_id = ?;", event.object.from_id)

                            if sql[0][0] >= 100 or sql[0][1] >= 3500:

                                up_bd("UPDATE persons SET scope = ? WHERE user_id = ?;", "Клиент", event.object.from_id)

                                ms("Статус {} повышен до <Клиент> из-за хорошей активности".format(mention(event.object.from_id, "Пользователя")))
                                pe_update()
                                ###ADMINS###
                                adminsPusher("chat_update_scope <Прохожий>", "[waiter_bot|Nekki]", [pe[event.object.from_id]])
                                ###ADMINS###
                        
                        else:

                            if not pe[event.object.from_id].bl and (not pe[event.object.from_id].softmute):

                            # Создание объектов по пользователю
                                UsSend = pe[event.object.from_id]
                                UsReply = False
                                UsFrw = False

                                text = event.object.text
                                recod_com = text[1:] if re.fullmatch(pr_pat, text) else ' '.join(text.split(' ')[1:])

                                if 'reply_message' in event.object and event.object.reply_message['from_id'] > 0:
                                    UsReply = pe[event.object.reply_message['from_id']]

                                elif len(event.object.fwd_messages) != 0 and event.object.fwd_messages[0]['from_id'] > 0 and event.object.fwd_messages[0]['from_id'] in pe:
                                    UsFrw = pe[event.object.fwd_messages[0]['from_id']]

                            # Функции для работы с сообщением пользвоателя
                                def sep(count = 1, sep = ' ', text = recod_com):
                                    return text.split(sep) if not count else text.split(sep, count)

                                def sep_wp(count = 1, sep = ' ', text = text):
                                    return text.split(sep) if not count else text.split(sep, count)

                                com = sep(0)
                                com1 = sep(1)[0].lower()


                            # Префиксные команды
                                if re.fullmatch(pr_pat, text) or text.lower().split(' ')[0] in word_tuple:

                                    if text.lower() in word_tuple:

                                        ms("✓ Работаю")

                                # Ответы ключ-значение
                                    elif com1 in simple_answers:
                                        ms(simple_answers[com1])

                                # Команда обновлений
                                    elif (sep(1)[0] == "обновить" or sep(1)[0] == "update") and UsSend.scope == "Владелец":



                                        if sep(1)[1] == "админов" or sep(1)[1] == "admins":

                                            members = vk.method("messages.getConversationMembers", {
                                                "peer_id": event.object.peer_id
                                            })

                                            for i in members["items"]:

                                                if "is_admin" in i and i["is_admin"]:

                                                    sql = "UPDATE persons SET scope = ? WHERE user_id = ?;"
                                                    cursor.execute(sql, ["Владелец", i["member_id"]])
                                                    conn.commit()

                                                else:


                                                
                                                    if i["member_id"] > 0 and pe[i["member_id"]].scope == "Владелец":

                                                        up_bd("UPDATE persons SET scope = ? WHERE user_id = ?;", "Клиент", i["member_id"])

                                            ms("✓ Администраторы беседы обновлены")
                                            pe_update()

                                        elif sep(1)[1] == "пол" or sep(1)[1] == "gender":

                                            members = vk.method("messages.getConversationMembers", {
                                                "peer_id": event.object.peer_id,
                                                "fields": "sex"
                                            })

                                            for i in members["profiles"]:

                                                if i["id"]:

                                                    up_bd("UPDATE persons SET gender = ? WHERE user_id = ?;", i["sex"], i["id"])
                                                    

                                            ms("✓ Пол пользователей обновлен")
                                            pe_update()

                                        elif sep(1)[1] == "пользователей" or sep(1)[1] == "users":

                                            members = vk.method("messages.getConversationMembers", {
                                                "peer_id": event.object.peer_id,
                                                "fields": "sex"
                                            })

                                            for i in members["profiles"]:

                                                if not i["id"] in pe and i["id"]:

                                                    up_bd("INSERT INTO persons (user_id, first_name, last_name, scope, softmute, nickname, badge, all_msg, all_smb, gender, in_chat, marriage, marriage_date, ban, bl) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", i["id"], i["first_name"], i["last_name"], "Прохожий", 0, '', '', 0, 0, i['sex'], 1, 0, 0, 0, 0)
                                                    up_bd("INSERT INTO pers_stats (user_id) VALUES (?)", i["id"])

                                            sql = bd("SELECT user_id FROM pers_stats;")
                                            sql = [i[0] for i in sql]

                                            for i in range(len(members["profiles"])):

                                                if not (members["profiles"][i]["id"] in sql):
                                                    up_bd("INSERT INTO pers_stats (user_id) VALUES (?)", members["profiles"][i]["id"])


                                            
                                            ms("✓ Пользователи обновлены")
                                            pe_update()

                                        elif com[1] == "вышедших" or com[1] == "left":

                                            if len(com) >= 3:

                                                ids = com[2:]

                                                for i in ids:

                                                    if get_id(i):

                                                        up_bd("UPDATE persons SET in_chat = ? WHERE user_id = ?;", 0, get_id(i))

                                                        ms("✓ Значение {} изменено на <Вышедший>".format(mention(get_id(i), "Пользователя")))

                                                
                                            elif len(com) == 2:

                                                up_bd("UPDATE persons SET in_chat = ?;", 0)

                                                resp =  vk.method("messages.getConversationMembers", {
                                                    "peer_id": event.object.peer_id,
                                                    "fields": "sex"
                                                    })

                                                for i in resp['profiles']:

                                                    up_bd("UPDATE persons SET in_chat = ? WHERE user_id = ?;", 1, i['id'])

                                                ms("✓ Вышедшие пользователи обновлены")

                                            pe_update()

                                # Команды для работы с рп
                                    elif com1 == "rp" or com1 == "рп":

                                        command = ' '.join(com[2:]).split(' & ', 3)

                                    # Создает рп
                                        if len(com) >= 9 and (com[1] == 'new' or com[1] == 'новое') and len(command) == 4 and (not (command[3].lower() in rp)) and len(command[3].split(' ')) == 1:

                                            up_bd("INSERT INTO role_play (action_1, action_2, emoji, assoc) VALUES (?, ?, ?, ?)", command[0], command[1], command[2], command[3].lower())
                                            ms("✓ Действие <{}> добавлено".format(command[3].lower()))
                                            rp_update()

                                    # Удаляет рп
                                        elif len(com) == 3 and (com[1] == 'del' or com[1] == 'удалить') and com[2] in rp:

                                            up_bd("DELETE FROM role_play WHERE assoc = ?;", com[2])
                                            ms("✓ Действие <{}> удалено".format(com[2]))
                                            rp_update()

                                        elif len(com) == 2 and (com[1] == 'list' or com[1] == 'лист'):

                                            will_msg = "〽️Список всех действий:\n\n"
                                            counter = 1

                                            for j in rp.items():
                                                will_msg += '{}. "{}/{}" ({}) <{}>\n'.format(counter, j[1].action_1, j[1].action_2, j[1].emoji, j[0])
                                                counter +=1

                                            
                                            ms(will_msg)
                                            rp_update()

                                        else:
                                            ms()
        
                                # рп на себя
                                    elif com1 == "me" or com1 == "я":

                                        ms("{}. {} {}".format(UsSend.first_name[0], UsSend.last_name, ' '.join(com[1:])))
    
                                # Устанавливает ник 
                                    elif (com1 == "nick" or com1 == "ник"):

                                        if len(com) > 1 and len(sep(1)[1]) <= 25:

                                            up_bd("UPDATE persons SET nickname = ? WHERE user_id = ?;", sep(1)[1], UsSend.user_id)
                                            ms("✓ Ник обновлен")
                                            pe_update()

                                        else:
                                            ms()

                                # Устанавливает значок
                                    elif com1 == "badge" or com1 == "значок":

                                        if len(com) == 2 and len(com[1]) <= 2:

                                            up_bd("UPDATE persons SET badge = ? WHERE user_id = ?;", ' ' + com[1], UsSend.user_id)
                                            ms("✓ Значок обновлен")
                                            pe_update()

                                        else:
                                            ms()

                                # Инфо о пользователе
                                    elif com1 == "info" or com1 == "инфо":

                                        def get_info_about(us_id):

                                            members = get_conversation_members()

                                            mem_joined = bd("SELECT join_date FROM persons WHERE user_id = ?;", us_id)[0][0]

                                            if not mem_joined:
                                                for i in range(members["count"]):
                                                    if us_id == members["items"][i]["member_id"]:
                                                        mem_joined = members["items"][i]["join_date"] 


                                            name_last = mention(us_id, f"{pe[us_id].first_name} {pe[us_id].last_name}")
                                            is_in_chat =  True if pe[us_id].in_chat else False
                                            nick = pe[us_id].nickname
                                            badge = pe[us_id].badge
                                            scope = pe[us_id].scope

                                            mar = f"{pe[pe[us_id].marriage].first_name[0]}. {pe[pe[us_id].marriage].last_name}{pe[pe[us_id].marriage].badge} ({(int(time.time() ) - pe[us_id].marriage_date) // 86400}дн)" if pe[us_id].marriage else "Не замужем" if pe[us_id].gender == 1 else "Не женат"
                                            
                                            join_date = "c " + str(time.strftime("%d.%m.%Y %H:%M", time.localtime(mem_joined))) if is_in_chat else "Нет"
                                            join_dif = f" ({(int(time.time() ) - mem_joined) // 86000}дн)" if is_in_chat else ''

                                            sql = bd("SELECT all_smb, all_msg FROM persons WHERE user_id = ?;", us_id)
                                            us_smb = sql[0][0]
                                            us_msg = sql[0][1]

                                            ms("📂 Информация об участнике {}\nНик: {}\nЗначок:{}\nСтатус: {}\nВ браке: {}\n\nВ чате: {}{}\nСимволов | Сообщений\n{} | {}".format(name_last, nick, badge, scope, mar, join_date, join_dif, us_smb, us_msg))


                                        if len(com) == 1:

                                            if UsReply:
                                                get_info_about(UsReply.user_id)

                                            elif UsFrw:
                                                get_info_about(UsFrw.user_id)
                                            
                                            else:
                                                get_info_about(UsSend.user_id)

                                        elif len(com) == 2:

                                            us_id = get_id(com[1])

                                            if us_id:

                                                get_info_about(us_id)

                                            else:
                                                ms()

                                # Повышает статус пользователю
                                    elif com1 == "статус" or com1 == "status":

                                        if UsSend.scope in ("Владелец" , "Бариста"):

                                            def up_status(us_id, scope):

                                                if UsSend.scope != scope:

                                                    up_bd("UPDATE persons SET scope = ? WHERE user_id = ?", scope.title(), us_id)

                                                    ms("Статус {} изменился на <{}>".format(mention(us_id, "Пользователя"), scope.title()))
                                                    pe_update()
                                                    ###ADMINS###
                                                    adminsPusher("chat_update_scope <{}>".format(scope.title()), UsSend, [pe[us_id]])
                                                    ###ADMINS###

                                                else:
                                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                                

                                            if len(com) == 2:

                                                if com[1].lower() == "клиент" or com[1].lower() == "бариста":

                                                    if UsReply and UsSend.user_id != UsReply.user_id:

                                                        up_status(UsReply.user_id, com[1])
                                                        

                                                    elif UsFrw and UsFrw.user_id != UsSend.user_id:

                                                        up_status(UsFrw.user_id, com[1])

                                                    else:
                                                        ms()

                                            elif len(com) >= 3:

                                                for i in com[2:]:

                                                    if com[1].lower() == "клиент" or com[1].lower() == "бариста" and get_id(i):

                                                        up_status(get_id(i), com[1])
                                                        
                                                    else:
                                                        ms()

                                            else:
                                                ms()

                                        else:
                                            ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                # Состав
                                    elif com1 == "состав" or com1 == "staff":

                                        members = bd('SELECT user_id, badge, scope FROM persons WHERE in_chat = ?;', 1)

                                        will_msg = "〽️Список пользователей беседы с их статусами:\n\nВладельцы:\n"

                                        counter = 1

                                        for i in range(len(members)):
                                            if members[i][2] == 'Владелец':
                                                will_msg += '{}. {}{}\n'.format(counter, pe[members[i][0]].men(), members[i][1])
                                                counter += 1 
                                        
                                        counter = 1

                                        will_msg += "\nБаристы:\n"

                                        for i in range(len(members)):
                                            if members[i][2] == 'Бариста':
                                                will_msg += '{}. {}{}\n'.format(counter, pe[members[i][0]].men(), members[i][1])
                                                counter += 1 
                                        
                                        counter = 1

                                        will_msg += "\n\nКлиенты:\n"

                                        for i in range(len(members)):
                                            if members[i][2] == 'Клиент':
                                                will_msg += '{}. {}{}\n'.format(counter, pe[members[i][0]].men(), members[i][1])
                                                counter += 1 
                                        
                                        counter = 1

                                        will_msg += "\n\nПрохожие:\n"

                                        for i in range(len(members)):
                                            if members[i][2] == 'Прохожий':
                                                will_msg += '{}. {}{}\n'.format(counter, pe[members[i][0]].men(), members[i][1])
                                                counter += 1 

                                        ms(will_msg)
                                        
                                # Онлайн
                                    elif com1 == "онлайн" or com1 == "online":

                                        members = vk.method("messages.getConversationMembers", {"peer_id": event.object.peer_id})
                                        will_msg = "〽️Список пользователей онлайн:\n\n" 
                                        numbers = 1

                                        for i in members["profiles"]:

                                            if i["online"] == 1:

                                                sql = bd("SELECT first_name, last_name, badge FROM persons WHERE user_id = ?;", i["id"])

                                                will_msg += "{}. {} {}{}\n".format(numbers, sql[0][0], sql[0][1], sql[0][2])
                                                numbers += 1

                                        ms(will_msg)

                                # Исключает пользователя
                                    elif com1 == "кик" or com1 == "kick":

                                        if UsSend.scope == "Владелец" or UsSend.scope == "Бариста":

                                            def kicker(obj, **kwargs):

                                                if UsSend.scope in ("Владелец", "Бариста" ) and obj.scope != UsSend.scope and UsSend.user_id != obj.user_id and obj.scope != "Владелец" :

                                                    ms("{} будет исключен".format(mention(obj.user_id, "Пользователь")))
                                                    kick(obj.user_id)
                                                    pe_update()
                                                    ###ADMINS###
                                                    adminsPusher("chat_kick_user", UsSend, [obj])
                                                    ###ADMINS###

                                            
                                                else:

                                                    ms("❕Нельзя исключить пользователя с таким же как у вас статусом <{}> или выше".format(UsSend.scope))


                                            if len(com) == 1:

                                                if UsReply:

                                                    kicker(UsReply)

                                                elif UsFrw:

                                                    kicker(UsFrw)

                                                else:
                                                    ms()

                                            if len(com) >=2:

                                                for i in com[1:]:

                                                    us_id = get_id(i)

                                                    if us_id:

                                                        kicker(pe[us_id])

                                        else:
                                            ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))
                                    
                                # Банит пользователя перманентно

                                    elif com1 == "пермбан" or com1 == "permban":

                                        def perm(obj):

                                            if UsSend.scope == 'Владелец':

                                                if UsSend.scope != obj.scope and UsSend.user_id != obj.user_id:

                                                    if obj.in_chat:

                                                        ms("✓ {} получил пермбан и будет исключен".format(mention(obj.user_id, "Пользователь")))
                                                        kick(obj.user_id)
                                                        up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", -1, obj.user_id)

                                                    else:

                                                        up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", -1, obj.user_id)
                                                        ms("✓ {} получил пермбан".format(mention(obj.user_id, "Пользователь")))

                                                    ###ADMINS###
                                                    adminsPusher("chat_perm_user", UsSend, [obj])
                                                    ###ADMINS###

                                                    pe_update()

                                                else:

                                                    ms("❕Нельзя исключить пользователя с таким же как у вас статусом <{}> или выше".format(UsSend.scope))

                                            else:
                                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                        if len(com) == 1:

                                            if UsReply:

                                                perm(UsReply)

                                            elif UsFrw:

                                                perm(UsFrw)

                                            else:
                                                ms()

                                        else:

                                            for i in com[1:]:

                                                us_id = get_id(i)

                                                if us_id:

                                                    perm(pe[us_id])

                                # Бан на время
                                    elif com1 == "бан" or com1 == "ban":

                                        def ban(obj, timer):

                                            if UsSend.scope == "Владелец":

                                                if UsSend.user_id != obj.user_id:


                                                    t = eval(' '.join(timer).replace("m", "60").replace("м", "60").replace("ч", "3600").replace("h", "3600").replace("d", "86400").replace("д", "86400").replace(",", "."))

                                                    setter_time = int(time.time()) + t + 3600*3

                                                    if obj.in_chat:
                                                        
                                                        ms("{} получил бан до [{}] и будет исключен".format(mention(obj.user_id, "Пользователь"), time.strftime("%d.%m.%Y %H:%M", time.localtime(setter_time))))
                                                        bd("UPDATE persons SET ban = ? WHERE user_id = ?;", setter_time, obj.user_id)
                                                        kick(obj.user_id)

                                                    else:

                                                        ms("{} получил бан до [{}]".format(mention(obj.user_id, "Пользователь"), time.strftime("%d.%m.%Y %H:%M", time.localtime(setter_time))))
                                                        bd("UPDATE persons SET ban = ? WHERE user_id = ?;", setter_time, obj.user_id)

                                                    pe_update()
                                                    ###ADMINS###
                                                    adminsPusher("chat_ban_user", UsSend, [obj])
                                                    ###ADMINS###



                                                else:
                                                    ms("❕Данная команда неприменима к себе")


                                            else:
                                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                        if UsReply:

                                            ban(UsReply, com[1:])

                                        elif UsFrw:

                                            ban(UsFrw, com[1:])

                                        else:

                                            us_id = get_id(com[1])

                                            if us_id:

                                                ban(pe[us_id], com[2:])

                                            else:
                                                ms()
                            
                                # Снимает бан
                                    elif com1 == "разбан" or com1 == "unban":

                                        def unban(obj):

                                            if UsSend.scope == "Владелец":

                                                if UsSend.scope != obj.scope:

                                                    up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", 0, obj.user_id)

                                                    ms("✓ С {} снят бан".format(mention(obj.user_id, "Пользователя")))

                                                    pe_update()

                                                    ###ADMINS###
                                                    adminsPusher("chat_unban_user", UsSend, [obj])
                                                    ###ADMINS###

                                                else:
                                                    
                                                    ms("❕Нельзя исключить пользователя с таким же как у вас статусом <{}> или выше".format(UsSend.scope))

                                            else:

                                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                        if UsReply:

                                            unban(UsReply)

                                        elif UsFrw:

                                            unban(UsFrw)

                                        else:

                                            for i in com[1:]:

                                                us_id = get_id(i)

                                                if us_id:

                                                    unban(pe[us_id])

                                # Список участников в бане

                                    elif com1 == "банлист" or com1 == "banlist":

                                        sql = bd("SELECT first_name, last_name, badge FROM persons WHERE ban < ?;", 0)
                                        msg_will = "〽️Список пользователей с банами:\n\n"

                                        count = 1

                                        for i in range(len(sql)):

                                            msg_will += "{}. {} {}{} [Пермь]\n".format(count, sql[i][0], sql[i][1], sql[i][2])
                                            count += 1

                                        sql = bd("SELECT user_id, badge, ban FROM persons WHERE ban > ?;", 0)

                                        sql = sorted(sql, key=operator.itemgetter(3), reverse = True)

                                        for i in range(len(sql)):

                                            msg_will += "{}. {}{} [до {}]\n".format(count, pe[sql[i][0]].men(), sql[i][1], time.strftime("%d.%m.%Y %H:%M", time.localtime(sql[i][3])))

                                            count += 1

                                        ms(msg_will if len(msg_will) != 34 else "Список с пользователями в бане пуст")

                                # Список участников в браке

                                    elif com1 == "браки" or com1 == "marriage":

                                        sql = bd("SELECT marriage_date FROM persons WHERE marriage > ?;", 0)

                                        li = sorted(list(set([sql[i][0] for i in range(len(sql))])))

                                        will_msg = "〽️Список зарегестрированных браков:\n\n"
                                        
                                        for i in range(len(li)):

                                            sql1 = bd("SELECT user_id, badge FROM persons WHERE marriage_date = ?;", li[i])

                                            will_msg += "{}. {}{} и {}{} ({}дн)\n".format(i + 1, pe[sql1[0][0]].men(), sql1[0][1], pe[sql1[1][0]].men(), sql1[1][1], (int(time.time() ) - li[i]) // 86400)

                                        ms(will_msg) if len(li) else ms("Браков нет")

                                # Топ пользователей
                                    elif recod_com == "топ чата" or recod_com == "top chat":

                                        will_msg = "〽️Топ пользователей чата за все время [Символы / Сообщения]:\n"
                            
                                        sql = bd("SELECT first_name, last_name, badge, all_smb, all_msg FROM persons WHERE all_smb > ? AND in_chat = ?;", 0, 1)
                            
                                        some = sorted(sql, key=operator.itemgetter(3), reverse = True)

                                        for i in range(len(some)):

                                            will_msg += '{}. {} {}{} [{} / {}]\n'.format(i + 1, some[i][0], some[i][1], some[i][2], some[i][3], some[i][4])
                            
                                        ms(will_msg)
                            
                                # ID

                                    elif com1 == "айди" or com1 == "id":

                                        if UsReply:

                                            ms(UsReply.user_id)

                                        elif UsFrw:

                                            ms(UsFrw.user_id)

                                        else:

                                            if len(com) == 2 and get_id(com[1]):

                                                get_id(ms(com[1]))

                                # Квиз

                                    elif recod_com == "квиз" or recod_com == "quiz":

                                        date_now1 = date("%d.%m.%Y")

                                        date_yest = date("%d.%m.%Y", h=-21)

                                        sql = bd("SELECT Q FROM quiz WHERE date = ?;", date_now1)

                                        if len(sql):

                                            sql1 = bd("SELECT A FROM quiz WHERE date = ?;", date_yest)

                                            ms("🔎 Вопрос на {} \n\nQ: {}\n\n{}".format(date_now1, sql[0][0], "Ответ на прошлый вопрос: {}".format(sql1[0][0]) if len(sql1) else ""))

                                # Команда статы
                                    elif com1 == "стата" or com1 == "stat":

                                        def get_stat_sm(obj, days=7):

                                            adder_msg = ""

                                            counter_days = 0

                                            for i in range(0, 86400 * days, 86400):

                                                date_now = time.strftime("%d_%m_%Y", time.localtime(time.time() - i ))


                                                try:

                                                    sql = "SELECT {}, {} FROM pers_stats WHERE user_id = ?;".format("s{}".format(date_now), "m{}".format(date_now))
                                                    cursor.execute(sql, [obj.user_id])
                                                    sql_bd = cursor.fetchall()
                                                    
                                                    if sql_bd[0][0] + sql_bd[0][1] or days != 7:

                                                        adder_msg += "{} -- [{} / {}]\n".format(date_now.replace("_", "."), sql_bd[0][0], sql_bd[0][1])

                                                        counter_days = ((i + 86400)// 86400)

                                                    else:

                                                        counter_days = (i// 86400)

                                                        break

                                                except:
                                                    
                                                    counter_days = (i// 86400)

                                                    break

                                            will_msg = "📂 Статистика {}{} за {}д:\n{}".format(obj.nickname if len(obj.nickname) else obj.first_name, obj.badge, counter_days, adder_msg)

                                            ms(will_msg)

                                        if com[1] == 'сс' or com[1] == 'sm':

                                            if len(com) == 2:

                                                if UsReply:

                                                    get_stat_sm(UsReply)

                                                elif UsFrw:

                                                    get_stat_sm(UsFrw)

                                                else:

                                                    get_stat_sm(UsSend)

                                            elif len(com) == 3:

                                                if com[2].isdigit():

                                                    get_stat_sm(UsSend, int(com[2]))

                                                elif get_id(com[2]):

                                                    get_stat_sm(pe[get_id(com[2])])

                                                else:
                                                    ms()

                                            elif len(com) == 4 and com[3].isdigit() and get_id(com[2]):

                                                    get_stat_sm(pe[get_id(com[2])], int(com[3]))

                                            else:
                                                ms()


                                        elif len(sep(0)) > 2 and (sep(0)[1].lower() == "чата" or sep(0)[1].lower() == "chat"):

                                            if sep(0)[2].lower() == "сс" or sep(0)[2].lower() == "sm":

                                                def get_chat_stat_sm(days):

                                                    adder_msg = ""

                                                    counter_days = None

                                                    for i in range(0, 86400 * days, 86400):

                                                        date_now = time.strftime("%d_%m_%Y", time.localtime(time.time()  - i))

                                                        try:

                                                            sql = "SELECT {}, {} FROM pers_stats;".format("s{}".format(date_now), "m{}".format(date_now))
                                                            cursor.execute(sql)
                                                            sql_bd = cursor.fetchall()

                                                            sym = 0
                                                            msg = 0
                                                            # Общее кол-во символов и сообщений
                                                            for j in sql_bd:
                                                                sym += j[0]
                                                                msg += j[1]

                                                            adder_msg += "{} -- [{} / {}]\n".format(date_now.replace("_", "."), sym, msg)

                                                            counter_days = ((i+86400) // 86400)

                                                        except:
                                                            
                                                            counter_days = (i // 86400)

                                                            break


                                                    will_msg = "📂 Статистика чата за {}д:\n{}".format(counter_days, adder_msg)

                                                    return will_msg

                                                if len(sep(0)) == 3:

                                                    ms(get_chat_stat_sm(7))

                                                elif len(sep(0)) == 4 and sep(0)[3].isdigit():


                                                    ms(get_chat_stat_sm(int(sep(0)[3])))


                                                else:

                                                    ms()

                                        else:

                                            ms()

                                # clear-команды
                                    elif com1 == "очистить" or com1 == "clear":

                                        if com[1] == "баны" or com[1] == "bans":

                                            if UsSend.scope == "Владелец":

                                                sql = bd("SELECT user_id FROM persons;")

                                                for i in range(len(sql)):

                                                    up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", 0, sql[i][0])
                                                    pe_update()
                                                    ###ADMINS###
                                                    adminsPusher("chat_clear_bans", UsSend)
                                                    ###ADMINS###

                                                ms("✓ Список банов очищен")

                                            else:
                                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                # Работа с квизом

                                    elif com1 == "квиз" or com1 == "quiz":

                                        if len(com) > 2 and (com[1] == "добавить" or com[1] == "add") and event.object.peer_id == 2000000002:

                                            if len(com) == 3 and re.fullmatch(r"\d\d\.\d\d\.\d\d\d\d", com[2]):

                                                sql = bd("SELECT date FROM quiz WHERE date = ?;", com[2])

                                                if not len(sql):

                                                    up_bd("""INSERT INTO quiz 
                                                    (date, Q, A)
                                                    VALUES
                                                    (?, ?, ?)""", com[2], '', '')

                                                    ms("✓ Ячейка на {} создана".format(sep(0)[2]))

                                                else:
                                                    ms("❕Такая ячейка существует")

                                            else:
                                                ms("❕Некорректный формат даты")

                                        elif len(sep(0)) > 2 and re.fullmatch(r"\d\d\.\d\d\.\d\d\d\d", sep(0)[1]) and event.object.peer_id == 2000000002:

                                            sql = bd("SELECT date FROM quiz WHERE date = ?;", com[1])

                                            if len(sql):

                                                if sep(0)[2].lower() == "в" or sep(0)[2].lower() == "q":

                                                    up_bd("UPDATE quiz SET Q = ? WHERE date = ?;", sep(3)[3], com[1])

                                                    ms("✓ Вопрос на {} создан".format(sep(0)[1]))

                                                elif sep(0)[2].lower() == "о" or sep(0)[2].lower() == "a":

                                                    up_bd("UPDATE quiz SET A = ? WHERE date = ?;", sep(3)[3], com[1])

                                                    ms("✓ Ответ на {} создан".format(sep(0)[1]))

                                                else:
                                                    ms("❕Неправильный формат команды")


                                        elif len(sep(0)) == 2 and (sep(0)[1].lower() == "лист" or sep(0)[1].lower() == "list") and event.object.peer_id == 2000000002:

                                            will_msg = "〽️Список добавленных квизов:\n\n"
                                            date1 = time.strftime("%d.%m.%Y", time.localtime(time.time() + 3 * 3600))

                                            for i in range(0,1000):

                                                try:

                                                    date1 = time.strftime("%d.%m.%Y", time.localtime(time.time()  + i*86400))

                                                    sql = bd("SELECT Q, A FROM quiz WHERE date = ?;", date1)

                                                    will_msg += "{}\nQ: {}\nA: {}\n\n".format("{} -- ({})".format(i + 1, date1), sql[0][0], sql[0][1])

                                                except:

                                                    break

                                            ms(will_msg)

                                        else:
                                            ms()

                                # Команда позывалка
                                    elif com1 == "позвать" or com1 == "call":

                                        def calling(name, last):

                                            if name.lower() != 'лети' and name.lower() != 'гин':

                                                sql = bd("SELECT user_id, first_name, last_name FROM persons;")

                                                for i in sql:

                                                    if re.search(name.lower(), i[1].lower()) and re.search(last.lower(), i[2].lower()):

                                                        return i[0]

                                                return False

                                            else:

                                                if name.lower() == 'лети':
                                                    return 535314275
                                                elif name.lower() == 'гин':
                                                    return 522782777

                                                

                                        if len(sep(1)) == 1:

                                            if UsReply:

                                                ms("{}{}, вас вызывает {}{}!".format(mention(UsReply.user_id, UsReply.nickname if len(UsReply.nickname) else UsReply.first_name), UsReply.badge, UsSend.nickname if len(UsSend.nickname) else UsSend.first_name, UsSend.badge), 0)

                                            if UsFrw:

                                                ms("{}{}, вас вызывает {}{}!".format(mention(UsFrw.user_id, UsFrw.nickname if len(UsFrw.nickname) else UsFrw.first_name), UsFrw.badge, UsSend.nickname if len(UsSend.nickname) else UsSend.first_name, UsSend.badge), 0)

                                            else:

                                                ms()


                                        elif len(com) == 2 or len(com) == 3:

                                            a = calling(com[1].title(), com[2].title() if len(com) == 3 else '')

                                            if a:

                                                UsFree = pe[a]

                                                ms("{}{}, вас вызывает {}{}!".format(mention(UsFree.user_id, UsFree.nickname if len(UsFree.nickname) else UsFree.first_name), UsFree.badge, UsSend.nickname if len(UsSend.nickname) else UsSend.first_name, UsSend.badge), 0)

                                            else:

                                                ms("❕Пользователь {} {} не найден ".format(sep(0)[1].title(), sep(0)[2].title() if len(sep(0)) == 3 else ''), 0)

                                        else:

                                            ms()

                                # чс
                                    elif com1 == "чс" or com1 == "bl":

                                        if len(com) == 2 and (com[1] == 'лист' or com[1] == 'лист'):

                                            sql = bd("SELECT user_id, badge FROM persons WHERE bl = ?;", 1)

                                            will_msg = "〽️Список пользователей в черном списке:\n\n"

                                            for i in range(len(sql)):

                                                will_msg += "{}. {}{}\n".format(i + 1, pe[sql[i][0]].men(), sql[i][1],)

                                            ms(will_msg if len(will_msg) != 41 else "Список пользователей в черном списке пуст")

                                        elif len(com) == 2 and (com[1] == 'очистить' or com[1] == 'clear'):

                                            if UsSend.scope == "Владелец":

                                                up_bd("UPDATE persons SET bl = ?", 0)
                                                ms("✓ Список с пользователями в черном списке очищен")
                                                pe_update()

                                            else:
                                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                        elif UsSend.scope == "Владелец":

                                            def to_bl(us_id):

                                                if UsSend.user_id != us_id and pe[us_id].scope != "Владелец":

                                                    sql = bd("SELECT bl FROM persons WHERE user_id = ?;", us_id)

                                                    if sql[0][0]:

                                                        up_bd("UPDATE persons SET bl = ? WHERE user_id = ?;", 0, us_id)

                                                        ms("✓ {} убран из черного списка".format(mention(us_id, "Пользователь")))

                                                        ###ADMINS###
                                                        adminsPusher("chat_from_bl_user", UsSend, [pe[us_id]])
                                                        ###ADMINS###

                                                    else:

                                                        up_bd("UPDATE persons SET bl = ? WHERE user_id = ?;", 1, us_id)

                                                        ms("✓ {} занесен в черный список бота".format(mention(us_id, "Пользователь")))

                                                        ###ADMINS###
                                                        adminsPusher("chat_to_bl_user", UsSend, [pe[us_id]])
                                                        ###ADMINS###

                                                    

                                                    pe_update()

                                            if UsReply:

                                                to_bl(UsReply.user_id)

                                            elif UsFrw:

                                                to_bl(UsFrw.user_id)

                                            elif len(com) >= 2:

                                                for i in com[1:]:

                                                    user_id1 = get_id(i)

                                                    if user_id1:

                                                        to_bl(user_id1)

                                                    else:
                                                        ms()
                                                        break

                                            else:
                                                ms()

                                # Софтмут

                                    elif com1 == "мут" or com1 == "mute":

                                        def softmute(obj):

                                            if UsSend.scope in ("Владелец", "Бариста") and UsSend.user_id != obj.user_id and UsSend.scope != obj.scope and obj.scope != "Владелец":

                                                if obj.softmute:

                                                    up_bd("UPDATE persons SET softmute = ? WHERE user_id = ?;", 0, obj.user_id)

                                                    ms("✓ {} лишился мута".format(mention(obj.user_id, "Пользователь")))
                                                    ###ADMINS###
                                                    adminsPusher("chat_from_mute_user", UsSend, [obj])
                                                    ###ADMINS###

                                                else:

                                                    up_bd("UPDATE persons SET softmute = ? WHERE user_id = ?;", 1, obj.user_id)

                                                    ms("✓ {} получил мут".format(mention(obj.user_id, "Пользователь")))

                                                    ###ADMINS###
                                                    adminsPusher("chat_to_mute_user", UsSend, [obj])
                                                    ###ADMINS###
                                                
                                                pe_update()

                                            else:
                                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                                        if len(com) == 2 and (com[1] == "лист" or com[1] == "list"):

                                            will_msg = "〽️Список пользователей в муте:\n\n"

                                            counter = 1

                                            for i in list(pe.values()):

                                                if i.softmute:

                                                    will_msg += "{}. {} {}{}".format(counter, i.first_name, i.last_name, i.badge)
                                                    counter +=1

                                            ms(will_msg if len(will_msg) != 32 else "Список с пользователями в муте пуст")

                                        elif UsReply:

                                            softmute(UsReply)

                                        elif UsFrw:

                                            softmute(UsFrw)

                                        elif len(com) >= 2:

                                            ids = com[1:]

                                            for i in ids:

                                                us_id = get_id(i)

                                                if us_id:

                                                    softmute(pe[us_id])

                                # Развод
                                    
                                    elif com1 == "развод" or com1 == "divorce":

                                        if UsSend.marriage:

                                            up_bd("UPDATE persons SET marriage = ?, marriage_date = ? WHERE user_id = ?;", 0, 0, UsSend.user_id)
                                            up_bd("UPDATE persons SET marriage = ?, marriage_date = ? WHERE user_id = ?;", 0, 0, UsSend.marriage)
                                            ms("Брак с {} расторжен 💔".format(mention(UsSend.marriage, "Пользвоателем")))
                                            pe_update()

                                        else:
                                            ms("❕У вас нет зарегестрированного брака")

                                # Заключение браков
                                    elif com1 == "брак" or com1 == "marriage":

                                        if not UsSend.marriage:

                                            def set_mar(obj):

                                                if not obj.marriage:

                                                    mr_date.append(event.object.date + 120)
                                                    mr_pe.append(obj.user_id)
                                                    mr_from_pe.append(UsSend.user_id)

                                                    ms('{}, согласны ли вы вступить в брак с {}?\n("офи брак да"/"офи брак нет")'.format(mention(obj.user_id, "{} {}{}".format(obj.first_name, obj.last_name, obj.badge)), mention(UsSend.user_id, UsSend.first_name)))

                                                else:
                                                    ms("Не приставай к {})".format("замужним" if pe[us_id].gender == 1 else "женатым"))

                                            if UsReply:

                                                set_mar(UsReply)

                                            elif UsFrw:

                                                set_mar(UsFrw)

                                            elif len(com) == 2:

                                                if get_id(com[1]):

                                                    set_mar(pe[get_id(com[1])])

                                                elif com[1] == "да":

                                                    if UsSend.user_id in mr_pe:

                                                        ms("Брак заключен 🎉")

                                                        date_index = mr_pe.index(UsSend.user_id)

                                                        up_bd("UPDATE persons SET marriage = ?, marriage_date = ? WHERE user_id = ?;", mr_pe[date_index], mr_date[date_index], mr_from_pe[date_index])
                                                        up_bd("UPDATE persons SET marriage = ?, marriage_date = ? WHERE user_id = ?;", mr_from_pe[date_index], mr_date[date_index], mr_pe[date_index])

                                                        mr_date.pop(date_index)
                                                        mr_pe.remove(UsSend.user_id)

                                                        pe_update()


                                                    else:

                                                        ms("❕Заявка на брак не найдена")

                                                        

                                                elif com[1] == "нет":

                                                    if UsSend.user_id in mr_pe:

                                                        ms("Брак не может состояться 💔")

                                                        date_index = mr_pe.index(UsSend.user_id)

                                                        mr_date.pop(date_index)
                                                        mr_pe.remove(UsSend.user_id)

                                                    else:
                                                        ms("❕Заявка на брак не найдена")
                                        else:
                                            ms("Изменять {}?".format("вздумала" if UsSend.gender == 1 else "вздумал"))
                                                
                                # Сводка

                                    elif com1 == "сводка" or com1 == "sumarry":

                                        def summary(obj):

                                            obj.setSummary()
                                            chat = Chat()

                                            msg = """📂 Сводка участника {}:\n\n[Всего (от кол-ва своих сообщений, от кол-ва сообщений чата, от кол-ва значения всех)]\n• Маты: {} ({}% | {}% | {}%)\n• Вложения: {} ({}% | {}% | {}%)\n• ГС: {} ({}% | {}% | {}%)\n\n• Символов: {} ({}%)\n• Сообщений: {} ({}%)\n• Последний актив: {} назад""".format(
                                            obj.men(),
                                            obj.swears, toFixed(obj.swears / obj.all_msg * 100, 2), toFixed(obj.swears / chat.all_msg * 100, 2), toFixed(obj.swears / chat.swears * 100, 2),
                                            obj.atts, toFixed(obj.atts / obj.all_msg * 100, 2), toFixed(obj.atts / chat.all_msg * 100, 2), toFixed(obj.atts / chat.atts * 100, 2),
                                            obj.gs, toFixed(obj.gs / obj.all_msg * 100, 2), toFixed(obj.gs / chat.all_msg * 100, 2), toFixed(obj.gs / chat.gs * 100, 2),
                                            obj.all_smb, toFixed(obj.all_smb / chat.all_smb * 100, 2) ,
                                            obj.all_msg, toFixed(obj.all_msg / chat.all_msg * 100, 2),
                                            simpleDiffirentTime(event.object.date, obj.last_active),
                                            )

                                            ms(msg)

                                        if UsReply:

                                            summary(UsReply)

                                        elif UsFrw:

                                            summary(UsFrw)

                                        elif len(com) == 2:

                                            if get_id(com[1]):

                                                summary(pe[get_id(com[1])])

                                        else:

                                            summary(UsSend)

                                # Актив

                                    elif com1 == "актив" or com1 == "active":

                                        def get_active():

                                            sql = bd("SELECT user_id, last_active FROM persons WHERE in_chat = ? ORDER BY last_active DESC;", 1)

                                            will_msg = "Последняя активность пользователей (назад):\n\n"

                                            t = event.object.date

                                            for i in range(len(sql)):

                                                will_msg += "{}. {}{} {}\n".format(i+1, pe[sql[i][0]].men(), pe[sql[i][0]].badge, simpleDiffirentTime(t,sql[i][1]) if sql[i][1] else "[неактив]")
                                        
                                            ms(will_msg)

                                        get_active()

                                # wiki
                                    elif com1 == "вики" or com1 == "wiki":

                                        if len(com) >= 2:

                                            ms(str(wikipedia.summary(com[1:], sentences=5)))

                                        else:
                                            ms()

                            # Беспрефиксные команды
                                else:

                                    text_sep =  text.split(' ', 1)

                                    
                                # Ответы на рп
                                    if text_sep[0].lower() in rp:

                                        act = rp[text_sep[0].lower()]

                                        if len(text_sep) == 1:

                                            if UsReply:
                                                ms("{}. {} {} {}. {} {}".format(UsSend.first_name[0], UsSend.last_name, act.action_1 if UsSend.gender == 2 else act.action_2, UsReply.first_name[0], UsReply.last_name, act.emoji))

                                            elif UsFrw:
                                                ms("{}. {} {} {}. {} {}".format(UsSend.first_name[0], UsSend.last_name, act.action_1 if UsSend.gender == 2 else act.action_2, UsFrw.first_name[0], UsFrw.last_name, act.emoji))

                                            else:
                                                ms()

                                        elif len(text_sep) == 2:

                                            text_split = text_sep[1].lower()

                                            if "вс" in text_split:

                                                ms("{}. {} {} {} {}".format(UsSend.first_name[0], UsSend.last_name, act.action_1 if UsSend.gender == 2 else act.action_2, text_split, act.emoji))

                                            else:

                                                us_id = get_id(text_split)

                                                if us_id:

                                                    ms("{}. {} {} {}. {} {}".format(UsSend.first_name[0], UsSend.last_name, act.action_1 if UsSend.gender == 2 else act.action_2, pe[us_id].first_name[0], pe[us_id].last_name, act.emoji))

                                                else:
                                                    ms()

                                        else:
                                            ms()

                                # Команда инфы
                                    elif text_sep[0].lower() == 'инфа' or text_sep[0].lower() == 'chance':

                                        if len(text_sep) > 1:

                                            ms("{}{}, вероятность того, что {} -- {}% &#127861;".format(UsSend.nickname if len(UsSend.nickname) else UsSend.first_name, UsSend.badge, text_sep[1], random.randint(0, 100)))

                                        else:
                                            ms("Инфа чего?")

                                # Команда выбери
                                    elif text_sep[0].lower() == 'выбери' or text_sep[0].lower() == 'choice':

                                        if len(text_sep) > 1:

                                            ms("{}{}, я выбираю -- {} &#129371;".format(UsSend.nickname if len(UsSend.nickname) else UsSend.first_name, UsSend.badge, random.choice(text_sep[1].replace(' or ', ' или ').split(' или '))))

                                        else:
                                            ms("Что выбрать?")

                                # Команда кто
                                    elif text_sep[0].lower() == 'кто' or text_sep[0].lower() == 'who':

                                        if len(text_sep) > 1:

                                            list_of_answers = (" мне кажется, что ", " я уверен, ", " уже каждый знает, что ", " никому не рассказывай, ведь ", " ЛоТ мне в ЧГК! ")
                                            
                                            r_p = random.sample(pe_ic.keys(), 1)

                                            ms("{}{},{}{} -- {}  ☕️".format(UsSend.nickname if len(UsSend.nickname) else UsSend.first_name, UsSend.badge, random.choice(list_of_answers), text_sep[1], mention(r_p[0], pe[r_p[0]].nickname if len(pe[r_p[0]].nickname) else pe[r_p[0]].first_name)))

                                        else:
                                            ms("Никто...")

                                # Бутылочка
                                    elif text.lower() == 'бутылочка' or text.lower() == 'bottle':

                                        r_p = random.sample(pe_ic.keys(), 2)

                                        ms("{}{} и {}{} -- прекрасная пара 💛".format(pe[r_p[0]].men(), pe[r_p[0]].badge, pe[r_p[1]].men(), pe[r_p[1]].badge)) 

                                    elif text.lower() == "кай заметка сон":
                                        ms("Текст заметки: Бурной ночи, пошлых снов")

                            # Обрабатывает время браков
                                for i in mr_date:

                                    t = event.object.date

                                    if t > i:

                                        ind = mr_date.index(i)

                                        UsFree = pe[mr_pe[ind]]

                                        ms("{}, время для ответа вышло!".format(mention(UsFree.user_id, UsFree.first_name)))

                                        mr_date.pop(ind)
                                        mr_from_pe.pop(ind)
                                        mr_pe.pop(ind)
            
                    # Надбавка кол-ва значений
                        up_bd("UPDATE persons SET all_msg = all_msg + ?, all_smb = all_smb + ?, last_active = ? WHERE user_id = ?;", 1, len(event.object.text), event.object.date, event.object.from_id)
                        up_bd("UPDATE pers_stats SET {0} = {0} + ?, {1} = {1} + ? WHERE user_id = ?;".format(date("m%d_%m_%Y"), date("s%d_%m_%Y")), 1, len(event.object.text), event.object.from_id)
                        if len(event.object.attachments) and event.object.attachments[0]["type"] == "audio_message":
                            up_bd("UPDATE persons SET last_active = last_active + ? WHERE user_id = ?;", 1, event.object.from_id)
                        if len(event.object.attachments):
                            up_bd("UPDATE persons SET atts = atts + ? WHERE user_id = ?;", len(event.object.attachments), event.object.from_id)
                        mat = ["хуй", "хуя", "хуе" "eба", "пизд", "бля", "еби"]
                        for i in mat:
                            if i in event.object.text:
                                up_bd("UPDATE persons SET swears = swears + ? WHERE user_id = ?;", 1, event.object.from_id)










            ###ADMINS CHAT###

                elif event.object.peer_id == 2000000003: 


                # Создание объектов по пользователю
                    UsSend = pe[event.object.from_id]
                    UsReply = False
                    UsFrw = False

                    text = event.object.text
                    recod_com = ' '.join(text.split(' ')[1:]) if re.fullmatch(r'jd.+', text.lower()) else False

                    if recod_com:

                        if 'reply_message' in event.object and event.object.reply_message['from_id'] > 0:
                            UsReply = pe[event.object.reply_message['from_id']]

                        elif len(event.object.fwd_messages) != 0 and event.object.fwd_messages[0]['from_id'] > 0 and event.object.fwd_messages[0]['from_id'] in pe:
                            UsFrw = pe[event.object.fwd_messages[0]['from_id']]

                    # Функции для работы с сообщением пользвоателя
                        def sep(count = 1, sep = ' ', text = recod_com):
                            return text.split(sep) if not count else text.split(sep, count)

                        def sep_wp(count = 1, sep = ' ', text = text):
                            return text.split(sep) if not count else text.split(sep, count)

                        com = sep(0)
                        com1 = sep(1)[0].lower()

                    # Повышает статус пользователю
                        if com1 == "статус" or com1 == "status":

                            if UsSend.scope == "Владелец":

                                def up_status(us_id, scope):

                                    up_bd("UPDATE persons SET scope = ? WHERE user_id = ?", scope.title(), us_id)

                                    ms("Статус {} изменился на <{}>".format(mention(us_id, "Пользователя"), scope.title()))
                                    pe_update()

                                    ###ADMINS###
                                    adminsPusher("chat_update_scope <{}>".format(scope), UsSend, [pe[us_id]])
                                    ###ADMINS###

                                if len(com) == 2:

                                    if com[1].lower() == "клиент" or com[1].lower() == "бариста":

                                        if UsReply and UsSend.user_id != UsReply.user_id:

                                            up_status(UsReply.user_id, com[1])

                                        elif UsFrw and UsFrw.user_id != UsSend.user_id:

                                            up_status(UsFrw.user_id, com[1])

                                        else:
                                            ms()

                                elif len(com) >= 3:

                                    for i in com[2:]:

                                        if com[1].lower() == "клиент" or com[1].lower() == "бариста" and get_id(i):

                                            up_status(get_id(i), com[1])
                                            
                                        else:
                                            ms()

                                else:
                                    ms()

                            else:
                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                    # Исключает пользователя
                        elif com1 == "кик" or com1 == "kick":

                            if UsSend.scope == "Владелец" or UsSend.scope == "Бариста":

                                def kicker(obj, **kwargs):

                                    if UsSend.scope in ("Владелец", "Бариста" ) and obj.scope != UsSend.scope and UsSend.user_id != obj.user_id and obj.scope != "Владелец" :

                                        ms("{} будет исключен".format(mention(obj.user_id, "Пользователь")))
                                        kick(obj.user_id, 1)
                                        pe_update()
                                        ###ADMINS###
                                        adminsPusher("chat_kick_user", UsSend, [obj])
                                        ###ADMINS###

                                
                                    else:

                                        ms("❕Нельзя исключить пользователя с таким же как у вас статусом <{}> или выше".format(UsSend.scope))


                                if len(com) == 1:

                                    if UsReply:

                                        kicker(UsReply)

                                    elif UsFrw:

                                        kicker(UsFrw)

                                    else:
                                        ms()

                                if len(com) >=2:

                                    for i in com[1:]:

                                        us_id = get_id(i)

                                        if us_id:

                                            kicker(pe[us_id])

                            else:
                                ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                    # Банит пользователя перманентно

                        elif com1 == "пермбан" or com1 == "permban":

                            def perm(obj):

                                if UsSend.scope == 'Владелец':

                                    if UsSend.scope != obj.scope and UsSend.user_id != obj.user_id:

                                        if obj.in_chat:

                                            ms("✓ {} получил пермбан и будет исключен".format(mention(obj.user_id, "Пользователь")))
                                            kick(obj.user_id, 1)
                                            up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", -1, obj.user_id)

                                        else:

                                            up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", -1, obj.user_id)
                                            ms("✓ {} получил пермбан".format(mention(obj.user_id, "Пользователь")))

                                        ###ADMINS###
                                        adminsPusher("chat_perm_user", UsSend, [obj])
                                        ###ADMINS###

                                        pe_update()

                                    else:

                                        ms("❕Нельзя исключить пользователя с таким же как у вас статусом <{}> или выше".format(UsSend.scope))

                                else:
                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                            if len(com) == 1:

                                if UsReply:

                                    perm(UsReply)

                                elif UsFrw:

                                    perm(UsFrw)

                                else:
                                    ms()

                            else:

                                for i in com[1:]:

                                    us_id = get_id(i)

                                    if us_id:

                                        perm(pe[us_id])

                    # Бан на время
                        elif com1 == "бан" or com1 == "ban":

                            def ban(obj, timer):

                                if UsSend.scope == "Владелец":

                                    if UsSend.user_id != obj.user_id:


                                        t = eval(' '.join(timer).replace("m", "60").replace("м", "60").replace("ч", "3600").replace("h", "3600").replace("d", "86400").replace("д", "86400").replace(",", "."))

                                        setter_time = int(time.time()) + t + 3600*3

                                        if obj.in_chat:
                                            
                                            ms("{} получил бан до [{}] и будет исключен".format(mention(obj.user_id, "Пользователь"), time.strftime("%d.%m.%Y %H:%M", time.localtime(setter_time))))
                                            bd("UPDATE persons SET ban = ? WHERE user_id = ?;", setter_time, obj.user_id)
                                            kick(obj.user_id, 1)

                                        else:

                                            ms("{} получил бан до [{}]".format(mention(obj.user_id, "Пользователь"), time.strftime("%d.%m.%Y %H:%M", time.localtime(setter_time))))
                                            bd("UPDATE persons SET ban = ? WHERE user_id = ?;", setter_time, obj.user_id)

                                        pe_update()
                                        ###ADMINS###
                                        adminsPusher("chat_ban_user", UsSend, [obj])
                                        ###ADMINS###



                                    else:
                                        ms("❕Данная команда неприменима к себе")


                                else:
                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                            if UsReply:

                                ban(UsReply, com[1:])

                            elif UsFrw:

                                ban(UsFrw, com[1:])

                            else:

                                us_id = get_id(com[1])

                                if us_id:

                                    ban(pe[us_id], com[2:])

                                else:
                                    ms()
                
                    # Снимает бан
                        elif com1 == "разбан" or com1 == "unban":

                            def unban(obj):

                                if UsSend.scope == "Владелец":

                                    if UsSend.scope != obj.scope:

                                        up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", 0, obj.user_id)

                                        ms("✓ С {} снят бан".format(mention(obj.user_id, "Пользователя")))

                                        pe_update()

                                        ###ADMINS###
                                        adminsPusher("chat_unban_user", UsSend, [obj])
                                        ###ADMINS###

                                    else:
                                        
                                        ms("❕Нельзя исключить пользователя с таким же как у вас статусом <{}> или выше".format(UsSend.scope))

                                else:

                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                            if UsReply:

                                unban(UsReply)

                            elif UsFrw:

                                unban(UsFrw)

                            else:

                                for i in com[1:]:

                                    us_id = get_id(i)

                                    if us_id:

                                        unban(pe[us_id])

                    # clear-команды
                        elif com1 == "очистить" or com1 == "clear":

                            if com[1] == "баны" or com[1] == "bans":

                                if UsSend.scope == "Владелец":

                                    sql = bd("SELECT user_id FROM persons;")

                                    for i in range(len(sql)):

                                        up_bd("UPDATE persons SET ban = ? WHERE user_id = ?;", 0, sql[i][0])
                                        pe_update()
                                        ###ADMINS###
                                        adminsPusher("chat_clear_bans", UsSend)
                                        ###ADMINS###

                                    ms("✓ Список банов очищен")

                                else:
                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                    # чс
                        elif com1 == "чс" or com1 == "bl":

                            if len(com) == 2 and (com[1] == 'лист' or com[1] == 'лист'):

                                sql = bd("SELECT user_id, badge FROM persons WHERE bl = ?;", 1)

                                will_msg = "〽️Список пользователей в черном списке:\n\n"

                                for i in range(len(sql)):

                                    will_msg += "{}. {}{}\n".format(i + 1, pe[sql[i][0]].men(), sql[i][1],)

                                ms(will_msg if len(will_msg) != 41 else "Список пользователей в черном списке пуст")

                            elif len(com) == 2 and (com[1] == 'очистить' or com[1] == 'clear'):

                                if UsSend.scope == "Владелец":

                                    up_bd("UPDATE persons SET bl = ?", 0)
                                    ms("✓ Список с пользователями в черном списке очищен")
                                    pe_update()

                                else:
                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                            elif UsSend.scope == "Владелец":

                                def to_bl(us_id):

                                    if UsSend.user_id != us_id and pe[us_id].scope != "Владелец":

                                        sql = bd("SELECT bl FROM persons WHERE user_id = ?;", us_id)

                                        if sql[0][0]:

                                            up_bd("UPDATE persons SET bl = ? WHERE user_id = ?;", 0, us_id)

                                            ms("✓ {} убран из черного списка".format(mention(us_id, "Пользователь")))

                                            ###ADMINS###
                                            adminsPusher("chat_from_bl_user", UsSend, [pe[us_id]])
                                            ###ADMINS###

                                        else:

                                            up_bd("UPDATE persons SET bl = ? WHERE user_id = ?;", 1, us_id)

                                            ms("✓ {} занесен в черный список бота".format(mention(us_id, "Пользователь")))

                                            ###ADMINS###
                                            adminsPusher("chat_to_bl_user", UsSend, [pe[us_id]])
                                            ###ADMINS###

                                        

                                        pe_update()

                                if UsReply:

                                    to_bl(UsReply.user_id)

                                elif UsFrw:

                                    to_bl(UsFrw.user_id)

                                elif len(com) >= 2:

                                    for i in com[1:]:

                                        user_id1 = get_id(i)

                                        if user_id1:

                                            to_bl(user_id1)

                                        else:
                                            ms()
                                            break

                                else:
                                    ms()

                    # Софтмут

                        elif com1 == "мут" or com1 == "mute":

                            def softmute(obj):

                                if UsSend.scope in ("Владелец", "Бариста") and obj.scope != "Бариста" and UsSend.user_id != obj.user_id and UsSend.scope != obj.scope:

                                    if obj.softmute:

                                        up_bd("UPDATE persons SET softmute = ? WHERE user_id = ?;", 0, obj.user_id)

                                        ms("✓ {} лишился мута".format(mention(obj.user_id, "Пользователь")))
                                        ###ADMINS###
                                        adminsPusher("chat_from_mute_user", UsSend, [obj])
                                        ###ADMINS###

                                    else:

                                        up_bd("UPDATE persons SET softmute = ? WHERE user_id = ?;", 1, obj.user_id)

                                        ms("✓ {} получил мут".format(mention(obj.user_id, "Пользователь")))

                                        ###ADMINS###
                                        adminsPusher("chat_to_mute_user", UsSend, [obj])
                                        ###ADMINS###
                                    
                                    pe_update()

                                else:
                                    ms("❕Вашего статуса <{}> недостаточно для данной команды".format(UsSend.scope))

                            if len(com) == 2 and (com[1] == "лист" or com[1] == "list"):

                                will_msg = "〽️Список пользователей в муте:\n\n"

                                counter = 1

                                for i in list(pe.values()):

                                    if i.softmute:

                                        will_msg += "{}. {} {}{}".format(counter, i.first_name, i.last_name, i.badge)
                                        counter +=1

                                ms(will_msg if len(will_msg) != 32 else "Список с пользователями в муте пуст")

                            elif UsReply:

                                softmute(UsReply)

                            elif UsFrw:

                                softmute(UsFrw)

                            elif len(com) >= 2:

                                ids = com[1:]

                                for i in ids:

                                    us_id = get_id(i)

                                    if us_id:

                                        softmute(pe[us_id])

    except:
        print(event.object.text)
        print(traceback.format_exc())

import vk_api, sqlite3, traceback, re
from vk_api.longpoll import VkEventType, VkLongPoll

# Подключение к странице
vk = vk_api.VkApi(token="8e03b3089681c4bcae0a65f229702f600300adcb43bc6ce6f501af4194fb86e40e3731de59db072f18534")
vk._auth_token()
vk.get_api()
longpoll = VkLongPoll(vk, wait=86400)

# Подключение к .bd
conn = sqlite3.connect("./Nekki_database/Nekki.bd")
cursor = conn.cursor()

# Шаблоны
pr_pat = r"[!/&^.,\"\\'$~:#%].+"
word_tuple = ("офи", "некки", "nekki", "ofi")

join_words = 0

def bd(request, *args):
    '''Выделяет данные из базы данных'''
    get_sql = request
    cursor.execute(get_sql, args)
    return cursor.fetchall()


def up_bd(request, *args):
    '''Обновляет данные в базе данных'''
    sql = request
    cursor.execute(sql, args)
    conn.commit()

def get_msg(ids):
    return vk.method("messages.getById", {
                "message_ids": ids,
                "extended": 1
            })

def deller(ids):
    vk.method("messages.delete", {
            "message_ids": ids,
            "delete_for_all": True
        })

rp_list = [i[0] for i in bd("SELECT assoc FROM role_play;")]

print("✓ Ready")

for event in longpoll.listen():

    try:

        if event.type == VkEventType.MESSAGE_NEW and get_msg(event.message_id)["items"][0]["from_id"] > 0: 

            

            message = get_msg(event.message_id)

            msg = message["items"][0]
            textSp = msg["text"].split(" ", 1)

            text = msg["text"]

            only_com = False

            if join_words:
                for i in ["хуй", "хуя", "хуе" "eба", "пизд", "бля"]:
                    if i in text:
                        deller(event.message_id)
                join_words -= 1

            # Оставляем от сообщения только текст (Для префиксных команд)
            if re.findall(pr_pat, text):

                only_com = text[1:]

            elif textSp[0] in word_tuple:

                only_com = textSp[1]
                deller(event.message_id)


        # Действие софтмута
            sql = bd("SELECT softmute, scope FROM persons WHERE user_id = ?;", msg["from_id"])

            if sql and sql[0][0]:

                deller(event.message_id)

        # Удалятор
            if (text.lower() == "del" or  text.lower() == "дел") and "fwd_messages" in msg and len(msg["fwd_messages"]):

                if sql[0][1] == "Владелец":

                    ids = []

                    deller(event.message_id)

                    for i in msg["fwd_messages"]:

                        ids.append(i["id"])

                    deller(ids)

            if "action" in message and (message["action"]["type"] == "chat_invite_user" or message["action"]["type"] == "chat_invite_user_by_link"):

                join_words = 50

            # Также удалятор
            elif (text.lower() == "del" or text.lower() == "дел") and "reply_message" in msg and len(msg["reply_message"]):

                if sql[0][1] == "Владелец":

                    deller(event.message_id)
                    deller(msg["reply_message"]["id"])

            elif textSp[0].lower() in rp_list:

                deller(event.message_id)

            elif only_com:

                if only_com.split(" ")[0] == "rp" or only_com.split(" ")[0] == "рп":

                    if only_com.split(" ")[1] == "new" or only_com.split(" ")[1] == "новое":

                        rp_list = [i[0] for i in bd("SELECT assoc FROM role_play;")]

                elif only_com.split(" ")[0] == "я" or only_com.split(" ")[0] == "me":

                    deller(event.message_id)

                
    except:
        print(traceback.format_exc())

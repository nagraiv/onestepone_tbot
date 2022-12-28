import pymysql
import contextlib
import qrcode

import base64
from io import BytesIO

from config import host, login, password, db_name

from aiogram import Bot, Dispatcher, executor, types

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@contextlib.contextmanager
def mysql():
    connection = pymysql.connect(
            host=host,
            user=login,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        connection.commit()
        cursor.close()
        connection.close()


def get_user(user_id):
    with mysql() as cursor:
        find_user = f"SELECT * FROM `users` WHERE ID_user = {user_id};"
        cursor.execute(find_user)
        user = cursor.fetchone()
        return user


def insert_user(user, ref, status):
    with mysql() as cursor:
        insert_query = "INSERT INTO `users` (ID_user, ID_sponsor, status, first_name, last_name, username) VALUES ({id}, {ref}, {status}, '{fn}', '{ln}', '{un}');".format(id=user["id"], ref=ref, status=status, fn = user["first_name"], ln = user["last_name"], un = user["username"])
        cursor.execute(insert_query)
        return True


def delete_user(user_id):
    with mysql() as cursor:
        delete_query = f"DELETE FROM `users` WHERE ID_user = {user_id};"
        cursor.execute(delete_query)
        return True


def change_status(user_id, new_status):
    with mysql() as cursor:
        update_query = f"UPDATE `users` SET status = {new_status} WHERE ID_user = {user_id};"
        cursor.execute(update_query)
        return True


def get_text(column):
    with mysql() as cursor:
        text_query = f"SELECT {column} FROM `base`"
        cursor.execute(text_query)
        text = cursor.fetchone()
        return text[column]


def count_child(user_id):
    with mysql() as cursor:
        count_query = f"SELECT COUNT(*) `ID_user` FROM `users` WHERE `ID_sponsor`={user_id};"
        cursor.execute(count_query)
        count = cursor.fetchone()
        return count["ID_user"]


def get_active_childs(user_id):
    with mysql() as cursor:
        new_query = f"SELECT `ID_user` FROM `users` WHERE `ID_sponsor`={user_id} and `status`=1;"
        cursor.execute(new_query)
        result = cursor.fetchall()
        childs = []
        for item in result:
            childs.append(item["ID_user"])
        return childs


def last_action(user_id):
    with mysql() as cursor:
        update_query = f"UPDATE `users` SET last_action = now() WHERE ID_user = {user_id};"
        cursor.execute(update_query)
        return True


def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn_mylink = types.InlineKeyboardButton("Моя реферальная ссылка", callback_data="ref_link")
    btn_myinfo = types.InlineKeyboardButton("Показать информацию о себе", callback_data="my_info")
    btn_edit = types.InlineKeyboardButton("Редактировать информацию о себе", callback_data="edit_info")
    btn_sponsor = types.InlineKeyboardButton("Вывести информацию о спонсорах", callback_data="meet_sponsor")
    btn_childinfo = types.InlineKeyboardButton("Показать представления личников", callback_data="child_info")
    btn_stop = types.InlineKeyboardButton("Приостановить работу бота", callback_data="good_luck")
    btn_rules = types.InlineKeyboardButton("Правила", callback_data="show_rules")
    btn_complaint = types.InlineKeyboardButton("Пожаловаться на партнёра", callback_data="to_complaint")
    kb.add(btn_mylink, btn_myinfo, btn_edit, btn_sponsor, btn_childinfo, btn_stop, btn_rules, btn_complaint)
    return kb


@dp.callback_query_handler(text="ref_link")
async def process_callback_ref_link(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    text = "https://t.me/onestepone_bot?start={}".format(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, text)
#    ref_link_qr = qrcode.make(text)
#    print(ref_link_qr)
#    binary_qr = types.BufferedInputFile(ref_link_qr)
#    print(binary_qr)
#    ref_link_qr.save("123.png")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image()
#    print(qr, img)
    buffered = BytesIO()
#    print(buffered)
    img.save(buffered, format="PNG")
#    print(img, buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
#    print(img_str, base64.b64decode(img_str))
    await bot.send_photo(callback_query.from_user.id, base64.b64decode(img_str))
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="my_info")
async def process_callback_show_my_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    current_user = get_user(callback_query.from_user.id)
    if current_user["description"] == "":
        await bot.send_message(callback_query.from_user.id, "Вы ещё не заполнили информацию о себе.")
    else:
        text = ""
        warning = ""
        if current_user["username"] == "":
            warning += "Настоятельно рекомендуем в настройках Telegram указать имя пользователя!\n"
        else:
            text += "@" + current_user["username"] + "\n"
        text += current_user["description"] + "\n"
        if current_user["contact"] == "":
            warning += "Рекомендуем указать дополнительный способ связи с Вами.\n"
        else:
            text += current_user["contact"]
        await bot.send_message(callback_query.from_user.id, text)
        if warning != "":
            await bot.send_message(callback_query.from_user.id, warning)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="edit_info")
async def process_callback_edit_my_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
#    current_user = get_user(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "Опишите, чем Вы можете быть интересны и полезны другим интернет бизнесменам:")
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="child_info")
async def process_callback_show_child_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    current_user = get_user(callback_query.from_user.id)
    childs = get_active_childs(current_user["ID_user"])
    text = "Ваша ссылка для регистрации использована {} раз.".format(count_child(callback_query.from_user.id))
    if len(childs) != 0:
        text += "\nВывожу информацию об активных участниках:"
    await bot.send_message(callback_query.from_user.id, text)
    for user in childs:
        current_user = get_user(user)
        text = "@" + current_user["username"] + "\n" + current_user["description"] + "\n" + current_user["contact"]
        await bot.send_message(callback_query.from_user.id, text)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="show_rules")
async def process_callback_show_rules(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, get_text("RULES"))
    last_action(callback_query.from_user.id)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    command = message.text.split()
    current_user = get_user(message.from_user.id)
    if current_user == None or current_user["status"] == 4: # пользователь ещё не зарегистрирован
        if len(command) < 2:  # проверка наличия реферальной ссылки
            if current_user == None:
                insert_user(message.from_user, 0, 4)
            await message.answer("Я работаю только с теми, кто пришёл по реферальной ссылке.\n" + get_text("NOT_WELCOME"))
        else:
            sponsor = get_user(command[1])
            if sponsor != None and sponsor["status"] != 4:  # спонсор прошел регистрацию
                if current_user != None:
                    delete_user(message.from_user.id)
                insert_user(message.from_user, command[1], 3)
                text = "Приветствую, {}!\nВы здесь по приглашению {}.\n".format(message.from_user.first_name, sponsor["first_name"])
                text += get_text("WELCOME")
                await message.answer(text)
            else:
                if current_user == None:
                    insert_user(message.from_user, 0, 4)
                await message.answer("Некорректная реферальная ссылка.\n" + get_text("NOT_WELCOME"))
    elif current_user["status"] == 0:  # пользователь есть в базе, но ранее приостановил участие
        button_yes = types.InlineKeyboardButton("Да", callback_data="activate")
        button_no = types.InlineKeyboardButton("Нет", callback_data="good_luck")
        inline_kb = types.InlineKeyboardMarkup(row_width=2).row(button_yes, button_no)
        await message.answer(f"Привет, {current_user['first_name']}!\nВозобновить работу бота?", reply_markup=inline_kb)
    elif current_user["status"] == 1:  # пользователь есть в базе и активен
        await message.answer(f"Привет, {current_user['first_name']}!\nКак дела?", reply_markup=main_menu())
    elif current_user["status"] == 2:  # пользователь был заблокирован по жалобе
        await message.answer(f"Ваш контакт заблокирован из-за жалоб участников.")
    elif current_user["status"] == 3:  # пользователь есть в базе, но не познакомился со спонсорами
        button_go = types.InlineKeyboardButton("Вперёд!", callback_data="meet_sponsor")
        inline_kb = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_go)
        await message.answer(f"Привет, {current_user['first_name']}!\nГотовы познакомиться со спонсорами?", reply_markup=inline_kb)
    else:
        await message.answer(f"Произошла ошибка. Воспользуйтесь сервисом позднее.")
    last_action(message.from_user.id)


@dp.callback_query_handler(text="good_luck")
async def process_callback_activate_user(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Всего доброго!\nНадеемся на будующее сотрудничество.\nДля возобновления работы бота отправьте /start")
    change_status(callback_query.from_user.id, 0)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="activate")
async def process_callback_activate_user(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "С возвращением!", reply_markup=main_menu())
    change_status(callback_query.from_user.id, 1)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="meet_sponsor")
async def process_callback_start_meeting(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Запрашиваю данные у сервера...")
    await meet_sponsor(callback_query.from_user.id)
    last_action(callback_query.from_user.id)


#@dp.message_handler(commands=['meet'])
async def meet_sponsor(user_id):
    depth = get_text("depth")
    current_user = get_user(user_id)
    n = 0
    while n < depth:
        if current_user["ID_sponsor"] == 0:
            break
        current_user = get_user(current_user["ID_sponsor"])
        if current_user["status"] == 1 and current_user["description"] != "":
            text = "@" + current_user["username"] + "\n" + current_user["description"] + "\n" + current_user["contact"]
            await bot.send_message(user_id, text)
            n += 1
    change_status(user_id, 1) #    когда пользователь познакомился со спонсорами, его статус позволяет заполнить информацию о себе


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
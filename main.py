import qrcode
from io import BytesIO

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext

from config import TOKEN

from db_requests import get_user, insert_user, delete_user, update_info, change_status
from db_requests import get_text, count_child, get_active_childs, last_action

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class UserInfo(StatesGroup):
    username = State()
    info = State()
    contact = State()


# class FileComplaint(StatesGroup):
#     bad_username = State()
#     complaint = State()


def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn_mylink = types.InlineKeyboardButton("Моя реферальная ссылка", callback_data="ref_link")
#    btn_myinfo = types.InlineKeyboardButton("Показать информацию о себе", callback_data="my_info")
    btn_edit = types.InlineKeyboardButton("Редактировать информацию о себе", callback_data="show_edit")
    btn_sponsor = types.InlineKeyboardButton("Вывести информацию о спонсорах", callback_data="meet_sponsor")
    btn_childinfo = types.InlineKeyboardButton("Показать представления личников", callback_data="child_info")
    btn_stop = types.InlineKeyboardButton("Приостановить работу бота", callback_data="good_luck")
    btn_rules = types.InlineKeyboardButton("Правила и инструкции", callback_data="show_rules")
#    btn_complaint = types.InlineKeyboardButton("Пожаловаться на партнёра", callback_data="to_complaint")
    kb.add(btn_mylink, btn_edit, btn_sponsor, btn_childinfo, btn_stop, btn_rules)
    return kb


@dp.callback_query_handler(text="ref_link")
async def process_callback_ref_link(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    text = "https://t.me/onestepone_bot?start={}".format(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "_Это ваша реферальная ссылка:_\n", parse_mode="Markdown")
    await bot.send_message(callback_query.from_user.id, text, disable_web_page_preview = True)
    ref_link_qr = qrcode.make(text)
    buffered = BytesIO()
    ref_link_qr.save(buffered, format="PNG")
    await bot.send_message(callback_query.from_user.id, "_А это QR код вашей реферальной ссылки:_\n", parse_mode="Markdown")
    await bot.send_photo(callback_query.from_user.id, buffered.getvalue())
    buffered.close()
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(text)
#     qr.make(fit=True)
#     img = qr.make_image()
#     buffered = BytesIO()
#     img.save(buffered, format="PNG")
#     await bot.send_photo(callback_query.from_user.id, buffered.getvalue())
    last_action(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "_Чем больше ваших друзей увидят вашу ссылку, тем полезней бот будет для вас._", reply_markup=main_menu(), parse_mode="Markdown")

#   кнопку убрали из главного меню, просмотреть свою информацию можно перед редактированием
@dp.callback_query_handler(text="my_info")
async def process_callback_show_my_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    current_user = get_user(callback_query.from_user.id)
    if current_user["description"] == "":
        await bot.send_message(callback_query.from_user.id, "_Вы ещё не заполнили информацию о себе._", parse_mode="Markdown")
    else:
        text = ""
        warning = ""
        if current_user["username"] == "":
            warning += "Настоятельно рекомендуем в настройках Telegram указать имя пользователя!\n"
        else:
            text += "@" + current_user["username"] + "\n"
        text += current_user["description"] + "\n"
        # if current_user["contact"] == "":
        #     warning += "Рекомендуем указать дополнительный способ связи с Вами.\n"
        # else:
        #     text += current_user["contact"]
        text += current_user["contact"]
        await bot.send_message(callback_query.from_user.id, text)
        if warning != "":
            await bot.send_message(callback_query.from_user.id, warning)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="show_edit")
async def process_callback_show_and_edit(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    current_user = get_user(callback_query.from_user.id)
    if current_user["description"] == "":
        button_fill = types.InlineKeyboardButton("Заполнить сейчас", callback_data="edit_info")
        inline_kb = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_fill)
        await bot.send_message(callback_query.from_user.id, "_Вы ещё не заполнили информацию о себе._", reply_markup=inline_kb, parse_mode="Markdown")
    else:
        await bot.send_message(callback_query.from_user.id, "_Вот что вы ранее написали о себе:_", parse_mode="Markdown")
        button_yes = types.InlineKeyboardButton("Редактировать", callback_data="edit_info")
        button_no = types.InlineKeyboardButton("Отменить", callback_data="no_action")
        inline_kb = types.InlineKeyboardMarkup(row_width=2).row(button_yes, button_no)
        await bot.send_message(callback_query.from_user.id, current_user["description"], reply_markup=inline_kb)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="no_action")
async def process_callback_return_to_main(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "_Редактирование отменено._", reply_markup=main_menu(), parse_mode="Markdown")


@dp.callback_query_handler(text="edit_info")
async def process_callback_edit_my_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    current_user = get_user(callback_query.from_user.id)
    if "username" not in callback_query.from_user:
        button_done = types.KeyboardButton("Готово!")
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button_done)
        await bot.send_message(callback_query.from_user.id,
                               "_Установите имя пользователя в настройках Telegram, чтобы другие участники могли вам написать!_",
                               reply_markup=kb, parse_mode="Markdown")
        await UserInfo.username.set()
    else:
        if current_user["username"] != callback_query.from_user["username"]:
            update_info(callback_query.from_user.id, "username", callback_query.from_user["username"])
        await bot.send_message(callback_query.from_user.id, "_Опишите, чем Вы можете быть интересны и полезны другим интернет бизнесменам _", parse_mode="Markdown")
        await bot.send_message(callback_query.from_user.id, "👇")
        await UserInfo.info.set()
    last_action(callback_query.from_user.id)


@dp.message_handler(state=UserInfo.username)
async def username_check(message: types.Message, state: FSMContext):
    if "username" not in message.from_user:
        await message.answer("_Пожалуйста, проверьте настройки Telegram ещё раз. Имя пользователя должно иметь вид @username_", parse_mode="Markdown")
    else:
        update_info(message.from_user.id, "username", message.from_user["username"])
        await message.answer("_Спасибо!\nТеперь опишите, чем Вы можете быть интересны и полезны другим интернет бизнесменам:_",
                             reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
        await UserInfo.info.set()
    last_action(message.from_user.id)


@dp.message_handler(state=UserInfo.info)
async def getting_my_info(message: types.Message, state: FSMContext):
    if len(message.text) < 10:
        await message.answer("_Пожалуйста, напишите о себе немного подробнее..._", parse_mode="Markdown")
    else:
        update_info(message.from_user.id, "description", message.text)
        await message.answer("👍")
        text = "_Отлично!\nИнформация сохранена и будет распространяться среди участников нашего сообщества. Ваша задача, раздать друзьям свою реферальную ссылку_"
        await state.finish()
        # current_user = get_user(message.from_user.id)
        # if current_user["contact"] == "":
        #     text += "Оставьте дополнительный контакт для связи с вами (например, e-mail, ваш сайт, соцсети, телефонный номер):"
        #     await UserInfo.contact.set()
        await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")
    last_action(message.from_user.id)


@dp.callback_query_handler(text="child_info")
async def process_callback_show_child_info(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "_Запрашиваю данные у сервера..._", parse_mode="Markdown")
    await bot.answer_callback_query(callback_query.id)
    current_user = get_user(callback_query.from_user.id)
    childs = get_active_childs(current_user["ID_user"])
    text = "Ваша ссылка для регистрации использована {} раз.".format(count_child(callback_query.from_user.id))
    if len(childs) != 0:
        text += "\nВывожу информацию об активных участниках:"
    await bot.send_message(callback_query.from_user.id, "_"+text+"_", parse_mode="Markdown")
    for user in childs:
        current_user = get_user(user)
        text = "@" + current_user["username"] + "\n" + current_user["description"] + "\n" + current_user["contact"]
        await bot.send_message(callback_query.from_user.id, text, disable_web_page_preview = True)
    last_action(callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, "_☝ тут точно не все ваши друзья._", reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query_handler(text="show_rules")
async def process_callback_show_rules(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "_"+get_text("RULES")+"_", parse_mode="Markdown")
    last_action(callback_query.from_user.id)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    command = message.text.split()
    current_user = get_user(message.from_user.id)
    if current_user is None or current_user["status"] == 4:  # пользователь ещё не зарегистрирован
        if len(command) < 2:  # проверка наличия реферальной ссылки
            if current_user is None:
                insert_user(message.from_user, 0, 4)
            await message.answer("_Я работаю только с теми, кто пришёл по реферальной ссылке.\n" + get_text("NOT_WELCOME")+"_", parse_mode="Markdown")
        else:
            sponsor = get_user(command[1])
            if sponsor is not None and sponsor["status"] != 4:  # спонсор прошел регистрацию
                if current_user is not None:
                    delete_user(message.from_user.id)
                insert_user(message.from_user, command[1], 3)
                text = "Приветствую, _*{}!*_\nВы здесь по приглашению _*{}*_.\n".format(message.from_user.first_name, sponsor["first_name"])
                text += get_text("WELCOME")
                button_meet = types.InlineKeyboardButton("Начать знакомства", callback_data="meet_sponsor")
                inline_kb = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_meet)
                await message.answer("_"+text+"_", reply_markup=inline_kb, parse_mode="Markdown")
                if sponsor["status"] == 1:
                    await bot.send_message(sponsor["ID_user"], "Приветствую!\nВ OneStepOne по вашей ссылке зарегистрован @" + message.from_user.username)
            else:
                if current_user is None:
                    insert_user(message.from_user, 0, 4)
                await message.answer("_Некорректная реферальная ссылка.\n" + get_text("NOT_WELCOME")+"_", parse_mode="Markdown")
    elif current_user["status"] == 0:  # пользователь есть в базе, но ранее приостановил участие
        button_yes = types.InlineKeyboardButton("Да", callback_data="activate")
        button_no = types.InlineKeyboardButton("Нет", callback_data="good_luck")
        inline_kb = types.InlineKeyboardMarkup(row_width=2).row(button_yes, button_no)
        await message.answer(f"_Привет,_* {current_user['first_name']}*_!\nВозобновить работу бота?_", reply_markup=inline_kb, parse_mode="Markdown")
    elif current_user["status"] == 1:  # пользователь есть в базе и активен
        await message.answer(f"_Привет,_* {current_user['first_name']}*_!\nКак дела?_", reply_markup=main_menu(), parse_mode="Markdown")
    elif current_user["status"] == 2:  # пользователь был заблокирован по жалобе
        await message.answer(f"_Ваш контакт заблокирован из-за жалоб участников._", parse_mode="Markdown")
    elif current_user["status"] == 3:  # пользователь есть в базе, но не познакомился со спонсорами
        button_go = types.InlineKeyboardButton("Вперёд!", callback_data="meet_sponsor")
        inline_kb = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_go)
        await message.answer(f"_Привет,_* {current_user['first_name']}*_!\nГотовы познакомиться со спонсорами?_", reply_markup=inline_kb, parse_mode="Markdown")
    else:
        await message.answer(f"_Произошла ошибка. Воспользуйтесь сервисом позднее._", parse_mode="Markdown")
    last_action(message.from_user.id)


@dp.callback_query_handler(text="good_luck")
async def process_callback_activate_user(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "_Всего доброго!\nНадеемся на будующее сотрудничество.\nДля возобновления работы бота отправьте_ /start", parse_mode="Markdown")
    change_status(callback_query.from_user.id, 0)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="activate")
async def process_callback_activate_user(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "_С возвращением!_", reply_markup=main_menu(), parse_mode="Markdown")
    change_status(callback_query.from_user.id, 1)
    last_action(callback_query.from_user.id)


@dp.callback_query_handler(text="meet_sponsor")
async def process_callback_start_meeting(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "_Запрашиваю данные у сервера..._", parse_mode="Markdown")
    await meet_sponsor(callback_query.from_user.id)
    last_action(callback_query.from_user.id)


async def meet_sponsor(user_id):
    depth = get_text("depth")
    current_user = get_user(user_id)
    status = current_user["status"]
    n = 0
    while n < depth:
        if current_user["ID_sponsor"] == 0:
            break
        current_user = get_user(current_user["ID_sponsor"])
        if current_user["status"] == 1 and current_user["description"] != "":
            text = "@" + current_user["username"] + "\n" + current_user["description"] + "\n" + current_user["contact"]
            await bot.send_message(user_id, text, disable_web_page_preview = True)
            n += 1
    if status == 1:
        await bot.send_message(user_id, "_Если вы еще не познакомились со спонсорами, сейчас самое время, это сделать_", reply_markup=main_menu(), parse_mode="Markdown")
    if status == 3:
        button_fill = types.InlineKeyboardButton("Написать о себе", callback_data="edit_info")
        inline_kb = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(button_fill)
        await bot.send_message(user_id, "☝")
        await bot.send_message(user_id, "_Напишите каждому из спонсоров приветственное сообщение, вначале которого поставьте_ *OSO*, _это даст им понимание, что письмо пришло от участника нашего сообщества, который открыт к  диалогу. Они все ждут от вас письма! \nПосле отправки писем спонсорам, вы можете заполнить информацию о себе._", reply_markup=inline_kb, parse_mode="Markdown")
        change_status(user_id, 1)  # когда пользователь познакомился со спонсорами, его статус позволяет заполнить информацию о себе
    last_action(user_id)


#   обработчик всех текстовых сообщений, не попавший в фильтры выше
# @dp.message_handler()
# async def echo(message: types.Message):
#     await message.answer(message.text)


#   обработчик любого другого непредвиденного контента от пользователя
@dp.message_handler(content_types=types.ContentType.ANY)
async def unknown_message(message: types.Message):
    await message.answer("Я не знаю, что с этим делать.\nДля начала работы с ботом отправь \n/start.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

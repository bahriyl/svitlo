import datetime
import config
import telebot
from telebot import types
from pymongo import MongoClient

bot = telebot.TeleBot(config.BOT_TOKEN)

client = MongoClient(config.MONGODB_CONNECTION_STRING)
db = client["svitlo"]
collection = db["schedules"]
users_collection = db["users"]

cities = [
    "Київ", "Сумська область", "Донецька область", "Херсонська область",
    "Івано-Франківська область", "Вінницька область", "Рівненська область",
    "Хмельницька область", "Київська область", "Харківська область",
    "Закарпатська область", "Миколаївська область", "Житомирська область",
    "Волинська область", "Запорізька область", "Кіровоградська область",
    "Полтавська область", "Тернопільська область", "Чернігівська область",
    "Луганська область", "Дніпропетровська область", "Одеська область",
    "Черкаська область", "Чернівецька область", "Львівська область",
    "Автономна Республіка Крим"
]
regions_websites = {
    "Київ": "https://www.dtek-kem.com.ua/ua/shutdowns",
    "Київська область": "https://www.dtek-krem.com.ua/ua/shutdowns",
    "Чернігівська область": "https://chernihivoblenergo.com.ua/blackouts",
    "Житомирська область": "https://www.ztoe.com.ua/unhooking.php",
    "Вінницька область": "https://voe.com.ua/disconnection/detailed",
    "Полтавська область": "https://www.poe.pl.ua/disconnection/poshuk-vidkliuchennia-za-osobovym-rakhunkom/",
    "Закарпатська область": "https://zakarpat.energy/customers/break-in-electricity-supply/schedule/",
    "Рівненська область": "https://www.roe.vsei.ua/disconnections",
    "Сумська область": "https://www.soe.com.ua/spozhivacham/vidklyuchennya",
    "Прикарпаття": "https://oe.if.ua/uk/sections/5e9f1c5fdb9c42704449b999#66fd0b3859d90f4e0e9a2396",
    "Дніпропетровська область": "https://www.dtek-dnem.com.ua/ua/shutdowns",
    "Львівська область": "https://poweron.loe.lviv.ua",
    "Одеська область": "https://www.dtek-oem.com.ua/ua/shutdowns",
    "Миколаївська область": "https://www.energy.mk.ua/vidklyuchennya/",
    "Запорізька область": "https://www.zoe.com.ua/графіки-погодинних-стабілізаційних/",
    "Хмельницька область": "https://hoe.com.ua/page/informatsija-vidkljuchennja",
    "Черкаська область": "https://www.cherkasyoblenergo.com/off"
}

user_city_selection = {}

main_menu_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_markup.add(types.KeyboardButton("Додати групу/чергу"))
main_menu_markup.add(types.KeyboardButton("Переглянути мої черги/групи"))
main_menu_markup.add(types.KeyboardButton("Видалити чергу/групу"))
main_menu_markup.add(types.KeyboardButton("Дізнатися групу/чергу відключень"))


@bot.message_handler(commands=['start'])
def start(message):
    is_present = users_collection.find_one({'tgID': message.from_user.id})
    document = {'firstName': message.from_user.first_name,
                'lastName': message.from_user.last_name,
                'tgID': message.from_user.id}
    if is_present is None:
        users_collection.insert_one(document)

    bot.send_message(message.from_user.id, 'Головне меню:', reply_markup=main_menu_markup)


@bot.message_handler(func=lambda message: message.text == "Додати групу/чергу", content_types=['text'])
def add_queue(message):
    markup = types.InlineKeyboardMarkup()

    for city in cities:
        button = types.InlineKeyboardButton(city, callback_data=f"city_{city}")
        markup.add(button)

    bot.send_message(
        message.chat.id,
        "Оберіть місто:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("city_"))
def handle_city_selection(call):
    selected_city = call.data.split("city_")[1]
    tg_id = call.from_user.id

    user_city_selection[tg_id] = selected_city

    bot.send_message(call.message.chat.id, f"Ви обрали місто: {selected_city}")

    date = datetime.datetime.now()
    city_doc = collection.find_one({"City": selected_city, "Date": date.replace(hour=0, minute=0, second=0,
                                                                                microsecond=0)})

    if city_doc:
        queues = city_doc.get("Queues", {}).keys()
        if queues:
            markup = types.InlineKeyboardMarkup()
            for queue in queues:
                button = types.InlineKeyboardButton(queue, callback_data=f"queue_{queue}")
                markup.add(button)

            bot.send_message(
                call.message.chat.id,
                "Оберіть чергу:",
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, "Для цього міста черги не знайдені.")
    else:
        bot.send_message(call.message.chat.id, "Дані для цього міста відсутні в базі даних.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("queue_"))
def handle_queue_selection(call):
    selected_queue = call.data.split("queue_")[1]
    tg_id = call.from_user.id

    selected_city = user_city_selection.get(tg_id)

    if not selected_city:
        bot.send_message(call.message.chat.id, "Спочатку оберіть місто.")
        return

    bot.send_message(call.message.chat.id, f"Ви обрали чергу: {selected_queue}")

    user_doc = users_collection.find_one({"tgID": tg_id})

    if not user_doc:
        users_collection.insert_one({
            "tgID": tg_id,
            "chosenCitiesAndQueues": [
                {"city": selected_city, "queue": selected_queue}
            ]
        })
        bot.send_message(call.message.chat.id,
                         f"Місто {selected_city} і черга {selected_queue} додані до вашого списку.")
    else:
        existing_list = user_doc.get("chosenCitiesAndQueues", [])

        if {"city": selected_city, "queue": selected_queue} not in existing_list:
            existing_list.append({"city": selected_city, "queue": selected_queue})
            users_collection.update_one(
                {"tgID": tg_id},
                {"$set": {"chosenCitiesAndQueues": existing_list}}
            )
            bot.send_message(call.message.chat.id,
                             f"Місто {selected_city} і черга {selected_queue} додані до вашого списку.")
        else:
            bot.send_message(call.message.chat.id, "Ця черга вже є у вашому списку.")


@bot.message_handler(func=lambda message: message.text == "Переглянути мої черги/групи", content_types=['text'])
def view_queues(message):
    tg_id = message.from_user.id
    user_doc = users_collection.find_one({"tgID": tg_id})

    if user_doc:
        chosen = user_doc.get("chosenCitiesAndQueues", [])
        if chosen:
            reply_text = "Ваші вибрані міста та черги:\n"
            markup = types.InlineKeyboardMarkup()
            for item in chosen:
                button = types.InlineKeyboardButton(f"{item['city']} - {item['queue']}", callback_data=f"viewqueue_{item['city']}_{item['queue']}")
                markup.add(button)
            bot.send_message(message.chat.id, reply_text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Ви ще не вибрали жодних черг.")
    else:
        bot.send_message(message.chat.id, "Ви ще не зареєстровані. Будь ласка, спочатку натисніть /start.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("viewqueue_"))
def handle_queue_selection(call):
    selected_city = call.data.split("_")[1]
    selected_queue = call.data.split("_")[2]  # Extract queue name
    tg_id = call.from_user.id

    if not selected_city:
        bot.send_message(call.message.chat.id, "Спочатку оберіть місто.")
        return

    date = datetime.datetime.now()
    city_doc = collection.find_one({"City": selected_city, "Date": date.replace(hour=0, minute=0, second=0, microsecond=0)})
    if city_doc and selected_queue in city_doc.get("Queues", {}):
        schedule = city_doc["Queues"][selected_queue]

        readable_schedule = {}
        for time, status in schedule.items():
            if status is True:
                readable_schedule[time] = "Є світло"
            elif status is False:
                readable_schedule[time] = "Немає світла"
            elif status == "Possible":
                readable_schedule[time] = "Можливе відключення"
            elif status is None:
                readable_schedule[time] = "Немає інформації"

        schedule_message = f"Графік для черги {selected_queue}:\n"
        for time, status in readable_schedule.items():
            schedule_message += f"{time}: {status}\n"

        bot.send_message(call.message.chat.id, schedule_message)
    else:
        bot.send_message(call.message.chat.id, "Для цієї черги відсутня інформація.")


@bot.message_handler(func=lambda message: message.text == "Видалити чергу/групу", content_types=['text'])
def remove_queue(message):
    tg_id = message.from_user.id
    user_doc = users_collection.find_one({"tgID": tg_id})

    if user_doc:
        chosen = user_doc.get("chosenCitiesAndQueues", [])
        if chosen:
            markup = types.InlineKeyboardMarkup()
            for item in chosen:
                button = types.InlineKeyboardButton(f"{item['city']} - {item['queue']}",
                                                    callback_data=f"delete_{item['city']}_{item['queue']}")
                markup.add(button)
            bot.send_message(message.chat.id, "Оберіть чергу для видалення:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "У вас немає вибраних черг для видалення.")
    else:
        bot.send_message(message.chat.id, "Ви ще не зареєстровані. Будь ласка, спочатку натисніть /start.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def handle_queue_deletion(call):
    selected_city, selected_queue = call.data.split("delete_")[1].split("_")
    tg_id = call.from_user.id

    user_doc = users_collection.find_one({"tgID": tg_id})

    if user_doc:
        updated_list = [item for item in user_doc.get("chosenCitiesAndQueues", []) if
                        not (item["city"] == selected_city and item["queue"] == selected_queue)]

        users_collection.update_one(
            {"tgID": tg_id},
            {"$set": {"chosenCitiesAndQueues": updated_list}}
        )
        bot.send_message(call.message.chat.id, f"Чергу {selected_queue} з міста {selected_city} було успішно видалено.")
    else:
        bot.send_message(call.message.chat.id, "Помилка при видаленні черги. Спробуйте ще раз.")


@bot.message_handler(func=lambda message: message.text == "Дізнатися групу/чергу відключень", content_types=['text'])
def show_regions(message):
    markup = types.InlineKeyboardMarkup()

    for region, link in regions_websites.items():
        button = types.InlineKeyboardButton(region, url=link)
        markup.add(button)

    bot.send_message(
        message.chat.id,
        "Оберіть регіон для перегляду черги відключень:",
        reply_markup=markup
    )


bot.polling(none_stop=True)

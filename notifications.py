import config
from datetime import datetime, timedelta
import pymongo
import telebot

client = pymongo.MongoClient(config.MONGODB_CONNECTION_STRING)
db = client["svitlo"]
schedules_collection = db["schedules"]
users_collection = db["users"]

bot = telebot.TeleBot(config.BOT_TOKEN)


def check_and_notify():
    current_time = datetime.now()
    half_hour_ahead = current_time + timedelta(minutes=30)
    current_hour = current_time.strftime("%H:00")
    next_hour = half_hour_ahead.strftime("%H:00")

    schedules = schedules_collection.find({"Date": {"$gte": datetime.combine(current_time.date(), datetime.min.time())}})
    for schedule in schedules:
        city = schedule["City"]
        queues = schedule["Queues"]

        for queue, hours in queues.items():
            current_status = hours.get(current_hour)
            next_status = hours.get(next_hour)

            if current_status and not next_status:
                event = "відключення світла"
            elif not current_status and next_status:
                event = "увімкнення світла"
            else:
                continue

            users = users_collection.find({"chosenCitiesAndQueues": {"$elemMatch": {"city": city, "queue": queue}}})
            for user in users:
                message = (
                    f"Попередження! У місті {city}, черзі {queue}, через 30 хвилин очікується {event}."
                )
                bot.send_message(user["tgID"], message)

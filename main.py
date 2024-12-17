import config
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from datetime import datetime

client = MongoClient(config.MONGODB_CONNECTION_STRING)
db = client["svitlo"]
collection = db["schedules"]

city_name_mapping = {
    "kyiv": "Київ",
    "sumska-oblast": "Сумська область",
    "donetska-oblast": "Донецька область",
    "hersonska-oblast": "Херсонська область",
    "ivano-frankivska-oblast": "Івано-Франківська область",
    "vinnitska-oblast": "Вінницька область",
    "rivnenska-oblast": "Рівненська область",
    "hmelnitska-oblast": "Хмельницька область",
    "kiivska-oblast": "Київська область",
    "harkivska-oblast": "Харківська область",
    "zakarpatska-oblast": "Закарпатська область",
    "mikolaivska-oblast": "Миколаївська область",
    "jitomirska-oblast": "Житомирська область",
    "volinska-oblast": "Волинська область",
    "zaporizka-oblast": "Запорізька область",
    "kirovogradska-oblast": "Кіровоградська область",
    "poltavska-oblast": "Полтавська область",
    "ternopilska-oblast": "Тернопільська область",
    "chernigivska-oblast": "Чернігівська область",
    "luganska-oblast": "Луганська область",
    "dnipropetrovska-oblast": "Дніпропетровська область",
    "odeska-oblast": "Одеська область",
    "cherkaska-oblast": "Черкаська область",
    "chernivetska-oblast": "Чернівецька область",
    "lvivska-oblast": "Львівська область",
    "avtonomna-respublika-krim": "Автономна Республіка Крим"
}


def transform_cell(cell_value):
    if cell_value == "●":
        return True
    elif cell_value == "✕":
        return False
    elif cell_value == "-":
        return None
    elif cell_value == "±":
        return "Possible"
    return cell_value


def update_schedule():
    for href in city_name_mapping.keys():
        page = requests.get(f'https://svitlo.live/{href}')
        html_content = page.text

        soup = BeautifulSoup(html_content, "html.parser")

        city_name_cyrillic = city_name_mapping[href]

        city_queues = {}

        for div in soup.find_all("div", id=lambda x: x and x.startswith("chergra")):
            first_div = div.find("div")
            table = first_div.find("table", class_="graph") if first_div else None

            if table:
                rows = table.find_all("tr")
                headers = [cell.text.strip() for cell in rows[0].find_all("td")]
                date_str = headers[0]
                date_obj = datetime.strptime(date_str, "%d.%m.%Y")

                for row in rows[1:]:
                    cells = row.find_all("td")
                    queue_name = cells[0].text.strip()
                    schedule = {
                        datetime.strptime(time, "%H:%M").strftime("%H:%M"): transform_cell(cells[i].text.strip())
                        for i, time in enumerate(headers[1:], start=1)
                    }
                    city_queues[queue_name] = schedule

        existing_doc = collection.find_one({"City": city_name_cyrillic, "Date": date_obj})

        if existing_doc:
            updated_queues = existing_doc.get("Queues", {})
            for queue_name, schedule in city_queues.items():
                if queue_name not in updated_queues or updated_queues[queue_name] != schedule:
                    updated_queues[queue_name] = schedule
            collection.update_one(
                {"_id": existing_doc["_id"]},
                {"$set": {"Queues": updated_queues}}
            )
            print(f"Updated queues for {city_name_cyrillic} on {date_str}.")
        else:
            city_document = {
                "City": city_name_cyrillic,
                "Date": date_obj,
                "Queues": city_queues
            }
            collection.insert_one(city_document)
            print(f"Inserted new document for {city_name_cyrillic} on {date_str}.")

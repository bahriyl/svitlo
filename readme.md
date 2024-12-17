
# Svitlo Power Outage Notification System

This project consists of a FastAPI-based backend application and a Telegram bot for managing and notifying users about power outage schedules. It is designed to work with a MongoDB database storing city-specific schedules and user preferences.

---

## Features

### Backend (FastAPI)

- **Get Available Cities**: Provides a list of cities with available power outage schedules.
- **Get Queues by City**: Retrieves available outage queues for a specific city.
- **Get Schedule**: Returns the outage schedule for a specified city, queue, and date.

### Telegram Bot

- **Add Queue**: Allows users to select their city and queue to monitor outage schedules.
- **View Queues**: Displays all saved queues for a user.
- **Delete Queue**: Enables users to remove selected queues.
- **Region Outage Info**: Provides external links to region-specific power outage websites.

---

## Project Structure

### Backend

- **application.py**: Contains the FastAPI app with endpoints to query the database.
  - Endpoints:
    - `/cities`: Retrieve the list of cities.
    - `/queues`: Retrieve queues by city.
    - `/schedule`: Retrieve outage schedules by city, queue, and date.

### Telegram Bot

- **bot.py**: Implements the Telegram bot logic for user interaction.
  - Features include:
    - Start and main menu commands.
    - Inline keyboard for city and queue selection.
    - Dynamic schedule retrieval.
    - Queue management.
- **main.py**: Handles scraping schedules from external website and storing them in DB.
- **scheduler.py**: Handles scheduling-related logic.

### Additional Scripts

- **notifications.py**: Script to notify users about power outages.

---

## Database Schema

### MongoDB Collections

1. **schedules**

   - Stores city-specific outage schedules.
   - Example document:
     ```json
     {
       "City": "Kyiv",
       "Date": "2024-12-17T00:00:00",
       "Queues": {
         "Queue1": {
           "00:00-03:00": false,
           "03:00-06:00": true,
           "06:00-09:00": "Possible"
         }
       }
     }
     ```

2. **users**

   - Stores user-specific data such as Telegram ID and chosen queues.
   - Example document:
     ```json
     {
       "tgID": 123456789,
       "firstName": "John",
       "lastName": "Doe",
       "chosenCitiesAndQueues": [
         {"city": "Kyiv", "queue": "Queue1"}
       ]
     }
     ```

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- MongoDB database
- Telegram Bot Token (from BotFather)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd svitlo
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `config.py`:
   ```python
   MONGODB_CONNECTION_STRING = "<your_mongodb_connection_string>"
   BOT_TOKEN = "<your_telegram_bot_token>"
   ```
4. Run the backend application:
   ```bash
   uvicorn application:app --reload
   ```
5. Start the Telegram bot:
   ```bash
   python bot.py
   ```

---

## Usage Instructions

### Telegram Bot

1. Start the bot by sending `/start`.
2. Use the main menu to:
   - Add queues by selecting your city and queue.
   - View your saved queues and their schedules.
   - Remove queues as needed.
   - Access region-specific outage information.

### Backend Endpoints

- Example request to fetch cities:
  ```bash
  curl -X GET http://localhost:8000/cities
  ```

---

## Contributing

1. Fork the repository.
2. Create a new feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the MIT License.

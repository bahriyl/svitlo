import notifications
import main
import schedule
import time

schedule.every().hour.at(":30").do(notifications.check_and_notify)
schedule.every(10).minutes.do(main.update_schedule)

while True:
    schedule.run_pending()
    time.sleep(1)

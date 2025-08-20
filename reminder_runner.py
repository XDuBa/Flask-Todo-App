import time
from models.todo_model import Todolist
from services.reminder_service import check_reminder
import config

if __name__ == "__main__":
    todo = Todolist(config.DB_PATH)

while True:
    try:
        check_reminder(todo, config.TOKEN, config.CHAT_ID)
    except Exception as e:
        print("检查提醒时出错：",e)
    time.sleep(60)
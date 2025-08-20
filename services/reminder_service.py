import requests
from datetime import datetime,timedelta

def send_telegram_message(token, chat_id, text):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url,data={'chat_id':chat_id,'text':text})

def check_reminder(todo, token, chat_id):
    now = datetime.now()
    tasks = todo.get_all_tasks()
    for task in tasks:
        task_id, description, due_time, status = task
        if status == "pending":
            time_left = datetime.fromisoformat(due_time) - now
            if timedelta(minutes=0) < time_left <= timedelta(minutes=30):
                minutes = int(time_left.total_seconds() // 60)
                msg = f"⏰ 提醒：任务《{description}》将在 {minutes} 分钟后到期！"
                send_telegram_message(token, chat_id, msg)
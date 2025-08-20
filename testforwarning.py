import requests

TOKEN = "7627030852:AAGvDRjERN9BorL9FQ70qbq-kjUOy6Mi0mo"
CHAT_ID = "7058970418"

Text = "⏰ 提醒：任务将在30分钟后到期！"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id":CHAT_ID,"text":Text}
r = requests.post(url,data=payload)

print(r.status_code,r.text)

from flask import Flask,render_template,request,jsonify,redirect,url_for
from models.todo_model import Todolist
from services.reminder_service import check_reminder
import config
from flask_apscheduler import APScheduler


app = Flask(__name__)
todo = Todolist(config.DB_PATH)

@app.route('/')
def index():
    tasks = todo.get_all_tasks()
    return render_template('index.html',tasks=tasks)

@app.route('/add',methods=['POST'])
def add_task():
    description = request.form['description']
    due_time = request.form['due_time']
    todo.add_task(description, due_time)
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>',methods=['POST'])
def complete_task(task_id):
    todo.complete_task(task_id)
    return redirect(url_for('index'))
    
@app.route('/delete/<int:task_id>',methods=['POST'])
def delete_task(task_id):
    todo.delete_task(task_id)
    return redirect(url_for('index'))
    
@app.route('/edit/<int:task_id>',methods=['GET','POST'])
def edit_task(task_id):
    if request.method == 'POST':
        description = request.form['description']
        due_time = request.form['due_time']
        todo.update_task(task_id, description, due_time)
        return redirect(url_for('index'))
    else:
        task = todo.get_task_by_id(task_id)
        return render_template('edit.html', task=task)

@app.route('/api/tasks')
def api_tasks():
    tasks = todo.load_tasks()
    return jsonify(tasks)
@app.route('/api/statistics')
def api_statistics():
    #返回完成率
    completion_stats = todo.get_completion_statistics()
    return jsonify(completion_stats)

@app.route('/api/daily-stats')
def api_daily_stats():
    #返回每日完成任务统计
    days = request.args.get('days', 7, type=int)
    if days > 30:
        days = 30
    daily_stats = todo.get_daily_completion_stats(days)
    return jsonify(daily_stats)

@app.route('/api/overall-stats')
def api_overall_stats():
    #返回总体统计
    overall_stats = todo.get_overall_statistics()
    return jsonify(overall_stats)

scheduler = APScheduler()

@scheduler.task('interval', id='check_reminders_task', seconds=60)
def scheduled_check():
    check_reminder(todo,config.TOKEN,config.CHAT_ID)

@app.route('/statistics')
def statistics():
    return render_template('statistics.html')

if __name__ == "__main__" :
    scheduler.init_app(app)
    scheduler.start()
    app.run(debug=True, host='0.0.0.0',port=5001)
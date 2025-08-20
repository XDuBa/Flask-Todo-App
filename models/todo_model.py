import os
import sqlite3
from datetime import datetime, timedelta

class Todolist:        
    def __init__(self,db_name = 'todo.db'):
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_path,db_name)
        self.create_table()
        self.valid_priorities = ['high','medium','low']
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            due_time TEXT
        )
        ''')
        conn.commit()
        conn.close()
    
    def load_tasks(self):
        #从数据库加载任务，设定默认值
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, description, due_time FROM tasks" )
        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            task['completed'] = bool(task['completed'])
            tasks.append(task)
        conn.close()
        return tasks
    
    def add_task(self,description,priority='medium',due_time = None):
        """添加新任务"""
        if priority not in self.valid_priorities:
            priority = 'medium'

        current_time = datetime.now().isoformat()
        due_iso = due_time.isoformat() if due_time else None

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO tasks (description, priority, completed, created_at, updated_at, due_time)
        VALUES (?,?,?,?,?,?)
        ''', (description,priority,False,current_time,current_time,due_iso))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def mark_completed(self,task_id):
        current_time = datetime.now().isoformat()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE tasks
        SET completed = 1, updated_at = ?
        WHERE id = ? AND completed = 0
        ''',(current_time, task_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_task(self, task_id):
        """删除任务"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def edit_task(self, task_id, new_description=None,new_priority=None,new_due_time=None):
        #编辑任务描述和/或优先级
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()

        if not task:
            conn.close()
            return False
        
        current_time = datetime.now().isoformat()
        updates = []
        params = []

        #更新描述
        if new_description is not None and new_description.strip():
            updates.append("description = ?")
            params.append(new_description.strip())

        #更新优先级
        if new_priority is not None and new_priority in self.valid_priorities:
            updates.append("priority = ?")
            params.append(new_priority)

        # 更新截止时间
        if new_due_time is not None:            
            if new_due_time == "":  # 清除截止时间
                updates.append("due_time = NULL")
            else:
                new_due_iso = new_due_time.isoformat() if hasattr(new_due_time, 'isoformat') else new_due_time
                updates.append("due_time = ?")
                params.append(new_due_iso)

        if updates:
            # 添加更新时间
            updates.append("updated_at = ?")
            params.append(current_time)
            
            # 构建更新语句
            update_query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            params.append(task_id)
            
            cursor.execute(update_query, tuple(params))
            conn.commit()
            success = True
        else:
            success = False
        
        conn.close()
        return success

    def get_upcoming_tasks(self):
        now = datetime.now()
        tasks = self.load_tasks()
        upcoming_tasks = []

        for task in tasks:
            if task['due_time'] and not task['completed']:
                try:
                    due_time = datetime.fromisoformat(task['due_time'])
                    time_left = due_time - now

                    if timedelta(minutes = 0) < time_left <= timedelta(hours=24):
                        task['time_left_minutes'] = int(time_left.total_seconds() // 60)
                        upcoming_tasks.append(task)
                except ValueError:
                    continue
        
        return upcoming_tasks
    def get_completion_statistics(self):
        #获取各优先级任务完成情况统计
        conn = self.get_connection()
        cursor = conn.cursor()

        #查询各优先级总任务数和已完成任务数
        cursor.execute('''
            SELECT
                    priority,
                    COUNT(*) as total_count,
                    SUM(completed) as completed_count
            FROM tasks
            GROUP BY priority
        ''')

        results = cursor.fetchall()
        conn.close()

        statistics = {}
        priority_labels = {
            'high': '高优先级',
            'medium': '中优先级',
            'low': '低优先级'
        }

        for row in results:
            priority = row['priority']
            total = row['total_count']
            completed = row['completed_count'] if row['completed_count'] else 0
            completion_rate = (completed / total * 100) if total > 0 else 0

            statistics[priority] = {
                'label': priority_labels.get(priority,priority),
                'total': total,
                'completed': completed,
                'pending': total - completed,
                'completion_rate': round(completion_rate, 1)
            }

        for priority in self.valid_priorities:
            if priority not in statistics:
                statistics[priority] = {
                    'label': priority_labels[priority],
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'completion_rate': 0.0
                }

        return statistics

    def get_daily_completion_stats(self, days=7):
        """获取最近几天的任务完成统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取最近N天的完成任务统计
        cursor.execute('''
            SELECT 
                DATE(updated_at) as completion_date,
                priority,
                COUNT(*) as count
            FROM tasks 
            WHERE completed = 1 
            AND DATE(updated_at) >= DATE('now', '-{} days')
            GROUP BY DATE(updated_at), priority
            ORDER BY completion_date DESC
        '''.format(days))
        
        results = cursor.fetchall()
        conn.close()
        
        # 处理数据，确保每天都有完整的优先级数据
        daily_stats = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_stats[date] = {
                'date': date,
                'high': 0,
                'medium': 0,
                'low': 0,
                'total': 0
            }
        
        for row in results:
            date = row['completion_date']
            priority = row['priority']
            count = row['count']
            
            if date in daily_stats:
                daily_stats[date][priority] = count
                daily_stats[date]['total'] += count
        
        # 转换为列表并按日期排序
        return sorted(daily_stats.values(), key=lambda x: x['date'])

    def get_overall_statistics(self):
        """获取总体统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 总任务统计
        cursor.execute('SELECT COUNT(*) as total FROM tasks')
        total_tasks = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as completed FROM tasks WHERE completed = 1')
        completed_tasks = cursor.fetchone()['completed']
        
        cursor.execute('SELECT COUNT(*) as pending FROM tasks WHERE completed = 0')
        pending_tasks = cursor.fetchone()['pending']
        
        # 今日完成任务
        cursor.execute('''
            SELECT COUNT(*) as today_completed 
            FROM tasks 
            WHERE completed = 1 AND DATE(updated_at) = DATE('now')
        ''')
        today_completed = cursor.fetchone()['today_completed']
        
        # 今日添加任务
        cursor.execute('''
            SELECT COUNT(*) as today_added 
            FROM tasks 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_added = cursor.fetchone()['today_added']
        
        # 即将过期任务（24小时内）
        now = datetime.now()
        upcoming_count = len(self.get_upcoming_tasks())
        
        conn.close()
        
        overall_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'today_completed': today_completed,
            'today_added': today_added,
            'upcoming_tasks': upcoming_count,
            'overall_completion_rate': round(overall_completion_rate, 1)
        }
    
    def get_all_tasks(self):
        #等同load_tasks，兼容新app.py的调用
        return self.load_tasks()
    
    def complete_task(self,task_id):
        return self.mark_completed(task_id)
    
    def get_task_by_id(self,task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            task = dict(row)
            task['completed'] = bool(task['completed'])
            return task
        return None
    
    def update_task(self, task_id, description=None, due_time=None):
        if due_time == '':
            due_time = None

        if due_time and isinstance(due_time,str):
            try:
                from datetime import datetime
                due_time = datetime.fromisoformat(due_time.replace('T',' '))
            except ValueError:
                due_time = None
            
        return self.edit_task(task_id,description,None,due_time)
    
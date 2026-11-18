from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
import csv
from datetime import datetime
from io import StringIO

app = Flask(__name__)
DB_FILE = 'school.db'

# ----------------------
# Database Setup
# ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        course TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# ----------------------
# Database Functions
# ----------------------
def get_all_students(sort_by='id'):
    order = {'id':'id','name':'name','age':'age','course':'course'}.get(sort_by,'id')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM students ORDER BY {order} ASC')
    students = cursor.fetchall()
    conn.close()
    return students

def add_student(name, age, course):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO students (name, age, course) VALUES (?, ?, ?)',
                   (name.strip(), age, course.strip()))
    conn.commit()
    conn.close()

def get_student(student_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    conn.close()
    return student

def update_student(student_id, name, age, course):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE students SET name=?, age=?, course=? WHERE id=?',
                   (name.strip(), age, course.strip(), student_id))
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()

def search_students(keyword):
    keyword = f'%{keyword.strip()}%'
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE name LIKE ? OR course LIKE ?',
                   (keyword, keyword))
    students = cursor.fetchall()
    conn.close()
    return students

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT course, COUNT(*) FROM students GROUP BY course')
    by_course = cursor.fetchall()
    cursor.execute('SELECT AVG(age) FROM students')
    avg_age = cursor.fetchone()[0] or 0
    conn.close()
    return total, by_course, round(avg_age, 1)

# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    sort = request.args.get('sort', 'id')
    students = get_all_students(sort)
    total, by_course, avg_age = get_stats()
    return render_template_string(HTML_TEMPLATE,
        students=students, total=total, avg_age=avg_age, by_course=by_course,
        sort=sort, search_query='')

@app.route('/add', methods=['GET','POST'])
def add():
    if request.method == 'POST':
        add_student(request.form['name'], int(request.form['age']), request.form['course'])
        return redirect(url_for('home'))
    return render_template_string(ADD_TEMPLATE, action='Add', student=None)

@app.route('/edit/<int:student_id>', methods=['GET','POST'])
def edit(student_id):
    if request.method == 'POST':
        update_student(student_id, request.form['name'], int(request.form['age']), request.form['course'])
        return redirect(url_for('home'))
    student = get_student(student_id)
    return render_template_string(ADD_TEMPLATE, action='Edit', student=student)

@app.route('/delete/<int:student_id>')
def delete(student_id):
    delete_student(student_id)
    return redirect(url_for('home'))

@app.route('/search', methods=['POST'])
def search():
    q = request.form['q']
    students = search_students(q)
    total, by_course, avg_age = get_stats()
    return render_template_string(HTML_TEMPLATE,
        students=students, total=total, avg_age=avg_age, by_course=by_course,
        sort='id', search_query=q)

@app.route('/export')
def export():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID','Name','Age','Course'])
    for s in get_all_students():
        cw.writerow([s[0], s[1], s[2], s[3]])
    from flask import make_response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# ----------------------
# Templates — Mobile Optimized
# ----------------------
BASE_CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; }
:root {
  --primary: #3b82f6; --primary-dark: #2563eb;
  --accent: #6366f1; --success: #10b981; --danger: #ef4444; --secondary: #64748b;
  --bg-dark: #0f172a; --bg-card: #1e293b; --bg-hover: #334155;
  --text-primary: #f8fafc; --text-secondary: #94a3b8; --border: #334155;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.3); --shadow-lg: 0 10px 40px rgba(0,0,0,0.4);
}
body {
  background: linear-gradient(160deg, var(--bg-dark) 0%, #1a2744 100%);
  min-height: 100vh; color: var(--text-primary); line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.container { max-width: 100%; margin: 0 auto; padding: 1rem; }
header { text-align: center; padding: 1.5rem 1rem; }
header h1 {
  font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: 700;
  background: linear-gradient(90deg, #60a5fa, var(--accent));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
header p { color: var(--text-secondary); font-size: 0.95rem; margin-top: 0.3rem; }

/* Stats Cards */
.stats {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem;
  margin-bottom: 1.2rem;
}
.stat-card {
  background: rgba(59, 130, 246, 0.08); border-radius: 14px; padding: 1rem 0.75rem;
  text-align: center; border: 1px solid rgba(96, 165, 250, 0.15);
  transition: transform 0.2s ease;
}
.stat-card:active { transform: scale(0.97); }
.stat-card h3 { font-size: 1.6rem; color: #60a5fa; font-weight: 700; }
.stat-card p { font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem; }

/* Controls */
.controls {
  display: flex; flex-direction: column; gap: 0.8rem; margin-bottom: 1rem;
  position: sticky; top: 0; z-index: 10; padding: 0.5rem 0;
  background: linear-gradient(180deg, var(--bg-dark) 0%, transparent 100%);
}
.search-bar { display: flex; gap: 0.6rem; width: 100%; }
.search-bar input { flex: 1; min-width: 0; }
.action-row { display: flex; gap: 0.6rem; flex-wrap: wrap; }

/* Buttons */
.btn {
  padding: 0.75rem 1rem; border-radius: 10px; border: none;
  font-weight: 600; font-size: 0.95rem; cursor: pointer;
  text-decoration: none; display: inline-flex; align-items: center;
  justify-content: center; gap: 0.4rem; transition: all 0.2s ease;
  min-height: 44px; -webkit-tap-highlight-color: transparent;
}
.btn:active { transform: scale(0.96); }
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--accent)); color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25); }
.btn-success { background: linear-gradient(135deg, #059669, var(--success)); color: white; }
.btn-danger { background: linear-gradient(135deg, #dc2626, var(--danger)); color: white; }
.btn-secondary { background: var(--secondary); color: white; }
.btn-sm { padding: 0.45rem 0.7rem; font-size: 0.85rem; min-height: 36px; }

/* Cards & Forms */
.card {
  background: var(--bg-card); border-radius: 16px; padding: 1rem; margin-bottom: 1rem;
  box-shadow: var(--shadow-lg); border: 1px solid var(--border);
  backdrop-filter: blur(12px);
}
.form-card { max-width: 480px; margin: 0 auto; }

/* Inputs */
input, select {
  width: 100%; padding: 0.85rem 1rem; border-radius: 10px;
  border: 1px solid var(--border); background: var(--bg-dark);
  color: var(--text-primary); font-size: 1rem; outline: none;
  transition: border-color 0.2s ease;
}
input:focus, select:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15); }
form label {
  display: block; margin: 1.2rem 0 0.5rem; font-weight: 500;
  color: var(--text-primary); font-size: 0.95rem;
}

/* Table — Mobile Optimized */
.table-wrapper { overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 12px; }
table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 0.5rem; min-width: 600px; }
th, td { padding: 0.9rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); vertical-align: middle; }
th { background: rgba(59, 130, 246, 0.1); color: #93c5fd; font-weight: 600; font-size: 0.9rem; white-space: nowrap; }
tr { transition: background 0.15s ease; }
tr:hover { background: rgba(148, 163, 184, 0.05); }
tr:last-child td { border-bottom: none; }

/* Empty & Links */
.empty { text-align: center; padding: 3rem 1rem; color: var(--text-secondary); }
.back-link {
  display: inline-flex; align-items: center; gap: 0.4rem;
  color: #60a5fa; text-decoration: none; font-size: 0.95rem;
  margin-bottom: 1rem; padding: 0.5rem 0;
}
.back-link:hover { text-decoration: underline; }

/* Responsive Adjustments */
@media (max-width: 640px) {
  .container { padding: 0.75rem; }
  header { padding: 1rem 0.5rem; }
  .stats { grid-template-columns: repeat(3, 1fr); gap: 0.6rem; }
  .stat-card { padding: 0.8rem 0.5rem; }
  .stat-card h3 { font-size: 1.3rem; }
  .controls { gap: 0.7rem; }
  .action-row { flex-direction: column; }
  .btn { width: 100%; }
  .table-wrapper { margin: 0 -0.5rem; padding: 0 0.5rem; }
}
'''

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>🎓 Student Record System</title>
<style>''' + BASE_CSS + '''</style>
</head>
<body>
<div class="container">
    <header>
        <h1>🎓 Student Records</h1>
        <p>Simple • Fast • Mobile-friendly</p>
    </header>

    <div class="stats">
        <div class="stat-card"><h3>{{ total }}</h3><p>Students</p></div>
        <div class="stat-card"><h3>{{ avg_age }}</h3><p>Avg Age</p></div>
        <div class="stat-card"><h3>{{ by_course|length }}</h3><p>Courses</p></div>
    </div>

    <div class="card">
        <div class="controls">
            <form action="{{ url_for('search') }}" method="POST" class="search-bar">
                <input type="text" name="q" placeholder="🔍 Search..." value="{{ search_query }}" required>
                <button type="submit" class="btn btn-secondary">Go</button>
            </form>
            <div class="action-row">
                <a href="{{ url_for('add') }}" class="btn btn-primary">➕ Add Student</a>
                <a href="{{ url_for('home') }}" class="btn btn-secondary">📋 All</a>
                <a href="{{ url_for('export') }}" class="btn btn-success">📂 CSV</a>
            </div>
        </div>

        {% if search_query %}
        <p style="margin-bottom:0.8rem; color:var(--text-secondary); font-size:0.9rem;">
          Results for: <strong>"{{ search_query }}"</strong> — 
          <a href="{{ url_for('home') }}" style="color:#60a5fa; text-decoration:none;">Clear search</a>
        </p>
        {% endif %}

        <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th><a href="{{ url_for('home', sort='id') }}" style="color:inherit;text-decoration:none">#</a></th>
                    <th><a href="{{ url_for('home', sort='name') }}" style="color:inherit;text-decoration:none">Name ↕</a></th>
                    <th><a href="{{ url_for('home', sort='age') }}" style="color:inherit;text-decoration:none">Age ↕</a></th>
                    <th><a href="{{ url_for('home', sort='course') }}" style="color:inherit;text-decoration:none">Course ↕</a></th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for s in students %}
                <tr>
                    <td><strong>{{ s[0] }}</strong></td>
                    <td>{{ s[1] }}</td>
                    <td>{{ s[2] }}</td>
                    <td>{{ s[3] }}</td>
                    <td>
                        <a href="{{ url_for('edit', student_id=s[0]) }}" class="btn btn-secondary btn-sm">✏️ Edit</a>
                        <a href="{{ url_for('delete', student_id=s[0]) }}" class="btn btn-danger btn-sm" onclick="return confirm('⚠️ Delete student #{{ s[0] }}?\\nThis cannot be undone!')">🗑️</a>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="5" class="empty">📭 No students yet.<br><a href="{{ url_for('add') }}" style="color:#60a5fa;">Tap here to add your first student!</a></td></tr>
                {% endfor %}
            </tbody>
        </table>
        </div>
    </div>
</div>
<script>
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.querySelector('input[name="q"]');
  if (searchInput) {
    searchInput.addEventListener('search', function() {
      this.blur();
    });
  }
});
</script>
</body>
</html>'''

ADD_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ action }} Student</title>
<style>''' + BASE_CSS + '''</style>
</head>
<body>
<div class="container">
    <a href="{{ url_for('home') }}" class="back-link">← Back to Records</a>
    <div class="card form-card">
        <h2 style="text-align:center; margin-bottom:1.5rem; color:#60a5fa; font-size:1.4rem;">
          {{ '✏️ Edit Student' if student else '➕ Add New Student' }}
        </h2>
        <form method="POST">
            <label>Full Name *</label>
            <input type="text" name="name" value="{{ student[1] if student else '' }}" placeholder="Enter full name" required>
            
            <label>Age *</label>
            <input type="number" name="age" min="10" max="100" value="{{ student[2] if student else '' }}" placeholder="Enter age" required>
            
            <label>Course *</label>
            <input type="text" name="course" value="{{ student[3] if student else '' }}" placeholder="Enter course name" required>
            
            <div style="text-align:center; margin-top:1.8rem;">
                <button type="submit" class="btn btn-primary" style="width:100%;">{{ '✅ Update Student' if student else '➕ Add Student' }}</button>
            </div>
        </form>
    </div>
</div>

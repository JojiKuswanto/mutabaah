from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rahasia123'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            tanggal TEXT,
            skor INTEGER
        )""")
    c.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES ('admin','admin','admin')")
    c.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES ('user1','user1','user')")
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('database.db')
    return conn

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT id,role FROM users WHERE username=? AND password=?", (u,p))
        row = c.fetchone()
        conn.close()
        if row:
            session['user_id'] = row[0]
            session['role'] = row[1]
            session['username'] = u
            return redirect('/dashboard' if row[1]=='user' else '/admin')
        return "Login gagal"
    return render_template('login.html')

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if session.get('role')!='user': return redirect('/login')
    user_id = session['user_id']
    if request.method=='POST':
        skor = int(request.form['skor'])
        tanggal = datetime.now().strftime('%Y-%m-%d')
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO activities (user_id,tanggal,skor) VALUES (?,?,?)", (user_id,tanggal,skor))
        conn.commit(); conn.close()
    week = request.args.get('week')
    month = request.args.get('month')
    q = "SELECT tanggal,skor FROM activities WHERE user_id=?"
    params=[user_id]
    if week: q += " AND strftime('%W',tanggal)=?"; params.append(week.zfill(2))
    if month: q += " AND strftime('%m',tanggal)=?"; params.append(month.zfill(2))
    conn = get_db(); c=conn.cursor()
    c.execute(q, params)
    data = c.fetchall(); conn.close()
    dates=[r[0] for r in data]; scores=[r[1] for r in data]
    return render_template('dashboard.html', dates=dates, scores=scores, week=week or '', month=month or '')

@app.route('/admin')
def admin():
    if session.get('role')!='admin': return redirect('/login')
    week = request.args.get('week'); month = request.args.get('month')
    q="SELECT users.username,SUM(activities.skor) FROM activities JOIN users ON activities.user_id=users.id WHERE 1=1"
    params=[]
    if week: q+=" AND strftime('%W',tanggal)=?"; params.append(week.zfill(2))
    if month: q+=" AND strftime('%m',tanggal)=?"; params.append(month.zfill(2))
    q+=" GROUP BY users.username"
    conn = get_db(); c=conn.cursor()
    c.execute(q,params); rows=c.fetchall(); conn.close()
    users=[r[0] for r in rows]; totals=[r[1] for r in rows]
    notifs=[]
    max_week=7*7
    for u,t in rows:
        if t<max_week*0.5:
            notifs.append({'user':u,'score':t,'target':max_week})
    return render_template('admin.html', users=users, totals=totals, notifs=notifs, week=week or '', month=month or '')

if __name__ == '__main__':
    app.run(debug=True)

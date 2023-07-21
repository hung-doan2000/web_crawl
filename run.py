from flask import Flask, render_template
from database import mysql
from scheduler import sched
from tool import tool
from product import product, crawl
from job import job
from home import home

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crawl'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_DB'] = 'blogs'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Anhhung040100'

mysql.init_app(app)
sched.init_app(app)

app.register_blueprint(tool)
app.register_blueprint(product)
app.register_blueprint(job)
app.register_blueprint(home)

@app.route("/")
def index():
    return render_template("dashboard.html", title="Trang chủ")

if __name__ == "__main__":

    sched.start()
    app.run(debug=True, use_reloader=False)

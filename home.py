from flask import Blueprint, render_template, url_for
from database import mysql

home = Blueprint("home", __name__, url_prefix="/")

@home.route("")
def dashboard():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        cursor.execute("Select count(*) from crawl_tools")
        total_tools = cursor.fetchone()

        cursor.execute("Select count(*) from products")
        total_products = cursor.fetchone()

        cursor.execute("Select count(*) from product_stores")
        total_stores = cursor.fetchone()

        cursor.execute("Select count(*) from admins")
        total_users = cursor.fetchone()

        data = {
            "tool": total_tools,
            "product": total_products,
            "store": total_stores,
            "user": total_users,
        }

        return render_template("dashboard.html", data = data)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()
from flask import Blueprint, render_template, request, url_for, jsonify, flash, redirect, abort
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Length, ValidationError, Regexp
from database import mysql
from scheduler import sched
from datetime import datetime
from product import product, autoCrawl

job = Blueprint("job", __name__, url_prefix="/job")

def required_validator(form, field):
    if len(field.data) == 0:
        raise ValidationError('Không được để trống.')
    
class JobForm(FlaskForm):
    name = StringField(label=('Tên Job'), validators=[required_validator, Length(max=255)])
    time = StringField(label=('Thời gian'), validators=[required_validator, Regexp(regex='^[1-9][0-9]*$', message="Đầu vào không hợp lệ.")])

@job.route("")
def showList(): 
    return render_template("job/list.html")

@job.route("/list", methods=["GET", "POST"])
def getListJob():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        cursor.execute('Select * from jobs order by jobs.id DESC')
        jobs = cursor.fetchall()

        data = []
        for row in jobs:
            cursor.execute('Select * from crawl_tools where id = %s', (row[2]))
            tool = cursor.fetchone()
            start_time = row[3].strftime("%Y-%m-%d %H:%M" )
            if int(row[5]) == 1:
                status = '<span class="badge badge-success"> Đã kích hoạt </span>'
            else:
                status = '<span class="badge badge-danger"> Chưa kích hoạt </span>'
            data.append({
                'id': row[0],       
                'name': row[1],
                'tool': tool[1],
                'start_time': start_time,
                'time': row[4] + ' ngày',
                'status': status,
                'action': '<a data-toggle-for="tooltip" title="Sửa thông tin" href="/job/update/' + format(row[0]) + '" class="btn text-info job-edit"><i class="fas fa-edit" ></i></a>' 
                        + '<a data-toggle-for="tooltip" title="Xóa" id="' + format(row[0]) + '" class="btn text-danger job-destroy"><i class="fas fa-trash" ></i></a>'
            })
                
        response = {
            'data': data,
        }
        return jsonify(response)
    except Exception as e:
        print(e)
        abort(500)
    finally:
        cursor.close()
        conn.close()

@job.route("/delete", methods=["POST", "GET"])     
def deleteJob():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        if request.method == 'POST':
            id_job = request.form['id']
            cursor.execute('Select name, is_active from jobs where id = {0}'. format(id_job))
            current_job = cursor.fetchone()

            cursor.execute('Delete from jobs where id = {0}'. format(id_job))
            conn.commit()
            if (current_job[1] and sched.get_job( id=current_job[0] )):
                sched.remove_job( id=current_job[0] )

            flash("Xóa job thành công", "success")    
        return jsonify()
    except Exception as e:
        flash("Xóa job thất bại", "error")    
        print(e)
    finally:
        cursor.close()
        conn.close()

@job.route("/create", methods=["GET", "POST"])
def createJob():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        cursor.execute('Select * from crawl_tools')
        tools = cursor.fetchall()

        tool_id = request.form.get('tools')
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = request.form.get('start_date')
        form = JobForm()
        check_active = request.form.get('is_active')
        if (check_active):
            is_active = 1
        else: 
            is_active = 0
        if form.validate_on_submit():  
            try:
                cursor.execute('Insert INTO jobs (name, tool_id, start_time, time, is_active, created_at, updated_at) VALUES(%s, %s, %s, %s, %s, %s, %s)', (form.name.data, tool_id, start_time, form.time.data, is_active, time, time))
                conn.commit()
                if (is_active == 1):
                    sched.add_job(id=form.name.data, func=autoCrawl, args=[tool_id], trigger = "interval", start_date = start_time, days = int(form.time.data))

                flash("Thêm mới thành công", "success")
                return redirect(url_for('job.showList'))
            except Exception as e:
                print(e)
                flash("Thêm mới thất bại", "error")

        data = {
            'tools': tools,
        }
        return render_template("job/create.html", form=form, data=data)
    except Exception as e:
        flash("Thêm mới thất bại", "error")
        print(e)
    finally:
        cursor.close()
        conn.close()

@job.route("/update/<string:id>", methods=["GET", "POST"])
def updateJob(id):  
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        cursor.execute('Select * from jobs where id=%s', (id))
        job = cursor.fetchone()
        
        cursor.execute('Select * from crawl_tools')
        tools = cursor.fetchall()
        
        form = JobForm()
        tool_id = request.form.get('tools')
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = request.form.get('start_date')
        check_active = request.form.get('is_active')
        if (check_active):
            is_active = 1
        else: 
            is_active = 0
        if form.validate_on_submit():  
            try:
                cursor.execute('Update jobs SET name=%s, tool_id=%s, start_time=%s, time=%s, is_active=%s, updated_at=%s where id=%s', (form.name.data, tool_id, start_time, form.time.data, is_active, time, id))
                conn.commit()
                if (is_active == 0 and sched.get_job(id=form.name.data)):
                    sched.remove_job(id=form.name.data)
                if (is_active == 1 and not sched.get_job(id=form.name.data)):
                    sched.add_job(id=form.name.data, func=autoCrawl, args=[tool_id], trigger = "interval", start_date=start_time, days = int(form.time.data))

                flash("Cập nhật thành công", "success")
                return redirect(url_for('job.showList'))
            except Exception as e:
                print(e)
                flash("Cập nhật thất bại", "error")

        data = {
            "job": job,
            "tools": tools,
            "tool_id": int(job[2]), 
            "start_date": str(job[3])
        }
        return render_template("job/edit.html", form=form, data=data)
    except Exception as e:
        print(e)
        abort(404)
    finally:
        cursor.close()
        conn.close()
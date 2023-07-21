from flask import Blueprint, render_template, request, url_for, jsonify, flash, redirect, abort
from database import mysql
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import Length, URL, ValidationError
import json
from datetime import datetime

tool = Blueprint("tool", __name__, url_prefix="/tool")

def required_validator(form, field):
    if len(field.data) == 0:
        raise ValidationError('Không được để trống.')
    
class ToolForm(FlaskForm):
    name = StringField(label=('Tên Tool'), validators=[required_validator, Length(max=255)])
    link = StringField(label=('Đường dẫn'), validators=[required_validator, URL(message="Đường dẫn không hợp lệ.", require_tld=True), Length(max=255)])
    check_box = BooleanField(label=('Sử dụng selector cửa hàng đã chọn'))

class ToolFormWithSelector(FlaskForm):
    name = StringField(label=('Tên Tool'), validators=[required_validator, Length(max=255)])
    link = StringField(label=('Đường dẫn'), validators=[required_validator, URL(message="Đường dẫn không hợp lệ.", require_tld=True), Length(max=255)])
    selector_item = StringField(label=('Selector Khung'), validators=[required_validator,Length(max=255)])
    selector_title = StringField(label=('Selector Tên'), validators=[required_validator,Length(max=255)])
    selector_price = StringField(label=('Selector Giá'), validators=[required_validator,Length(max=255)])
    selector_image = StringField(label=('Selector Ảnh'), validators=[required_validator,Length(max=255)])
    selector_link = StringField(label=('Selector Đường dẫn'), validators=[required_validator,Length(max=255)])
    selector_detail_link = StringField(label=('Selector Đường dẫn con'), validators=[Length(max=255)])
    selector_button = StringField(label=('Selector Load Button'), validators=[Length(max=255)])
    selector_detail = StringField(label=('Selector Khung Thông Số'), validators=[required_validator,Length(max=255)])
    selector_detail_title = StringField(label=('Selector Tên Thông Số'), validators=[required_validator,Length(max=255)])
    selector_detail_value = StringField(label=('Selector Chi Tiết'), validators=[required_validator,Length(max=255)])
    check_box = BooleanField(label=('Sử dụng selector cửa hàng đã chọn'))

@tool.route("")
def showListTool(): 
    return render_template("tool/list.html")

@tool.route("/list", methods=["POST", "GET"])
def getListTool():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        ## Total number of records
        cursor.execute('Select count(*) from crawl_tools')
        totalRecords = cursor.fetchone()
        
        ## List records
        cursor.execute('Select * from crawl_tools')
        tools = cursor.fetchall()

        data =[]
        index = 1
        for row in tools:
            cursor.execute('Select * from product_stores where id = %s', (row[3]))
            store = cursor.fetchone()

            cursor.execute('Select * from product_categories where id = %s', (row[4]))
            category = cursor.fetchone()
            data.append({
                'id': index,
                'name': row[1],
                'store': '<span class="badge badge-warning">' + store[1] + '</span>',
                'category': '<span class="badge badge-info">' + category[1] + '</span>',
                
                'link': '<a target="_blank" href="' + format(row[2]) + '">' + format(row[2]) + '</a>' ,
                'action': '<a data-toggle-for="tooltip" title="Crawl dữ liệu" id="' + format(row[0]) + '" class="btn text-secondary tool-crawl"><i class="fas fa-spider"></i></a>' 
                        + '<a data-toggle-for="tooltip" title="Sửa thông tin" href="/tool/update/' + format(row[0]) + '" class="btn text-info tool-edit"><i class="fas fa-edit" ></i></a>' 
                        + '<a data-toggle-for="tooltip" title="Xóa" id="' + format(row[0]) + '" class="btn text-danger tool-destroy"><i class="fas fa-trash" ></i></a>'
            })
            index += 1
        response = {
            'data': data,
            'iTotalDisplayRecords': totalRecords,
        }
        return jsonify(response)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()

@tool.route("/delete", methods=["POST", "GET"])     
def deleteTool():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        if request.method == 'POST':
            id_tool = request.form['id']
            cursor.execute('Delete from crawl_tools where id = {0}'. format(id_tool))
            conn.commit()
            flash("Xóa tool thành công", "success")    
            msg = 'Xóa thành công'

        return jsonify(msg)
    except Exception as e:
        flash("Xóa tool thất bại", "error")    
        msg = 'Xóa thất bại'
        print(e)
    finally:
        cursor.close()
        conn.close()

@tool.route("/create", methods=["GET", "POST"])
def createTool():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        cursor.execute('Select * from product_stores where status = 1')
        stores = cursor.fetchall()

        cursor.execute('Select * from product_categories where status = 1')
        categories = cursor.fetchall()

        form = ToolForm()
        selector_msg = ''
        store_id = request.form.get('stores')
        cate_id = request.form.get('categories')
        checked = 0
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if form.check_box.data:   
            if form.validate_on_submit():   
                cursor.execute('Select selector from crawl_tools where store_id=%s', (store_id))
                selector = cursor.fetchone()

                if not selector:
                    selector_msg = 'Cửa hàng đã chọn chưa có bộ selector.'
                else:
                    try:
                        cursor.execute('Insert INTO crawl_tools (name, link, store_id, category_id, selector, created_at. updated_at) VALUES(%s, %s, %s, %s, %s, %s, %s)', (form.name.data, form.link.data, store_id, cate_id, selector, time, time))
                        conn.commit()
                        flash("Thêm mới thành công", "success")
                        return redirect(url_for('tool.showListTool'))
                    except:
                        flash("Thêm mới thất bại", "error")
            else:
                checked = 1

        form = ToolFormWithSelector()
        if form.validate_on_submit():  
            selector = {
                'selector_item': form.selector_item.data,
                'selector_title': form.selector_title.data,
                'selector_price': form.selector_price.data,
                'selector_image': form.selector_image.data,
                'selector_link': form.selector_link.data,
                'selector_detail_link': form.selector_detail_link.data,
                'selector_load_button': form.selector_button.data,
                'selector_detail': form.selector_detail.data,
                'selector_detail_title': form.selector_detail_title.data,
                'selector_detail_value': form.selector_detail_value.data,
                'selector_detail_btn': request.form.get('selector_detail_btn'),
                'selector_detail_des': request.form.get('selector_detail_des'),
                'selector_detail_rating': request.form.get('selector_detail_rating')
            }
            json_selector = json.dumps(selector, indent = 4) 

            try:
                cursor.execute('Insert INTO crawl_tools (name, link, store_id, category_id, selector, created_at, updated_at) VALUES(%s, %s, %s, %s, %s, %s, %s)', (form.name.data, form.link.data, store_id, cate_id, json_selector, time, time))
                conn.commit()
                flash("Thêm mới thành công", "success")
                return redirect(url_for('tool.showListTool'))
            except Exception as e:
                print(e)
                flash("Thêm mới thất bại", "error")
        
        form.check_box.data = False  
        data = {
            'stores': stores,
            'categories': categories,
            'selector_msg': selector_msg
        }
        return render_template("tool/form.html", form=form, data = data, checked = checked)
    except Exception as e:
        flash("Thêm mới thất bại", "error")
        print(e)
    finally:
        cursor.close()
        conn.close()

@tool.route("/update/<string:id>", methods=["GET", "POST"])
def updateTool(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        
        cursor.execute('Select * from crawl_tools where id=%s', (id))
        tool = cursor.fetchone()

        cursor.execute('Select * from product_stores where status = 1')
        stores = cursor.fetchall()

        cursor.execute('Select * from product_categories where status = 1')
        categories = cursor.fetchall()

        selector_msg =''
        form = ToolFormWithSelector()
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            selector = json.loads(str(tool[5]))
            print(type(selector))
            if type(selector) is not dict:
                selector_msg = 'Selector không đúng định dạng.'
            
            if form.validate_on_submit():  
                store_id = request.form.get('stores')
                cate_id = request.form.get('categories')
                selector = {
                    'selector_item': form.selector_item.data,
                    'selector_title': form.selector_title.data,
                    'selector_price': form.selector_price.data,
                    'selector_image': form.selector_image.data,
                    'selector_link': form.selector_link.data,
                    'selector_detail_link': form.selector_detail_link.data,
                    'selector_load_button': form.selector_button.data,
                    'selector_detail': form.selector_detail.data,
                    'selector_detail_title': form.selector_detail_title.data,
                    'selector_detail_value': form.selector_detail_value.data,
                    'selector_detail_btn': request.form.get('selector_detail_btn'),
                    'selector_detail_des': request.form.get('selector_detail_des'),
                    'selector_detail_rating': request.form.get('selector_detail_rating')
                }
                json_selector = json.dumps(selector, indent = 4) 

                try:
                    cursor.execute('Update crawl_tools SET name = %s, link=%s, store_id=%s, category_id=%s, selector=%s, updated_at=%s WHERE id = %s', (form.name.data, form.link.data, store_id, cate_id, json_selector, time, id))
                    conn.commit()
                    flash("Cập nhật thành công", "success")

                    return redirect(url_for('tool.showListTool'))
                except Exception as e:
                    print(e)
                    flash("Cập nhật thất bại", "error")            

        except Exception as e:
            print(e)
            selector_msg = 'Selector không đúng định dạng.'

        data = {
            'stores': stores,
            'categories': categories,
            'store_id': int(tool[3]),
            'category_id': int(tool[4]),
            'selector_msg': selector_msg, 
            'tool' : tool, 
            'selector' : selector
        } 
        
        return render_template("tool/edit.html", form = form, data = data)
            
    except Exception as e:
        print(e)
        abort(404)
    finally:
        cursor.close()
        conn.close()
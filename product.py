from flask import Blueprint, render_template, jsonify, flash, abort
from database import mysql
import json, os, ast
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime

product = Blueprint("product", __name__, url_prefix = "/crawl", static_folder="static")

@product.route("")
def showListProduct(): 
    return render_template("product/list.html")

@product.route("/list_product", methods=["GET", "POST"])
def getListProduct():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        filename = os.path.join(product.static_folder, 'data', 'product.json')
        with open(filename, encoding='utf-8') as f:
            json_data = json.load(f)

        data = []
        index = 1
        for row in json_data:
            cursor.execute('Select * from product_stores where id = %s', (row["store_id"]))
            store = cursor.fetchone()

            cursor.execute('Select * from product_categories where id = %s', (row["category_id"]))
            category = cursor.fetchone()

            data.append({
                'id': index,    
                'name': row["title"],
                'image': '<img width="100%" src="' + format(row["img"]) + '" alt="">' ,
                'price':  row["price"] ,
                'store': '<span class="badge badge-warning">' + format(store[1]) + '</span>',
                'category': '<span class="badge badge-info">' + format(category[1]) + '</span>',
                'action': '<a data-toggle-for="tooltip" title="Chi tiết" href="crawl/product_detail/' + format(index) + '" class="btn text-success tool-edit"><i class="fas fa-eye"></i></a>' 
            })
            index += 1
                
        response = {
            'data': data,
        }

        return jsonify(response)
    except Exception as e:
        flash("Crawl thất bại", "error")
        print(e)
        return jsonify({'msg': 'Crawl thất bại'}), 500
    finally:
        cursor.close()
        conn.close()

@product.route("/product_detail/<string:id>", methods=["GET", "POST"])
def detailProduct(id):
    try: 
        filename = os.path.join(product.static_folder, 'data', 'product.json')
        with open(filename, encoding='utf-8') as f:
            json_data = json.load(f)
    
        data = json_data[int(id)-1]

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('Select * from product_stores where id = %s', (data["store_id"]))
        store = cursor.fetchone()

        cursor.execute('Select * from product_categories where id = %s', (data["category_id"]))
        category = cursor.fetchone()

        if data["specifications"] :
            specifications = ast.literal_eval(data["specifications"])
        else : 
            specifications = ''
        return render_template("product/detail.html", product = data, store=store, cate = category, specifications=specifications)
    
    except Exception as e:
        print(e)
        abort(500)
    
@product.route("/<string:id>", methods=["GET", "POST"])
def crawl(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('Select link, selector, store_id, category_id from crawl_tools where id=%s', (id))
        tool = cursor.fetchone()
        if tool:
            # Save data json
            filename = os.path.join(product.static_folder, 'data', 'product.json')
            with open(filename,'w', encoding='utf-8') as f:
                json.dump([],f,ensure_ascii=False)

            def save_data(new_data):
                with open(filename, 'r+', encoding='utf-8') as file:
                    file_data = json.load(file)
                    file_data.append(new_data)
                    file.seek(0)
                    json.dump(file_data, file,ensure_ascii=False, indent=4)

            selector = json.loads(tool[1])
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options = options)
            driver.get(tool[0])
            sleep(2)
            try:
                if (selector["selector_load_button"]):
                    while(1):
                        btn_load_more = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_load_button"]))
                        if(btn_load_more):
                            try:
                                btn_load_more[0].click()
                                sleep(2)
                            except Exception as e:
                                print(e)
                                break
                        else: break

                item_links = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_link"]))
                if not (selector["selector_detail_link"]):
                    item_titles =  driver.find_elements(By.CSS_SELECTOR, str(selector["selector_title"]))    
                    item_prices = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_price"]))
                    item_images = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_image"]))
                    titles = [item.get_attribute('innerText') for item in item_titles]
                    links = [item.get_attribute('href') for item in item_links]
                    prices = [item.get_attribute('innerText') for item in item_prices]
                    images = [item.get_attribute('src') for item in item_images]

                    specifications = {}
                    description = ''
                    rating = ''
                    for i in range(len(links)):
                        driver.get(links[i])  
                        sleep(1)   
                        
                        if selector["selector_detail_btn"]:
                            btn = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_btn"]))
                            if btn:
                                try:
                                    btn[0].click()
                                    sleep(2)
                                except Exception as e:
                                    print(e)
                        
                        if selector["selector_detail_des"]:   
                            item_description = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_des"]))
                            if (item_description):
                                description = item_description[0].get_attribute('innerHTML') 
                        if selector["selector_detail_rating"]:   
                            item_rating = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_rating"]))   
                            if (item_rating):
                                rating = item_rating[0].get_attribute('innerText')    
                                count = rating.find("/")
                                rating = rating[:count]

                        names = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_title"]))
                        print(names)
                        spe_names = [name.get_attribute('innerText') for name in names]
                        values = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_value"]))
                        spe_values = [value.get_attribute('innerText') for value in values]

                        for j in range(len(spe_names)):
                            specifications[str(spe_names[j])] = spe_values[j]

                        save_data({
                            "title": titles[i],
                            "link": links[i],
                            "price": prices[i],
                            "img": images[i],
                            "specifications": str(specifications),
                            "description": description,
                            "rating": rating,
                            "store_id" : tool[2],
                            "category_id" : tool[3],
                        })

                    driver.close()
                    flash("Crawl thành công", "success")
                    return jsonify({"msg": "Thành công"}), 200
                else:
                    links = [item.get_attribute('href') for item in item_links]
                    item_images = driver.find_elements(By.CSS_SELECTOR, selector["selector_image"]) 
                    imgs = []
                    for x in  range(len(item_images)):
                        img = item_images[x].get_attribute('data-src')
                        if not img:
                            img = item_images[x].get_attribute('src') 
                        imgs.append(img)

                    specifications = {}
                    description = ''
                    rating = ''

                    for i in range(len(links)):
                        driver.get(links[i])  
                        sleep(1)   

                        items = driver.find_elements(By.CSS_SELECTOR, selector["selector_detail_link"])
                        if items:
                            child_links = [item.get_attribute('href') for item in items]
                            j = 0
                            while j < len(child_links):
                                title = driver.find_element(By.CSS_SELECTOR, selector["selector_title"]).get_attribute('innerText')
                                price = driver.find_element(By.CSS_SELECTOR, selector["selector_price"]).get_attribute('innerText')

                                if j+1 < len(child_links):
                                    driver.get(child_links[j+1])
                                    sleep(1)

                                if selector["selector_detail_des"]:   
                                    item_description = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_des"]))
                                    if (item_description):
                                        description = item_description[0].get_attribute('innerHTML') 
                                if selector["selector_detail_rating"]:   
                                    item_rating = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_rating"]))   
                                    if (item_rating):
                                        rating = item_rating[0].get_attribute('innerText')  

                                names = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_title"]))
                                spe_names = [name.get_attribute('innerText') for name in names]
                                values = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_value"]))
                                spe_values = [value.get_attribute('innerText') for value in values]

                                for index in range(len(spe_names)):
                                    specifications[str(spe_names[index])] = spe_values[index]

                                save_data({
                                    "title": title,
                                    "link": child_links[j],
                                    "price": price,
                                    "img": imgs[i],
                                    "specifications": str(specifications),
                                    "description": description,
                                    "rating": rating,
                                    "store_id" : tool[2],
                                    "category_id" : tool[3], 
                                })
                                j = j+1
                        else:
                            title = driver.find_element(By.CSS_SELECTOR, selector["selector_title"]).get_attribute('innerText')
                            price = driver.find_element(By.CSS_SELECTOR, selector["selector_price"]).get_attribute('innerText')

                            if selector["selector_detail_des"]:   
                                item_description = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_des"]))
                                if (item_description):
                                    description = item_description[0].get_attribute('innerHTML') 
                            if selector["selector_detail_rating"]:   
                                item_rating = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_rating"]))   
                                if (item_rating):
                                    rating = item_rating[0].get_attribute('innerText')  

                            names = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_title"]))
                            spe_names = [name.get_attribute('innerText') for name in names]
                            values = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_value"]))
                            spe_values = [value.get_attribute('innerText') for value in values]

                            for index in range(len(spe_names)):
                                specifications[str(spe_names[index])] = spe_values[index]

                            save_data({
                                "title": title,
                                "link": links[i],
                                "price": price,
                                "img": imgs[i],
                                "specifications": str(specifications),
                                "description": description,
                                "rating": rating,
                                "store_id" : tool[2],
                                "category_id" : tool[3], 
                            })
                    driver.close()
                    flash("Crawl thành công", "success")
                    return jsonify({"msg": "Thành công"}), 200
            except Exception as e:
                print(e)
                return jsonify({'msg': 'Crawl thất bại:  Lỗi Selector'}), 500
        else:
            print(e)
            return jsonify({'msg': 'Crawl thất bại:  Tool không hợp lệ'}), 500
        
    except Exception as e:
        print(e)
        abort(404)
        
    finally:
        cursor.close()
        conn.close()

@product.route("/save", methods=["GET", "POST"])
def save():
    try:
        conn = mysql.connect()
        cursor = conn.cursor()

        filename = os.path.join(product.static_folder, 'data', 'product.json')
        with open(filename, encoding='utf-8') as f:
            json_data = json.load(f)

        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(time)
        for row in json_data:
            cursor.execute('SELECT count(*) from products_demo where title=%s', (row["title"]))
            record_exist = cursor.fetchone()

            if record_exist[0] != 0:
                cursor.execute('UPDATE products_demo SET price=%s, link=%s, img=%s, specifications=%s, description=%s, store_id=%s, category_id=%s, rating=%s, updated_at=%s  where title=%s',
                               (row["price"],row["link"],row["img"],row["specifications"],row["description"],row["store_id"],row["category_id"],row["rating"], time, row["title"]))
                conn.commit()
            else: 
                cursor.execute('INSERT INTO products_demo (title, price, link, img, specifications, description, store_id, category_id, rating, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (row["title"], row["price"],row["link"],row["img"],row["specifications"],row["description"],row["store_id"],row["category_id"],row["rating"], time, time))
                conn.commit()

        return jsonify({'msg': 'Lưu thành công'}), 200
    except Exception as e:
        print(e)
        flash("Lưu thất bại", "error")
        return jsonify({'msg': 'Lưu thất bại'}), 500
    finally:
        cursor.close()
        conn.close()

def autoCrawl(id):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('Select link, selector, store_id, category_id from crawl_tools where id=%s', (id))
        tool = cursor.fetchone()
        if tool:
            # Save data json
            filename = os.path.join(product.static_folder, 'data', 'product.json')
            with open(filename,'w', encoding='utf-8') as f:
                json.dump([],f,ensure_ascii=False)

            def save_data(new_data):
                with open(filename, 'r+', encoding='utf-8') as file:
                    file_data = json.load(file)
                    file_data.append(new_data)
                    file.seek(0)
                    json.dump(file_data, file,ensure_ascii=False, indent=4)

            selector = json.loads(tool[1])
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options = options)
            driver.get(tool[0])
            sleep(2)
            try:
                if (selector["selector_load_button"]):
                    while(1):
                        btn_load_more = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_load_button"]))
                        if(btn_load_more):
                            try:
                                btn_load_more[0].click()
                                sleep(2)
                            except Exception as e:
                                print(e)
                                break
                        else: break

                item_links = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_link"]))
                if not (selector["selector_detail_link"]):
                    item_titles =  driver.find_elements(By.CSS_SELECTOR, str(selector["selector_title"]))    
                    item_prices = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_price"]))
                    item_images = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_image"]))
                    titles = [item.get_attribute('innerText') for item in item_titles]
                    links = [item.get_attribute('href') for item in item_links]
                    prices = [item.get_attribute('innerText') for item in item_prices]
                    images = [item.get_attribute('src') for item in item_images]

                    specifications = {}
                    description = ''
                    rating = ''
                    for i in range(len(links)):
                        driver.get(links[i])  
                        sleep(1)   
                        
                        if selector["selector_detail_btn"]:
                            btn = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_btn"]))
                            if btn:
                                try:
                                    btn[0].click()
                                    sleep(2)
                                except Exception as e:
                                    print(e)
                        
                        if selector["selector_detail_des"]:   
                            item_description = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_des"]))
                            if (item_description):
                                description = item_description[0].get_attribute('innerHTML') 
                        if selector["selector_detail_rating"]:   
                            item_rating = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_rating"]))   
                            if (item_rating):
                                rating = item_rating[0].get_attribute('innerText')    
                                count = rating.find("/")
                                rating = rating[:count]

                        names = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_title"]))
                        print(names)
                        spe_names = [name.get_attribute('innerText') for name in names]
                        values = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_value"]))
                        spe_values = [value.get_attribute('innerText') for value in values]

                        for j in range(len(spe_names)):
                            specifications[str(spe_names[j])] = spe_values[j]

                        save_data({
                            "title": titles[i],
                            "link": links[i],
                            "price": prices[i],
                            "img": images[i],
                            "specifications": str(specifications),
                            "description": description,
                            "rating": rating,
                            "store_id" : tool[2],
                            "category_id" : tool[3],
                        })

                    driver.close()
                    save()
                else:
                    links = [item.get_attribute('href') for item in item_links]
                    item_images = driver.find_elements(By.CSS_SELECTOR, selector["selector_image"]) 
                    imgs = []
                    for x in  range(len(item_images)):
                        img = item_images[x].get_attribute('data-src')
                        if not img:
                            img = item_images[x].get_attribute('src') 
                        imgs.append(img)

                    specifications = {}
                    description = ''
                    rating = ''

                    for i in range(len(links)):
                        driver.get(links[i])  
                        sleep(1)   

                        items = driver.find_elements(By.CSS_SELECTOR, selector["selector_detail_link"])
                        if items:
                            child_links = [item.get_attribute('href') for item in items]
                            j = 0
                            while j < len(child_links):
                                title = driver.find_element(By.CSS_SELECTOR, selector["selector_title"]).get_attribute('innerText')
                                price = driver.find_element(By.CSS_SELECTOR, selector["selector_price"]).get_attribute('innerText')

                                if j+1 < len(child_links):
                                    driver.get(child_links[j+1])
                                    sleep(1)

                                if selector["selector_detail_des"]:   
                                    item_description = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_des"]))
                                    if (item_description):
                                        description = item_description[0].get_attribute('innerHTML') 
                                if selector["selector_detail_rating"]:   
                                    item_rating = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_rating"]))   
                                    if (item_rating):
                                        rating = item_rating[0].get_attribute('innerText')  

                                names = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_title"]))
                                spe_names = [name.get_attribute('innerText') for name in names]
                                values = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_value"]))
                                spe_values = [value.get_attribute('innerText') for value in values]

                                for index in range(len(spe_names)):
                                    specifications[str(spe_names[index])] = spe_values[index]

                                save_data({
                                    "title": title,
                                    "link": child_links[j],
                                    "price": price,
                                    "img": imgs[i],
                                    "specifications": str(specifications),
                                    "description": description,
                                    "rating": rating,
                                    "store_id" : tool[2],
                                    "category_id" : tool[3], 
                                })
                                j = j+1
                        else:
                            title = driver.find_element(By.CSS_SELECTOR, selector["selector_title"]).get_attribute('innerText')
                            price = driver.find_element(By.CSS_SELECTOR, selector["selector_price"]).get_attribute('innerText')

                            if selector["selector_detail_des"]:   
                                item_description = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_des"]))
                                if (item_description):
                                    description = item_description[0].get_attribute('innerHTML') 
                            if selector["selector_detail_rating"]:   
                                item_rating = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_rating"]))   
                                if (item_rating):
                                    rating = item_rating[0].get_attribute('innerText')  

                            names = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_title"]))
                            spe_names = [name.get_attribute('innerText') for name in names]
                            values = driver.find_elements(By.CSS_SELECTOR, str(selector["selector_detail_value"]))
                            spe_values = [value.get_attribute('innerText') for value in values]

                            for index in range(len(spe_names)):
                                specifications[str(spe_names[index])] = spe_values[index]

                            save_data({
                                "title": title,
                                "link": links[i],
                                "price": price,
                                "img": imgs[i],
                                "specifications": str(specifications),
                                "description": description,
                                "rating": rating,
                                "store_id" : tool[2],
                                "category_id" : tool[3], 
                            })
                    driver.close()
                    save()
            except Exception as e:
                print(e)
        else:
            print(e)
    except Exception as e:
        print(e)
        
    finally:
        cursor.close()
        conn.close()
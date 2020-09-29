from flask import Flask, render_template, url_for, request, redirect, session,flash
import pymysql
import os
import pandas as pd
import datetime
import numpy as np
from sklearn.svm import SVR

app = Flask(__name__)

app.secret_key = os.urandom(24)

# configuaring database
db = pymysql.connect("localhost", "root", "", "webapp")


@app.route('/')
def home():
    c_dic = all_ltp()
    return render_template('home.html', c=c_dic)


@app.route('/index')
def index():
    c_dic = all_ltp()
    if(session['user'] != None):
        return render_template('index.html', user=session['user'], c=c_dic)
    else:
        return redirect('/')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        result = request.form
        cur = db.cursor()
        cur.execute("SELECT `user_password`, `user_type` FROM `users` WHERE `user_mail`='{}'".format(
            result.getlist('mail')[0]))
        cur.close()
        data = cur.fetchall()
        if(cur.rowcount > 0):
            if(data[0][0] == result.getlist('pass')[0]):
                session['user'] = data[0][1]
                return redirect('/index')
            else:
                flash('Invalid username or Password')
                
            
    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        result = request.form
        cur = db.cursor()
        cur.execute("SELECT `user_name` FROM `users` WHERE `user_mail`='{}'".format(
            result.getlist('mail')[0]))
        cur.close()
        if(cur.rowcount == 0):
            fn = result.getlist('fname')[0]
            un = result.getlist('uid')[0]
            um = result.getlist('mail')[0]
            up = result.getlist('pass')[0]
            ut = 'users'
            cur = db.cursor()
            cur.execute("INSERT INTO `users`(`full_name`, `user_name`, `user_mail`, `user_password`,`user_type`) VALUES ('{}','{}','{}','{}','{}')".format(
                fn, un, um, up, ut))
            db.commit()
            cur.close()
            return redirect('/login')
        else:
            return redirect('/signup')

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session['user'] = None
    return redirect('/')


@app.route('/users')
def users():
    if(session['user'] == 'admins'):
        cur = db.cursor()
        cur.execute(
            "SELECT `full_name`, `user_name`, `user_mail`, `user_password`, `user_type` FROM `users` WHERE 1")
        cur.close()
        data = cur.fetchall()
        return render_template('userlist.html', data=data, user=session['user'])


@app.route('/edituser', methods=['POST', 'GET'])
def edituser():
    if(session['user'] == 'admins'):
        if request.method == 'GET':
            result = request.values

            cm = result.get('c_mail')
            # for delete from list
            cur = db.cursor()
            cur.execute(
                "SELECT `full_name`, `user_name`, `user_mail`, `user_password`, `user_type` FROM `users` WHERE `user_mail`='{}'".format(cm))
            cur.close()
            data = cur.fetchall()

            return render_template('edituser.html', data=data)
        if request.method == 'POST':
            result = request.form
            fn = result.getlist('fname')[0]
            un = result.getlist('uid')[0]
            um = result.getlist('mail')[0]
            up = result.getlist('pass')[0]
            ut = result.getlist('utype')[0]
            # for update in table
            cur = db.cursor()
            cur.execute("UPDATE `users` SET `full_name`='{}',`user_name`='{}',`user_password`='{}',`user_type`='{}' WHERE `user_mail`='{}'".format(
                fn, un, up, ut, um))
            db.commit()
            cur.close()
            return redirect('/users')


@app.route('/deleteuser')
@app.route('/companies')
def companies():
    if(session['user'] == 'admins' or session['user'] == 'users'):
        cur = db.cursor()
        cur.execute("SELECT `c_name`, `c_code` FROM `companies` WHERE 1")
        cur.close()
        data = cur.fetchall()
        return render_template('companies.html', data=data, user=session['user'])


@app.route('/addcompany', methods=['POST', 'GET'])
def addcompany():
    if(session['user'] == 'admins'):
        if request.method == 'POST':
            result = request.form

            cur = db.cursor()
            cur.execute("SELECT `c_code` FROM `companies` WHERE `c_name`='{}'".format(
                result.getlist('c_name')[0]))
            cur.close()
            if(cur.rowcount == 0):
                cn = result.getlist('c_name')[0]
                cd = result.getlist('c_code')[0]
                # insert into company list
                cur = db.cursor()
                cur.execute(
                    "INSERT INTO `companies`(`c_name`, `c_code`,`date_added`) VALUES ('{}','{}','{}')".format(cn, cd, datetime.date.today()))
                db.commit()
                cur.close()

                # create new table for new entry
                cur = db.cursor()
                cur.execute(
                    "CREATE TABLE {} (id int NOT NULL AUTO_INCREMENT,Date varchar(20),LTP float,High float,Low float,Close float,PRIMARY KEY (id))".format(cd))
                db.commit()
                cur.close()

                return redirect('/index')
        return render_template('addcompany.html')


@app.route('/deletecompany', methods=['POST', 'GET'])
def del_company():
    if request.method == 'POST':
        result = request.form
        cd = result.getlist('c_code')[0]
        # for delete from list
        cur = db.cursor()
        cur.execute("DELETE FROM `companies` WHERE `c_code`='{}'".format(cd))
        db.commit()
        cur.close()
        # for delete table
        cur = db.cursor()
        cur.execute("DROP TABLE {};".format(cd))
        db.commit()
        cur.close()
    return redirect('/companies')


@app.route('/adddata', methods=['POST', 'GET'])
def adddata():
    if(session['user'] == 'admins'):
        if request.method == 'POST':
            f = request.files['file']
            f.save(f.filename)
            # specifiy your application paht
            #df=pd.read_csv("C:/Users/Aminul Islam/Desktop/webapp/{}".format(f.filename))
            df = pd.read_csv(
                "C:/Users/Sharif Hossain/Desktop/webapp/{}".format(f.filename))
            # df=pd.read_csv("C:/Users/ASUS/Desktop/webapp/webapp/{}".format(f.filename))

            lists = df.values.tolist()
            # for inserting value in each table
            for i in lists:
                cur = db.cursor()
                cur.execute("INSERT INTO `{}`(`Date`,`LTP`,`High`,`Low`,`Close`) VALUES ('{}','{}','{}','{}','{}')".format(
                    i[1], i[0], i[2], i[3], i[4], i[5]))
                db.commit()
                cur.close()
            os.remove(
                "C:/Users/Sharif Hossain/Desktop/Webapp/{}".format(f.filename))
            # os.remove("C:/Users/ASUS/Desktop/webapp/webapp/{}".format(f.filename))
            #os.remove("C:/Users/Aminul Islam/Desktop/Webapp/{}".format(f.filename))
            return redirect('/index')

        return render_template('adddata.html')


@app.route('/individuals', methods=['POST', 'GET'])
def individuals():
    if request.method == 'POST':
        result = request.form
        cpy = result.getlist('c_code')[0]
        individuals.company = cpy
        # get data from a company
        cur = db.cursor()
        cur.execute(
            "SELECT `Date`,`LTP`,`High`,`Low`,`Close` FROM `{}`".format(cpy))
        cur.close()
        data = cur.fetchall()
        # for ploting in a graph
        x = []
        y = []
        for i in data:
            x.append(str(i[0]))
            y.append(i[4])

        return render_template('individuals.html',user=session['user'],  data=data, x=x, y=y, cpy=cpy)


@app.route('/previndividual', methods=['POST', 'GET'])
def ind_pev():
    if request.method == 'POST':
        result = request.form
        cpy = individuals.company
        f_d = result.getlist('f_date')[0]
        t_d = result.getlist('t_date')[0]
        # get data from a company
        cur = db.cursor()
        cur.execute("SELECT `Date`,`LTP`,`High`,`Low`,`Close` FROM `{}` WHERE Date BETWEEN '{}' and '{}'".format(
            cpy, f_d, t_d))
        cur.close()
        data = cur.fetchall()
        # for ploting in a graph
        x = []
        y = []
        for i in data:
            x.append(str(i[0]))
            y.append(i[4])

        return render_template('individuals.html',user=session['user'], data=data, x=x, y=y, cpy=cpy)


# returning Function
# return all data to show in home
def all_ltp():
    cur = db.cursor()
    cur.execute("SELECT `c_code` FROM `companies` WHERE 1")
    cur.close()
    data = cur.fetchall()
    c_list = []
    c_dic = {}
    for i in data:
        c_list.append(i[0])
    c_ltp = []
    second_ltp = []
    c_name = []
    for i in c_list:
        cur = db.cursor()
        cur.execute(
            "SELECT `LTP` FROM `{}` WHERE id = (SELECT MAX(id) FROM {})".format(i, i))
        cur.close()
        data = cur.fetchone()
        if data is not None:
            c_ltp.append(data[0])
            c_name.append(i)

        cur = db.cursor()
        cur.execute(
            "SELECT `LTP` FROM `{}` WHERE id = ((SELECT MAX(id) FROM {})-1)".format(i, i))
        cur.close()
        data = cur.fetchone()
        if data is not None:
            second_ltp.append(data[0])
        c_dic = {'c': c_list, 't': c_ltp, 'st': second_ltp}
    return c_dic


# short term prediction
@app.route('/prediction', methods=['POST', 'GET'])
def prediction():

    if(session['user'] == 'admins' or session['user'] == 'users'):
        if request.method == 'GET':
            # for company list
            cur = db.cursor()
            cur.execute("SELECT `c_code`,`c_name` FROM `companies` WHERE 1")
            cur.close()
            data = cur.fetchall()
            c_list = []
            c_last_close = []
            c_predicted_price = []
            for i in data:
                c_list.append(i[0])
            for i in c_list:
                time = []
                price = []
                cur = db.cursor()
                cur.execute("SELECT `Date`,`Close` FROM `{}`".format(i))
                cur.close()
                data = cur.fetchall()
                if len(data) == 0:
                    c_list.remove(i)
                if len(data) != 0:
                    for data in data:
                        tm = data[0].replace('-', '')
                        time.append(int(tm))
                        price.append(data[1])
                    oned_time = np.array(time)
                    twod_time = oned_time.reshape(-1, 1)
                    # Function to make predictions using support vector regression models with rbf kernals
                    def predict_prices(dates, prices, x):

                        svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.01)
                        # Train the models on the dates and prices
                        svr_rbf.fit(dates, prices)

                        # return all three model predictions
                        return svr_rbf.predict(x)[0]
                    # Predict the price
                    nt = int(str(datetime.date.today()).replace('-', ''))
                    dtt = np.array(nt)
                    dt = dtt.reshape(-1, 1)

                    predicted_price = predict_prices(twod_time, price, dt)
                    c_predicted_price.append(predicted_price)
                    c_last_close.append(price[-1])

            return render_template('prediction.html', user=session['user'], data={'company': c_list, 'p_price': c_predicted_price, 'c_l': c_last_close})

        else:
            c_list = []
            c_all_company_all_date = []
            c_all_price = []
            c_last_close = []
            c_predicted_price = []
            result = request.form
            selected_c = result.getlist('company_list')
            for i in selected_c:
                c_list.append(i)
            for i in c_list:
                time = []
                price = []
                c_all_date = []
                cur = db.cursor()
                cur.execute("SELECT `Date`,`Close` FROM `{}`".format(i))
                cur.close()
                data = cur.fetchall()
                if data is not None:
                    for data in data:
                        c_all_date.append(data[0])
                        tm = data[0].replace('-', '')
                        time.append(int(tm))
                        price.append(data[1])

                    c_all_date.append(str(datetime.date.today()))

                    oned_time = np.array(time)
                    twod_time = oned_time.reshape(-1, 1)
                    # Function to make predictions using support vector regression models with rbf kernals
                    def predict_prices(dates, prices, x):

                        svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.01)
                        # Train the models on the dates and prices
                        svr_rbf.fit(dates, prices)

                        # return all three model predictions
                        return svr_rbf.predict(x)[0]
                    # Predict the price
                    nt = int(str(datetime.date.today()).replace('-', ''))
                    dtt = np.array(nt)
                    dt = dtt.reshape(-1, 1)

                    predicted_price = predict_prices(twod_time, price, dt)
                    c_predicted_price.append(predicted_price)
                    c_last_close.append(price[-1])

                    price.append(predicted_price)

                    c_all_price.append(price)
                    c_all_company_all_date.append(c_all_date)

            return render_template('comparission.html', user=session['user'], x=c_all_company_all_date, y=c_all_price, z=c_list, data={'company': c_list, 'p_price': c_predicted_price, 'c_l': c_last_close})


@app.route('/reports')
def reports():
    cur = db.cursor()
    cur.execute("SELECT `c_name`,`c_code`,`date_added` FROM `companies` WHERE `date_added` LIKE '%{}%' ".format(datetime.datetime.now().year))
    cur.close()
    data=cur.fetchall()
    new_company=[]
    for i in data:
        new_c={
            'cn':i[0],
            'cc':i[1],
            'date':i[2]
        }
        new_company.append(new_c)


    cur = db.cursor()
    cur.execute("SELECT `c_code`,`c_name`FROM `companies` WHERE 1")
    cur.close()
    data = cur.fetchall()
    c_list = []
    for i in data:
        c_list.append(i[0])
    
    companydata=[]
    for i in c_list:
        time = []
        price = []
        cur = db.cursor()
        cur.execute("SELECT `Date`,`Close` FROM `{}` WHERE `id` BETWEEN (SELECT MAX(id) FROM `{}`)-6 and (SELECT MAX(id) FROM `{}`) ".format(i,i,i))
        cur.close()
        data = cur.fetchall()
        if len(data) == 0:
            c_list.remove(i)
        if len(data) != 0:
            for data in data:
                tm = data[0]
                time.append(tm)
                price.append(data[1])
        data={
            'cname':i,
            'dates':time,
            'price':price,
            'avg': (sum(price) / len(price)) if(len(price)!=0) else 0
        }
        companydata.append(data)
    
    return render_template('report.html', user=session['user'], new_company=new_company,data=companydata)

import os
#import sys
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from app import app
import psycopg2
from psycopg2 import sql
from datetime import datetime

def Open(DATABASE_URL=None):
    print("-------Opening DB-------")
    if not DATABASE_URL:
        DATABASE_URL=app.config['SQLALCHEMY_DATABASE_URI']
    print("[DATABASE_URL]: ", DATABASE_URL)
    global conn
    if 'localhost' in DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    global cur
    cur = conn.cursor()
    print("-------DB opened-------")
    return

def Close():
    print ("-------Closing DB-------")
    cur.close()
    conn.close()
    print ("-------DB Closed--------")
    return

def db_connection_checker():
    try:
        if cur.closed:
            Open()
        else:
            pass
    except Exception as e:
        print(str(e))
        Open()
    return

def execute_query(query, var=None, db_url=None):
    if db_url:
        Open(DATABASE_URL=db_url)
    db_connection_checker()
    print ("-------Executing query-------")
    #print (query.as_string(cur), type(query), var, type(var))
    if (isinstance(query, str) or isinstance(query, sql.Composed) or isinstance(query, sql.SQL)) and ((not var) or isinstance(var, dict) or isinstance(var, tuple)):
        if isinstance(query, sql.Composed):
            print ("[Executed_query]: %s" %(query.as_string(cur)), var)
        else:
            print ("[Executed_query]: %s" %query, var)
        try:
            cur.execute(query, var)
            conn.commit()
        except Exception as e:
            print("[DB Error]: "+str(e))
            Open()
        return
    else:
        print (query)
        print (var)
        print ("Either Not a valid string query: ", type(query))
        print ("Or Not a valid variable format: ", type(var))
        return

def delete_data(table=None, query=None, var=None, db_url=None):
    if (query and var) and not table:
        execute_query(query=query, var=var, db_url=db_url)
    elif table and not (query or var):
        query = sql.SQL("DELETE FROM {tbl};").format(tbl=sql.Identifier(table))
        execute_query(query=query, db_url=db_url)
    else:
        pass
    return

def type_checker(col_type, val_type):
    if col_type.startswith('timestamp') and isinstance(val_type, datetime):
        return True
    if col_type == 'boolean' and isinstance(val_type, bool):
        return True
    if col_type in ['bigint', 'integer'] and isinstance(val_type, int):
        return True
    if col_type in ['character varying', 'text'] and isinstance(val_type, str):
        return True
    if col_type == 'USER-DEFINED' and isinstance(val_type, str):
        return True
    if col_type == 'ARRAY' and isinstance(val_type, (str)):
        return True
    return False

def select_columns(table, unique_key=None, unique_val=None, columns=None, array_key=None, db_url=None):
    if isinstance(table, str):
        if not check_table(table):
            print ("DB doesn't have a table with the given name '%s'" %(table))
            return
        tbl_str = sql.Identifier(table)
    else:
        print ("Invalid format (%s). Only 'str' type is allowed" %type(table))
        return
    if columns and isinstance(columns, list):
        if len(columns) != len(set(columns)):
            print ("There are duplicates in your given list. Provide only the unique values")
            return
        col_dict = get_columns(table=table)
        for col in columns:
            if (col != "*") and (col not in col_dict):
                print ("Given column %s is not present in the given '%s'" %(col,table))
                return
        if len(columns) == 1:
            if columns[0] != "*":
                cols = sql.Identifier(columns[0])
        else:
            cols = sql.SQL(', ').join(map(sql.Identifier, columns))
    else:
        print ("Either empty list of columns or invalid format (%s). Only 'list' type is allowed." %type(columns))
        return
    if unique_key or array_key:
        key = unique_key
        if key and array_key:
            print ("Provide either unique_key or array_key. Not both")
            return
        if array_key:
            key = array_key
            if col_dict[key] != 'ARRAY':
                print ("Only provide %s's columns which are of array type. Given: %s" %(table,col_dict[key]))
                return
        if key not in col_dict:
            print ("Given column '%s' is not present in the given '%s'" %(key,table))
            return
        if unique_val:
            print (col_dict[key], type(unique_val))
            if not type_checker(col_dict[key], unique_val):
                print ("unique_val should be a python type applicable for postgres' %s type. Given: %s" %(col_dict[key],type(unique_val)))
                return
            else:
                if unique_key:
                    if columns[0] == "*":
                        execute_query(sql.SQL("select * from {tbl} where {ukey} = %s;").format(tbl=tbl_str, 
                            ukey=sql.Identifier(unique_key)), (unique_val,), db_url)
                    else:
                        execute_query(sql.SQL("select {col} from {tbl} where {ukey} = %s;").format(col=cols, tbl=tbl_str, 
                            ukey=sql.Identifier(unique_key)), (unique_val,), db_url)
                else:
                    if columns[0] == "*":
                        execute_query(sql.SQL("select * from {tbl} where %s = any ({ukey});").format(tbl=tbl_str, 
                            ukey=sql.Identifier(array_key)), (unique_val,), db_url)
                    else:
                        execute_query(sql.SQL("select {col} from {tbl} where %s = any ({ukey});").format(col=cols, tbl=tbl_str, 
                            ukey=sql.Identifier(array_key)), (unique_val,), db_url)
        else:
            print ("unique_val for the given key '%s' is missing and should be %s type" %(key,col_dict[key]))
            return
    else:
        if unique_val:
            print ("key for the given unique_val '%s' is missing" %unique_val)
            return
        else:
            if columns[0] == "*":
                execute_query(sql.SQL("select * from {tbl};").format(tbl=tbl_str), db_url=db_url)
            else:
                execute_query(sql.SQL("select {col} from {tbl};").format(col=cols, tbl=tbl_str), db_url=db_url)
    return

def fetch_column(table=None, unique_key=None, unique_val=None, columns=list(["*"]), array_key=None, fetch='one', query=None, var=None, db_url=None):
    if query:
        execute_query(query=query, var=var, db_url=db_url)
    else:
        select_columns(table=table, unique_key=unique_key, unique_val=unique_val, columns=columns, array_key=array_key, db_url=db_url)
    if fetch == 'one':
        return cur.fetchone()
    if fetch == 'all':
        return cur.fetchall()
    if isinstance(fetch, int):
        return cur.fetchmany(fetch)

def check_table(table):
    query = "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = %s AND c.relkind = 'r');"
    exists = fetch_column(query=query, var=(table,))
    return exists[0]

def get_columns(table):
    query = "select column_name, data_type from information_schema.columns where table_name = %s;"
    col_names = fetch_column(query=query, var=(table,), fetch='all')
    col_dict = {}
    for value in col_names:
        col_dict[value[0]] = value[1]
    return col_dict

def insert_values(table, columns=[], values=(), db_url=None):
    '''if isinstance(table, str):
        if not check_table(table):
            print ("DB doesn't have a table with the given name '%s'" %(table))
            return'''
    if len(values) >= 1:
        if columns:
            if len(columns) == len(values):
                try:
                    execute_query(sql.SQL("INSERT INTO {tbl} ({cols}) VALUES ({vals});").format(
                        tbl=sql.Identifier(table), cols=sql.SQL(', ').join(map(sql.Identifier, columns)), 
                        vals=sql.SQL(', ').join(sql.Placeholder()*len(columns))), var=values, db_url=db_url)
                except Exception as e:
                    print (str(e))
                    print ("One or more values do not follow their respective col type of %s" %table)
            else:
                print ("Insufficient values (%d) for the given columns (%d)" %(len(values), len(columns)))
        else:
            try:
                execute_query(sql.SQL("INSERT INTO {tbl} VALUES ({vals});").format(tbl=sql.Identifier(table), 
                    vals=sql.SQL(', ').join(sql.Placeholder()*len(columns))), values, db_url)
                conn.commit()
                print ("Inserted!")
            except:
                print ("Check if %s exists and given values follow the table's current schema along with the columns sequence" %table)
    else:
        print ("%d values provided: 'values' attribute should be provided atleast one value in the tuple format (,)" %len(values))
    return

def update_columns(table, unique_key, unique_val, list_of_pairs, db_url=None):
    if isinstance(table, str):
        if not check_table(table):
            print ("DB doesn't have a table with the given name '%s'" %(table))
            return
    print ("------Updating Columns------")
    prev_vals = fetch_column(table=table, unique_key=unique_key, unique_val=unique_val, db_url=db_url)
    print ("Before update: ", prev_vals)

    update_pairs = [list_of_pairs[x:x+2] for x in range(0, len(list_of_pairs), 2)]
    for pair in update_pairs:
        column = pair[0]
        new_value = pair[1]
        if new_value or new_value == False:
            execute_query(sql.SQL("UPDATE {tbl} SET {col} = %s WHERE {ukey} = %s;").format(tbl=sql.Identifier(table), 
                col=sql.Identifier(column), ukey=sql.Identifier(unique_key)), (new_value, unique_val), db_url)
        else:
            execute_query(sql.SQL("UPDATE {tbl} SET {col} = null WHERE {ukey} = %s;").format(tbl=sql.Identifier(table), 
                col=sql.Identifier(column), ukey=sql.Identifier(unique_key)), (unique_val,), db_url)
        conn.commit()

    new_vals = fetch_column(table=table, unique_key=unique_key, unique_val=unique_val, db_url=db_url)
    print ("After update: ", new_vals)
    print ("------Columns Updated------")
    return

def user_creator(user_details):
    execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print (cur.fetchall())
    print ("---------------------Creating User-----------------------")
    existing_user = fetch_column(table="users", unique_key="user_id", unique_val=user_details["id"], 
        columns=list(["user_id"]))
    #print existing_user
    if existing_user != None:
        print ("-------------User Already Added-------------")
        details = fetch_column(table="users", unique_key="user_id", unique_val=user_details["id"])
        print ("User Details: ", details)
        return

    if 'email' in user_details:
        print ("Sucker! Left the e-mail address ;)!")
        insert_values("users", ["user_id", "first_name", "last_name", "email", "clicked_at"], 
            (user_details["id"],user_details["first_name"],user_details["last_name"],user_details["email"],datetime.utcnow()))
    else:
        print ("This guy wants privacy!! No Email!")
        insert_values("users", ["user_id", "first_name", "last_name", "clicked_at"], 
            (user_details["id"],user_details["first_name"],user_details["last_name"],datetime.utcnow()))

    print ("added ", user_details["id"], " to users")

    added_data = fetch_column(table="users", unique_key="user_id", unique_val=user_details["id"])
    print ("Added data: ", added_data)
    print ("-------User Created-------")
    return

def bot_prev_message(user_id, size=None):
    query = sql.SQL('SELECT {col} FROM user_events WHERE {ukey1} = %s AND {ukey2} = %s ORDER BY {okey} DESC;').format(
        col=sql.Identifier('stimuli'), ukey1=sql.Identifier('user_id'), ukey2=sql.Identifier('direction'), 
        okey=sql.Identifier('time'))
    '''query = sql.SQL("select max ({t}) from user_events where user_id = %s and direction = %s").format(t=sql.Identifier('time'))
    value = fetch_column(table='user_events', unique_key='time', unique_val=fetch_column(query=query, 
        var=(user_id, 'sent'))[0], columns=list(['stimuli']))'''
    if size:
        values = fetch_column(query=query, var=(user_id, 'sent'), fetch=size)
    else:
        values = fetch_column(query=query, var=(user_id, 'sent'))
    return values

def user_last_message(user_id):
    query = sql.SQL('SELECT {cols} FROM user_events WHERE {ukey1} = %s ORDER BY {okey} DESC;').format(
        cols=sql.Identifier('time'), ukey1=sql.Identifier('user_id'), okey=sql.Identifier('time'))
    last_message = fetch_column(query=query, var=(user_id, 'received'))
    return last_message

def get_current_order(user_id):
    current_order = fetch_column('users', columns=list(['current_order']), unique_key='user_id', 
        unique_val=user_id)[0]
    return current_order

def get_current_booking(user_id):
    current_booking = fetch_column('users', columns=list(['current_booking']), unique_key='user_id', 
            unique_val=user_id)[0]
    return current_booking
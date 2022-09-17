#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# created : 09-Apr-2019
# author  : daBve, dabve@gmail.fr
#
# description   : sqlite operations to help work with sqlite databases
# requirement   : sys, csv, collections(namedtuple, OrderedDict), sqlite3, terminaltables, xlsxwriter
# version       : from 1.0.0 to 1.1.0
# ---------------------------------------------------------------------------------------------


import pathlib, sys
from collections import namedtuple, OrderedDict
import sqlite3
from sqlite3 import Error
from sqlite3 import IntegrityError

from prompt_toolkit import print_formatted_text, HTML
from datetime import datetime
tday = datetime.today()


class MissingDbName(BaseException):
    def __str__(self):
        return 'You need to specify a database name'


class Display:
    def __init__(self, desc, rows):
        """
        Display result as: (table | vertical | return a namedtuple object | return a dict object | return an OrderedDict
        """
        self.desc = desc
        self.rows = rows

    @property
    def as_dict(self):
        # return a list of dict objects
        rowdicts = [dict(zip(self.desc, row)) for row in self.rows]
        return rowdicts

    @property
    def as_orderedDict(self):
        # return a list of OrderedDict
        rowdicts = [OrderedDict(zip(self.desc, row)) for row in self.rows]
        return rowdicts

    @property
    def as_namedtuple(self):
        for ind, value in enumerate(self.desc):
            # namedtuple take this form: Parts = namedtuple('Parts', 'id_num desc cost amount')
            # find white space on fields_name and change it to '_' chars
            index = value.find(' ')     # index of white space inside value; find return the index
            if index > 0:
                self.desc[ind] = value.replace(' ', '_')
        Row = namedtuple('Row', self.desc)               # getting the key from description
        rows = [Row(*r) for r in self.rows]              # getting values
        return rows


class SqliteFunc:
    def __init__(self, db_name):
        if pathlib.Path(db_name).is_file() and pathlib.Path(db_name).exists():
            self.db_name = db_name
        else:
            self.error_msg('DB with name {} does not exits.'.format(db_name))
            create = input('do you want to create it [y/N]: ')
            if create.lower() in ('y', 'yes'):
                self.db_name = db_name
            else:
                sys.exit()

    def error_msg(self, msg):
        print_formatted_text(HTML('<b>[<style fg="#dc3545">error</style>] <style fg="#dc3545">{}</style></b>'.format(msg)))

    def success_msg(self, msg):
        print_formatted_text(HTML('<b>[<style fg="#17a2b8">success</style>] {}</b>'.format(msg)))

    def login(self):
        """
        login to database; if database does not exist; than create it
        """
        try:
            conn = sqlite3.connect(self.db_name)
        except Error as err:
            print_formatted_text(HTML('<b><style fg="#dc3545">[Err] {}</style></b>'.format(err)))
        else:
            conn.execute('PRAGMA foreign_keys = 1')
            curs = conn.cursor()
            return conn, curs

    @property
    def show_tables(self):
        """
        Show All Tables in database
        return a display instance
        """
        query = 'SELECT name FROM sqlite_master WHERE type = "table"'
        desc, rows = self.make_query(query)
        return self.display(desc, rows)

    def make_query(self, query, params=(), display=False):
        """
        usage : make_query('select * from table_name where id = ?', [1])
        return: tuple (desc, rows) | rowcount for update and delete operations
        """
        conn, curs = self.login()
        try:
            curs.execute(query, params)
        except Error as err:
            self.error_msg(err)
        else:
            stmt = query.split()[0].upper()
            if stmt == 'SELECT':
                desc = [desc[0] for desc in curs.description]
                rows = curs.fetchall()
                if display:
                    # return display instance ex.
                    # >>> make_query(query, params, display=True).display(desc, rows).as_named_tuple
                    return self.display(desc, rows)
                else:
                    return (desc, rows)
            else:
                conn.commit()
                return True
        finally:
            if conn: conn.close()

    def create_tables(self, table_name, fields):
        """
        usage : create_tables('table_name', ['id INTEGER', 'add_date DATETIME'])
        return: result from sqlite3
        """
        query = 'CREATE TABLE {}(\n{}\n)'.format(table_name, ',\n'.join(fields))
        return self.make_query(query)

    def add_clients(self, name, phone):
        # insert new client in database

        conn, curs = self.login()
        query = 'INSERT INTO Clients(name, phone, credit) VALUES(?, ?, ?)'
        params = [name, phone, 0]
        try:
            curs.execute(query, params)
        except IntegrityError as err:
            self.error_msg(err)
            return 'sqlite integrity error'
        else:
            conn.commit()
        finally:
            if conn: conn.close()

    def add_credit(self, client_id, credit, credit_date):
        conn, curs = self.login()
        query = 'SELECT credit FROM Clients WHERE id = ?'
        params = [client_id]
        desc, rows = self.make_query(query, params)
        old_credit = rows[0][0]

        update_clients_query = 'UPDATE Clients SET credit = ? WHERE id = ?'
        new_credit = old_credit + credit

        reste = credit - 0
        insert_credits_query = 'INSERT INTO Credits(client_id, credit_date, credit, reste) VALUES(?, ?, ?, ?)'
        try:
            curs.execute(update_clients_query, [new_credit, client_id])
            curs.execute(insert_credits_query, [client_id, credit_date, credit, reste])
        except Error as err:
            self.error_msg(err)
        else:
            conn.commit()
            conn.close()

    def add_payment(self, client_id, fact_id, payment):
        conn, curs = self.login()
        fetch_query = 'SELECT credit, versement FROM Credits WHERE id = ?'
        rows = self.make_query(fetch_query, [fact_id], display=True).as_namedtuple
        db_client = rows[0]

        new_payment = payment + db_client.versement
        reste = db_client.credit - new_payment

        update_pay_query = 'UPDATE Credits SET versement = ?, reste = ? WHERE id = ?'
        update_client_credit = 'UPDATE Clients SET credit = credit - ? WHERE id = ?'
        insert_new_pay = 'INSERT INTO Payments_log(fact_id, payment_date, payment) VALUES(?, ?, ?)'
        try:
            curs.execute(update_pay_query, [new_payment, reste, fact_id])
            curs.execute(update_client_credit, [payment, client_id])
            curs.execute(insert_new_pay, [fact_id, tday, payment])
        except Error as err:
            self.error_msg(err)
        else:
            conn.commit()
            conn.close()
            self.check_if_paid(fact_id)

    def check_if_paid(self, fact_id):
        conn, curs = self.login()
        query = 'SELECT reste FROM Credits WHERE id = ?'
        params = [fact_id]
        desc, rows = self.make_query(query, params)
        reste = rows[0][0]
        if reste == 0:
            query = 'UPDATE Credits SET paid = ? WHERE id = ?'
            params = ["paid", fact_id]
            try:
                curs.execute(query, params)
            except Error as err:
                self.error_msg(err)
            else:
                conn.commit()
                conn.close()

    def get_payment_log(self, fact_id):
        query = 'SELECT DATE(payment_date), payment FROM Payments_log WHERE fact_id = ?'
        params = [fact_id]
        desc, rows = self.make_query(query, params)
        return rows

    def search(self, search_word, table_name, fields, search_fields):
        for field in search_fields:
            if field == 'paid':
                search_word = search_word.replace('%', '').title()
                query = 'SELECT {} FROM {} WHERE {} = ?'.format(', '.join(fields), table_name, field)
            else:
                search_word = '%' + search_word + '%'
                query = 'SELECT {} FROM {} WHERE {} LIKE ?'.format(', '.join(fields), table_name, field)

            desc, rows = self.make_query(query, [search_word])
            if len(rows) > 0:
                break
        return rows

    def get_client_reste(self, fact_id):
        query = 'SELECT reste FROM Credits WHERE id = ?'
        params = [fact_id]
        desc, rows = self.make_query(query, params)
        return rows[0][0]

    def client_badge(self, client_id):
        # this will return client details as a namedtuple.
        query = 'SELECT name, phone, credit FROM Clients WHERE id = ?'
        rows = self.make_query(query, [client_id], display=True).as_namedtuple
        return rows[0]

    def get_clients(self):
        query = 'SELECT id, name FROM Clients ORDER BY id'
        desc, clients = self.make_query(query)
        return clients

    def delete_client(self, client_id):
        query = 'DELETE FROM clients WHERE id = ?'
        result = self.make_query(query, [client_id])
        return result

    def product_exists(self, table, column, value):
        """
        usage : product_exists('magasin', 'reference', 'product_reference')
        return True or False
        """
        conn, curs = self.login()
        try:
            curs.execute('SELECT id FROM ' + table + ' WHERE ' + column + ' = ?', [value])
        except Error as err:
            self.error_msg(err)
        else:
            if curs.fetchone(): return True
            else: return False
        finally:
            if conn: conn.close()

    def display(self, desc, rows):
        display_inst = Display(desc, rows)
        return display_inst

    def __repr__(self):
        return '<{!r} connected to {!r} >'.format(self.__class__.__name__, self.db_name)

# ------------------ End of Class


def atache_database(curs, dbname, alias):
    """
    # When you have multiple databases available and you want to use any one of them at a time.
    # SQLite ATTACH DATABASE statement is used to select a particular database,
      and after this command, all SQLite statements will be executed under the attached database.
    """
    query = 'ATTACH DATABASE ' + dbname + ' AS ' + alias
    curs.execute(query)


if __name__ == '__main__':
    db_name = './creadit.db'
    db_handler = SqliteFunc(db_name)

    # db_handler.show_tables.terminal_display()                   # terminal_default
    # db_handler.describe_table('State').terminal_display('vertical')

    # Example of creating table:

    # fields = [
        # 'id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        # 'add_date TIMESTAMP DEFAULT(CURRENT_TIMESTAMP)',
        # 'name VARCHAR(255)',
        # 'phone VARCHAR(20) NOT NULL UNIQUE',
        # 'credit DECIMAL(15, 2) NOT NULL',
    # ]
    # fields = [
        # 'id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        # 'client_id INTEGER NOT NULL',
        # 'credit_date TIMESTAMP NOT NULL DEFAULT(CURRENT_TIMESTAMP)',
        # 'credit DECIMAL(15, 2) NOT NULL',
        # 'versement DECIMAL(15, 2) DEFAULT(0)',
        # 'reste DECIMAL(15, 2) DEFAULT(0)',
        # 'paid VARCHAR(25) DEFAULT "not paid"',
        # 'FOREIGN KEY("client_id") REFERENCES "clients"("id") ON DELETE CASCADE',
    # ]
    fields = [
        'id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'fact_id INTEGER NOT NULL',
        'payment_date TIMESTAMP NOT NULL DEFAULT(CURRENT_TIMESTAMP)',
        'payment DECIMAL(15, 2) DEFAULT(0)',
        'FOREIGN KEY("fact_id") REFERENCES "Credits"("id") ON DELETE CASCADE',
    ]
    query = 'DROP TABLE Payments_log'
    params = []
    result = db_handler.make_query(query, params)
    print(result)
    table_name = 'Payments_log'
    result = db_handler.create_tables(table_name, fields)
    print(result)

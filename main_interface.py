#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# author        : el3arbi bdabve@gmail.com
# created       : 14-August-2022
# description   : credit app
#
# from stacked_widgetAnimation import QCustomStackedWidget
# self.stackedWidgetMain = QCustomStackedWidget(self.widget_2)
# ----------------------------------------------------------------------------

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5 import QtCore
import qtawesome as qta
from headers.h_interface import Ui_MainWindow
import app_utils
import sqlite_utils
db_name = './creadit.db'
db_handler = sqlite_utils.SqliteFunc(db_name)


class CreditApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.table = self.ui.tableWidget
        self.table_details = self.ui.tableWidgetDetails
        self.client_id = ''

        # set main table column size
        columns_size = [(0, 60), (1, 300), (2, 300)]
        app_utils.table_column_size(self.table, columns_size)

        # set details table column size
        columns_size = [(0, 50), (1, 120), (2, 120), (3, 120), (4, 120), (5, 60)]
        app_utils.table_column_size(self.table_details, columns_size)

        self.ui.stackedWidgetMain.setCurrentWidget(self.ui.main_page)       # the main stacked widget

        # =========| Setup Icons |====================================================
        app_utils.icons(self)

        # =========| Callback Functions |=============================================
        self.ui.lineEditCalculator.returnPressed.connect(self.calculate)
        self.ui.pushButtonMenu.clicked.connect(self.display_menu)

        self.table.itemDoubleClicked.connect(self.display_client_details)
        self.table.itemSelectionChanged.connect(self.enable_credits)
        self.table_details.itemSelectionChanged.connect(self.enable_payment_form)

        self.ui.lineEditSearch.returnPressed.connect(self.search)

        self.ui.pushButtonAddClient.clicked.connect(self.create_client)
        self.ui.pushButtonAddCredit.clicked.connect(self.add_credit)
        self.ui.pushButtonDetails.clicked.connect(self.display_client_details)
        self.ui.pushButtonMainPage.clicked.connect(self.switch_to_main)
        self.ui.pushButtonAddPayment.clicked.connect(self.add_payment)
        self.ui.pushButtonDelClient.clicked.connect(self.del_client)

        # =========| Initial Display |================================================
        self.display_all_records()
        self.total_credit()

    def calculate(self):
        try:
            to_calculate = eval(self.ui.lineEditCalculator.text())
        except NameError:
            to_calculate = 'number + number'
        self.ui.lineEditCalculator.setText(str(to_calculate))

    def search(self):
        by = self.ui.stackedWidgetMain.currentIndex()
        search_word = self.ui.lineEditSearch.text()
        if by == 0:
            table_name = 'Clients'
            table_widget = self.table
            fields = ['id', 'name', 'phone', 'credit']
            search_fields = ['name', 'phone', 'credit']
            headers = ['ID', 'Name', 'Phone', 'Credit']
            right_column = [3]
        elif by == 1:
            table_name = 'Credits'
            table_widget = self.table_details
            fields = ['id', 'credit_date', 'credit', 'versement', 'reste', 'paid']
            search_fields = ['credit_date', 'versement', 'paid']
            headers = ['ID', 'Date', 'Credit', 'Versement', 'Reste', 'Paid']
            right_column = [2, 3, 4, 5]

        rows = db_handler.search(search_word, table_name, fields, search_fields)
        app_utils.display_table_records(table_widget, rows, headers, right_column)

    def display_menu(self):
        left_menu = self.ui.leftMenuContainer
        width = left_menu.width()
        if width == 0:
            new_width = 270
            menu_icon = qta.icon('mdi.dots-horizontal', color='white')
        else:
            new_width = 0
            menu_icon = qta.icon('mdi.dots-vertical', color='white')

        self.ui.pushButtonMenu.setIcon(menu_icon)

        self.animation = QtCore.QPropertyAnimation(left_menu, b'minimumWidth')          # wont work without self
        self.animation.setDuration(250)
        self.animation.setStartValue(width)
        self.animation.setEndValue(new_width)
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()

    def switch_to_main(self):
        # this function to update tables and cards
        self.ui.stackedWidgetMain.setCurrentWidget(self.ui.main_page)
        self.display_all_records()

    def display_all_records(self):
        # this function dump all records; send result to display_records method
        # fields = ['id', 'name', 'phone', 'credit']
        query = 'SELECT id, name, phone, credit FROM Clients'
        params = []
        desc, rows = db_handler.make_query(query, params)
        headers = ['ID', 'Name', 'Phone', 'Credit']
        right_column = []
        app_utils.display_table_records(self.table, rows, headers, right_column)
        self.total_credit()         # count total credits and clients

    def total_credit(self):
        query = 'SELECT COUNT(id), SUM(credit) FROM Clients'
        desc, rows = db_handler.make_query(query)
        clients, credits = rows[0]
        self.ui.labelTotalClients.setText(str(clients))
        self.ui.labelTotalCredits.setText(str(credits) + ' DA')

    def create_client(self):
        name = self.ui.lineEditName.text()
        phone = self.ui.lineEditPhone.text()
        valid = app_utils.validate_phonenumber(phone)
        if not valid:
            error_msg = 'Invalid phone number.\nMust start with 05 | 06 | 07 and 10 digits long\nExample: 0556000000'
            app_utils.error_msgbox(self, error_msg)
        else:
            result = db_handler.add_clients(name, phone)
            if result == 'sqlite integrity error':
                # if result == 'UNIQUE constraint failed: Clients.phone':
                error_msg = 'This phone already exist.'
                app_utils.error_msgbox(self, error_msg)
            self.display_all_records()

    def get_badge(self, reset=False):
        if reset:
            self.ui.labelClientName.setText('')
            self.ui.labelClientPhone.setText('')
            self.ui.labelClientTotalCredit.setText('')
        else:
            badge = db_handler.client_badge(self.client_id)
            self.ui.labelClientName.setText(badge.name)
            self.ui.labelClientPhone.setText(badge.phone)
            self.ui.labelClientTotalCredit.setText(str(badge.credit))

    def enable_credits(self):
        self.client_id = app_utils.get_item_id(self.table)

        if len(self.table.selectionModel().selectedRows()) > 0:
            self.get_badge()
            self.ui.pushButtonDetails.setEnabled(True)
            self.ui.pushButtonDetails.setStyleSheet('color: #ffffff;')

            self.ui.labelAddCreditTitle.setStyleSheet('color: #ffffff;')
            self.ui.dateEditCredit.setEnabled(True)
            self.ui.doubleSpinBoxCredit.setEnabled(True)

            self.ui.pushButtonAddCredit.setEnabled(True)
            self.ui.pushButtonAddCredit.setStyleSheet('color: #ffffff')
        else:
            self.get_badge(reset=True)
            self.ui.pushButtonDetails.setEnabled(False)
            self.ui.pushButtonDetails.setStyleSheet('color: #88898a;')

            self.ui.labelAddCreditTitle.setStyleSheet('color: #88898a;')
            self.ui.dateEditCredit.setEnabled(False)
            self.ui.doubleSpinBoxCredit.setEnabled(False)

            self.ui.pushButtonAddCredit.setEnabled(False)
            self.ui.pushButtonAddCredit.setStyleSheet('color: #88898a')

    def display_client_details(self):
        if len(self.table.selectionModel().selectedRows()) > 0:
            self.ui.stackedWidgetMain.setCurrentWidget(self.ui.details_page)
            self.dump_client_records()

    def del_client(self):
        msg_title = 'Delete Client'
        msg = 'Are you sure to delete Client.'
        msg_box = app_utils.question_msgbox(self, msg_title, msg)
        if msg_box == QMessageBox.Yes:
            result = db_handler.delete_client(self.client_id)
            if result:
                self.get_badge(reset=True)
                self.display_all_records()
                self.ui.stackedWidgetMain.setCurrentWidget(self.ui.main_page)

    def dump_client_records(self):
        query = 'SELECT id, DATE(credit_date), credit, versement, reste, paid FROM Credits WHERE client_id = ? ORDER BY id'
        params = [self.client_id]
        desc, rows = db_handler.make_query(query, params)
        headers = ['ID', 'Date', 'Credit', 'Payment', 'Reste', 'Paid']
        right_column = [2, 3, 4, 5]
        app_utils.display_table_records(self.table_details, rows, headers, right_column)

    def add_credit(self):
        # client_id = app_utils.get_item_id(self.table)
        credit_date = self.ui.dateEditCredit.date().toPyDate()
        credit = self.ui.doubleSpinBoxCredit.value()
        if credit == 0:
            error_msg = 'You must add a credit.'
            app_utils.error_msgbox(self, error_msg)
        else:
            db_handler.add_credit(self.client_id, credit, credit_date)
            self.ui.doubleSpinBoxCredit.setValue(0)
            self.display_client_details()
            self.total_credit()
            self.get_badge()

    def enable_payment_form(self):
        fact_id = app_utils.get_item_id(self.table_details)
        # display data in payment table
        rows = db_handler.get_payment_log(fact_id)
        app_utils.display_table_records(self.ui.tableWidgetPayement, rows, ['Date', 'Payment'], [])

        query = 'SELECT reste FROM Credits WHERE id = ?'
        desc, rows = db_handler.make_query(query, [fact_id])
        try:
            reste = rows[0][0]
        except Exception:
            pass
        else:
            if len(self.table_details.selectionModel().selectedRows()) > 0 and reste != 0:
                self.ui.doubleSpinBoxPayment.setEnabled(True)
                self.ui.pushButtonAddPayment.setEnabled(True)
                self.ui.pushButtonAddPayment.setStyleSheet('color: #ffffff;')
                self.ui.labelPaymentTitle.setStyleSheet('color: #ffffff')
            else:
                self.ui.doubleSpinBoxPayment.setEnabled(False)
                self.ui.pushButtonAddPayment.setEnabled(False)
                self.ui.pushButtonAddPayment.setStyleSheet('color: #88898a;')
                self.ui.labelPaymentTitle.setStyleSheet('color: #88898a')

    def add_payment(self):
        payment = self.ui.doubleSpinBoxPayment.value()
        fact_id = app_utils.get_item_id(self.table_details)

        # fetch if Payment !> facture reste
        reste = db_handler.get_client_reste(fact_id)
        if payment > reste:
            error_msg = 'Your payment is greater than reste'
            app_utils.error_msgbox(self, error_msg)
        else:
            db_handler.add_payment(self.client_id, fact_id, payment)
            self.dump_client_records()
            self.total_credit()
            self.get_badge()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = CreditApp()
    window.show()
    sys.exit(app.exec_())

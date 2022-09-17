#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt5 import QtCore
import qtawesome as qta
from datetime import date

tday = date.today()


# =========| PushButton Icons |===============================================
def icons(root):
    icons_str = [('mdi.dots-vertical', 'white', root.ui.pushButtonMenu),
                 ('mdi.account-plus-outline', 'white', root.ui.pushButtonAddClient),
                 ('mdi.currency-usd', 'white', root.ui.pushButtonAddCredit),
                 ('mdi.arrow-left', 'white', root.ui.pushButtonMainPage),
                 ('mdi.currency-usd', 'white', root.ui.pushButtonAddPayment),
                 ('mdi.account-card-details-outline', 'white', root.ui.pushButtonDetails),
                 ('mdi.delete-circle-outline', 'red', root.ui.pushButtonDelClient),
                 ]

    for icon_str, icon_color, btn_name in icons_str:
        icon = qta.icon(icon_str, color=icon_color)
        btn_name.setIcon(icon)
        if icon_str == 'mdi.arrow-collapse-left':
            btn_name.setIconSize(QtCore.QSize(30, 30))

    # =========| Labels and icons |=====================================================
    root.ui.dateEditCredit.setDate(tday)
    root.ui.labelDate.setText(tday.strftime('%A %d %b %Y'))

    icons_str = ['mdi.account-group-outline', 'mdi.cash-usd-outline', 'mdi.account-question-outline']
    labels = [root.ui.label_8, root.ui.label_6, root.ui.clientIconLabel]
    for icon_name, label in zip(icons_str, labels):
        icon = qta.icon(icon_name, color='#ffffff')
        label.setPixmap(icon.pixmap(QtCore.QSize(50, 50)))

    # =========| stacked layout animation |=============================================
    root.ui.stackedWidgetMain.setTransitionDirection(QtCore.Qt.Horizontal)
    root.ui.stackedWidgetMain.setTransitionSpeed(500)
    root.ui.stackedWidgetMain.setTransitionEasingCurve(QtCore.QEasingCurve.Linear)
    root.ui.stackedWidgetMain.setSlideTransition(True)


def table_column_size(table, columns: list):
    # column = list[(column, size), ]
    for column in columns:
        c, size = column
        table.setColumnWidth(c, size)


def display_table_records(table, rows, headers, right_column):
    table.clear()
    table.setRowCount(len(rows))       # required set row count for the tableWidget
    table_row = 0                           # table Row
    for row in rows:
        # we are inside a tuple of records
        for column, r in enumerate(row):
            # index, item_text
            item = QTableWidgetItem(str(r))                     # required; item must be QTableWidgetItem
            table.setItem(table_row, column, item)         # add item to the table
            if column in right_column:
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)   # align credit field left
        table_row += 1

    # horizontal headers labels
    table.setHorizontalHeaderLabels(headers)


def get_item_id(table):
    row = table.currentRow()
    id_table = str(table.item(row, 0).text())   # column 0 = art_id; this will return QTableWidgetItem.text()
    return id_table


def validate_phonenumber(phone):
    import re
    phone_regex = re.compile(r'^0(5|6|7)\d{8}')
    if len(phone) > 10:
        return False
    else:
        if phone_regex.search(phone):
            return True
        else:
            return False


def error_msgbox(parent, error_msg):
    msg = '<p style=font-family: "Monaco"; font-size: 14>{}</p>'.format(error_msg)
    QMessageBox.warning(parent, 'Error on payment.', msg, QMessageBox.Close)


def question_msgbox(parent, msg_title, message):
    msg = '<p style=font-family: "Monaco"; font-size: 14>{}</p>'.format(message)
    msg_box = QMessageBox.question(parent, msg_title, msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    return msg_box

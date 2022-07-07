from email.mime.text import MIMEText
import logging as log
import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime as dt 
import smtplib, ssl
from email.mime.multipart import MIMEMultipart

logger = log.basicConfig(level=log.DEBUG, filename="/home/sujeet99/Desktop/cron_test.log", filemode="w")

smtp_server = "smtp.gmail.com"
port = 587  
sender_email = "testingsynoshiv@gmail.com"
password = 'wrldgrtgxfcknzqy'
msg = MIMEMultipart('alternative')
server = smtplib.SMTP(smtp_server, port) 
msg['From'] = sender_email


def send_simple_message(email_data:dict):
    try:

        to = email_data.get('email')
        # to.append("shivam.sharma@synoriq.in")
        msg['Subject'] = email_data.get('subject')
        msg['Bcc'] = ",".join(to)
        link = email_data.get('class_link')
        Body = MIMEText(link)
        msg.attach(Body)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, to, msg.as_string())
    except Error as e:
        log.info(f"{e}")

# send_simple_message({"email":['shivadec1254@gmail.com', 'sujeet.mazumdar@synoriq.in', 'shivnbt82@gmail.com'], 
# "subject":"Testing bulk emailing Cron ", "class_link":"https://levelup.gitconnected.com/sending-bulk-emails-via-python-4592b7ee57a5"})
        


def query_list(sql_query, check_index=0):
    return [columns[check_index] for columns in sql_query]

def live_class_reccur():
    try:
        connection = mysql.connector.connect(host='172.18.0.2',
                                                database='edxapp',
                                                user='synoriq25',
                                                password='25082017')
        if connection.is_connected():
            db_Info = connection.get_server_info()
            cursor = connection.cursor()
            column_query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS  WHERE TABLE_NAME = 'course_overviews_liveclasses';"
            cursor.execute(column_query)
            column_list =query_list(cursor.fetchall())
            cursor = connection.cursor()
            active_recurr_class_query = f"""Select * From  course_overviews_liveclasses Where is_recurrence_meeting is true 
            And end_date >= {dt.now().date()};"""
            cursor.execute(active_recurr_class_query)
            live_class_list = cursor.fetchall()
            day_index = column_list.index('days')
            id_index = column_list.index('id')
            week_day = dt.now().strftime("%A")


            for live_class in live_class_list:
                send_email_dict = {}
                if week_day in live_class[day_index]:
                    start_time_index = column_list.index('start_time')
                    enrolled_query = f"""Select user_id From  student_liveclassenrollment Where live_class_id = {live_class[id_index]};"""
                    cursor.execute(enrolled_query)
                    send_email_dict["class_link"] = f"your live class is scheduled \n\n {live_class[column_list.index('meeting_link')]}"
                    user_id_list = query_list(cursor.fetchall())
                    email_list = []
                    for user_id in user_id_list:
                        # access_use_email_query = f"Select * from auth_user where id={user_id};"
                        access_use_email_query = f"Select email from auth_user where id={user_id};"


                        cursor.execute(access_use_email_query)
                        email_list.extend(list(cursor.fetchone()))
                        # email = cursor.fetchone()
                        # email_list.append( email[0])
                    send_email_dict['email'] = email_list
                    send_email_dict['subject'] =f"Live class at {live_class[start_time_index]}" 
                send_simple_message(send_email_dict)

    except Error as e:
        log.info("Error while connecting to MySQL", e)

live_class_reccur()



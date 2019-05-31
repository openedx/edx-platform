# coding=utf-8
"""
Script for load user from csv file
"""
import csv
import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management.base import BaseCommand
from django.utils.translation import trans_real as trans
from mock import MagicMock

from student.views import create_account_with_params, reverse

log = logging.getLogger()


class Command(BaseCommand):
    """
    Management command for adding all users to the discussion service.
    """
    help = 'Load users from csv file'

    message = (
        u"""
        Вы зарегистрированы на платформе Accel, которая является библиотекой нашего курса.
        
        В ней вы найдете материалы по открытию онлайн-школы и онлайн-образованию.
         
        Запомните ваши данные для входа на платформу:
         
        → Логин: {login}
        → Пароль: {password}
        → Ссылка на платформу: {login_link}
        
        
        С уважением, команда Accel.    
        """)
    subject = u'Добро пожаловать на платформу Accel.'

    def add_arguments(self, parser):
        parser.add_argument('file_path',
                            help='path to the user list')

    def handle(self, *args, **options):
        user_path = options['file_path']

        trans.activate('ru')

        with open(user_path, 'rb') as csvfile:

            is_header = True
            user_reader = csv.reader(csvfile, delimiter=';')
            for email, password, first_name, last_name in user_reader:
                if is_header:
                    is_header = False
                    continue
                params = {
                    'email': email,
                    'username': email.replace('@', '-').replace('.', '-').replace('+', '-'),
                    'name': ' '.join([first_name, last_name]),
                    'honor_code': 'true',
                    'terms_of_service': 'true',
                    'password': password,
                    'country': 'Россия',
                    'first_name': first_name,
                    'last_name': last_name,
                }
                fake_request = MagicMock()
                fake_request.session.session_key = ''
                fake_request.site = Site.objects.get_current()
                try:
                    new_user = create_account_with_params(fake_request, params)
                    log.info('created new user :: {user}'.format(user=new_user))
                except Exception:
                    log.exception("Can not create new user with email %s", email)
                    continue

                try:
                    email_message = self.message.format(
                        login=email,
                        password=password,
                        login_link=reverse("signin_user")
                    )
                    mail.send_mail(self.subject, email_message, settings.DEFAULT_FROM_EMAIL, [email],
                                   fail_silently=False)
                    log.info("Send email to new user {user_email}".format(
                        user_email=email
                    ))
                except Exception as e:
                    log.error('Can not send email to user %s', e)
                    print (e.message)

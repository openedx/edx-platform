# -*- coding:utf-8 -*-
import re
import time


class ValidateDataForEducation(object):
    """
    正则验证类
    """

    def is_email(self, field):
        """
        验证合法邮箱
        /**
        * @descrition:邮箱规则
        * 1.邮箱以a-z、A-Z、0-9开头，最小长度为1.
        * 2.如果左侧部分包含-、_、.则这些特殊符号的前面必须包一位数字或字母。
        * 3.@符号是必填项
        * 4.右则部分可分为两部分，第一部分为邮件提供商域名地址，第二部分为域名后缀，现已知的最短为2位。最长的为6为。
        * 5.邮件提供商域可以包含特殊字符-、_、.
        /^[a-z0-9]+([._\\-]*[a-z0-9])*@([a-z0-9]+[-a-z0-9]*[a-z0-9]+.){1,63}[a-z0-9]+$/
        /^(\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14})$/
        /^[a-zA-Z0-9]([a-zA-Z0-9_.-]*)@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$/
        */
        Returns:

        """
        reg_str = r'^[a-zA-Z0-9]([a-zA-Z0-9_.-]*)@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_ip(self, field):
        """
        验证合法IP地址
        /**
         * [ip ipv4、ipv6]
         * "192.168.0.0"
         * "192.168.2.3.1.1"
         * "235.168.2.1"
         * "192.168.254.10"
         * "192.168.254.10.1.1"
         */
         /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}|(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){5})$/
        Returns:

        """
        reg_str = r'^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}|(\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){5})$'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_fax(self, field):
        """
        验证传真
        /**
        * @descrition:判断输入的参数是否是个合格的固定电话号码。
        * 待验证的固定电话号码。
        * 国家代码(2到3位)-区号(2到3位)-电话号码(7到8位)-分机号(3位)
        **/
        /^(([0\+]\d{2,3}-)?(0\d{2,3})-)(\d{7,8})(-(\d{3,}))?$/
        Returns:

        """
        reg_str = r'^(([0\+]\d{2,3}-)?(0\d{2,3})-)(\d{7,8})(-(\d{3,}))?$'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_tel(self, field):
        """
        验证座机
        /**
        * @descrition:判断输入的参数是否是个合格的固定电话号码。
        * 待验证的固定电话号码。
        * 国家代码(2到3位)-区号(2到3位)-电话号码(7到8位)-分机号(3位)
        **/
        /^(([0\+]\d{2,3}-)?(0\d{2,3})-)(\d{7,8})(-(\d{3,}))?$/
        Returns:

        """
        reg_str = r'^(([0\+]\d{2,3}-)?(0\d{2,3})-)(\d{7,8})(-(\d{3,}))?$'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_mobile(self, field):
        """
        验证手机
        /**
        *@descrition:手机号码段规则
        * 13段：130、131、132、133、134、135、136、137、138、139
        * 14段：145、146、147、148、149
        * 15段：150、151、152、153、155、156、157、158、159
        * 16段：165、166
        * 17段：170、171、172、173、174、175、176、177、178
        * 18段：180、181、182、183、184、185、186、187、188、189
        * 19段：198、199
        * 国际码 如：中国(+86)
        */
        /^((\+?[0-9]{1,4})|(\(\+86\)))?(13[0-9]|14[56789]|15[0-9]|16[6]|17[0-9]|18[0-9]|19[89])\d{8}$/

        Returns:

        """
        reg_str = r'^((\+?[0-9]{1,4})|(\(\+86\)))?(13[0-9]|14[56789]|15[0-9]|16[56]|17[0-9]|18[0-9]|19[89])\d{8}$'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_duty(self, field):
        """
        验证税号
        /**
         * @descrition 匹配 URL
         */
         /^[A-Za-z0-9]{15,20}$/
        Returns:

        """
        reg_str = r'^[A-Za-z0-9]{15,20}$'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_url(self, field):
        """
        验证url
        /**
         * @descrition 匹配 URL
         */
         /[a-zA-z]+:\/\/[^\s]/
        Returns:

        """
        reg_str = r'[a-zA-z]+:\/\/[^\s]'
        if re.match(reg_str, field):
            return True
        else:
            return False

    def is_required(self, field):
        """
        验证是否为必填
        Returns:

        """
        if field:
            return True
        else:
            return False

    def max_length(self, field, length):
        """
        最大长度
        Returns:

        """
        if len(field) <= length:
            return True
        else:
            return False

    def min_length(self, field, length):
        """
        最小长度
        Returns:

        """
        if len(field) >= length:
            return True
        else:
            return False

    def equal(self, field, length):
        """
        是否等于
        Returns:

        """
        if len(field) == length:
            return True
        else:
            return False

    def is_valid_date(self, field):
        """
        判断是否是一个有效的日期字符串
        """
        try:
            time.strptime(field, "%Y-%m-%d")
            return True
        except:
            return False



# -*- coding: utf-8 -*-

import polib
import re
import os
import time

from path import Path
from shutil import move
from tempfile import mkstemp
from os import remove, walk

BASE_DIR = Path('.').abspath()

HEADER = """
# edX translation file
# Copyright (C) 2018 edX
# This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.
# EdX Team <info@edx.org>, 2018.
#
"""

CONFIG = {
    'edx': 'conf/locale/en/LC_MESSAGES',
    'xadmin': 'eliteu_admin/lib/xadmin/locale/zh_CN/LC_MESSAGES',
    'membership': '/Users/yingli/Documents/Github/docker-edx/edx-membership/conf/locale/zh_CN/LC_MESSAGES'
}


def valid(text, pattern):
    """
    Use re to match text to decide whether text is valid

    :param text: str
    :param pattern: re compiled rule
    :return: True if match and False if mismatch
    """

    match = pattern.search(text)
    return match


def check(path):
    """
    Use for extract function.
    If file doesn't exists, create.
    If file exists, truncate.

    :param path: path of file
    :return: Pofile of path
    """

    f = open(path, 'w')
    # f.write(HEADER)
    f.close()

    pomsgs = polib.pofile(path)
    return pomsgs


def trans_unicode(source_file_path):
    """
    Cause some translate string would be Escaped to unicode,
    use the function to escaped unicode to cn.

    :param source_file_path: path of file
    :return:
    """

    fh, target_file_path = mkstemp()

    source = polib.pofile(source_file_path)

    target = open(target_file_path, 'w')
    target.close()

    target_po = polib.pofile(target_file_path)

    for s in source:

        if "\\u" in s.msgid:
            s.msgid = s.msgid.encode('utf-8').decode('unicode_escape')

        target_po.append(s)

    target_po.save()
    remove(source_file_path)
    move(target_file_path, source_file_path)


def update(source_file, target_file):
    """
    Update trans of to target_file from source_file
    :param source_file: File contains msgstr u need
    :param target_file: File which need to be updated msgstr
    :return:
    """
    import polib

    source = polib.pofile(source_file)
    target = polib.pofile(target_file)

    target_ids = [(t.msgid, t.msgid_plural, t.msgctxt) for t in target]
    target_msgctxt = [(t.msgid, t.msgctxt) for t in target]

    length = len(source)

    for i in range(0, length):

        s = source[i]
        msgid = s.msgid
        msgstr = s.msgstr
        msgctxt = s.msgctxt
        msgid_plural = s.msgid_plural
        msgstr_plural = s.msgstr_plural

        try:
            # pgettext
            if msgctxt is not None:
                index = target_msgctxt.index((msgid, msgctxt))

                t = target[index]
                t.msgstr = msgstr

            # plural
            elif msgid_plural != "":
                index = target_ids.index((msgid, msgid_plural, msgctxt))
                
                t = target[index]
                for k in t.msgstr_plural.keys():
                    t.msgstr_plural[k] = msgstr_plural[k]

            # ordinary
            elif msgstr != "":
                index = target_ids.index((msgid, '', None))

                t = target[index]
                t.msgstr = msgstr

        except:
            continue

    target.save()


def exchange(source_file_path):
    """
    Exchange msgid and msgstr position of zh.po

    :param source_file_path: File which need to be exchange
    :return:
    """

    source = polib.pofile(source_file_path)

    fh, target_file_path = mkstemp()
    target = open(target_file_path, 'w')
    target.close()
    target = polib.pofile(target_file_path)
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

    for s in source:
        if valid(s.msgid.strip(), zhPattern):
            s.msgid, s.msgstr = s.msgstr, s.msgid
        target.append(s)

    target.save()
    remove(source_file_path)
    move(target_file_path, source_file_path)


def extract(project):
    """
    Extract chinese msgid from po files

    :param project:
    :return:
    """

    names = ['django.po', 'djangojs.po']

    path = CONFIG.get(project)

    for name in names:
        spath = os.path.join(path, name)
        tpath = os.path.join(path, 'zh-' + name)
        source = polib.pofile(spath)
        target = check(tpath)

        for msg in source:

            zhPattern = re.compile(u'[\u4e00-\u9fa5]+')
            text = msg.msgid.strip()
            if valid(text, zhPattern):
                target.append(msg)

        target.sort(key=lambda x: len(x.msgid), reverse=True)

        target.save()


def replace(source_file_path, pattern, substring):
    """
    Update msgid with specified pattern and replace to substring

    :param source_file_path:
    :param pattern:
    :param substring:
    :return:
    """
    fh, target_file_path = mkstemp()

    target_file = open(target_file_path, 'w')
    source_file = open(source_file_path, 'r')

    # print(source_file_path, pattern, substring)
    for line in source_file:
        # TODO： 待处理
        if pattern in line:
            if line.lstrip().startswith('#'):
                target_file.write(line)
            elif line.lstrip().startswith("//"):
                target_file.write(line)
            elif line.lstrip().startswith('<! --'):
                target_file.write(line)
            else:
                target_file.write(line.replace(pattern, substring))
        else:
            target_file.write(line)

    target_file.close()
    source_file.close()
    remove(source_file_path)
    move(target_file_path, source_file_path)


def replace_code(project):
    path = CONFIG.get(project)
    names = ['zh-django.po', 'zh-djangojs.po']

    source = [os.path.join(path, name) for name in names]

    for s in source:
        pomsgs = polib.pofile(s)

        for msg in pomsgs:
            msgid = msg.msgid.encode('utf-8')
            msgstr = msg.msgstr.encode('utf-8')

            # A list of file path
            occurrences = msg.occurrences

            for (path, line) in occurrences:
                fpath = os.path.join(BASE_DIR, path)

                if os.path.exists(fpath) and msgstr != '':
                    replace(fpath, msgid, msgstr)


def find(project):
    names = ['django.po']

    path = CONFIG.get(project)

    for name in names:
        spath = os.path.join(path, name)
        tpath = os.path.join(path, 'zh-' + name)
        source = polib.pofile(spath)
        target = check(tpath)

        for msg in source:
            if msg.msgstr == "":
                target.append(msg)

        target.save()


def i18n_dirty_check(path):
    flag = False
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')
    source = polib.pofile(path)

    for msg in source:
        text = msg.msgid.strip()
        match = zhPattern.search(text)
        if match:
            flag = True
            break

    return flag


def main():
    path = 'conf/locale/zh_CN/LC_MESSAGES'
    files= os.listdir(path)
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

    po = []
    for f in files:
        if os.path.splitext(f)[1] == '.po':
            po.append(f)

    popath = [os.path.join(path, p) for p in po]
    for path in popath:
        exchange(path)
        if i18n_dirty_check(path) is True:
            print("%s is dirty.") % path
    

# main()
# exchange('conf/locale/zh_CN/LC_MESSAGES/djangojs1.po')
# exchange('conf/locale/zh_CN/LC_MESSAGES/django.po')
# update('conf/locale/zh_CN/LC_MESSAGES/djangojs1.po', 'conf/locale/zh_CN/LC_MESSAGES/djangojs.po')
# update('conf/locale/zh_CN/LC_MESSAGES/django1.po', 'conf/locale/zh_CN/LC_MESSAGES/django.po')

extract('edx')

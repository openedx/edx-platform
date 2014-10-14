# -*- coding: utf-8 -*-

__author__ = 'omar'
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import landscape, A4
import arabicreshaper
from bidi.algorithm import get_display
import re
from os import path
from django.core.files.temp import NamedTemporaryFile

static_dir = path.join(path.dirname(__file__), 'assets')

light_font_url = path.join(static_dir, "DINNextLTArabic-Light.ttf")
pdfmetrics.registerFont(TTFont("DIN Next LT Arabic Light", light_font_url, validate=True))

bold_font_url = path.join(static_dir, "DinTextArabic-Bold.ttf")
pdfmetrics.registerFont(TTFont("DIN Next LT Arabic Bold", bold_font_url, validate=True))

SIZE = landscape(A4)


def course_org_to_logo(course_org):
    if course_org == 'MITX' or course_org == 'HarvardX':
        return 'edx.png'
    elif course_org == u'بيت.كوم':
        return 'bayt-logo2-en.png'
    elif course_org == u'إدراك':
        return 'qrta_logo.jpg'
    elif course_org == 'AUB':
        return 'Full-AUB-Seal.jpg'
    else:
        return ''


def text_to_bidi(text):
    text = normalize_spaces(text)

    reshaped_text = arabicreshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text


def course_org_disclaimer(course_org):
    if course_org == 'MITX':
        return (u'تم طرح هذا المساق من قبل إدراك تحت إشراف فريق من الأكاديمين الذين اشرفوا' +
                u' على تعليم وإدارة النقاش وتقييم الأجوبة والإمتحانات، و ذلك بالتعاون مع معهد' +
                u' ماسشوستس للتكنولوجيا .')
    else:
        return (u'تم طرح هذا المساق من قبل إدراك وتحت إشراف فريق من الأكاديمين ' +
                u'الذين اشرفوا على تعليم وإدارة النقاش وتقييم الأجوبة والإمتحانات.')


def normalize_spaces(text):
    return re.sub(' +', ' ', text)


class EdraakCertificate(object):
    def __init__(self, user_profile_name, course_name, course_desc, instructor, course_end_date, course_org=None):
        self.user_profile_name = user_profile_name
        self.course_name = course_name
        self.course_desc = course_desc
        self.instructor = instructor
        self.course_end_date = course_end_date
        self.course_org = course_org

        self.temp_file = NamedTemporaryFile(suffix='-cert.pdf')

        self.ctx = None

    def init_context(self):
        ctx = canvas.Canvas(self.temp_file.name)
        ctx.setPageSize(SIZE)
        self.ctx = ctx

    def add_certificate_bg(self):
        width, height = SIZE
        bg_path = path.join(static_dir, 'certificate_layout3.jpg')
        self.ctx.drawImage(bg_path, 0, 0, width, height)

    def _set_font(self, size, is_bold):
        if is_bold:
            font = "DIN Next LT Arabic Bold"
        else:
            font = "DIN Next LT Arabic Light"

        self.ctx.setFont(font, size)
        self.ctx.setFillColorRGB(66 / 255.0, 74 / 255.0, 82 / 255.0)

    def draw_single_line_bidi_text(self, text, x, y, size, bold=False, max_width=7.494):
        x *= inch
        y *= inch
        size *= inch
        max_width *= inch

        text = text_to_bidi(text)

        while True:
            self._set_font(size, bold)
            lines = list(self._wrap_text(text, max_width))

            if len(lines) > 1:
                size *= 0.9  # reduce font size by 10%
            else:
                self.ctx.drawRightString(x, y, lines[0])
                break

    def draw_bidi_text(self, text, x, y, size, bold=False, max_width=7.494, lh_factor=1.3):
        x *= inch
        y *= inch
        size *= inch
        max_width *= inch
        line_height = size * lh_factor

        self._set_font(size, bold)

        text = text_to_bidi(text)

        for line in self._wrap_text(text, max_width):
            self.ctx.drawRightString(x, y, line)
            y -= line_height

    def add_course_org_logo(self, course_org):
        if course_org:
            image = path.join(static_dir, course_org_to_logo(course_org))
            self.ctx.drawImage(image, 3.519 * inch, 6.444 * inch, 2.467 * inch, 1.378 * inch)

    def _wrap_text(self, text, max_width):
        words = reversed(text.split(u' '))

        def de_reverse(text_to_reverse):
            return u' '.join(reversed(text_to_reverse.split(u' ')))

        line = u''
        for next_word in words:
            next_width = self.ctx.stringWidth(line + u' ' + next_word)

            if next_width >= max_width:
                yield de_reverse(line).strip()
                line = next_word
            else:
                line += u' ' + next_word

        if line:
            yield de_reverse(line).strip()

    def save(self):
        self.ctx.showPage()
        self.ctx.save()

    def generate_and_save(self):
        self.init_context()

        x = 10.8
        self.add_certificate_bg()
        self.add_course_org_logo(self.course_org)

        self.draw_bidi_text(u'تم منح شهادة إتمام المساق هذﮦ إلى:', x, 5.8, size=0.25)

        self.draw_single_line_bidi_text(self.user_profile_name, x, 5.124, size=0.5, bold=True)

        self.draw_bidi_text(u'لإتمام المساق التالي بنجاح:', x, 4.63, size=0.25)
        self.draw_bidi_text(self.course_name, x, 4.1, size=0.33, bold=True)
        self.draw_bidi_text(self.course_desc, x, 3.78, size=0.16)

        self.draw_single_line_bidi_text(self.instructor, x, 1.8, size=0.26, bold=True)
        self.draw_bidi_text(course_org_disclaimer(self.course_org), x, 1.48, size=0.16)
        self.draw_bidi_text(self.course_end_date, 2.7, 4.82, size=0.27)

        self.save()
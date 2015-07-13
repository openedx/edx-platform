"""
Utility methods for the Shopping Cart app
"""

from django.conf import settings
from microsite_configuration import microsite
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure


def is_shopping_cart_enabled():
    """
    Utility method to check the various configuration to verify that
    all of the settings have been enabled
    """
    enable_paid_course_registration = microsite.get_value(
        'ENABLE_PAID_COURSE_REGISTRATION',
        settings.FEATURES.get('ENABLE_PAID_COURSE_REGISTRATION')
    )

    enable_shopping_cart = microsite.get_value(
        'ENABLE_SHOPPING_CART',
        settings.FEATURES.get('ENABLE_SHOPPING_CART')
    )

    return enable_paid_course_registration and enable_shopping_cart


def parse_pages(pdf_buffer, password):
    """
    With an PDF buffer object, get the pages, parse each one, and return the entire pdf text
    """
    # Create a PDF parser object associated with the file object.
    parser = PDFParser(pdf_buffer)
    # Create a PDF document object that stores the document structure.
    # Supply the password for initialization.
    document = PDFDocument(parser, password)

    resource_manager = PDFResourceManager()
    la_params = LAParams()
    device = PDFPageAggregator(resource_manager, laparams=la_params)
    interpreter = PDFPageInterpreter(resource_manager, device)

    text_content = []  # a list of strings, each representing text collected from each page of the doc
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        # receive the LTPage object for this page
        layout = device.get_result()
        # layout is an LTPage object which may contain
        #  child objects like LTTextBox, LTFigure, LTImage, etc.
        text_content.append(parse_lt_objects(layout._objs))  # pylint: disable=protected-access

    return text_content


def parse_lt_objects(lt_objects):
    """
    Iterate through the list of LT* objects and capture the text data contained in each object
    """
    text_content = []

    for lt_object in lt_objects:
        if isinstance(lt_object, LTTextBox) or isinstance(lt_object, LTTextLine):
            # text
            text_content.append(lt_object.get_text().encode('utf-8'))
        elif isinstance(lt_object, LTFigure):
            # LTFigure objects are containers for other LT* objects, so recurse through the children
            text_content.append(parse_lt_objects(lt_object._objs))  # pylint: disable=protected-access

    return '\n'.join(text_content)

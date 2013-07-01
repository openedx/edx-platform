"""
Test the lms/staticbook views.
"""

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


PDF_BOOK = {
    "tab_title": "Textbook",
    "title": "A PDF Textbook",
    "chapters": [
        { "title": "Chapter 1 for PDF", "url": "https://somehost.com/the_book/chap1.pdf" },
        { "title": "Chapter 2 for PDF", "url": "https://somehost.com/the_book/chap2.pdf" },
    ],
}

HTML_BOOK = {
    "tab_title": "Textbook",
    "title": "An HTML Textbook",
    "chapters": [
        { "title": "Chapter 1 for HTML", "url": "https://somehost.com/the_book/chap1.html" },
        { "title": "Chapter 2 for HTML", "url": "https://somehost.com/the_book/chap2.html" },
    ],
}

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class StaticBookTest(ModuleStoreTestCase):
    """
    Helpers for the static book tests.
    """

    def __init__(self, *args, **kwargs):
        super(StaticBookTest, self).__init__(*args, **kwargs)
        self.course = None

    def make_course(self, **kwargs):
        """
        Make a course with an enrolled logged-in student.
        """
        self.course = CourseFactory.create(**kwargs)
        user = UserFactory.create()
        CourseEnrollmentFactory.create(user=user, course_id=self.course.id)
        self.client.login(username=user.username, password='test')

    def make_url(self, url_name, **kwargs):
        """
        Make a URL for a `url_name` using keyword args for url slots.

        Automatically provides the course id.

        """
        kwargs['course_id'] = self.course.id
        url = reverse(url_name, kwargs=kwargs)
        return url


class StaticPdfBookTest(StaticBookTest):
    """
    Test the PDF static book view.
    """

    def test_book(self):
        # We can access a book.
        self.make_course(pdf_textbooks=[PDF_BOOK])
        url = self.make_url('pdf_book', book_index=0)
        response = self.client.get(url)
        self.assertContains(response, "Chapter 1 for PDF")
        self.assertNotContains(response, "options.chapterNum =")
        self.assertNotContains(response, "options.pageNum =")

    def test_book_chapter(self):
        # We can access a book at a particular chapter.
        self.make_course(pdf_textbooks=[PDF_BOOK])
        url = self.make_url('pdf_book', book_index=0, chapter=2)
        response = self.client.get(url)
        self.assertContains(response, "Chapter 2 for PDF")
        self.assertContains(response, "options.chapterNum = 2;")
        self.assertNotContains(response, "options.pageNum =")

    def test_book_page(self):
        # We can access a book at a particular page.
        self.make_course(pdf_textbooks=[PDF_BOOK])
        url = self.make_url('pdf_book', book_index=0, page=17)
        response = self.client.get(url)
        self.assertContains(response, "Chapter 1 for PDF")
        self.assertNotContains(response, "options.chapterNum =")
        self.assertContains(response, "options.pageNum = 17;")

    def test_book_chapter_page(self):
        # We can access a book at a particular chapter and page.
        self.make_course(pdf_textbooks=[PDF_BOOK])
        url = self.make_url('pdf_book', book_index=0, chapter=2, page=17)
        response = self.client.get(url)
        self.assertContains(response, "Chapter 2 for PDF")
        self.assertContains(response, "options.chapterNum = 2;")
        self.assertContains(response, "options.pageNum = 17;")

    def test_bad_book_id(self):
        # If we have one book, asking for the second book will fail with a 404.
        self.make_course(pdf_textbooks=[PDF_BOOK])
        url = self.make_url('pdf_book', book_index=1, chapter=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_book(self):
        # If we have no books, asking for the first book will fail with a 404.
        self.make_course()
        url = self.make_url('pdf_book', book_index=0, chapter=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class StaticHtmlBookTest(StaticBookTest):
    """
    Test the HTML static book view.
    """

    def test_book(self):
        # We can access a book.
        self.make_course(html_textbooks=[HTML_BOOK])
        url = self.make_url('html_book', book_index=0)
        response = self.client.get(url)
        self.assertContains(response, "Chapter 1 for HTML")
        self.assertNotContains(response, "options.chapterNum =")

    def test_book_chapter(self):
        # We can access a book at a particular chapter.
        self.make_course(html_textbooks=[HTML_BOOK])
        url = self.make_url('html_book', book_index=0, chapter=2)
        response = self.client.get(url)
        self.assertContains(response, "Chapter 2 for HTML")
        self.assertContains(response, "options.chapterNum = 2;")

    def test_bad_book_id(self):
        # If we have one book, asking for the second book will fail with a 404.
        self.make_course(html_textbooks=[HTML_BOOK])
        url = self.make_url('html_book', book_index=1, chapter=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_no_book(self):
        # If we have no books, asking for the first book will fail with a 404.
        self.make_course()
        url = self.make_url('html_book', book_index=0, chapter=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

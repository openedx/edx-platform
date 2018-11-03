import unittest

from qtconsole.qt import QtCore, QtGui
from qtconsole.qt_loaders import load_qtest

from qtconsole.console_widget import ConsoleWidget
import ipython_genutils.testing.decorators as dec

setup = dec.skip_file_no_x11(__name__)
QTest = load_qtest()

class TestConsoleWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Create the application for the test case.
        """
        cls._app = QtGui.QApplication.instance()
        if cls._app is None:
            cls._app = QtGui.QApplication([])
        cls._app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        """ Exit the application.
        """
        QtGui.QApplication.quit()

    def assert_text_equal(self, cursor, text):
        cursor.select(cursor.Document)
        selection = cursor.selectedText()
        self.assertEqual(selection, text)

    def test_special_characters(self):
        """ Are special characters displayed correctly?
        """
        w = ConsoleWidget()
        cursor = w._get_prompt_cursor()

        test_inputs = ['xyz\b\b=\n',
                       'foo\b\nbar\n',
                       'foo\b\nbar\r\n',
                       'abc\rxyz\b\b=']
        expected_outputs = [u'x=z\u2029',
                            u'foo\u2029bar\u2029',
                            u'foo\u2029bar\u2029',
                            'x=z']
        for i, text in enumerate(test_inputs):
            w._insert_plain_text(cursor, text)
            self.assert_text_equal(cursor, expected_outputs[i])
            # clear all the text
            cursor.insertText('')

    def test_link_handling(self):
        noKeys = QtCore.Qt
        noButton = QtCore.Qt.MouseButton(0)
        noButtons = QtCore.Qt.MouseButtons(0)
        noModifiers = QtCore.Qt.KeyboardModifiers(0)
        MouseMove = QtCore.QEvent.MouseMove
        QMouseEvent = QtGui.QMouseEvent

        w = ConsoleWidget()
        cursor = w._get_prompt_cursor()
        w._insert_html(cursor, '<a href="http://python.org">written in</a>')
        obj = w._control
        tip = QtGui.QToolTip
        self.assertEqual(tip.text(), u'')

        # should be somewhere else
        elsewhereEvent = QMouseEvent(MouseMove, QtCore.QPoint(50,50),
                                     noButton, noButtons, noModifiers)
        w.eventFilter(obj, elsewhereEvent)
        self.assertEqual(tip.isVisible(), False)
        self.assertEqual(tip.text(), u'')
        # should be over text
        overTextEvent = QMouseEvent(MouseMove, QtCore.QPoint(1,5),
                                    noButton, noButtons, noModifiers)
        w.eventFilter(obj, overTextEvent)
        self.assertEqual(tip.isVisible(), True)
        self.assertEqual(tip.text(), "http://python.org")

        # should still be over text
        stillOverTextEvent = QMouseEvent(MouseMove, QtCore.QPoint(1,5),
                                         noButton, noButtons, noModifiers)
        w.eventFilter(obj, stillOverTextEvent)
        self.assertEqual(tip.isVisible(), True)
        self.assertEqual(tip.text(), "http://python.org")

    def test_width_height(self):
        # width()/height() QWidget properties should not be overridden.
        w = ConsoleWidget()
        self.assertEqual(w.width(), QtGui.QWidget.width(w))
        self.assertEqual(w.height(), QtGui.QWidget.height(w))

    def test_prompt_cursors(self):
        """Test the cursors that keep track of where the prompt begins and
        ends"""
        w = ConsoleWidget()
        w._prompt = 'prompt>'
        doc = w._control.document()

        # Fill up the QTextEdit area with the maximum number of blocks
        doc.setMaximumBlockCount(10)
        for _ in range(9):
            w._append_plain_text('line\n')

        # Draw the prompt, this should cause the first lines to be deleted
        w._show_prompt()
        self.assertEqual(doc.blockCount(), 10)

        # _prompt_pos should be at the end of the document
        self.assertEqual(w._prompt_pos, w._get_end_pos())

        # _append_before_prompt_pos should be at the beginning of the prompt
        self.assertEqual(w._append_before_prompt_pos,
                         w._prompt_pos - len(w._prompt))

        # insert some more text without drawing a new prompt
        w._append_plain_text('line\n')
        self.assertEqual(w._prompt_pos,
                         w._get_end_pos() - len('line\n'))
        self.assertEqual(w._append_before_prompt_pos,
                         w._prompt_pos - len(w._prompt))

        # redraw the prompt
        w._show_prompt()
        self.assertEqual(w._prompt_pos, w._get_end_pos())
        self.assertEqual(w._append_before_prompt_pos,
                         w._prompt_pos - len(w._prompt))

        # insert some text before the prompt
        w._append_plain_text('line', before_prompt=True)
        self.assertEqual(w._prompt_pos, w._get_end_pos())
        self.assertEqual(w._append_before_prompt_pos,
                         w._prompt_pos - len(w._prompt))

    def test_select_all(self):
        w = ConsoleWidget()
        w._append_plain_text('Header\n')
        w._prompt = 'prompt>'
        w._show_prompt()
        control = w._control

        cursor = w._get_cursor()
        w._insert_plain_text_into_buffer(cursor, "if:\n    pass")

        cursor.clearSelection()
        control.setTextCursor(cursor)

        # "select all" action selects cell first
        w.select_all_smart()
        QTest.keyClick(control, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier)
        copied = QtGui.qApp.clipboard().text()
        self.assertEqual(copied,  'if:\n>     pass')

        # # "select all" action triggered a second time selects whole document
        w.select_all_smart()
        QTest.keyClick(control, QtCore.Qt.Key_C, QtCore.Qt.ControlModifier)
        copied = QtGui.qApp.clipboard().text()
        self.assertEqual(copied,  'Header\nprompt>if:\n>     pass')

    def test_keypresses(self):
        """Test the event handling code for keypresses."""
        w = ConsoleWidget()
        w._append_plain_text('Header\n')
        w._prompt = 'prompt>'
        w._show_prompt()
        control = w._control

        # Test setting the input buffer
        w._set_input_buffer('test input')
        self.assertEqual(w._get_input_buffer(), 'test input')

        # Ctrl+K kills input until EOL
        w._set_input_buffer('test input')
        c = control.textCursor()
        c.setPosition(c.position() - 3)
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_K, QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(), 'test in')

        # Ctrl+V pastes
        w._set_input_buffer('test input ')
        QtGui.qApp.clipboard().setText('pasted text')
        QTest.keyClick(control, QtCore.Qt.Key_V, QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(), 'test input pasted text')
        self.assertEqual(control.document().blockCount(), 2)

        # Paste should strip indentation
        w._set_input_buffer('test input ')
        QtGui.qApp.clipboard().setText('    pasted text')
        QTest.keyClick(control, QtCore.Qt.Key_V, QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(), 'test input pasted text')
        self.assertEqual(control.document().blockCount(), 2)

        # Multiline paste, should also show continuation marks
        w._set_input_buffer('test input ')
        QtGui.qApp.clipboard().setText('line1\nline2\nline3')
        QTest.keyClick(control, QtCore.Qt.Key_V, QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         'test input line1\nline2\nline3')
        self.assertEqual(control.document().blockCount(), 4)
        self.assertEqual(control.document().findBlockByNumber(1).text(),
                         'prompt>test input line1')
        self.assertEqual(control.document().findBlockByNumber(2).text(),
                         '> line2')
        self.assertEqual(control.document().findBlockByNumber(3).text(),
                         '> line3')

        # Multiline paste should strip indentation intelligently
        # in the case where pasted text has leading whitespace on first line
        # and we're pasting into indented position
        w._set_input_buffer('    ')
        QtGui.qApp.clipboard().setText('    If 1:\n        pass')
        QTest.keyClick(control, QtCore.Qt.Key_V, QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         '    If 1:\n        pass')

        # Ctrl+Backspace should intelligently remove the last word
        w._set_input_buffer("foo = ['foo', 'foo', 'foo',    \n"
                            "       'bar', 'bar', 'bar']")
        QTest.keyClick(control, QtCore.Qt.Key_Backspace,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         ("foo = ['foo', 'foo', 'foo',    \n"
                            "       'bar', 'bar', '"))
        QTest.keyClick(control, QtCore.Qt.Key_Backspace,
                       QtCore.Qt.ControlModifier)
        QTest.keyClick(control, QtCore.Qt.Key_Backspace,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         ("foo = ['foo', 'foo', 'foo',    \n"
                          "       '"))
        QTest.keyClick(control, QtCore.Qt.Key_Backspace,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         ("foo = ['foo', 'foo', 'foo',    \n"
                          ""))
        QTest.keyClick(control, QtCore.Qt.Key_Backspace,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         "foo = ['foo', 'foo', 'foo',")

        # Ctrl+Delete should intelligently remove the next word
        w._set_input_buffer("foo = ['foo', 'foo', 'foo',    \n"
                            "       'bar', 'bar', 'bar']")
        c = control.textCursor()
        c.setPosition(35)
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_Delete,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         ("foo = ['foo', 'foo', ',    \n"
                          "       'bar', 'bar', 'bar']"))
        QTest.keyClick(control, QtCore.Qt.Key_Delete,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         ("foo = ['foo', 'foo', \n"
                          "       'bar', 'bar', 'bar']"))
        QTest.keyClick(control, QtCore.Qt.Key_Delete,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         "foo = ['foo', 'foo', 'bar', 'bar', 'bar']")
        w._set_input_buffer("foo = ['foo', 'foo', 'foo',    \n"
                            "       'bar', 'bar', 'bar']")
        c = control.textCursor()
        c.setPosition(48)
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_Delete,
                       QtCore.Qt.ControlModifier)
        self.assertEqual(w._get_input_buffer(),
                         ("foo = ['foo', 'foo', 'foo',    \n"
                          "'bar', 'bar', 'bar']"))

        # Left and right keys should respect the continuation prompt
        w._set_input_buffer("line 1\n"
                            "line 2\n"
                            "line 3")
        c = control.textCursor()
        c.setPosition(20)  # End of line 1
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_Right)
        # Cursor should have moved after the continuation prompt
        self.assertEqual(control.textCursor().position(), 23)
        QTest.keyClick(control, QtCore.Qt.Key_Left)
        # Cursor should have moved to the end of the previous line
        self.assertEqual(control.textCursor().position(), 20)

        # TODO: many more keybindings

    def test_indent(self):
        """Test the event handling code for indent/dedent keypresses ."""
        w = ConsoleWidget()
        w._append_plain_text('Header\n')
        w._prompt = 'prompt>'
        w._show_prompt()
        control = w._control

        # TAB with multiline selection should block-indent
        w._set_input_buffer("")
        c = control.textCursor()
        pos=c.position()
        w._set_input_buffer("If 1:\n    pass")
        c.setPosition(pos, QtGui.QTextCursor.KeepAnchor)
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_Tab)
        self.assertEqual(w._get_input_buffer(),"    If 1:\n        pass")

        # TAB with multiline selection, should block-indent to next multiple
        # of 4 spaces, if first line has 0 < indent < 4
        w._set_input_buffer("")
        c = control.textCursor()
        pos=c.position()
        w._set_input_buffer(" If 2:\n     pass")
        c.setPosition(pos, QtGui.QTextCursor.KeepAnchor)
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_Tab)
        self.assertEqual(w._get_input_buffer(),"    If 2:\n        pass")

        # Shift-TAB with multiline selection should block-dedent
        w._set_input_buffer("")
        c = control.textCursor()
        pos=c.position()
        w._set_input_buffer("    If 3:\n        pass")
        c.setPosition(pos, QtGui.QTextCursor.KeepAnchor)
        control.setTextCursor(c)
        QTest.keyClick(control, QtCore.Qt.Key_Backtab)
        self.assertEqual(w._get_input_buffer(),"If 3:\n    pass")

    def test_complete(self):
        class TestKernelClient(object):
            def is_complete(self, source):
                calls.append(source)
                return msg_id
        w = ConsoleWidget()
        cursor = w._get_prompt_cursor()
        w._execute = lambda *args: calls.append(args)
        w.kernel_client = TestKernelClient()
        msg_id = object()
        calls = []

        # test incomplete statement (no _execute called, but indent added)
        w.execute("thing", interactive=True)
        self.assertEqual(calls, ["thing"])
        calls = []
        w._handle_is_complete_reply(
            dict(parent_header=dict(msg_id=msg_id),
                 content=dict(status="incomplete", indent="!!!")))
        self.assert_text_equal(cursor, u"thing\u2029> !!!")
        self.assertEqual(calls, [])

        # test complete statement (_execute called)
        msg_id = object()
        w.execute("else", interactive=True)
        self.assertEqual(calls, ["else"])
        calls = []
        w._handle_is_complete_reply(
            dict(parent_header=dict(msg_id=msg_id),
                 content=dict(status="complete", indent="###")))
        self.assertEqual(calls, [("else", False)])
        calls = []
        self.assert_text_equal(cursor, u"thing\u2029> !!!else\u2029")

        # test missing answer from is_complete
        msg_id = object()
        w.execute("done", interactive=True)
        self.assertEqual(calls, ["done"])
        calls = []
        self.assert_text_equal(cursor, u"thing\u2029> !!!else\u2029")
        event = QtCore.QEvent(QtCore.QEvent.User)
        w.eventFilter(w, event)
        self.assert_text_equal(cursor, u"thing\u2029> !!!else\u2029\u2029> ")

        # assert that late answer isn't destroying anything
        w._handle_is_complete_reply(
            dict(parent_header=dict(msg_id=msg_id),
                 content=dict(status="complete", indent="###")))
        self.assertEqual(calls, [])

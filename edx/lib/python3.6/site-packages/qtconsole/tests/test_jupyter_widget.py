import unittest

from qtconsole.qt import QtGui
from qtconsole.qt_loaders import load_qtest
from qtconsole.client import QtKernelClient
from qtconsole.jupyter_widget import JupyterWidget
import ipython_genutils.testing.decorators as dec

setup = dec.skip_file_no_x11(__name__)
QTest = load_qtest()


class TestJupyterWidget(unittest.TestCase):

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

    def test_stylesheet_changed(self):
        """ Test changing stylesheets.
        """
        w = JupyterWidget(kind='rich')

        # By default, the background is light. White text is rendered as black
        self.assertEqual(w._ansi_processor.get_color(15).name(), '#000000')

        # Change to a dark colorscheme. White text is rendered as white
        w.syntax_style = 'monokai'
        self.assertEqual(w._ansi_processor.get_color(15).name(), '#ffffff')

    def test_other_output(self):
        """ Test displaying output from other clients.
        """
        w = JupyterWidget(kind='rich')
        w._append_plain_text('Header\n')
        w._show_interpreter_prompt(1)
        w.other_output_prefix = '[other] '
        w.syntax_style = 'default'
        control = w._control
        document = control.document()

        msg = dict(
            execution_count=1,
            code='a = 1 + 1\nb = range(10)',
        )
        w._append_custom(w._insert_other_input, msg, before_prompt=True)

        self.assertEqual(document.blockCount(), 6)
        self.assertEqual(document.toPlainText(), (
            u'Header\n'
            u'\n'
            u'[other] In [1]: a = 1 + 1\n'
            u'           ...: b = range(10)\n'
            u'\n'
            u'In [2]: '
        ))

        # Check proper syntax highlighting
        self.assertEqual(document.toHtml(), (
            u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n'
            u'<html><head><meta name="qrichtext" content="1" /><style type="text/css">\n'
            u'p, li { white-space: pre-wrap; }\n'
            u'</style></head><body style=" font-family:\'Monospace\'; font-size:9pt; font-weight:400; font-style:normal;">\n'
            u'<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Header</p>\n'
            u'<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>\n'
            u'<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" color:#000080;">[other] In [</span><span style=" font-weight:600; color:#000080;">1</span><span style=" color:#000080;">]:</span> a = 1 + 1</p>\n'
            u'<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" color:#000080;">\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0...:</span> b = range(10)</p>\n'
            u'<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>\n'
            u'<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" color:#000080;">In [</span><span style=" font-weight:600; color:#000080;">2</span><span style=" color:#000080;">]:</span> </p></body></html>'
        ))

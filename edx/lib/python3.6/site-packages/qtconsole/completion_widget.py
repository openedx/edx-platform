"""A dropdown completer widget for the qtconsole."""

from qtconsole.qt import QtCore, QtGui


class CompletionWidget(QtGui.QListWidget):
    """ A widget for GUI tab completion.
    """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, console_widget):
        """ Create a completion widget that is attached to the specified Qt
            text edit widget.
        """
        text_edit = console_widget._control
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CompletionWidget, self).__init__()

        self._text_edit = text_edit
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        # We need Popup style to ensure correct mouse interaction
        # (dialog would dissappear on mouse click with ToolTip style)
        self.setWindowFlags(QtCore.Qt.Popup)

        self.setAttribute(QtCore.Qt.WA_StaticContents)
        original_policy = text_edit.focusPolicy()

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        text_edit.setFocusPolicy(original_policy)

        # Ensure that the text edit keeps focus when widget is displayed.
        self.setFocusProxy(self._text_edit)

        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setFrameShape(QtGui.QFrame.StyledPanel)

        self.itemActivated.connect(self._complete_current)

    def eventFilter(self, obj, event):
        """ Reimplemented to handle mouse input and to auto-hide when the
            text edit loses focus.
        """
        if obj is self:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                pos = self.mapToGlobal(event.pos())
                target = QtGui.QApplication.widgetAt(pos)
                if (target and self.isAncestorOf(target) or target is self):
                    return False
                else:
                    self.cancel_completion()

        return super(CompletionWidget, self).eventFilter(obj, event)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter,
                   QtCore.Qt.Key_Tab):
            self._complete_current()
        elif key == QtCore.Qt.Key_Escape:
            self.hide()
        elif key in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down,
                     QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown,
                     QtCore.Qt.Key_Home, QtCore.Qt.Key_End):
            return super(CompletionWidget, self).keyPressEvent(event)
        else:
            QtGui.QApplication.sendEvent(self._text_edit, event)

    #--------------------------------------------------------------------------
    # 'QWidget' interface
    #--------------------------------------------------------------------------

    def hideEvent(self, event):
        """ Reimplemented to disconnect signal handlers and event filter.
        """
        super(CompletionWidget, self).hideEvent(event)
        self._text_edit.cursorPositionChanged.disconnect(self._update_current)
        self.removeEventFilter(self)

    def showEvent(self, event):
        """ Reimplemented to connect signal handlers and event filter.
        """
        super(CompletionWidget, self).showEvent(event)
        self._text_edit.cursorPositionChanged.connect(self._update_current)
        self.installEventFilter(self)

    #--------------------------------------------------------------------------
    # 'CompletionWidget' interface
    #--------------------------------------------------------------------------

    def show_items(self, cursor, items):
        """ Shows the completion widget with 'items' at the position specified
            by 'cursor'.
        """
        text_edit = self._text_edit
        point = text_edit.cursorRect(cursor).bottomRight()
        point = text_edit.mapToGlobal(point)
        self.clear()
        self.addItems(items)
        height = self.sizeHint().height()
        screen_rect = QtGui.QApplication.desktop().availableGeometry(self)
        if (screen_rect.size().height() + screen_rect.y() -
                point.y() - height < 0):
            point = text_edit.mapToGlobal(text_edit.cursorRect().topRight())
            point.setY(point.y() - height)
        w = (self.sizeHintForColumn(0) +
             self.verticalScrollBar().sizeHint().width())
        self.setGeometry(point.x(), point.y(), w, height)
        self._start_position = cursor.position()
        self.setCurrentRow(0)
        self.raise_()
        self.show()

    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _complete_current(self):
        """ Perform the completion with the currently selected item.
        """
        self._current_text_cursor().insertText(self.currentItem().text())
        self.hide()

    def _current_text_cursor(self):
        """ Returns a cursor with text between the start position and the
            current position selected.
        """
        cursor = self._text_edit.textCursor()
        if cursor.position() >= self._start_position:
            cursor.setPosition(self._start_position,
                               QtGui.QTextCursor.KeepAnchor)
        return cursor

    def _update_current(self):
        """ Updates the current item based on the current text.
        """
        prefix = self._current_text_cursor().selection().toPlainText()
        if prefix:
            items = self.findItems(prefix, (QtCore.Qt.MatchStartsWith |
                                            QtCore.Qt.MatchCaseSensitive))
            if items:
                self.setCurrentItem(items[0])
            else:
                self.hide()
        else:
            self.hide()

    def cancel_completion(self):
        self.hide()

from edxmako.shortcuts import render_to_string


def EdxNotes(cls):
    """
    Docstring for the decorator.
    """
    original_get_html = cls.get_html

    def get_html(self, *args, **kargs):
        template_context = {
            'content': original_get_html(self, *args, **kargs)
        }
        return render_to_string('edxnotes_wrapper.html', template_context)

    cls.get_html = get_html

    return cls

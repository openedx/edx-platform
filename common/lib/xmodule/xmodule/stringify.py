from itertools import chain
from lxml import etree

def stringify_children(node):
    '''
    Return all contents of an xml tree, without the outside tags.
    e.g. if node is parse of
        "<html a="b" foo="bar">Hi <div>there <span>Bruce</span><b>!</b></div><html>"
    should return
        "Hi <div>there <span>Bruce</span><b>!</b></div>"

    fixed from
    http://stackoverflow.com/questions/4624062/get-all-text-inside-a-tag-in-lxml
    '''
    parts = ([node.text] +
            list(chain(*([etree.tostring(c), c.tail]
                         for c in node.getchildren())
                         )))
    # filter removes possible Nones in texts and tails
    return ''.join(filter(None, parts))

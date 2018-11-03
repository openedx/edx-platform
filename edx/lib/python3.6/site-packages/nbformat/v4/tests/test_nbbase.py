# coding: utf-8
"""Tests for the Python API for composing notebook elements"""

from nbformat.validator import isvalid, validate, ValidationError
from ..nbbase import (
    NotebookNode, nbformat,
    new_code_cell, new_markdown_cell, new_notebook,
    new_output, new_raw_cell,
)

def test_empty_notebook():
    nb = new_notebook()
    assert nb.cells == []
    assert nb.metadata == NotebookNode()
    assert nb.nbformat == nbformat

def test_empty_markdown_cell():
    cell = new_markdown_cell()
    assert cell.cell_type == 'markdown'
    assert cell.source == ''

def test_markdown_cell():
    cell = new_markdown_cell(u'* Søme markdown')
    assert cell.source == u'* Søme markdown'

def test_empty_raw_cell():
    cell = new_raw_cell()
    assert cell.cell_type == u'raw'
    assert cell.source == ''

def test_raw_cell():
    cell = new_raw_cell('hi')
    assert cell.source == u'hi'

def test_empty_code_cell():
    cell = new_code_cell('hi')
    assert cell.cell_type == 'code'
    assert cell.source == u'hi'

def test_empty_display_data():
    output = new_output('display_data')
    assert output.output_type == 'display_data'

def test_empty_stream():
    output = new_output('stream')
    assert output.output_type == 'stream'
    assert output.name == 'stdout'
    assert output.text == ''

def test_empty_execute_result():
    output = new_output('execute_result', execution_count=1)
    assert output.output_type == 'execute_result'

mimebundle = {
    'text/plain': "some text",
    "application/json": {
        "key": "value"
    },
    "image/svg+xml": 'ABCDEF',
    "application/octet-stream": 'ABC-123',
    "application/vnd.foo+bar": "Some other stuff",
}

def test_display_data():
    output = new_output('display_data', mimebundle)
    for key, expected in mimebundle.items():
        assert output.data[key] == expected

def test_execute_result():
    output = new_output('execute_result', mimebundle, execution_count=10)
    assert output.execution_count == 10
    for key, expected in mimebundle.items():
        assert output.data[key] == expected

def test_error():
    o = new_output(output_type=u'error', ename=u'NameError',
        evalue=u'Name not found', traceback=[u'frame 0', u'frame 1', u'frame 2']
    )
    assert o.output_type == u'error'
    assert o.ename == u'NameError'
    assert o.evalue == u'Name not found'
    assert o.traceback == [u'frame 0', u'frame 1', u'frame 2']

def test_code_cell_with_outputs():
    cell = new_code_cell(execution_count=10, outputs=[
        new_output('display_data', mimebundle),
        new_output('stream', text='hello'),
        new_output('execute_result', mimebundle, execution_count=10),
    ])
    assert cell.execution_count == 10
    assert len(cell.outputs) == 3
    er = cell.outputs[-1]
    assert er.execution_count == 10
    assert er['output_type'] == 'execute_result'

def test_stream():
    output = new_output('stream', name='stderr', text='hello there')
    assert output.name == 'stderr'
    assert output.text == 'hello there'

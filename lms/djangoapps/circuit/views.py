import json

import xml.etree.ElementTree

from django.http import Http404
from django.http import HttpResponse
from edxmako.shortcuts import render_to_response

from .models import ServerCircuit


def circuit_line(circuit):
    ''' Returns string for an appropriate input element for a circuit.
        TODO: Rename. '''
    if not circuit.isalnum():
        raise Http404()
    try:
        server_circuit = ServerCircuit.objects.get(name=circuit)
    except Exception:
        schematic = ''
    else:
        schematic = server_circuit.schematic

    circuit_line = xml.etree.ElementTree.Element('input')
    circuit_line.set('type', 'hidden')
    circuit_line.set('class', 'schematic')
    circuit_line.set('width', '640')
    circuit_line.set('height', '480')
    circuit_line.set('name', 'schematic')
    circuit_line.set('id', 'schematic_' + circuit)
    circuit_line.set('value', schematic)  # We do it this way for security -- guarantees users cannot put funny stuff in schematic.
    return xml.etree.ElementTree.tostring(circuit_line)


def edit_circuit(request, circuit):
    try:
        server_circuit = ServerCircuit.objects.get(name=circuit)
    except Exception:
        server_circuit = None

    if not circuit.isalnum():
        raise Http404()
    response = render_to_response('edit_circuit.html', {'name': circuit,
                                                        'circuit_line': circuit_line(circuit)})
    response['Cache-Control'] = 'no-cache'
    return response


def save_circuit(request, circuit):
    if not circuit.isalnum():
        raise Http404()
    print dict(request.POST)
    schematic = request.POST['schematic']
    print schematic
    try:
        server_circuit = ServerCircuit.objects.get(name=circuit)
    except Exception:
        server_circuit = ServerCircuit()
        server_circuit.name = circuit
    server_circuit.schematic = schematic
    print ":", server_circuit.schematic
    server_circuit.save()
    json_str = json.dumps({'results': 'success'})
    response = HttpResponse(json_str, mimetype='application/json')
    response['Cache-Control'] = 'no-cache'
    return response

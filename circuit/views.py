from djangomako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect
import os
from django.conf import settings
from django.http import Http404
from models import ServerCircuit
import json
import xml.etree.ElementTree
from django.http import HttpResponse

def circuit_line(circuit):
    if not circuit.isalnum():
        raise Http404()
    try:
        sc = ServerCircuit.objects.get(name=circuit)
        schematic = sc.schematic
        print "Got"
    except:
        schematic = ''
        print "not got"
    print "X", schematic

    circuit_line = xml.etree.ElementTree.Element('input')
    circuit_line.set('type', 'hidden')
    circuit_line.set('class', 'schematic')
    circuit_line.set('width', '640')
    circuit_line.set('height', '480')
    circuit_line.set('name', 'schematic')
    circuit_line.set('id', 'schematic_'+circuit)
    circuit_line.set('value', schematic) # We do it this way for security -- guarantees users cannot put funny stuff in schematic. 
    return xml.etree.ElementTree.tostring(circuit_line)

def edit_circuit(request, circuit):
    try:
        sc = ServerCircuit.objects.get(name=circuit)
    except:
        sc = None

    if not circuit.isalnum():
        raise Http404()
    response = render_to_response('edit_circuit.html', {'name':circuit, 
                                                        'circuit_line':circuit_line(circuit)})
    response['Cache-Control'] = 'no-cache'
    return response

def save_circuit(request, circuit):
    if not circuit.isalnum():
        raise Http404()
    print dict(request.POST)
    schematic = request.POST['schematic']
    print schematic
    try:
        sc = ServerCircuit.objects.get(name=circuit)
    except:
        sc = ServerCircuit()
        sc.name = circuit
    sc.schematic = schematic
    print ":", sc.schematic
    sc.save()
    json_str = json.dumps({'results': 'success'})
    response = HttpResponse(json_str, mimetype='application/json')
    response['Cache-Control'] = 'no-cache'
    return response


# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
  from google.protobuf import descriptor as _descriptor
  from google.protobuf import message as _message
  from google.protobuf import reflection as _reflection
  from google.protobuf import symbol_database as _symbol_database
  # @@protoc_insertion_point(imports)
except ImportError:
  pass
else:
  _sym_db = _symbol_database.Default()


  DESCRIPTOR = _descriptor.FileDescriptor(
    name='infinite_tracing.proto',
    package='com.newrelic.trace.v1',
    syntax='proto3',
    serialized_options=None,
    serialized_pb=b'\n\x16infinite_tracing.proto\x12\x15\x63om.newrelic.trace.v1\"\x86\x04\n\x04Span\x12\x10\n\x08trace_id\x18\x01 \x01(\t\x12?\n\nintrinsics\x18\x02 \x03(\x0b\x32+.com.newrelic.trace.v1.Span.IntrinsicsEntry\x12H\n\x0fuser_attributes\x18\x03 \x03(\x0b\x32/.com.newrelic.trace.v1.Span.UserAttributesEntry\x12J\n\x10\x61gent_attributes\x18\x04 \x03(\x0b\x32\x30.com.newrelic.trace.v1.Span.AgentAttributesEntry\x1aX\n\x0fIntrinsicsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x34\n\x05value\x18\x02 \x01(\x0b\x32%.com.newrelic.trace.v1.AttributeValue:\x02\x38\x01\x1a\\\n\x13UserAttributesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x34\n\x05value\x18\x02 \x01(\x0b\x32%.com.newrelic.trace.v1.AttributeValue:\x02\x38\x01\x1a]\n\x14\x41gentAttributesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x34\n\x05value\x18\x02 \x01(\x0b\x32%.com.newrelic.trace.v1.AttributeValue:\x02\x38\x01\"t\n\x0e\x41ttributeValue\x12\x16\n\x0cstring_value\x18\x01 \x01(\tH\x00\x12\x14\n\nbool_value\x18\x02 \x01(\x08H\x00\x12\x13\n\tint_value\x18\x03 \x01(\x03H\x00\x12\x16\n\x0c\x64ouble_value\x18\x04 \x01(\x01H\x00\x42\x07\n\x05value\"%\n\x0cRecordStatus\x12\x15\n\rmessages_seen\x18\x01 \x01(\x04\x32\x65\n\rIngestService\x12T\n\nRecordSpan\x12\x1b.com.newrelic.trace.v1.Span\x1a#.com.newrelic.trace.v1.RecordStatus\"\x00(\x01\x30\x01\x62\x06proto3'
  )




  _SPAN_INTRINSICSENTRY = _descriptor.Descriptor(
    name='IntrinsicsEntry',
    full_name='com.newrelic.trace.v1.Span.IntrinsicsEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
      _descriptor.FieldDescriptor(
        name='key', full_name='com.newrelic.trace.v1.Span.IntrinsicsEntry.key', index=0,
        number=1, type=9, cpp_type=9, label=1,
        has_default_value=False, default_value=b"".decode('utf-8'),
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='value', full_name='com.newrelic.trace.v1.Span.IntrinsicsEntry.value', index=1,
        number=2, type=11, cpp_type=10, label=1,
        has_default_value=False, default_value=None,
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=b'8\001',
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=291,
    serialized_end=379,
  )

  _SPAN_USERATTRIBUTESENTRY = _descriptor.Descriptor(
    name='UserAttributesEntry',
    full_name='com.newrelic.trace.v1.Span.UserAttributesEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
      _descriptor.FieldDescriptor(
        name='key', full_name='com.newrelic.trace.v1.Span.UserAttributesEntry.key', index=0,
        number=1, type=9, cpp_type=9, label=1,
        has_default_value=False, default_value=b"".decode('utf-8'),
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='value', full_name='com.newrelic.trace.v1.Span.UserAttributesEntry.value', index=1,
        number=2, type=11, cpp_type=10, label=1,
        has_default_value=False, default_value=None,
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=b'8\001',
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=381,
    serialized_end=473,
  )

  _SPAN_AGENTATTRIBUTESENTRY = _descriptor.Descriptor(
    name='AgentAttributesEntry',
    full_name='com.newrelic.trace.v1.Span.AgentAttributesEntry',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
      _descriptor.FieldDescriptor(
        name='key', full_name='com.newrelic.trace.v1.Span.AgentAttributesEntry.key', index=0,
        number=1, type=9, cpp_type=9, label=1,
        has_default_value=False, default_value=b"".decode('utf-8'),
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='value', full_name='com.newrelic.trace.v1.Span.AgentAttributesEntry.value', index=1,
        number=2, type=11, cpp_type=10, label=1,
        has_default_value=False, default_value=None,
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=b'8\001',
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=475,
    serialized_end=568,
  )

  _SPAN = _descriptor.Descriptor(
    name='Span',
    full_name='com.newrelic.trace.v1.Span',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
      _descriptor.FieldDescriptor(
        name='trace_id', full_name='com.newrelic.trace.v1.Span.trace_id', index=0,
        number=1, type=9, cpp_type=9, label=1,
        has_default_value=False, default_value=b"".decode('utf-8'),
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='intrinsics', full_name='com.newrelic.trace.v1.Span.intrinsics', index=1,
        number=2, type=11, cpp_type=10, label=3,
        has_default_value=False, default_value=[],
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='user_attributes', full_name='com.newrelic.trace.v1.Span.user_attributes', index=2,
        number=3, type=11, cpp_type=10, label=3,
        has_default_value=False, default_value=[],
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='agent_attributes', full_name='com.newrelic.trace.v1.Span.agent_attributes', index=3,
        number=4, type=11, cpp_type=10, label=3,
        has_default_value=False, default_value=[],
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[_SPAN_INTRINSICSENTRY, _SPAN_USERATTRIBUTESENTRY, _SPAN_AGENTATTRIBUTESENTRY, ],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=50,
    serialized_end=568,
  )


  _ATTRIBUTEVALUE = _descriptor.Descriptor(
    name='AttributeValue',
    full_name='com.newrelic.trace.v1.AttributeValue',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
      _descriptor.FieldDescriptor(
        name='string_value', full_name='com.newrelic.trace.v1.AttributeValue.string_value', index=0,
        number=1, type=9, cpp_type=9, label=1,
        has_default_value=False, default_value=b"".decode('utf-8'),
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='bool_value', full_name='com.newrelic.trace.v1.AttributeValue.bool_value', index=1,
        number=2, type=8, cpp_type=7, label=1,
        has_default_value=False, default_value=False,
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='int_value', full_name='com.newrelic.trace.v1.AttributeValue.int_value', index=2,
        number=3, type=3, cpp_type=2, label=1,
        has_default_value=False, default_value=0,
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
      _descriptor.FieldDescriptor(
        name='double_value', full_name='com.newrelic.trace.v1.AttributeValue.double_value', index=3,
        number=4, type=1, cpp_type=5, label=1,
        has_default_value=False, default_value=float(0),
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
      _descriptor.OneofDescriptor(
        name='value', full_name='com.newrelic.trace.v1.AttributeValue.value',
        index=0, containing_type=None, fields=[]),
    ],
    serialized_start=570,
    serialized_end=686,
  )


  _RECORDSTATUS = _descriptor.Descriptor(
    name='RecordStatus',
    full_name='com.newrelic.trace.v1.RecordStatus',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
      _descriptor.FieldDescriptor(
        name='messages_seen', full_name='com.newrelic.trace.v1.RecordStatus.messages_seen', index=0,
        number=1, type=4, cpp_type=4, label=1,
        has_default_value=False, default_value=0,
        message_type=None, enum_type=None, containing_type=None,
        is_extension=False, extension_scope=None,
        serialized_options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=688,
    serialized_end=725,
  )

  _SPAN_INTRINSICSENTRY.fields_by_name['value'].message_type = _ATTRIBUTEVALUE
  _SPAN_INTRINSICSENTRY.containing_type = _SPAN
  _SPAN_USERATTRIBUTESENTRY.fields_by_name['value'].message_type = _ATTRIBUTEVALUE
  _SPAN_USERATTRIBUTESENTRY.containing_type = _SPAN
  _SPAN_AGENTATTRIBUTESENTRY.fields_by_name['value'].message_type = _ATTRIBUTEVALUE
  _SPAN_AGENTATTRIBUTESENTRY.containing_type = _SPAN
  _SPAN.fields_by_name['intrinsics'].message_type = _SPAN_INTRINSICSENTRY
  _SPAN.fields_by_name['user_attributes'].message_type = _SPAN_USERATTRIBUTESENTRY
  _SPAN.fields_by_name['agent_attributes'].message_type = _SPAN_AGENTATTRIBUTESENTRY
  _ATTRIBUTEVALUE.oneofs_by_name['value'].fields.append(
    _ATTRIBUTEVALUE.fields_by_name['string_value'])
  _ATTRIBUTEVALUE.fields_by_name['string_value'].containing_oneof = _ATTRIBUTEVALUE.oneofs_by_name['value']
  _ATTRIBUTEVALUE.oneofs_by_name['value'].fields.append(
    _ATTRIBUTEVALUE.fields_by_name['bool_value'])
  _ATTRIBUTEVALUE.fields_by_name['bool_value'].containing_oneof = _ATTRIBUTEVALUE.oneofs_by_name['value']
  _ATTRIBUTEVALUE.oneofs_by_name['value'].fields.append(
    _ATTRIBUTEVALUE.fields_by_name['int_value'])
  _ATTRIBUTEVALUE.fields_by_name['int_value'].containing_oneof = _ATTRIBUTEVALUE.oneofs_by_name['value']
  _ATTRIBUTEVALUE.oneofs_by_name['value'].fields.append(
    _ATTRIBUTEVALUE.fields_by_name['double_value'])
  _ATTRIBUTEVALUE.fields_by_name['double_value'].containing_oneof = _ATTRIBUTEVALUE.oneofs_by_name['value']
  DESCRIPTOR.message_types_by_name['Span'] = _SPAN
  DESCRIPTOR.message_types_by_name['AttributeValue'] = _ATTRIBUTEVALUE
  DESCRIPTOR.message_types_by_name['RecordStatus'] = _RECORDSTATUS
  _sym_db.RegisterFileDescriptor(DESCRIPTOR)

  Span = _reflection.GeneratedProtocolMessageType('Span', (_message.Message,), {

    'IntrinsicsEntry' : _reflection.GeneratedProtocolMessageType('IntrinsicsEntry', (_message.Message,), {
      'DESCRIPTOR' : _SPAN_INTRINSICSENTRY,
      '__module__' : 'infinite_tracing_pb2'
      # @@protoc_insertion_point(class_scope:com.newrelic.trace.v1.Span.IntrinsicsEntry)
      })
    ,

    'UserAttributesEntry' : _reflection.GeneratedProtocolMessageType('UserAttributesEntry', (_message.Message,), {
      'DESCRIPTOR' : _SPAN_USERATTRIBUTESENTRY,
      '__module__' : 'infinite_tracing_pb2'
      # @@protoc_insertion_point(class_scope:com.newrelic.trace.v1.Span.UserAttributesEntry)
      })
    ,

    'AgentAttributesEntry' : _reflection.GeneratedProtocolMessageType('AgentAttributesEntry', (_message.Message,), {
      'DESCRIPTOR' : _SPAN_AGENTATTRIBUTESENTRY,
      '__module__' : 'infinite_tracing_pb2'
      # @@protoc_insertion_point(class_scope:com.newrelic.trace.v1.Span.AgentAttributesEntry)
      })
    ,
    'DESCRIPTOR' : _SPAN,
    '__module__' : 'infinite_tracing_pb2'
    # @@protoc_insertion_point(class_scope:com.newrelic.trace.v1.Span)
    })
  _sym_db.RegisterMessage(Span)
  _sym_db.RegisterMessage(Span.IntrinsicsEntry)
  _sym_db.RegisterMessage(Span.UserAttributesEntry)
  _sym_db.RegisterMessage(Span.AgentAttributesEntry)

  AttributeValue = _reflection.GeneratedProtocolMessageType('AttributeValue', (_message.Message,), {
    'DESCRIPTOR' : _ATTRIBUTEVALUE,
    '__module__' : 'infinite_tracing_pb2'
    # @@protoc_insertion_point(class_scope:com.newrelic.trace.v1.AttributeValue)
    })
  _sym_db.RegisterMessage(AttributeValue)

  RecordStatus = _reflection.GeneratedProtocolMessageType('RecordStatus', (_message.Message,), {
    'DESCRIPTOR' : _RECORDSTATUS,
    '__module__' : 'infinite_tracing_pb2'
    # @@protoc_insertion_point(class_scope:com.newrelic.trace.v1.RecordStatus)
    })
  _sym_db.RegisterMessage(RecordStatus)


  _SPAN_INTRINSICSENTRY._options = None
  _SPAN_USERATTRIBUTESENTRY._options = None
  _SPAN_AGENTATTRIBUTESENTRY._options = None

  _INGESTSERVICE = _descriptor.ServiceDescriptor(
    name='IngestService',
    full_name='com.newrelic.trace.v1.IngestService',
    file=DESCRIPTOR,
    index=0,
    serialized_options=None,
    serialized_start=727,
    serialized_end=828,
    methods=[
    _descriptor.MethodDescriptor(
      name='RecordSpan',
      full_name='com.newrelic.trace.v1.IngestService.RecordSpan',
      index=0,
      containing_service=None,
      input_type=_SPAN,
      output_type=_RECORDSTATUS,
      serialized_options=None,
    ),
  ])
  _sym_db.RegisterServiceDescriptor(_INGESTSERVICE)

  DESCRIPTOR.services_by_name['IngestService'] = _INGESTSERVICE

  # @@protoc_insertion_point(module_scope)


"""
Show Event outputs.
"""


import json
import sys
import traceback

try:
    import dateutil.parser
except ImportError:
    def date_string(ds, fmt=''):
        return ds
else:
    def date_string(ds, fmt='%Y-%m-%d %H:%M:%S.%f'):
        d = dateutil.parser.parse(ds).astimezone(dateutil.tz.tzutc())
        return d.strftime(fmt)


def display(message):
    print('{} - {}'.format(date_string(message['time']), message['event_type']))
    if message.get('event'):
        event = json.loads(message['event'])
        for k in sorted(event):
            print('\t{}: {}'.format(k, event[k]))
    print()

while 1:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        obj = json.loads(line)
        display(obj)
    except Exception:
        traceback.print_exc()
        continue

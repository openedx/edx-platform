#!/bin/bash

# Used in prod config
export DD_DJANGO_USE_HANDLER_RESOURCE_FORMAT=true
export DD_DJANGO_INSTRUMENT_MIDDLEWARE=false


ddtrace-run "$@"

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Testing encoding on second line does not cause violation
message = "<script>alert('XSS');</script>"
x = "<string>{}</strong>".format(message)

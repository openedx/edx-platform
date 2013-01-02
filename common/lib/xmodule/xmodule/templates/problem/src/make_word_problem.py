#!/usr/bin/python
#
# example: python make_word_problem.py "word_example_problems" "Problem Written in Word: Examples"

import os, sys
import yaml
import base64, gzip

pre = sys.argv[1]
name = sys.argv[2]

outfn = pre + ".yaml"
sourcefn= pre + ".rtf.gz"
xmlfn= pre + ".xml"

source_code = base64.b64encode(open(sourcefn).read())

metadata = dict(display_name=name,
                source_processor_url="https://studio-input-filter.mitx.mit.edu/word2edx",
                source_code=source_code,
                source_code_encoding="base64/gzip",
                source_code_mimetype='application/msword',
                )

prob = dict(metadata=metadata,
            data=open(xmlfn).read(),
            children=[],
            )

open(outfn,'w').write(yaml.dump(prob))

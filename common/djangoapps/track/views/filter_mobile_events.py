#!/usr/bin/python

import sys, getopt, json

def main(argv):
    def usage():
        print 'filter_mobile_events.py -i <inputfile> -o <outputfile>'
        sys.exit()

    input_filename = None
    output_filename = None
    json_filter = {"event_source": "mobile"}
    try:
        opts, args = getopt.getopt(argv, "hi:o:")
        if len(opts) != 2:
            usage()

        for opt, arg in opts:
            if opt == '-h':
                usage()
            elif opt in ("-i"):
                input_filename = arg
                print 'Input file is', input_filename
            elif opt in ("-o"):
                output_filename = arg
                print 'Output file is', output_filename

    except getopt.GetoptError:
        usage()

    with open(input_filename, "r") as inputfile:
        with open(output_filename, "w") as outputfile:
            lines_copied = 0
            lines_skipped = 0
            for line in inputfile:
                line_json = json.loads(line)
                if all(item in line_json.items() for item in json_filter.items()):
                    outputfile.write(line)
                    lines_copied = lines_copied + 1
                else:
                    lines_skipped = lines_skipped + 1

    print 'Lines skipped:', lines_skipped, 'Lines copied:', lines_copied

if __name__ == "__main__":
   main(sys.argv[1:])
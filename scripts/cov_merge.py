import os
import sys
from textwrap import dedent
from bs4 import BeautifulSoup
import multiprocessing


FIRST = dedent(
    '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
    <html>
    <head>
    <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
    <title>CMS Python Test Coverage Report</title>
    <link rel='stylesheet' href='https://googledrive.com/host/0B0bNP036USIkLWdyRFFlSDNzZHc/style.css' type='text/css'>

    <script type='text/javascript' src='https://googledrive.com/host/0B0bNP036USIkLWdyRFFlSDNzZHc/jquery.min.js'></script>
    <script type='text/javascript' src='https://googledrive.com/host/0B0bNP036USIkLWdyRFFlSDNzZHc/jquery.tablesorter.min.js'></script>
    <script type='text/javascript' src='https://googledrive.com/host/0B0bNP036USIkLWdyRFFlSDNzZHc/jquery.hotkeys.js'></script>
    <script type='text/javascript' src='https://googledrive.com/host/0B0bNP036USIkLWdyRFFlSDNzZHc/coverage_html.js'></script>
    <script type='text/javascript' charset='utf-8'>
        jQuery(document).ready(coverage.index_ready);
    </script>
    <style>
        .hide-content {
            display: none;
        }
    </style>
    </head>''')


LAST = dedent(
    '''<script type="text/javascript">
    String.prototype.replaceAll = function (find, replace) {
        var str = this;
        return str.replace(new RegExp(find, 'g'), replace);
    };

    $('.file a').click(function(event) {
        event.preventDefault();
        var id = "#" + event.currentTarget.innerHTML.replaceAll('/', '_');
        if (typeof window.last_source_file_id !== 'undefined'){
            $(window.last_source_file_id).addClass( "hide-content" );
        }
        window.last_source_file_id = id;
        $(id).removeClass( "hide-content" );
        location.href = id;
    });
    </script>

    </body>
    </html>''')


class ReportMerge(object):
    """Merge multiple html coverage reports"""

    DESTINATION = os.path.join(os.environ['HOME'], 'results', os.environ['TDDIUM_SESSION_ID'], 'session')

    def __init__(self):
        self.reports_dir = os.path.realpath(__file__).replace("scripts/cov_merge.py", "reports/")

    def _files(self, cover_path):
        """
        Return list of file paths in `cover_path`. `cover_path` will be something like */reports/cms/cover
        """
        include = lambda f: f.endswith('.html') and os.path.basename(f) != 'index.html'
        return [os.path.join(cover_path, f) for f in os.listdir(cover_path) if include(f)]

    def merge(self, modules, output_file=None):
        """
        Merge reports for `modules`

        Arguments:
            output_file (str): name of output report file -- only used for bok_choy reports

        """
        for module in modules:
            for (path, _, _) in os.walk(os.path.join(self.reports_dir, module)):
                if os.path.basename(path) == 'cover':
                    self.merge_report(path, output_file)

    def merge_report(self, path, output_file):
        """
        Collect multiple parts of a report and join them to create a single report.

        Arguments:
            path (str): path where multiple files are located to be merged
            output_file (str): name of output report file -- only used for bok_choy reports

        """
        content = list()

        # Extract total coverage percentage and file links table
        index_html = os.path.join(path, 'index.html')
        with open(index_html) as index_file:
            soup = BeautifulSoup(index_file)
            total_percentage = soup.find('div', id='header')
            total_percentage.find('img').decompose()
            index_table = soup.find('div', id='index')

        # Extract file names
        files = [os.path.join(path, name['href']) for name in index_table.find_all('a')]
        if not files:
            return

        print 'Merging Report for {}'.format(path)

        # Collect different parts of html report
        content.append(FIRST)
        content.append('<body>')
        content.append(str(total_percentage))
        content.append(str(index_table))
        for html in files:
            content.append(self._html_content(html))

        content.append(LAST)

        if output_file:
            report_path = os.path.join(self.DESTINATION, output_file)
        else:
            report_filename = path.split('reports/')[1].split('/cover')[0].replace('/', '_')
            report_path = os.path.join(self.DESTINATION, report_filename + '_coverage.html')

        # Write everything to single report file
        with open(report_path, 'w') as report_file:
            report_file.write('\n'.join(content))

        print 'Report Merged for {}'.format(path)

    def _html_content(self, html):
        """
        Returns html tags of interest for file specified by `html`
        """
        # Create id for each link in file links table
        navigate_div_id = os.path.basename(html).split('.')[0].replace('/', '_')
        navigate_div_start = "<div id='{}' class='hide-content'>\n".format(navigate_div_id)
        navigate_div_close = "\n</div>".format(navigate_div_id)

        content = list()
        content.append(navigate_div_start)

        with open(html) as html_file:
            soup = BeautifulSoup(html_file)
            header = soup.find('div', id='header')
            header.find('img').decompose()
            source = soup.find('div', id='source')
            source_img = source.find('img')
            if source_img:
                source_img.decompose()

            content.append(str(header))
            content.append(str(source))

        content.append(navigate_div_close)

        return '\n'.join(content)

if __name__ == '__main__':
    args = sys.argv

    if 'bok_choy' in args[1]:
        paths = ['bok_choy']
        rm = ReportMerge()
        rm.merge(paths, output_file=args[2])
    elif 'unit' in args[1]:
        paths = ['common', 'cms', 'lms']
        for pth in paths:
            rm = ReportMerge()
            mp = multiprocessing.Process(target=rm.merge, args=([pth],))
            mp.start()
    else:
        print 'Unsupported Test Suit'

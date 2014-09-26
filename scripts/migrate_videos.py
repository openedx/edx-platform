#!/usr/bin/env python
import tarfile
import sys
from xml.etree.cElementTree import fromstring, tostring
import io
import os.path
import getpass
import requests
import argparse
import pprint
import time


class MissingVideo(Exception):
    pass


class Migrator(object):
    studio_url = 'https://studio.edx.org'
    val_url = 'https://studio.edx.org/api/val/v0'

    # studio_url = 'http://studio.mobile3.m.sandbox.edx.org'
    # val_url = 'http://studio.mobile3.m.sandbox.edx.org/api/val/v0'

    def __init__(self, course_id=None):
        self.course_id = course_id
        self.sess = requests.Session()
        self.course_vids = []


    def get_csrf(self, url):
        response = self.sess.get(url)
        csrf = response.cookies['csrftoken']
        return {'X-CSRFToken': csrf, 'Referer': url}


    def get_course_youtube_videos(self, course_id=None):
        course_id = course_id or self.course_id
        url = self.val_url + '/videos/'
        videos = self.sess.get(url, params={'course': self.course_id}).json()
        # HACK for messed up ids
        if self.course_id == 'MITx/6.002x_4x/3T2014' and not videos:
            videos = self.get_course_youtube_videos('MITx/6.002_4x/3T2014')
        self.course_vids = videos

    def match_video(self, youtube_id=None, client_id=None):
        for vid in self.course_vids:
            if youtube_id:
                for enc in vid['encoded_videos']:
                    if enc['profile'] == 'youtube' and enc['url'].strip() == youtube_id:
                        return vid['edx_video_id']
            if vid['client_video_id'] == client_id:
                return vid['edx_video_id']



    def import_tgz(self, tgz):
        url = '{}/import/{}'.format(self.studio_url, self.course_id)
        print 'Importing {} to {} from {}'.format(self.course_id, url, tgz)
        headers = self.get_csrf(url)
        headers['Accept'] = 'application/json'
        with open(tgz, 'rb') as upload:
            filename = os.path.basename(tgz)
            start = 0
            upload.seek(0, 2)
            end = upload.tell()
            upload.seek(0, 0)

            while 1:
                start = upload.tell()
                data = upload.read(2 * 10**7)
                if not data:
                    break
                stop = upload.tell() - 1
                files = [
                    ('course-data', (filename, data, 'application/x-gzip'))
                ]
                headers['Content-Range'] = crange = '%d-%d/%d' % (start, stop, end)
                print crange, 
                response = self.sess.post(url, files=files, headers=headers)
                print response.status_code
            # now check import status
            print 'Checking status'
            import_status_url = '{}/import_status/{}/{}'.format(self.studio_url, self.course_id, filename)
            status = 0
            while status != 4:
                status = self.sess.get(import_status_url).json()['ImportStatus']
                print status,
                time.sleep(3)
            print 'Uploaded'

    def login(self, email, password):
        signin_url = '%s/signin' % self.studio_url
        headers = self.get_csrf(signin_url)

        login_url = '%s/login_post' % self.studio_url
        print 'Logging in to %s' % self.studio_url

        response = self.sess.post(login_url, {
            'email': email,
            'password': password,
            'honor_code': 'true'
            }, headers=headers).json()
        
        if not response['success']:
            raise Exception(str(response))


    def export_tgz(self):
        export_url = '{studio_url}/export/{course}'.format(
                    studio_url=self.studio_url,
                    course=self.course_id)

        print 'Exporting from %s' % export_url
        response = self.sess.get(
            export_url,
            params={'_accept': 'application/x-tgz'},
            headers={'Referer': export_url},
            stream=True)
        print response.status_code
        return response


    def get_id(self, path):
        split = path.split('/')[-1]
        return split.split('_')[0]


    def process_video(self, xml):
        source = xml.get('source') or ''
        edx_video_id = xml.get('edx_video_id')
        youtube_id = xml.get('youtube_id_1_0')

        for elt in xml.findall('./source'):
            src = elt.get('src')
            if src:
                edx_video_id = self.get_id(src)
                source = src
                break
        else:
            if source:
                edx_video_id = self.get_id(source)
        # import pdb;pdb.set_trace()
        if self.course_id.startswith(('MITx', 'DelftX', 'LouvainX/Louv1.1x')) or not edx_video_id:
            # for mit, the filename will be the client id
            client_id = edx_video_id
            vid = self.match_video(client_id=client_id, youtube_id=youtube_id)
            if vid:
                edx_video_id = vid
            elif source:
                # try different client id
                source = source.split('/')[-1].rsplit('.', 1)[0]
                vid = self.match_video(client_id=source)
                if not vid:
                    # try again!
                    vid = self.match_video(client_id=source.replace('_', '-'))
                if vid:
                    edx_video_id = vid
                else:
                    raise MissingVideo(source)
            else:
                raise MissingVideo(source)

        if edx_video_id:
            print 'Found %s' % edx_video_id
            if youtube_id:
                for vid in self.course_vids:
                    if vid['edx_video_id'] == edx_video_id:
                        for enc in vid['encoded_videos']:
                            if enc['profile'] == 'youtube':
                                if enc['url'].strip() != youtube_id:
                                    print 'youtube mismatch', edx_video_id, youtube_id, enc['url']
                        break
            xml.set('edx_video_id', edx_video_id)

            xml = tostring(xml)
            return xml

    def process_export(self, infile, outfile):
        kwargs = {}
        fname = infile
        if hasattr(infile, 'read'):
            kwargs['fileobj'] = infile
            fname = ''
        intar = tarfile.TarFile.gzopen(fname, **kwargs)
        outtar = tarfile.TarFile.gzopen(outfile, mode='w')

        has_course = bool(self.course_id)

        not_found = []

        if has_course:
            self.get_course_youtube_videos()

        for finfo in intar:
            if not has_course:
                course_xml = intar.extractfile(os.path.join(finfo.name, 'course.xml')).read()
                course_xml = fromstring(course_xml)
                self.course_id = '%s/%s/%s' % (course_xml.get('org'), course_xml.get('course'), course_xml.get('url_name'))
                print '\nFound course.xml for %s' % self.course_id
                print '-' * 40
                has_course = True
                self.get_course_youtube_videos()

            infile = intar.extractfile(finfo.name)
            if '/video/' in finfo.name:
                xml = fromstring(infile.read())
                try:
                    new_xml = self.process_video(xml)
                except MissingVideo as e:
                    new_xml = None
                    not_found.append(xml)

                if new_xml:
                    infile = io.BytesIO(new_xml)
                    finfo.size = len(new_xml)
                else:
                    infile.seek(0)
            outtar.addfile(finfo, fileobj=infile)

        if not_found:
            print 'Missing videos:'
            for xml in not_found:
                print '{}\t"{}"'.format(xml.get('youtube_id_1_0'), xml.get('display_name', u'').encode('utf8'))


    def migrate_many(self, courses):
        for line in courses:
            course_id = line.strip()
            if course_id.startswith('#') or not course_id:
                continue

            self.course_id = course_id
            response = self.export_tgz()


            infile = io.BytesIO(response.content)

            outfile = '%s.tar.gz' % self.course_id.replace('/', '_')
            print 'Saving to %s' % outfile
            self.process_export(infile, outfile)
            response = infile = None

            if raw_input('\n\nImport course? [y/N] ').lower().strip() == 'y':
                self.import_tgz(outfile)


def main():
    parser = argparse.ArgumentParser()
    parser.usage = '''
    {cmd} -c org/course/run [-e email@domain]
or
    {cmd} -f path/to/exported.tar.gz
'''.format(cmd=sys.argv[0])
    parser.description = 'prints counts of xblock types per course'
    parser.add_argument('-c', '--course', help='Course', default='')
    parser.add_argument('-i', '--courses', type=argparse.FileType('rb'), default=None)
    parser.add_argument('-f', '--export', help='Path to export file', default='')
    parser.add_argument('-e', '--email', help='Studio email address', default='')

    args = parser.parse_args()
    if not (args.export or args.course or args.courses):
        parser.print_usage()
        return -1

    email = args.email or raw_input('Studio email address: ')
    password = getpass.getpass('Studio password: ')

    mig = Migrator()
    mig.login(email, password)

    if args.export:
        print 'Processing exported archive %s' % args.export
        infile = args.export
        indir, fname = os.path.split(infile)
        outfile = os.path.join(indir, 'NEW_' + fname)
        print '\nSaving to %s' % outfile
        mig.process_export(infile, outfile)
    elif args.course or args.courses:

        courses = args.courses or [args.course]
        mig.migrate_many(courses)


if __name__ == '__main__':
    sys.exit(main())

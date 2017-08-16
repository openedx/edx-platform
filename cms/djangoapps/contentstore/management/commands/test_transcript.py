from django.core.management.base import BaseCommand, CommandError
from edxval.api import create_update_video_transcript


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=int)
        parser.add_argument('file_data', type=file)

    def handle(self, *args, **options):
        video_id = options['video_id']
        file_data = options['file_data']
        from nose.tools import set_trace; set_trace()
        transcript_url = create_update_video_transcript(video_id=video_id, language='en', file_data=file_data)
        print transcript_url

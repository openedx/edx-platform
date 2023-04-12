import logging
import json
import requests
from django.conf import settings
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
TOLERANCE = 0.5


class EdenAIImageExplicitContent:
    def __init__(self):
        self.url = "https://api.edenai.run/v2/image/explicit_content"
        self.headers = {
            "Authorization": f"Bearer {settings.EDEN_API_KEY}"
        }
        self.providers = ",".join(settings.EDEN_PROVIDERS)

    def detect_explicit_content(self, show_original_response, file_url=None, file=None):
        json_payload = {
            "providers": self.providers,
            "show_original_response": show_original_response,
        }
        if file_url:
            json_payload['file_url'] = file_url
        response = requests.post(self.url, json=json_payload, headers=self.headers)
        return json.loads(response.text)

    def nsfw_labels(self, nsfw_dict) -> list:
        labels = []
        for provider, result in nsfw_dict.items():
            nsfw_labels = [item['label'] for item in result['items']]
            labels.append(nsfw_labels)
        return labels

    def nsfw_likelihood(self, responses) -> int:
        total = 0
        for key, value in responses.items():
            total = total + value['nsfw_likelihood']
        return total

    def get_nsfw_likelihood(self, file=None, file_url=None, show_original_response=False) -> tuple:
        responses = self.detect_explicit_content(show_original_response, file=file, file_url=file_url)
        self.nsfw_labels(responses)
        return self.nsfw_likelihood(responses), self.nsfw_labels(responses)

    def has_clean_html(self, html):

        soup = BeautifulSoup(html, 'html.parser')
        img_tags = soup.find_all('img')

        src_list = [img['src'] for img in img_tags]

        for src in src_list:
            total, labels = self.get_nsfw_likelihood(file_url=src)
            log.info(f""
                     f"\n\n\n\n\n\n"
                     f"============================================================================================\n"
                     f"This image has a total of {total} nsfw likelihood score. Labels: {labels} \n"
                     f"============================================================================================"
                     f"\n\n\n\n\n\n"
                     )
            if total > TOLERANCE:
                return False
        return True

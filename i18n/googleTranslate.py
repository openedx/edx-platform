import urllib, urllib2, json

# Google Translate API
# see https://code.google.com/apis/language/translate/v2/getting_started.html
#
#
# usage: translate('flower', 'fr') => 'fleur'


# --------------------------------------------
# Translation limit = 100,000 chars/day (request submitted for more)
# Limit of 5,000 characters per request
# This key is personally registered to Steve Strassmann
#
#KEY = 'AIzaSyCDapmXdBtIYw3ofsvgm6gIYDNwiVmSm7g'
KEY = 'AIzaSyDOhTQokSOqqO-8ZJqUNgn12C83g-muIqA'

URL = 'https://www.googleapis.com/language/translate/v2'

SOURCE = 'en'                         # source: English

TARGETS = ['zh-CN', 'ja', 'fr', 'de', # tier 1: Simplified Chinese, Japanese, French, German
           'es', 'it',                # tier 2: Spanish, Italian
           'ru']                      # extra credit: Russian


def translate (string, target):
    return extract(fetch(string, target))


# Ask Google to translate string to target language
#   string: English string
#   target: lang (e.g. 'fr', 'cn')
# Returns JSON object
def fetch (string, target, url=URL, key=KEY, source=SOURCE):
    data = {'key':key,
            'q':string,
            'source': source,
            'target':target}
    fullUrl = '%s?%s' % (url, urllib.urlencode(data))
    try:
        response = urllib2.urlopen(fullUrl)
        return json.loads(response.read())
    except urllib2.HTTPError as err:
        if err.code == 403:
            print "***"
            print "*** Possible daily limit exceeded for Google Translate:"
        print "***"
        print "***", json.loads("".join(err.readlines()))
        print "***"
        raise



# Extracts a translated result from a json object returned from Google
def extract (response):
    data = response['data']
    translations = data['translations']
    first = translations[0]
    result = first.get('translated_text', None)
    if result != None:
        return result
    else:
        result = first.get('translatedText', None)
        if result != None:
            return result
        else:
            raise Exception("Could not read translation from: %s" % translations)

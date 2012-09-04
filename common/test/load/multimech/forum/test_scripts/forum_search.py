import random
import time
import requests
import random

# NOTE: Script relies on this user being signed up for cs188, and cs188 having started.
email = 'victor+test@edx.org'
password = 'abc123'

machine = 'load-test-001.m.edx.org'
protocol = 'http://'

auth = ('anant', 'agarwal')

def url(path):
    """
    path should be something like '/', '/courses'
    """
    return ''.join([protocol, machine, path])

class Transaction(object):
    def __init__(self):
        # Load / to get csrf cookie
        s = requests.session(auth=auth)
        r = s.get(url('/'))
        # Need to set the header as well as the cookie.  Why? No one knows.
        headers = {'X-CSRFToken' : s.cookies['csrftoken']}
        # login
        r = s.post(url('/login'), data={'email' : email, 'password': password}, headers=headers)
        print r.text
        self.session = s

    def run(self):
        s = self.session
        path = '/courses/BerkeleyX/CS188/fa12/discussion/forum/?tags=' + random.choice(WORDS)
        r = s.get(url(path))
        assert r.status_code == requests.codes.ok

if __name__ == '__main__':
    trans = Transaction()
    print "running..."
    trans.run()
    print "run done"


WORDS = """    Adroit
    Anthropomorphism
    Antiquate
    Aphorism
    Aplomb
    Apoplectic
    Apothecary
    Argy-Bargy
    Bamboozle
    Bauble
    Boing
    Boogie-woogie
    Bulbous Bouffant
    Bunkum
    Cacophony
    Chechnya
    Chiropodist
    Collieshangie
    Collywobbles
    Combustible
    Corpuscle
    Corroborated
    Dawdle
    Decoupage
    Deliquesce
    Dillydally
    Diphthong
    Dirigible
    Doppelganger
    Dupe
    Effervescent
    Efficacious
    Elegiac
    Enunciation
    Erudite
    Fastidious
    Fiddle-Faddle
    Finagle
    Fissure
    Flapjacks
    Flibbertigibbet
    Flimflam
    Foible
    Frenetic
    Frigorific
    Gangly
    Giblets
    Ginkgo Biloba
    Gobbledygook
    Gooey
    Gormandize
    Grotesque
    Haberdashery
    Heebee Jeebees
    Hemidemisemiquaver
    Hoary
    Hobbledehoy
    Hodgepodge
    Hoity-Toity
    Hornswoggle
    Hullabaloo
    Humdinger
    Insouciance
    Iridescence
    Jambalaya
    Jejune
    Jujube
    Juxtapose
    Kumquat
    Lackadaisical
    Ladle
    Lampoon
    Lilliputian
    Lollygag
    Look-see
    Luminescence
    Mahatma
    Malarkey
    Marmoset
    Marsupial
    Masticate
    Matriculate
    Medulla Oblongata
    Micturate
    Mnemonic
    Mulch
    Naugahyde
    Namby-pamby
    Newfangled
    Odoriferous
    Ointment
    Ostracize
    Ostensibly
    Ostentatious
    Oyster
    Palpitation
    Percolate
    Perfidious
    Persnickety
    Perturbable
    Phalange
    Pheromone
    Phlegmatic
    Pitter-Patter
    Pizzazz
    Platitudinous
    Poignant
    Pointillism
    Polliwog
    Polypeptides
    Phantasmagorical
    Pneumatic
    Prosaic
    Pubescent
    Pugilistic
    Pungent
    Pusillanimous
    Qualm
    Quench
    Quid Pro Quo
    Quiddity
    Quidnunc
    Quiescent
    Rarer
    Razzle-dazzle
    Razzmatazz
    Regurgitate
    Resplendent
    Reticent
    Rhododendron
    Salve
    Sassafras
    Scallywag
    Scaramouch
    Scatological
    Schadenfreude
    Schism
    Schmooze
    Schnitzel
    Schoolmarm
    Scrod
    Scrumptious
    Sesquipedalian
    Shambles
    Shard
    Shenanigan
    Shiatsu
    Shih Tzu
    Shirk
    Sisyphean
    Skedaddle
    Skewer
    Skirmish
    Sluice
    Smarmy
    Smatter
    Smegma
    Smorgasbord
    Smudge
    Sniggle
    Soiree
    Soliloquy
    Spiel
    Splendiferous
    Sporadic
    Spritz
    Spume
    Spurious
    Sputter
    Squeamish
    Squelch
    Stalagmite
    Sumptuous
    Supercilious
    Swizzle Stick
    Syzygy
    Szechuan
    Tchotchke
    Thespian
    Tiramisu
    Tomfoolery
    Troglodyte
    Trudge
    Ubiquitous
    Unctuous
    Usury
    Uvula
    Vacillate
    Veritable
    Virulent
    Whittle
    Worcestershire
    Yucatan
""".split()

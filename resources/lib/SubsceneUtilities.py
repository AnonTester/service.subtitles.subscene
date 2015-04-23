# -*- coding: utf-8 -*-
import gzip
import time
from StringIO import StringIO
import xbmc
import urllib2
import re

LANGUAGES = (
    ("Albanian", "29", "sq", "alb", "0", 30201, 1),
    ("Arabic", "12", "ar", "ara", "1", 30202, 2),
    ("Belarusian", "0", "hy", "arm", "2", 30203, 68),
    ("Bosnian", "10", "bs", "bos", "3", 30204, 60),
    ("Bulgarian", "33", "bg", "bul", "4", 30205, 5, 6),
    ("Catalan", "53", "ca", "cat", "5", 30206, 49),
    ("Chinese", "17", "zh", "chi", "6", 30207, 7),
    ("Croatian", "38", "hr", "hrv", "7", 30208, 8),
    ("Czech", "7", "cs", "cze", "8", 30209, 9),
    ("Danish", "24", "da", "dan", "9", 30210, 10),
    ("Dutch", "23", "nl", "dut", "10", 30211, 11, 12),
    ("English", "2", "en", "eng", "11", 30212, 13),
    ("Estonian", "20", "et", "est", "12", 30213, 16),
    ("Persian", "52", "fa", "per", "13", 30247, 46),
    ("Finnish", "31", "fi", "fin", "14", 30214, 17),
    ("French", "8", "fr", "fre", "15", 30215, 18),
    ("German", "5", "de", "ger", "16", 30216, 19, 15),
    ("Greek", "16", "el", "ell", "17", 30217, 21),
    ("Hebrew", "22", "he", "heb", "18", 30218, 22),
    ("Hindi", "42", "hi", "hin", "19", 30219, 51),
    ("Hungarian", "15", "hu", "hun", "20", 30220, 23, 24),
    ("Icelandic", "6", "is", "ice", "21", 30221, 25),
    ("Indonesian", "0", "id", "ind", "22", 30222, 44),
    ("Italian", "9", "it", "ita", "23", 30224, 26),
    ("Japanese", "11", "ja", "jpn", "24", 30225, 27),
    ("Korean", "4", "ko", "kor", "25", 30226, 28),
    ("Latvian", "21", "lv", "lav", "26", 30227, 29),
    ("Lithuanian", "0", "lt", "lit", "27", 30228, 43),
    ("Macedonian", "35", "mk", "mac", "28", 30229, 48),
    ("Malay", "0", "ms", "may", "29", 30248, 50, 64),
    ("Norwegian", "3", "no", "nor", "30", 30230, 30),
    ("Polish", "26", "pl", "pol", "31", 30232, 31),
    ("Portuguese", "32", "pt", "por", "32", 30233, 32),
    ("PortugueseBrazil", "48", "pb", "pob", "33", 30234, 4),
    ("Romanian", "13", "ro", "rum", "34", 30235, 33),
    ("Russian", "27", "ru", "rus", "35", 30236, 34),
    ("Serbian", "36", "sr", "scc", "36", 30237, 35),
    ("Slovak", "37", "sk", "slo", "37", 30238, 36),
    ("Slovenian", "1", "sl", "slv", "38", 30239, 37),
    ("Spanish", "28", "es", "spa", "39", 30240, 38),
    ("Swedish", "25", "sv", "swe", "40", 30242, 39),
    ("Thai", "0", "th", "tha", "41", 30243, 40),
    ("Turkish", "30", "tr", "tur", "42", 30244, 41),
    ("Ukrainian", "46", "uk", "ukr", "43", 30245, 56),
    ("Vietnamese", "51", "vi", "vie", "44", 30246, 45),
    ("BosnianLatin", "10", "bs", "bos", "100", 30204, 60),
    ("Farsi", "52", "fa", "per", "13", 30247, 46),
    ("English (US)", "2", "en", "eng", "100", 30212, 13),
    ("English (UK)", "2", "en", "eng", "100", 30212, 13),
    ("Portuguese (Brazilian)", "48", "pt-br", "pob", "100", 30234, 4),
    ("Portuguese (Brazil)", "48", "pb", "pob", "33", 30234, 4),
    ("Portuguese-BR", "48", "pb", "pob", "33", 30234, 4),
    ("Brazilian", "48", "pb", "pob", "33", 30234, 4),
    ("Español (Latinoamérica)", "28", "es", "spa", "100", 30240, 38),
    ("Español (España)", "28", "es", "spa", "100", 30240, 38),
    ("Spanish (Latin America)", "28", "es", "spa", "100", 30240, 38),
    ("Español", "28", "es", "spa", "100", 30240, 38),
    ("SerbianLatin", "36", "sr", "scc", "100", 30237, 35),
    ("Spanish (Spain)", "28", "es", "spa", "100", 30240, 38),
    ("Chinese (Traditional)", "17", "zh", "chi", "100", 30207, 7),
    ("Chinese (Simplified)", "17", "zh", "chi", "100", 30207, 7))

subscene_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}


def get_language_info(language):
    if language in subscene_languages:
        language = subscene_languages[language]

    for lang in LANGUAGES:
        if lang[0] == language:
            return {'name': lang[0], '2let': lang[2], '3let': lang[3], '_': lang[5]}


def get_language_codes(languages):
    codes = {}
    for lang in LANGUAGES:
        if lang[3] in languages:
            try:
                codes[str(lang[6])] = 1
                codes[str(lang[7])] = 1
            except IndexError:
                pass

    keys = codes.keys()
    return keys


subscene_start = time.time()


def log(module, msg):
    global subscene_start
    xbmc.log((u"### [%s] %f - %s" % (module, time.time()-subscene_start, msg,)).encode('utf-8'), level=xbmc.LOGDEBUG)


def geturl(url, cookies=None):
    log(__name__, "Getting url: %s" % url)
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        if cookies:
            request.add_header('Cookie', cookies)
        log(__name__, "request done")
        response = urllib2.urlopen(request)
        log(__name__, "request done")
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO( response.read())
            f = gzip.GzipFile(fileobj=buf)
            content = f.read()
        else:
            content = response.read()
        log(__name__, "read done")
        #Fix non-unicode characters in movie titles
        strip_unicode = re.compile("([^-_a-zA-Z0-9!@#%&=,/'\";:~`\$\^\*\(\)\+\[\]\.\{\}\|\?<>\\]+|[^\s]+)")
        content = strip_unicode.sub('', content)
        return_url = response.geturl()
        log(__name__, "fetching done")
    except:
        log(__name__, "Failed to get url: %s" % url)
        content = None
        return_url = None
    return content, return_url

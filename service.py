# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import shutil
import unicodedata
import re
import string
import difflib
import HTMLParser

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib')).decode("utf-8")
__temp__ = xbmc.translatePath(os.path.join(__profile__, 'temp')).decode("utf-8")

sys.path.append(__resource__)

from SubsceneUtilities import log, geturl, get_language_info

main_url = "http://subscene.com"

# Seasons as strings for searching
seasons = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
seasons = seasons + ["Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
                     "Eighteenth", "Nineteenth", "Twentieth"]
seasons = seasons + ["Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
                     "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"]

movie_season_pattern = "<a href=\"(/subtitles/[^\"]*)\">([^<]+)\((\d{4})\)</a>\s+</div>\s+<div class=\"subtle\">\s+(\d+)"
# group(1) = link, group(2) = movie_season_title,  group(3) = year, group(4) = num subtitles

subtitle_pattern = "<a href=\"(/subtitles/[^\"]+)\">\s+<div class=\"visited\">\s+<span class=\"[^\"]+ (\w+-icon)\">\s+([^\r\n\t]+)\s+</span>\s+\
<span>\s+([^\r\n\t]+)\s+</span>\s+</div>\s+</a>\s+</td>\s+<td class=\"[^\"]+\">\s+[^\r\n\t]+\s+</td>\s+<td class=\"([^\"]+)\">"
# group(1) = downloadlink, group(2) = qualitycode, group(3) = language, group(4) = filename, group(5) = hearing impaired

downloadlink_pattern = "...<a href=\"(.+?)\" rel=\"nofollow\" onclick=\"DownloadSubtitle"
# group(1) = link


def find_movie(content, title, year):
    url_found = None
    h = HTMLParser.HTMLParser();
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        found_title = matches.group(2)
        found_title = h.unescape(found_title)
        log(__name__, "Found movie on search page: %s (%s)" % (found_title, matches.group(3)))
        if string.find(string.lower(found_title), string.lower(title)) > -1:
            if matches.group(3) == year:
                log(__name__, "Matching movie found on search page: %s (%s)" % (found_title, matches.group(3)))
                url_found = matches.group(1)
                break
    return url_found


def find_tv_show_season(content, tvshow, season):
    url_found = None
    possible_matches = []
    all_tvshows = []

    h = HTMLParser.HTMLParser();
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        found_title = matches.group(2)
        found_title = h.unescape(found_title)

        log(__name__, "Found tv show season on search page: %s" % (found_title.decode("utf-8")))
        s = difflib.SequenceMatcher(None, string.lower(found_title + ' ' + matches.group(3)), string.lower(tvshow))
        all_tvshows.append(matches.groups() + (s.ratio() * int(matches.group(4)),))
        if string.find(string.lower(found_title), string.lower(tvshow) + " ") > -1:
            if string.find(string.lower(found_title), string.lower(season)) > -1:
                log(__name__, "Matching tv show season found on search page: %s" % (found_title.decode("utf-8")))
                possible_matches.append(matches.groups())

        if len(possible_matches) > 0:
            possible_matches = sorted(possible_matches, key=lambda x: -int(x[3]))
            url_found = possible_matches[0][0]
            log(__name__, "Selecting matching tv show with most subtitles: %s (%s)" % (
                possible_matches[0][1].decode("utf-8"), possible_matches[0][3].decode("utf-8")))
        else:
            if len(all_tvshows) > 0:
                all_tvshows = sorted(all_tvshows, key=lambda x: -int(x[4]))
                url_found = all_tvshows[0][0]
                log(__name__, "Selecting tv show with highest fuzzy string score: %s (score: %s subtitles: %s)" % (
                    all_tvshows[0][1].decode("utf-8"), all_tvshows[0][4], all_tvshows[0][3].decode("utf-8")))

        return url_found


def append_subtitle(item):
    log(__name__, "append subtitle = %s" % item)
    listitem = xbmcgui.ListItem(label=item['lang']['name'],
                                label2=item['filename'],
                                iconImage=item['rating'],
                                thumbnailImage=item['lang']['2let'])

    listitem.setProperty("sync", 'false')  # not supported
    listitem.setProperty("hearing_imp", ("false", "true")[int(item["hearing_imp"]) != 0])

    ## below arguments are optional, it can be used to pass any info needed in download function
    ## anything after "action=download&" will be sent to addon once user clicks listed subtitle to downlaod
    url = "plugin://%s/?action=download&link=%s&filename=%s" % (__scriptid__,
                                                                item['link'],
                                                                item['filename'])
    ## add it to list, this can be done as many times as needed for all subtitles found
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False)


def getallsubs(content, allowed_languages, search_string=""):
    for matches in re.finditer(subtitle_pattern, content, re.IGNORECASE | re.DOTALL):
        languagefound = matches.group(3)
        language_info = get_language_info(languagefound)

        if language_info and language_info['3let'] in allowed_languages:
            link = main_url + matches.group(1)
            filename = matches.group(4)
            hearing_imp = (matches.group(5) == "a41")
            rating = '0'
            if matches.group(2) == "bad-icon":
                continue
            if matches.group(2) == "positive-icon":
                rating = '10'
            if search_string != "":
                if string.find(string.lower(filename), string.lower(search_string)) > -1:
                    append_subtitle({'rating': rating, 'filename': filename, 'sync': False, 'link': link,
                                     'lang': language_info, 'hearing_imp': hearing_imp})
            else:
                append_subtitle({'rating': rating, 'filename': filename, 'sync': False, 'link': link,
                                 'lang': language_info, 'hearing_imp': hearing_imp})


def prepare_search_string(s):
    # dots in words seem to trigger direct file search on subscene, so remove them (e.g. "Agents of S.H.I.E.L.D.")
    s = string.strip(s)
    s = string.strip(s,'.');
    s = re.sub(r'(\w)\.(?=\w)', r'\1', s)
    return s


def search_movie(title, year, languages):
    title = string.strip(title, '. ')
    search_string = prepare_search_string(title)

    log(__name__, "Search movie = %s" % search_string)
    url = main_url + "/subtitles/title?q=" + urllib.quote_plus(search_string)
    content, response_url = geturl(url)

    if content is not None:
        log(__name__, "Multiple movies found, searching for the right one ...")
        subspage_url = find_movie(content, title, year)
        if subspage_url is not None:
            log(__name__, "Movie found in list, getting subs ...")
            url = main_url + subspage_url
            content, response_url = geturl(url)
            if content is not None:
                getallsubs(content, languages)
        else:
            log(__name__, "Movie not found in list: %s" % title)
            if string.find(string.lower(title), "&") > -1:
                title = string.replace(title, "&", "and")
                log(__name__, "Trying searching with replacing '&' to 'and': %s" % title)
                subspage_url = find_movie(content, title, year)
                if subspage_url is not None:
                    log(__name__, "Movie found in list, getting subs ...")
                    url = main_url + subspage_url
                    content, response_url = geturl(url)
                    if content is not None:
                        getallsubs(content, languages)
                else:
                    log(__name__, "Movie not found in list: %s" % title)


def search_tvshow(tvshow, season, episode, languages):
    tvshow = string.strip(tvshow, '. ')
    search_string = prepare_search_string(tvshow)
    search_string += " - " + seasons[int(season)] + " Season"

    log(__name__, "Search tvshow = %s" % search_string)
    url = main_url + "/subtitles/title?q=" + urllib.quote_plus(search_string)
    content, response_url = geturl(url)

    if content is not None:
        log(__name__, "Multiple tv show seasons found, searching for the right one ...")
        tv_show_seasonurl = find_tv_show_season(content, tvshow, seasons[int(season)])
        if tv_show_seasonurl is not None:
            log(__name__, "Tv show season found in list, getting subs ...")
            url = main_url + tv_show_seasonurl
            content, response_url = geturl(url)
            if content is not None:
                search_string = "s%#02de%#02d" % (int(season), int(episode))
                getallsubs(content, languages, search_string)


def search(item):
    log(__name__, "Search_subscene= '%s'" % item)

    if len(item['tvshow']) == 0:
        search_movie(item['title'], item['year'], item['3let_language'])
    else:
        search_tvshow(item['tvshow'], item['season'], item['episode'], item['3let_language'])


def download(link, filename):
    subtitle_list = []
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass" ]

    content, response_url = geturl(link)
    match = re.compile(downloadlink_pattern).findall(content)
    if match:
        downloadlink = main_url + match[0]
        log(__name__, "Downloadlink %s" % downloadlink)
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0

        postparams = urllib.urlencode(
            {'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate,
             '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})

        class MyOpener(urllib.FancyURLopener):
            version = "User-Agent=Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)"

        my_urlopener = MyOpener()
        my_urlopener.addheader('Referer', link)
        log(__name__, "Fetching subtitles using url '%s' with referer header '%s' and post parameters '%s'" % (
            downloadlink, link, postparams))
        response = my_urlopener.open(downloadlink, postparams)
        local_tmp_file = os.path.join(__temp__, "subscene.xxx")
        packed = False
        if xbmcvfs.exists(__temp__):
            shutil.rmtree(__temp__)
        xbmcvfs.mkdirs(__temp__)
        try:
            log(__name__, "Saving subtitles to '%s'" % local_tmp_file)
            local_file_handle = open(local_tmp_file, "wb")
            local_file_handle.write(response.read())
            local_file_handle.close()

            #Check archive type (rar/zip/else) through the file header (rar=Rar!, zip=PK)
            myfile = open(local_tmp_file, "rb")
            myfile.seek(0)
            if myfile.read(1) == 'R':
                typeid = "rar"
                packed = True
                log(__name__, "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if myfile.read(1) == 'P':
                    typeid = "zip"
                    packed = True
                    log(__name__, "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
                    log(__name__, "Discovered a non-archive file")
            myfile.close()
            local_tmp_file = os.path.join(__temp__, "subscene." + typeid)
            os.rename(os.path.join(__temp__, "subscene.xxx"), local_tmp_file)
            log(__name__, "Saving to %s" % local_tmp_file)
        except:
            log(__name__, "Failed to save subtitle to %s" % local_tmp_file)

        if packed:
            xbmc.sleep(200)
            xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (local_tmp_file, __temp__,)).encode('utf-8'), True)

        for file in xbmcvfs.listdir(local_tmp_file)[1]:
            file = os.path.join(__temp__, file)
            if (os.path.splitext( file )[1] in exts):
                log(__name__, "=== returning subtitle file %s" % file)
                subtitle_list.append(file)

    return subtitle_list


def normalizeString(str):
    return unicodedata.normalize(
        'NFKD', unicode(unicode(str, 'utf-8'))
    ).encode('ascii', 'ignore')


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = paramstring
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


params = get_params()

if params['action'] == 'search':
    item = {}
    item['temp'] = False
    item['rar'] = False
    item['year'] = xbmc.getInfoLabel("VideoPlayer.Year")                             # Year
    item['season'] = str(xbmc.getInfoLabel("VideoPlayer.Season"))                    # Season
    item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                  # Episode
    item['tvshow'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))   # Show
    item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))  # try to get original title
    item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path
    item['3let_language'] = []

    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_2))

    if item['title'] == "":
        item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))      # no original title, get just Title

    if item['episode'].lower().find("s") > -1:                                      # Check if season is "Special"
        item['season'] = "0"                                                          #
        item['episode'] = item['episode'][-1:]

    if item['file_original_path'].find("http") > -1:
        item['temp'] = True

    elif item['file_original_path'].find("rar://") > -1:
        item['rar'] = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif item['file_original_path'].find("stack://") > -1:
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    search(item)

elif params['action'] == 'download':
    ## we pickup all our arguments sent from def Search()
    subs = download(params["link"], params["filename"])
    ## we can return more than one subtitle for multi CD versions, for now we are still working out how to handle that
    ## in XBMC core
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))  # send end of directory to XBMC
  
  
  
  
  
  
  
  
  
    

from urllib .request import urlopen
import re
import json
import time
import settings
import sys
import glob,os
import os.path
import shutil




from Ini_Parser import Ini_Parser


from collections import OrderedDict
from bs4 import BeautifulSoup as BS
from bottle import route, run, template, static_file, HTTPResponse, auth_basic


maplist_path="maplist.json"
#base_url="http://steamcommunity.com/workshop/browse/?appid=232090&searchtext=map&browsesort=mostrecent&p={page}"
base_url="https://steamcommunity.com/workshop/browse/?appid=232090&browsesort=mostrecent&section=readytouseitems&p={page}"
mapfile_extension = ".kfm"


r_id = re.compile("id=([0-9]+)")
r_rating = re.compile("sharedfiles/(.+?\.png)")

def usage():
    print("Usage: wsmap.py (--server|--sync)")

def get_url(page):
    return base_url.replace("{page}", str(page));

def get_maps(content):
    soup = BS(content, "html.parser")
    items = []
    divs = soup.find_all("div", class_="workshopItem")
    for div in divs:
        itemUrl=div.find("a")["href"]
        match=r_id.search(itemUrl)
        if not match:
            continue
        itemId = match.group(1)
        itemName = div.find("div", class_="workshopItemTitle").text
        itemAuthor = div.find("div", class_="workshopItemAuthorName").find("a").text
        ratingUrl = div.find("img", class_="fileRating")["src"]
        match=r_rating.search(ratingUrl)
        if not match:
            continue
        itemRating=match.group(1)
        itemPreviewUrl=div.find("img", class_="workshopItemPreviewImage")["src"]

        item=dict(url=itemUrl,
            id=itemId,
            name=itemName,
            author=itemAuthor,
            rating=itemRating,
            previewUrl=itemPreviewUrl)
        items.append(item)
    return items

def get_all_maps():
    f = urlopen(get_url(1));
    content = f.read()
    soup = BS(content, "html.parser")
    lastPageLink = soup.find_all("a", class_="pagelink")[-1]
    lastPage = int(lastPageLink.text)
    items = get_maps(content)

    for page in range(2, lastPage+1, 1):
        time.sleep(1)
        f = urlopen(get_url(page))
        items.extend(get_maps(f))

    return items

def update_maplist():
    maps = get_all_maps()
    with open(maplist_path, "w") as fp:
        json.dump(maps, fp)


def get_subscribed_id_list():
    id_list = []
    inifile = settings.idlist_file()
    ini = Ini_Parser.fromFile(inifile)

    section = "OnlineSubsystemSteamworks.KFWorkshopSteamworks"
    option = "ServerSubscribedWorkshopItems"
    if section in ini and option in ini[section]:
        id_list = ini[section][option]
        if isinstance(id_list, str):
            id_list = [id_list]

        if "" in id_list:
            id_list.remove("")
    return id_list

def set_subscribed_id_list(idlist):
    inifile = settings.idlist_file()
    ini = Ini_Parser.fromFile(inifile)
    section = "OnlineSubsystemSteamworks.KFWorkshopSteamworks"
    option = "ServerSubscribedWorkshopItems"
    if not section in ini:
        ini[section] = {}
    
    ini[section][option] = idlist

    Ini_Parser.toFile(inifile, ini)

def find_map_file_from_cache(id):
    for root, subdirs, files in os.walk(settings.cache_dir() + "/" + id):
        for f in files:
            if f.endswith(".kfm"):
                return root.replace("\\", "/") + "/" + f.replace("\\", "/")
    
    return None


def sync_map(id, ini):
    cachefile = find_map_file_from_cache(id)
    if cachefile == None:
        print("map file in cache not found")
        return []

    print ("map file(cache): " + cachefile)
    filename = os.path.basename(cachefile)

    if sys.platform == "linux" or sys.platform == "linux2":
        dest = settings.map_dir() + "/" + filename
        if os.path.exists(dest):
            os.remove(dest)
        os.symlink(cachefile, dest)
    else:
        try:
            shutil.copy2(cachefile, settings.map_dir())
        except e:
            print(e)
            return []

    mapname = os.path.splitext(filename)[0]

    ssKey = "ScreenshotPathName"
    ssValue = "UI_MapPreview_TEX.UI_MapPreview_Placeholder"
    def addMap(difficulty):
        suffix = "?Difficulty=" + str(difficulty)
        sectionName = mapname + suffix + " KFMapSummary"
        ini[sectionName] = {}
        ini[sectionName]["MapName"] = mapname + "?Difficulty=" + str(difficulty)
        ini[sectionName][ssKey] = ssValue
        return mapname + suffix

    mapnames = []

    if settings.SPLIT_MAP_DIFFICULTY:
        mapnames.append(addMap(1))
        mapnames.append(addMap(2))
        mapnames.append(addMap(3))
        
    else:
        sectionName = mapname + " KFMapSummary"
        ini[sectionName] = {}
        ini[sectionName]["MapName"] = mapname
        ini[sectionName][ssKey] = ssValue
        mapnames.append(mapname)

    return mapnames


def get_official_map_names():
    inifile = settings.maplist_file()
    ini = Ini_Parser.fromFile(inifile)
    officialmaps = filter(lambda key:
        "ScreenshotPathName" in ini[key] and
            ini[key]["ScreenshotPathName"] != "UI_MapPreview_TEX.UI_MapPreview_Placeholder"
        ,ini.keys())
    officialmapNames = map(lambda key:
        ini[key]["MapName"], officialmaps)

    return list(officialmapNames)
    

def sync():
    subscribed_ids = get_subscribed_id_list()
    inifile = settings.maplist_file()
    ini = Ini_Parser.fromFile(inifile)
    customMaps = []

    for id in subscribed_ids:
        print("workshop ID: " + id)
        addedmaps = sync_map(id, ini)

        if len(addedmaps) > 0:
            print(id + " added")
            customMaps.extend(addedmaps)

        else:
            print(id + " failed")
    print("Custom Maps: " + ",".join(customMaps))

    officialMaps = get_official_map_names()
    print("Official Maps: " + ",".join(officialMaps))

    allMaps = []
    allMaps.extend(officialMaps)
    allMaps.extend(customMaps)

    mapcycleStr = ",".join(allMaps)
    print("Map Cycle: " + mapcycleStr)

    ini["KFGame.KFGameInfo"]["GameMapCycles"] = "(Maps=(" + mapcycleStr + "))"

    Ini_Parser.toFile(inifile, ini)

def auth(username, password):
    return settings.USERNAME == username and settings.PASSWORD == password


@route("/static/<filename:path>")
def send_static(filename):
    return static_file(filename, root="static")

# bottle route
@route("/")
def list_maps():
    maps = []
    try:
        with open(maplist_path) as fp:
            maps = json.load(fp)
    except:
        maps = []

    
    if not maps or len(maps) == 0:
        return template("list_maps_error")

    subscribedIDList = get_subscribed_id_list()

    return template("list_maps", maps=maps, subscribed=subscribedIDList)

@route("/update_list")
@auth_basic(auth)
def update_list():
    update_maplist()
    r = HTTPResponse(status=302)
    r.set_header("Location", "/")
    return r

@route("/unsubscribe/<id:re:[0-9]+>")
@auth_basic(auth)
def unsubscribe(id):
    idlist = get_subscribed_id_list()
    if id in idlist:
        idlist.remove(id)
        set_subscribed_id_list(idlist)
    r = HTTPResponse(status=302)
    r.set_header("Location", "/")
    return r

@route("/subscribe/<id:re:[0-9]+>")
@auth_basic(auth)
def subscribe(id):
    idlist = get_subscribed_id_list()
    if not id in idlist:
        idlist.append(id)
        set_subscribed_id_list(idlist)
    r = HTTPResponse(status=302)
    r.set_header("Location", "/")
    return r


if len(sys.argv) < 2:
    usage()
    quit(0)

if sys.argv[1] == "--server":
    run(host=settings.HTTP_LISTEN_ADDRESS, port=settings.HTTP_LISTEN_PORT, debug=True)
    quit(0)

if sys.argv[1] == "--sync":
    sync()
    quit(0)


#items = get_maps(1)


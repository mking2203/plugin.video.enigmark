#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# copyright (C) 2021 Mark Koenig
#
# Enigna Interface
# https://dream.reichholf.net/wiki/Enigma2:WebInterface
#
# Alternativ für VU+ OpenWebif
# https://github.com/E2OpenPlugins/e2openplugin-OpenWebif
# z.B.:
# http://192.168.178.140/api/statusinfo?_=1613129255743
# http://192.168.178.140/api/zap?sRef=1%3A0%3A19%3A285A%3A401%3A1%3AC00000%3A0%3A0%3A0%3A&_=1613129255749
# http://192.168.178.140/api/zap?sRef=1:0:19:285A:401:1:C00000:0:0:0:&_=1613129255749

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, os
import time

from urllib.parse import urlparse
import urllib
import xml.etree.ElementTree

import re
import requests
from datetime import datetime

CommonRootView = 50
FullWidthList = 51
ThumbnailView = 500
PictureWrapView = 510
PictureThumbView = 514
MediaListView2 = 503
MediaListView3 = 504

class ItemClass(object):
    pass

_listMode_ = ''

_url = sys.argv[0]
_handle = int(sys.argv[1])

__addon = xbmcaddon.Addon()
__addonId =__addon.getAddonInfo('id')
__addonname = __addon.getAddonInfo('name')

__icon = __addon.getAddonInfo('icon')

__addonpath = __addon.getAddonInfo('path')

__ip = __addon.getSetting('ip')
__stream = __addon.getSetting('stream')

# -------------------------------------------------------------------------

def mainSelector():

    addLog('main selector - receiver ' + __ip)
    xbmcplugin.setContent(_handle, 'files')

    item = getActual()

    if(not 'OFFLINE' in item.Name):

        pic = 'http://' + __ip + '/picon/' + item.Picture +'.png'
        pic = pic.replace(' ','%20')

        addPictureItem(item.Name, _url + '?live=' + item.ID, pic)
        addPictureItem('RECORDS', _url + '?records=show', 'DefaultFolder.png')

        items = getBouquet()
        for item in items:
            addPictureItem(item.Name, _url + '?bouq=' + item.ID, 'DefaultFolder.png')

    else:
        xbmcgui.Dialog().notification(__addonname, 'Receiver is offline (' + __ip + ')' , time=2000)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

# -------------------------------------------------------------------------

def showBouquet(id):

    xbmc.log('- bouquet - id ' + id)

    items = getServices(id)
    for item in items:
        pic = 'http://' + __ip + '/picon/' + item.Picture +'.png'
        pic = pic.replace(' ','%20')

        list_item = xbmcgui.ListItem(label=item.Name)
        list_item.setArt({'thumb': pic,
                          'icon': pic,
                          'fanart': pic})

        list_item.setInfo('video', { 'plot': item.EPGnow + '\n' + item.EPGnext  })

        url = _url + '?play=' + urllib.parse.quote_plus(item.ID)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

# -------------------------------------------------------------------------

def playLive(id):

    addLog('playLive - ID: ' + id)

    xbmc.Player().play('http://' + __ip + ':' + __stream + '/' + id)

    xbmc.executebuiltin('Container.Refresh')

# -------------------------------------------------------------------------

def playFile(id):

    addLog('playFile: ID ' + id)

    file = 'http://' + __ip + '/file?file=' + id
    xbmc.Player().play(file.replace(' ','%20'))

    xbmc.executebuiltin('Container.Refresh')

# -------------------------------------------------------------------------

def play(id):

    addLog('play ID: ' + id)

    result = setService(id)
    addLog('result setService: ' + result)

    #time.sleep(3)

    xbmc.Player().play('http://' + __ip + ':' + __stream + '/' + id)

    xbmc.executebuiltin('Container.Refresh')

# -------------------------------------------------------------------------

def showRecords():

    addLog('showRecords')

    items = getRecords()
    for item in items:

        thumb = 'DefaultVideo.png'

        list_item = xbmcgui.ListItem(label=item.Name)

        list_item.setArt({'thumb': thumb,
                          'icon': thumb,
                          'fanart': thumb})

        list_item.setInfo('video', { 'plot': item.Info, 'duration': item.Duration })

        url = _url + '?playfile=' + item.ID
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle)

# -------------------------------------------------------------------------

def getActual():

    addLog('getactual')

    # init with OFFLINE
    item = ItemClass()
    item.Name = 'Receiver\nOFFLINE'
    item.ID = ''
    item.Picture = ''

    try:
        r = requests.get('http://' + __ip + '/web/subservices', timeout=1.0)
        r.encoding = 'utf-8'

        if r.status_code == requests.codes.ok:

            page = r.text

            e = xml.etree.ElementTree.fromstring(page)

            serv = e.find('e2service')
            id = serv.find('e2servicereference')
            name = serv.find('e2servicename')

            item.ID = urllib.parse.quote_plus(id.text)
            item.Name = 'LIVE ' + name.text
            item.Picture = name.text

            if(id.text.startswith('1:0:0:0:0:0:0:0:0:0:')):
                item.Name = 'PLAY ' + name.text

    except:
            addLog('getActual fails')

    return item

# -------------------------------------------------------------------------

def getBouquet():

    addLog('getBouquet')

    itemList =[]
    try:
        r = requests.get('http://' + __ip + '/web/getservices', timeout=1.0)
        r.encoding = 'utf-8'

        page = r.text

        e = xml.etree.ElementTree.fromstring(page)
        serv = e.findall('e2service')

        for child in serv:
            id = child.find('e2servicereference')
            name = child.find('e2servicename')

            item = ItemClass()
            item.ID = urllib.parse.quote_plus(id.text)
            item.Name = name.text
            item.Picture = name.text

            itemList.append(item)

    except:
        addLog('getBouquet fails')

    return itemList

# -------------------------------------------------------------------------

def getServices(id):

    addLog('getServices: http://' + __ip + '/web/getservices?sRef=' + id)

    itemList =[]
    try:
        r = requests.get('http://' + __ip + '/web/getservices?sRef=' + urllib.parse.quote_plus(id), timeout=1.0)
        r.encoding = 'utf-8'

        page = r.text

        e = xml.etree.ElementTree.fromstring(page)
        serv = e.findall('e2service')

        for child in serv:
            ref = child.find('e2servicereference')
            name = child.find('e2servicename')

            item = ItemClass()
            item.ID = ref.text
            item.Name = name.text
            item.Picture = name.text
            item.EPGnow = ''
            item.EPGnext = ''

            itemList.append(item)

        r = requests.get('http://' + __ip + '/web/epgnow?bRef=' + urllib.parse.quote_plus(id), timeout=1.0)
        r.encoding = 'utf-8'

        page = r.text

        e = xml.etree.ElementTree.fromstring(page)
        serv = e.findall('e2event')

        for child in serv:
            ref = child.find('e2eventservicereference')
            name = child.find('e2eventtitle').text
            start = child.find('e2eventstart').text
            duration = child.find('e2eventduration').text

            if not (ref is None):
                for aItem in itemList:
                    if ((name != 'None') & (start != 'None')):
                        if(aItem.ID == ref.text):
                            strStart = datetime.fromtimestamp(int(start)).strftime('%H:%M')  # '%d.%m.%Y %H:%M'
                            aItem.EPGnow = strStart + " - " + name
                            break

        r = requests.get('http://' + __ip + '/web/epgnext?bRef=' + urllib.parse.quote_plus(id), timeout=0.5)
        r.encoding = 'utf-8'

        page = r.text

        e = xml.etree.ElementTree.fromstring(page)
        serv = e.findall('e2event')

        for child in serv:
            ref = child.find('e2eventservicereference')
            name = child.find('e2eventtitle').text
            start = child.find('e2eventstart').text
            duration = child.find('e2eventduration').text

            if not (ref is None):
                for aItem in itemList:
                    if ((name != 'None') & (start != 'None')):
                        if(aItem.ID == ref.text):
                            strStart = datetime.fromtimestamp(int(start)).strftime('%H:%M')  # '%d.%m.%Y %H:%M'
                            aItem.EPGnext = strStart + " - " + name
                            break

    except:
        addLog('getServices fails')

    return itemList

# -------------------------------------------------------------------------

def setService(id):

    addLog('setService ' + str(id))

    actID = 'n.a.'
    result = 'n.a.'

    try:
        r = requests.get('http://' + __ip + '/web/subservices', timeout=1.0)
        r.encoding = 'utf-8'

        if r.status_code == requests.codes.ok:

            e = xml.etree.ElementTree.fromstring(r.text)
            serv = e.find('e2service')
            ref = serv.find('e2servicereference')
            actID = ref.text

            addLog('actual channel: ' + actID)
    except:
        pass

    if(actID not in id):

        xbmcgui.Dialog().notification(__addonname, 'ZAP to channel', time=2000)
        try:
            r = requests.get('http://' + __ip + '/web/zap?sRef=' + urllib.parse.quote_plus(id), timeout=2.0)
            e = xml.etree.ElementTree.fromstring(r.text)

            serv = e.find('e2statetext')
            result = serv.text

        except:
            addLog('setServices fails')

    else:
        addLog('channel already active')
        result = 'Active service is now \'' + actID + '\''

    return result

# -------------------------------------------------------------------------

def getRecords():

    addLog('getRecords')

    itemList =[]
    try:
        # timeout little longer since HDD maybe in sleep
        r = requests.get('http://' + __ip + '/web/getlocations', timeout=3.0)
        r.encoding = 'utf-8'

        e = xml.etree.ElementTree.fromstring(r.text)
        loc = e.find('e2location')
        location = loc.text

        r = requests.get('http://' + __ip + '/web/movielist?dirname=' + urllib.parse.quote_plus(location), timeout=1.0)
        r.encoding = 'utf-8'

        e = xml.etree.ElementTree.fromstring(r.text)
        serv = e.findall('e2movie')

        for child in serv:
            id = child.find('e2servicereference')
            name = child.find('e2title')

            desc = child.find('e2description')
            descExt = child.find('e2descriptionextended')
            date = child.find('e2time')
            duration = child.find('e2length')

            item = ItemClass()

            x = id.text.index('/')
            link = id.text[x:]

            item.ID = urllib.parse.quote_plus(link)
            item.Name = name.text

            item.Info = ''

            if not (desc.text is None):
                item.Info = desc.text

            item.Info = item.Info + '\n'

            if not (descExt.text is None):
                item.Info = item.Info + descExt.text

            item.Date = date.text
            item.Duration = duration.text

            itemList.append(item)

    except:
        addLog('getRecords fails')

    return itemList

 # --------------  helper -------------------

def addPictureItem(title, url, thumb):

    list_item = xbmcgui.ListItem(label=title)

    list_item.setArt({'thumb': thumb,
                      'icon': thumb,
                      'fanart': thumb})

    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

# -------------------------------------------------------------------------

def addLog(msg):

    xbmc.log("ENIGMARK: %s" % msg)

#### main entry point ####

if __name__ == '__main__':

    PARAMS = urllib.parse.parse_qs(sys.argv[2][1:])

    if 'bouq' in PARAMS:
        showBouquet(PARAMS['bouq'][0])
    elif 'play' in PARAMS:
        play(PARAMS['play'][0])
    elif 'live' in PARAMS:
        playLive(PARAMS['live'][0])
    elif 'playfile' in PARAMS:
        playFile(PARAMS['playfile'][0])
    elif 'records' in PARAMS:
        showRecords()
    else:
        mainSelector()


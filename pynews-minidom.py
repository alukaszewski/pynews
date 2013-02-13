#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# filename: pynews.py
# author: Albert Lukaszewski
# version: 0.01
# 
# Released under the GPLv2:
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.

import MySQLdb
import re

from datetime import datetime
from urllib2 import urlopen
from xml.dom import minidom

# Read in list of feeds
rssFile = 'rssfeeds.tsv'
RSSfile = open(rssFile, 'r')
feedFile = RSSfile.readlines()
RSSfile.close()

# Read in list of common words that will be removed from the title to
# determine what the keywords of an item are.
wordFile = 'commonwords.txt'
WORDSfile = open(wordFile, 'r')
weedFile = WORDSfile.readlines()
WORDSfile.close()

# Define what whitespace is in the context of a title element
whitespacers = re.compile('([:,;.!?\s\)\(])')

# Define the database access credentials
dbhost = "localhost"
dbuser = "rootbeer"
dbpass = "s0m3p4ss"
dbdb = "pynews"

def getItems(feed):
    """
    Receives lines of RSS feed to build and parse the dom and return
    all items out of the file as well as the time of retrieval.
    """

    retrieval = datetime.now()
    data = feed.read().replace('\n', '')   
    dom = minidom.parseString(data)

    channels = dom.getElementsByTagName("channel")[0]
    items = channels.getElementsByTagName("item")

    return items, retrieval

def getData(item):
    """
    Receives RSS item (item), parses it, and returns the item's title
    (title), URL (link), and publication date (pubdate), if available.
    """

    title = item.getElementsByTagName("title")[0].childNodes[0].data
    link =  item.getElementsByTagName("link")[0].childNodes[0].data

    # The 'description' tag is unreliable as it is not always used for
    # descriptions.  It can sometimes contain 'comments' (e.g., Hacker
    # News) 
    # desc = item.getElementsByTagName("description")[0].childNodes[0].data

    try: # Get publication date
        pubdate = item.getElementsByTagName("pubDate")[0].childNodes[0].data
    except: # If publication date is not available, note so
        pubdate = "not available"
    return title, link, pubdate

def getKeywords(title):
    """
    Receives title of item, sorts out of it the most common English
    words, and returns a string of keywords found in the title.
    """
    keywords = list()
    # Substitute ' - ' separately as the re module tends to botch a
    # match of ' - ' when used with the other regex.
    title = title.replace(' - ', ' ')
    title = re.sub(whitespacers, ' ', title)
    titlewords = title.split(' ')
    for word in titlewords:
        match = 0
        for weed in weedFile:
            weed = weed.strip()
            if word == weed:
                match = 1
            elif word == weed.upper():
                match = 1
            elif word == weed.capitalize():
                match = 1
        if match == 0:
            keywords.append(word)
        
    keywords.sort()
    keywords = ' '.join(keywords)
    keywords = keywords.replace('  ', ' ')
    keywords = keywords.strip()
    return keywords


def main():
    for line in feedFile:
        lines = line.split('\t')
        feedname = lines[0].strip()
        feed = urlopen(lines[1])
        items, feedretrieved = getItems(feed)

        feeddeleted = 0

        for item in items:
            title, link, pubdate = getData(item)
            itemposted = str(datetime.now())
            feedname = feedname.encode("utf-8")
            title = title.encode("utf-8")
            link = link.encode("utf-8")
            pubdate = pubdate.encode("utf-8")
            keywords = getKeywords(title)
            # values = (feedname, title, link, pubdate)

            print("Feed Name: " + feedname)
            print("Title: " + title)
            print("URL: " + link)
            print("Publication Date: " + pubdate)
            print("Keywords: " + keywords)
            print("\n")

            db = MySQLdb.connect(dbhost, dbuser, dbpass, dbdb)
            cursor = db.cursor()
            if feeddeleted == 0:
                try:
                    cursor.execute("""DELETE FROM feeditems WHERE feedname = "%s" """, (feedname))
                    feeddeleted = 1
                except:
                    pass

            # statement = """INSERT INTO feeditems(feedname,title,url,pubdate) values("%s", "%s", "%s", "%s")""" %(feedname, title, link, pubdate)
            # print "\n\n" + statement + "\n\n"
            cursor.execute("""INSERT INTO feeditems(feedname,title,url,pubdate,keywords,itemposted, feedretrieved) values("%s", "%s", "%s", "%s", "%s", "%s", "%s")""", (feedname, title, link, pubdate, keywords, itemposted, feedretrieved))

            db.commit()
            db.close()

    return 1

if __name__ == "__main__":
    main()

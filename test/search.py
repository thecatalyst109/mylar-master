#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.


import mylar
from mylar import logger, db, updater, helpers, parseit

nzbsu_APIkey = mylar.NZBSU_APIKEY
dognzb_APIkey = mylar.DOGNZB_APIKEY

LOG = mylar.LOG_DIR

import lib.feedparser as feedparser
import urllib
import os, errno
import string
import sqlite3 as lite
import sys
import getopt
import re
import time
from datetime import datetime

def search_init(ComicName, IssueNumber, ComicYear, SeriesYear):
    if ComicYear == None: ComicYear = '2012'
    else: ComicYear = str(ComicYear)[:4]
    ##nzb provider selection##
    ##'dognzb' or 'nzb.su' or 'experimental'
    nzbprovider = []
    nzbp = 0
    if mylar.NZBSU == 1:
        nzbprovider.append('nzb.su')
        nzbp+=1
    if mylar.DOGNZB == 1:
        nzbprovider.append('dognzb')
        nzbp+=1
    # -------- 
    #  Xperimental
    if mylar.EXPERIMENTAL == 1:
        nzbprovider.append('experimental')
        nzbp+=1
    # --------
    nzbpr = nzbp-1
    while (nzbpr >= 0 ):
        if nzbprovider[nzbpr] == 'experimental':
        #this is for experimental
            nzbprov = 'experimental'
            findit = NZB_SEARCH(ComicName, IssueNumber, ComicYear, SeriesYear, nzbprov, nzbpr)
            if findit == 'yes':
                break
            else:
                nzbpr-=1

        if nzbprovider[nzbpr] == 'nzb.su':
        # ----
        # this is for nzb.su
            #d = feedparser.parse("http://nzb.su/rss?t=7030&dl=1&i=" + str(nzbsu_APIID) + "&r=" + str(nzbsu_APIkey))
            #--LATER ?search.rss_find = RSS_SEARCH(ComicName, IssueNumber)
            #if rss_find == 0:
            nzbprov = 'nzb.su'
            findit = NZB_SEARCH(ComicName, IssueNumber, ComicYear, SeriesYear, nzbprov, nzbpr)
            if findit == 'yes':
                break
            else:
                nzbpr-=1
        # ----
       
        elif nzbprovider[nzbpr] == 'dognzb':
        # this is for dognzb.com
            #d = feedparser.parse("http://dognzb.cr/rss.cfm?r=" + str(dognzb_APIkey) + "&t=7030&num=100")
            #RSS_SEARCH(ComicName, IssueNumber)
            nzbprov = 'dognzb'
            findit = NZB_SEARCH(ComicName, IssueNumber, ComicYear, SeriesYear, nzbprov, nzbpr)
            if findit == 'yes':
                break
            else:
                nzbpr-=1
        # ----
    return findit

def RSS_Search(ComicName, IssueNumber):
    #this all needs to be REDONE...#    
    loopd = int(w-1)
    ssab = []
    ssabcount = 0
    print ("--------RSS MATCHING-----------------")
    for entry in d['entries']:
        # test for comic name here
        print loopd, entry['title']
        #print kc[loopd]
        #while (loopd > -1):
        #    if str(kc[loopd]).lower() in str(entry['title'].lower()):
        #print entry['title']
            # more precision - let's see if it's a hit on issue as well
            # Experimental process
            # since we're comparing the watchlist titles to the rss feed (for more robust matching)

            # the results will be 2nd/3rd variants, MR's, and comics on the watchlist but not necessarily 'NEW' rele$
            # let's first compare watchlist to release list
        incloop = int (tot -1)
        while (incloop > -1):
            #print ("Comparing " + str(entry['title']) + " - for - " + str(watchfnd[incloop]))
            cleantitle = helpers.cleanName(entry['title'])
            if str(watchfnd[incloop]).lower() in str(cleantitle).lower():
                #print ("MATCHED - " + str(watchfnd[incloop]).lower())
                if str(watchfndextra[incloop]).lower() is not None:
                    if str(watchfndextra[incloop]).lower() not in str(cleantitle).lower():
                        #print ("no extra matching - not a match")
                        #print (watchfndextra[incloop].lower())
                        break
                # now we have a match on watchlist and on release list, let's check if the issue is the same
                # on the feed and the releaselist
                # we have to remove the # sign from the ki[array] field first
                ki[incloop] = re.sub("\D", "", str(ki[incloop]))
                if str(ki[incloop]) in str(cleantitle):
                    print ("MATCH FOR DOWNLOAD!!\n    WATCHLIST: " + str(watchfnd[incloop]) + "\n    RLSLIST: " + str(kc[incloop]) + " ISSUE# " + str(ki[incloop]) + "\n    RSS: " + str(cleantitle))
                        #let's do the DOWNLOAD and send to SABnzbd
                        #this is for nzb.su - API LIMIT :(
                    linkstart = os.path.splitext(entry['link'])[0]
                        #following is JUST for nzb.su
                    if nzbprov == 'nzb.su':
                        linkit = os.path.splitext(entry['link'])[1]
                        linkit = linkit.replace("&", "%26")
                        thislink = str(linkstart) + str(linkit)
                    else:
                        # this should work for every other provider
                        linkstart = linkstart.replace("&", "%26")
                        thislink = str(linkstart)
                    tmp = "http://192.168.2.2:8085/api?mode=addurl&name=" + str(thislink) + "&pp=3&cat=comics&apikey=" + str(SABAPI)
                    print tmp
                    ssab.append(str(watchfnd[incloop]))
                    ssabcount+=1
                    urllib.urlopen(tmp);
                    # time.sleep(5)
            incloop-=1
                # - End of Experimental Process
                #break
            #loopd-=1
    print ("snatched " + str(ssabcount) + " out of " + str(tot) + " comics via rss...")
    return ssabcount

def NZB_SEARCH(ComicName, IssueNumber, ComicYear, SeriesYear, nzbprov, nzbpr):
    logger.info(u"Shhh be very quiet...I'm looking for " + ComicName + " issue: " + str(IssueNumber) + " using " + str(nzbprov))
    if nzbprov == 'nzb.su':
        apikey = mylar.NZBSU_APIKEY
    elif nzbprov == 'dognzb':
        apikey = mylar.DOGNZB_APIKEY
    elif nzbprov == 'experimental':
        apikey = 'none'
    #print ("-------------------------")

    if mylar.PREFERRED_QUALITY == 0: filetype = ""
    elif mylar.PREFERRED_QUALITY == 1: filetype = ".cbr"
    elif mylar.PREFERRED_QUALITY == 2: filetype = ".cbz"

    # figure out what was missed via rss feeds and do a manual search via api
    #tsc = int(tot-1)
    findcomic = []
    findcomiciss = []
    findcount = 0
    ci = ""
    comsearch = []
    isssearch = []
    comyear = str(ComicYear)

    #print ("-------SEARCH FOR MISSING------------------")
    findcomic.append(str(ComicName))
    IssueNumber = str(re.sub("\.00", "", str(IssueNumber)))
    #print ("issueNumber" + str(IssueNumber))
    findcomiciss.append(str(re.sub("\D", "", str(IssueNumber))))
    
    #print ("we need : " + str(findcomic[findcount]) + " issue: #" + str(findcomiciss[findcount]))
    # replace whitespace in comic name with %20 for api search
    cm = re.sub(" ", "%20", str(findcomic[findcount]))
    #print (cmi)
    if len(str(findcomiciss[findcount])) == 1:
        cmloopit = 3
    elif len(str(findcomiciss[findcount])) == 2:
        cmloopit = 2
    else:
        cmloopit = 1
    isssearch.append(str(findcomiciss[findcount]))
    comsearch.append(cm)
    findcount+=1

    # ----

    #print ("------RESULTS OF SEARCH-------------------")
    findloop = 0
    foundcomic = []

    #---issue problem
    # if issue is '011' instead of '11' in nzb search results, will not have same
    # results. '011' will return different than '11', as will '009' and '09'.

    while (findloop < (findcount) ):
        comsrc = comsearch[findloop]
        #print (str(comsearch[findloop]))
        while (cmloopit >= 1 ):
                # here we account for issue pattern variations
            if cmloopit == 3:
                comsearch[findloop] = comsrc + "%2000" + isssearch[findloop] + "%20" + str(filetype)
                #print (comsearch[findloop])
            elif cmloopit == 2:
                comsearch[findloop] = comsrc + "%200" + isssearch[findloop] + "%20" + str(filetype)
                #print (comsearch[findloop])
            elif cmloopit == 1:
                comsearch[findloop] = comsrc + "%20" + isssearch[findloop] + "%20" + str(filetype)
                #print (comsearch[findloop])
            #print ("NZB Provider set to: " + nzbprov)
            if nzbprov != 'experimental':
                if nzbprov == 'dognzb':
                    #print ("dog-search.")
                    findurl = "http://dognzb.cr/api?t=search&apikey=" + str(apikey) + "&q=" + str(comsearch[findloop]) + "&o=xml&cat=7030"
                elif nzbprov == 'nzb.su':
                    #print ("nzb.su search")
                    findurl = "http://nzb.su/api?t=search&q=" + str(comsearch[findloop]) + "&apikey=" + str(apikey) + "&o=xml&cat=7030"
                bb = feedparser.parse(findurl)
                #print (findurl)
            elif nzbprov == 'experimental':
                #print ("experimental raw search")
                bb = parseit.MysterBinScrape(comsearch[findloop], comyear)
            done = False
            foundc = "no"
            if bb == "no results":               
                #print ("no results found...attempting alternate search")
                pass
            elif (len(bb['entries']) == 0):
                #print ("Nothing found for : " + str(findcomic[findloop]) + " Issue: #" + str(findcomiciss[findloop]))
                foundc = "no"
            else:
                #print ("Found for: " + str(findcomic[findloop]))
                for entry in bb['entries']:
                    #print str(entry['title'])
                    cleantitle = helpers.cleanName(str(entry['title']))
                    if done:
                        break
                    #print ("title: " + str(cleantitle))
                    #print ("link: " + entry['link'])
                #let's narrow search down - take out year (2010), (2011), etc
                #let's check for first occurance of '(' as generally indicates
                #that the 'title' has ended

                    ripperlist=['digital-',
                                'empire',
                                'dcp']
                    #this takes care of the brackets :)                    
#                    m = re.findall(r"\((\w+)\)", cleantitle)                 
                    m = re.findall('[^()]+', cleantitle)
                    lenm = len(m)
                    #print ("there are " + str(lenm) + " words.")
                    cnt = 0
                    while (cnt < lenm):
                        if m[cnt] is None: break
                        #if m[cnt] == ' ': print ("space detected")
                        #print (str(cnt) + ". Bracket Word: " + m[cnt] )                        
                        if cnt == 0:
                            comic_andiss = m[cnt]
                            print ("Comic:" + str(comic_andiss))
                        if m[cnt][:-2] == '19' or m[cnt][:-2] == '20': 
                            print ("year detected!")
                            result_comyear = m[cnt]
                            if str(comyear) in result_comyear:
                                print (str(comyear) + " - right - years match baby!")
                                yearmatch = "true"
                            else:
                                print (str(comyear) + " - not right - years don't match ")
                                yearmatch = "false"
                        if 'digital' in m[cnt] and len(m[cnt]) == 7: 
                            pass
                            #print ("digital edition")
                        if ' of ' in m[cnt]:
                            #print ("mini-series detected : " + str(m[cnt]))
                            result_of = m[cnt]
                        if 'cover' in m[cnt]: 
                            #print ("covers detected")
                            result_comcovers = m[cnt]
                        for ripper in ripperlist:
                            if ripper in m[cnt]:
                                #print ("Scanner detected:" + str(m[cnt]))
                                result_comscanner = m[cnt]
                        cnt+=1

                    if yearmatch == "false": break
                    
                    splitit = []   
                    watchcomic_split = []
                    comic_iss = re.sub('[\-\:\,]', '', str(comic_andiss))
                    splitit = comic_iss.split(None)
                    watchcomic_split = findcomic[findloop].split(None)

                    bmm = re.findall('v\d', comic_iss)
                    #print ("vers - " + str(bmm))
                    if len(bmm) > 0: splitst = len(splitit) - 2
                    else: splitst = len(splitit) - 1
                    if (splitst) != len(watchcomic_split):
                        print ("incorrect comic lengths...not a match")
                        if str(splitit[0]).lower() == "the":
                            print ("THE word detected...attempting to adjust pattern matching")
                            splitit[0] = splitit[4:]
                    else:
                        print ("length match..proceeding")
                        n = 0
                        scount = 0
                        #print ("length:" + str(len(splitit)))
                        while ( n <= len(splitit)-1 ):
                            if n < len(splitit)-1:
                                #print ( str(n) + ". Comparing: " + watchcomic_split[n] + " .to. " + splitit[n] )
                                if str(watchcomic_split[n].lower()) in str(splitit[n].lower()):
                                    #print ("word matched on : " + splitit[n])
                                    scount+=1
                                #elif ':' in splitit[n] or '-' in splitit[n]:
                                #    splitrep = splitit[n].replace('-', '')
                                #    print ("non-character keyword...skipped on " + splitit[n])
                                elif len(splitit[n]) < 3 or (splitit[n][1:]) == "v":
                                    #print ("possible verisoning..checking")
                                    #we hit a versioning # - account for it
                                    if splitit[n][2:].isdigit():
                                        comicversion = str(splitit[n])
                                        #print ("version found:" + str(comicversion))
                            else:
                                if splitit[n].isdigit():
                                    print ("issue detected")
                                    comiss = splitit[n]
                                    comicNAMER = n - 1
                                    comNAME = splitit[0]
                                    cmnam = 1
                                    while (cmnam < comicNAMER):
                                        comNAME = str(comNAME) + " " + str(splitit[cmnam])
                                        cmnam+=1
                                    #print ("comic: " + str(comNAME))
                                else:
                                    #print ("non-match for: " + splitit[n])
                                    pass
                            n+=1
                        spercent = ( scount/int(len(splitit)) ) * 100
                        #print (str(spercent) + "% match")
                        #if spercent >= 75: print ("it's a go captain...")
                        #if spercent < 75: print ("failure - we only got " + str(spercent) + "% right!")
                        print ("this should be a match!")
                        #issue comparison now as well
                        if int(findcomiciss[findloop]) == int(comiss):
                            print ("issues match!")

                        ## -- inherit issue. Comic year is non-standard. nzb year is the year
                        ## -- comic was printed, not the start year of the comic series and
                        ## -- thus the deciding component if matches are correct or not
                            linkstart = os.path.splitext(entry['link'])[0]
                        #following is JUST for nzb.su
                            if nzbprov == 'nzb.su':
                                linkit = os.path.splitext(entry['link'])[1]
                                #print ("linkit: " + str(linkit))
                                linkit = linkit.replace("&", "%26")
                                linkapi = str(linkstart) + str(linkit)
                            else:
                                # this should work for every other provider
                                linkstart = linkstart.replace("&", "%26")
                                linkapi = str(linkstart)
                            #here we distinguish between rename and not.
                            #blackhole functinality---
                            #let's download the file to a temporary cache.

                            if mylar.BLACKHOLE:
                                if os.path.exists(mylar.BLACKHOLE_DIR):
                                    filenamenzb = str(ComicName) + " " + str(IssueNumber) + " (" + str(comyear) + ").nzb"
                                    urllib.urlretrieve(linkapi, str(mylar.BLACKHOLE_DIR) + str(filenamenzb))
                                    logger.info(u"Successfully sent .nzb to your Blackhole directory : " + str(mylar.BLACKHOLE_DIR) + str(filenamenzb) )
                            #end blackhole

                            else:
                                tmppath = mylar.CACHE_DIR
                                print ("cache directory set to: " + str(tmppath))
                                if os.path.exists(tmppath):
                                    filenamenzb = os.path.split(linkapi)[1]
                                    #filenzb = os.path.join(tmppath,filenamenzb)
                                    if nzbprov == 'nzb.su':
                                        filenzb = linkstart[21:]
                                    if nzbprov == 'experimental':
                                        filenzb = filenamenzb[6:]
                                    if nzbprov == 'dognzb':
                                        filenzb == str(filenamenzb)
                                    savefile = str(tmppath) + "/" + str(filenzb) + ".nzb"
                                else:
                                #let's make the dir.
                                    try:
                                        os.makedirs(str(mylar.CACHE_DIR))
                                        logger.info(u"Cache Directory successfully created at: " + str(mylar.CACHE_DIR))
                                        savefile = str(mylar.CACHE_DIR) + "/" + str(filenzb) + ".nzb"

                                    except OSError.e:
                                        if e.errno != errno.EEXIST:
                                            raise
                                print ("savefile set to: " + str(savefile))
                                urllib.urlretrieve(linkapi, str(savefile))
								#print (str(mylar.RENAME_FILES))
				print ("sucessfully retrieve nzb to : " + str(savefile))			
								#check sab for current pause status
                                print ("sab host set to :" + str(mylar.SAB_HOST))
                                sabqstatusapi = str(mylar.SAB_HOST) + "/api?mode=qstatus&output=xml&apikey=" + str(mylar.SAB_APIKEY)
                                from xml.dom.minidom import parseString
                                import urllib2
                                file = urllib2.urlopen(sabqstatusapi);
                                data = file.read()
                                file.close()
                                dom = parseString(data)
                                for node in dom.getElementsByTagName('paused'):
									pausestatus = node.firstChild.wholeText
									#print pausestatus
                                if pausestatus != 'True':
									#pause sab first because it downloads too quick (cbr's are small!)
                                    pauseapi = str(mylar.SAB_HOST) + "/api?mode=pause&apikey=" + str(mylar.SAB_APIKEY)
                                    urllib.urlopen(pauseapi);
                                    print "Queue paused"
                                else:
				    print "Queue already paused"
                                
                                if mylar.RENAME_FILES == 1:
                                    #print ("Saved file to: " + str(savefile))
                                    tmpapi = str(mylar.SAB_HOST) + "/api?mode=addlocalfile&name=" + str(savefile) + "&pp=3&cat=" + str(mylar.SAB_CATEGORY) + "&script=ComicRN.py&apikey=" + str(mylar.SAB_APIKEY)
                                else:
                                    tmpapi = str(mylar.SAB_HOST) + "/api?mode=addurl&name=" + str(linkapi) + "&pp=3&cat=" + str(mylar.SAB_CATEGORY) + "&script=ComicRN.py&apikey=" + str(mylar.SAB_APIKEY)
                                print ("sab api string:" + str(tmpapi))
                                time.sleep(5)
                                urllib.urlopen(tmpapi);
                                if mylar.RENAME_FILES == 1:
                                    #let's give it 5 extra seconds to retrieve the nzb data...

                                    time.sleep(5)
                              
                                    outqueue = str(mylar.SAB_HOST) + "/api?mode=queue&start=START&limit=LIMIT&output=xml&apikey=" + str(mylar.SAB_APIKEY)
                                    print ("outqueue line generated")
                                    urllib.urlopen(outqueue);
                                    time.sleep(5)
                                    print ("passed api request to SAB")
                                #<slots><slot><filename>.nzb filename
                                #chang nzbfilename to include series(SAB will auto rename based on this)
                                #api?mode=queue&name=rename&value=<filename_nzi22ks>&value2=NEWNAME
                                    from xml.dom.minidom import parseString
                                    import urllib2
                                    file = urllib2.urlopen(outqueue);
                                    data = file.read()
                                    file.close()
                                    dom = parseString(data)
                                    queue_slots = dom.getElementsByTagName('filename')
                                    queue_cnt = len(queue_slots)
                                    print ("there are " + str(queue_cnt) + " things in SABnzbd's queue")
                                    que = 0
                                    slotmatch = "no"
                                    for queue in queue_slots:
                                    #retrieve the first xml tag (<tag>data</tag>)
                                    #that the parser finds with name tagName:
                                        queue_file = dom.getElementsByTagName('filename')[que].firstChild.wholeText
                                        while ('Trying to fetch NZB' in queue_file):
                                            #let's keep waiting until nzbname is resolved by SABnzbd
                                            time.sleep(5)
                                            file = urllib2.urlopen(outqueue);
                                            data = file.read()
                                            file.close()
                                            dom = parseString(data)
                                            queue_file = dom.getElementsByTagName('filename')[que].firstChild.wholeText
                                        print (str(queue_file))
                                        print (str(filenzb))                              
                                        queue_file = queue_file.replace("_", " ")
                                        if str(queue_file) in str(filenzb):
                                            print ("matched")
                                            slotmatch = "yes"
                                            slot_nzoid = dom.getElementsByTagName('nzo_id')[que].firstChild.wholeText
                                            print ("slot_nzoid: " + str(slot_nzoid))
                                            break
                                        que+=1
                                    if slotmatch == "yes":
                                        if mylar.REPLACE_SPACES:
                                            repchar = mylar.REPLACE_CHAR
                                        else:
                                            repchar = ' '
                                        #let's make sure there's no crap in the ComicName since it's O.G.
                                        ComicNM = re.sub('[\:\,]', '', str(ComicName))
                                        renameit = str(ComicNM) + " " + str(IssueNumber) + " (" + str(SeriesYear) + ")" + " " + "(" + str(comyear) + ")"
                                        renameit = renameit.replace(' ', repchar)
                                        nzo_ren = str(mylar.SAB_HOST) + "/api?mode=queue&name=rename&apikey=" + str(mylar.SAB_APIKEY) + "&value=" + str(slot_nzoid) + "&value2=" + str(renameit)
                                        print ("attempting to rename queue to " + str(nzo_ren))
                                        urllib2.urlopen(nzo_ren);
                                        print ("renamed!")
                                        #delete the .nzb now.
                                        #delnzb = str(mylar.PROG_DIR) + "/" + str(filenzb) + ".nzb"
                                        #if mylar.PROG_DIR is not "/":
                                             #os.remove(delnzb)
                                            #we need to track nzo_id to make sure finished downloaded with SABnzbd.
                                            #controlValueDict = {"nzo_id":      str(slot_nzoid)}
                                            #newValueDict = {"ComicName":       str(ComicName),
                                            #                "ComicYEAR":       str(comyear),
                                            #                "ComicIssue":      str(IssueNumber),
                                            #                "name":            str(filenamenzb)}
                                            #print ("updating SABLOG")
                                            #myDB = db.DBConnection()
                                            #myDB.upsert("sablog", newValueDict, controlValueDict)
                                    else: logger.info(u"Couldn't locate file in SAB - are you sure it's being downloaded?")
                                #resume sab if it was running before we started
                                if pausestatus != 'True':
                                    #let's unpause queue now that we did our jobs.
                                    resumeapi = str(mylar.SAB_HOST) + "/api?mode=resume&apikey=" + str(mylar.SAB_APIKEY)
                                    urllib.urlopen(resumeapi);
                                    #print "Queue resumed"
                                #else:
									#print "Queue already paused"

                            #raise an exception to break out of loop
                            foundc = "yes"
                            done = True
                            break
                        else:
                            #print ("issues don't match..")
                            foundc = "no"
                if done == True: break
            cmloopit-=1
        findloop+=1
        if foundc == "yes":
            foundcomic.append("yes")
            logger.info(u"Found :" + str(ComicName) + " (" + str(comyear) + ") issue: " + str(IssueNumber) + " using " + str(nzbprov))
            break
        elif foundc == "no" and nzbpr <> 0:
            logger.info(u"More than one search provider given - trying next one.")
        elif foundc == "no" and nzbpr == 0:
            foundcomic.append("no")
            logger.info(u"Couldn't find Issue " + str(IssueNumber) + " of " + str(ComicName) + "(" + str(comyear) + "). Status kept as wanted." )
            break
    return foundc

def searchforissue(issueid=None, new=False):
    myDB = db.DBConnection()

    if not issueid:

        myDB = db.DBConnection()

        results = myDB.select('SELECT * from issues WHERE Status="Wanted"')
       
        new = True

        for result in results:
            comic = myDB.action('SELECT * from comics WHERE ComicID=?', [result['ComicID']]).fetchone()
            foundNZB = "none"
            SeriesYear = comic['ComicYear']
            if result['IssueDate'] == None: 
                ComicYear = comic['ComicYear']
            else: 
                ComicYear = str(result['IssueDate'])[:4]

            if (mylar.NZBSU or mylar.DOGNZB or mylar.EXPERIMENTAL) and (mylar.SAB_HOST):
                    foundNZB = search_init(result['ComicName'], result['Issue_Number'], str(ComicYear), comic['ComicYear'])
                    if foundNZB == "yes": 
                        #print ("found!")
                        updater.foundsearch(result['ComicID'], result['IssueID'])
                    else:
                        pass 
                        #print ("not found!")
    else:
        result = myDB.action('SELECT * FROM issues where IssueID=?', [issueid]).fetchone()
        ComicID = result['ComicID']
        comic = myDB.action('SELECT * FROM comics where ComicID=?', [ComicID]).fetchone()
        SeriesYear = comic['ComicYear']
        if result['IssueDate'] == None:
            IssueYear = comic['ComicYear']
        else:
            IssueYear = str(result['IssueDate'])[:4]

        foundNZB = "none"
        if (mylar.NZBSU or mylar.DOGNZB or mylar.EXPERIMENTAL) and (mylar.SAB_HOST):
            foundNZB = search_init(result['ComicName'], result['Issue_Number'], str(IssueYear), comic['ComicYear'])
            if foundNZB == "yes":
                #print ("found!")
                updater.foundsearch(ComicID=result['ComicID'], IssueID=result['IssueID'])
            else:
                pass 
                #print ("not found!")

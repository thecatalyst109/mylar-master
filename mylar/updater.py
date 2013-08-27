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

import time
import datetime
from xml.dom.minidom import parseString
import urllib2
import shlex
import re 
import os

import mylar
from mylar import db, logger, helpers, filechecker

def dbUpdate():

    myDB = db.DBConnection()

    activecomics = myDB.select('SELECT ComicID, ComicName from comics WHERE Status="Active" or Status="Loading" order by LastUpdated ASC')

    logger.info('Starting update for %i active comics' % len(activecomics))
    
    for comic in activecomics:
    
        comicid = comic[0]
        mismatch = "no"
        if not mylar.CV_ONLY or comicid[:1] == "G":
            CV_EXcomicid = myDB.action("SELECT * from exceptions WHERE ComicID=?", [comicid]).fetchone()
            if CV_EXcomicid is None: pass
            else:
                if CV_EXcomicid['variloop'] == '99':
                    mismatch = "yes"
            if comicid[:1] == "G":
                mylar.importer.GCDimport(comicid)
            else: 
                mylar.importer.addComictoDB(comicid,mismatch)
        else:
            if mylar.CV_ONETIMER == 1:
                logger.fdebug("CV_OneTimer option enabled...")

                #in order to update to JUST CV_ONLY, we need to delete the issues for a given series so it's a clean refresh.
                logger.fdebug("Gathering the status of all issues for the series.")
                issues = myDB.select('SELECT * FROM issues WHERE ComicID=?', [comicid])
                #store the issues' status for a given comicid, after deleting and readding, flip the status back to what it is currently.                
                logger.fdebug("Deleting all issue data.")
                myDB.select('DELETE FROM issues WHERE ComicID=?', [comicid])            
                logger.fdebug("Refreshing the series and pulling in new data using only CV.")
                mylar.importer.addComictoDB(comicid,mismatch)
                issues_new = myDB.select('SELECT * FROM issues WHERE ComicID=?', [comicid])
                icount = 0
                logger.fdebug("Attempting to put the Status' back how they were.")
                for issue in issues:
                    for issuenew in issues_new:
                        if issuenew['IssueID'] == issue['IssueID'] and issuenew['Status'] != issue['Status']:
                            #change the status to the previous status
                            ctrlVAL = {'IssueID':  issue['IssueID']}
                            newVAL = {'Status':  issue['Status']}
                            myDB.upsert("Issues", newVAL, ctrlVAL)
                            icount+=1
                            break
                logger.info("In converting data to CV only, I changed the status of " + str(icount) + " issues.")
                mylar.CV_ONETIMER = 0   
            else:
                mylar.importer.addComictoDB(comicid,mismatch)
        time.sleep(5) #pause for 5 secs so dont hammer CV and get 500 error
    logger.info('Update complete')


def latest_update(ComicID, LatestIssue, LatestDate):
    # here we add to comics.latest
    myDB = db.DBConnection()
    latestCTRLValueDict = {"ComicID":      ComicID}
    newlatestDict = {"LatestIssue":      str(LatestIssue),
                    "LatestDate":       str(LatestDate)}
    myDB.upsert("comics", newlatestDict, latestCTRLValueDict)

def upcoming_update(ComicID, ComicName, IssueNumber, IssueDate, forcecheck=None):
    # here we add to upcoming table...
    myDB = db.DBConnection()

    controlValue = {"ComicID":      ComicID}
    newValue = {"ComicName":        str(ComicName),
                "IssueNumber":      str(IssueNumber),
                "IssueDate":        str(IssueDate)}

    #let's refresh the artist here just to make sure if an issue is available/not.
    mismatch = "no"
    CV_EXcomicid = myDB.action("SELECT * from exceptions WHERE ComicID=?", [ComicID]).fetchone()
    if CV_EXcomicid is None: pass
    else:
        if CV_EXcomicid['variloop'] == '99':
            mismatch = "yes"
    lastupdatechk = myDB.action("SELECT * FROM comics WHERE ComicID=?", [ComicID]).fetchone()
    if lastupdatechk is None:
        pullupd = "yes"
    else:
        c_date = lastupdatechk['LastUpdated']
        if c_date is None:
            logger.error(lastupdatechk['ComicName'] + " failed during a previous add /refresh. Please either delete and readd the series, or try a refresh of the series.")
            return
        c_obj_date = datetime.datetime.strptime(c_date, "%Y-%m-%d %H:%M:%S")
        n_date = datetime.datetime.now()
        absdiff = abs(n_date - c_obj_date)
        hours = (absdiff.days * 24 * 60 * 60 + absdiff.seconds) / 3600.0
        # no need to hammer the refresh 
        # let's check it every 5 hours (or more)
        #pullupd = "yes"

    issuechk = myDB.action("SELECT * FROM issues WHERE ComicID=? AND Issue_Number=?", [ComicID, IssueNumber]).fetchone()
    if issuechk is None:
        logger.fdebug(ComicName + " Issue: " + str(IssueNumber) + " not present in listings to mark for download...updating comic and adding to Upcoming Wanted Releases.")
        # we need to either decrease the total issue count, OR indicate that an issue is upcoming.
        upco_results = myDB.action("SELECT COUNT(*) FROM UPCOMING WHERE ComicID=?",[ComicID]).fetchall()
        upco_iss = upco_results[0][0]
        #logger.info("upco_iss: " + str(upco_iss))
        if int(upco_iss) > 0:
            #logger.info("There is " + str(upco_iss) + " of " + str(ComicName) + " that's not accounted for")
            newKey = {"ComicID": ComicID}
            newVal = {"not_updated_db": str(upco_iss)}
            myDB.upsert("comics", newVal, newKey)
        elif int(upco_iss) <=0 and lastupdatechk['not_updated_db']:
            #if not_updated_db has a value, and upco_iss is > 0, let's zero it back out cause it's updated now.
            newKey = {"ComicID": ComicID}
            newVal = {"not_updated_db": ""}
            myDB.upsert("comics", newVal, newKey)

        if hours > 5 or forcecheck == 'yes':
            pullupd = "yes"
            logger.fdebug("Now Refreshing comic " + ComicName + " to make sure it's up-to-date")
            if ComicID[:1] == "G": mylar.importer.GCDimport(ComicID,pullupd)
            else: mylar.importer.addComictoDB(ComicID,mismatch,pullupd)
        else:
            logger.fdebug("It hasn't been longer than 5 hours since we last did this...let's wait so we don't hammer things.")
            return
    elif issuechk['Issue_Number'] == IssueNumber:
        logger.fdebug("Comic series already up-to-date ... no need to refresh at this time.")
        logger.fdebug("Available to be marked for download - checking..." + str(issuechk['ComicName']) + " Issue: " + str(issuechk['Issue_Number']))
        logger.fdebug("...Existing status: " + str(issuechk['Status']))
        control = {"IssueID":   issuechk['IssueID']}
        newValue['IssueID'] = issuechk['IssueID']
        if issuechk['Status'] == "Snatched":
            values = { "Status":   "Snatched"}
            newValue['Status'] = "Snatched"
        elif issuechk['Status'] == "Downloaded":
            values = { "Status":    "Downloaded"}
            newValue['Status'] = "Downloaded"
            #if the status is Downloaded and it's on the pullist - let's mark it so everyone can bask in the glory

        elif issuechk['Status'] == "Wanted":
            values = { "Status":    "Wanted"}
            newValue['Status'] = "Wanted"            
        else:
            values = { "Status":    "Skipped"}
            newValue['Status'] = "Skipped"
        #was in wrong place :(
    if mylar.AUTOWANT_UPCOMING:
        #for issues not in db - to be added to Upcoming table.
        if issuechk is None:
            newValue['Status'] = "Wanted"
            logger.fdebug("...Changing Status to Wanted and throwing it in the Upcoming section since it's not published yet.")
        #this works for issues existing in DB...        
        elif issuechk['Status'] == "Skipped":
            newValue['Status'] = "Wanted"
            values = { "Status":  "Wanted"}
            logger.fdebug("...New status of Wanted")
        elif issuechk['Status'] == "Wanted":
            logger.fdebug("...Status already Wanted .. not changing.")
        else:
            logger.fdebug("...Already have issue - keeping existing status of : " + issuechk['Status'])
        if issuechk is None:
            myDB.upsert("upcoming", newValue, controlValue)
        else:
            logger.fdebug("--attempt to find errant adds to Wanted list")
            logger.fdebug("UpcomingNewValue: " + str(newValue))
            logger.fdebug("UpcomingcontrolValue: " + str(controlValue))
            myDB.upsert("issues", values, control)
            if issuechk['Status'] == 'Downloaded': 
                logger.fdebug("updating Pull-list to reflect status.")
                downstats = {"Status":  issuechk['Status'],
                             "ComicID": issuechk['ComicID']}
                return downstats
    else:
        logger.fdebug("Issues don't match for some reason...weekly new issue: " + str(IssueNumber))


def weekly_update(ComicName,IssueNumber,CStatus,CID):
    # here we update status of weekly table...
    # added Issue to stop false hits on series' that have multiple releases in a week
    # added CStatus to update status flags on Pullist screen
    myDB = db.DBConnection()
    issuecheck = myDB.action("SELECT * FROM weekly WHERE COMIC=? AND ISSUE=?", [ComicName,IssueNumber]).fetchone()
    if issuecheck is not None:
        controlValue = { "COMIC":         str(ComicName),
                         "ISSUE":         str(IssueNumber)}
        if CStatus:
            newValue = {"STATUS":             CStatus,
                        "ComicID":            CID}
        else:
            if mylar.AUTOWANT_UPCOMING:
                newValue = {"STATUS":             "Wanted"}
            else:
                newValue = {"STATUS":             "Skipped"}

        myDB.upsert("weekly", newValue, controlValue)

def newpullcheck(ComicName, ComicID):
    # When adding a new comic, let's check for new issues on this week's pullist and update.
    mylar.weeklypull.pullitcheck(ComicName, ComicID)
    return

def no_searchresults(ComicID):
    # when there's a mismatch between CV & GCD - let's change the status to
    # something other than 'Loaded'
    myDB = db.DBConnection()
    controlValue = { "ComicID":        ComicID}
    newValue = {"Status":       "Error",
                "LatestDate":   "Error",
                "LatestIssue":  "Error"}    
    myDB.upsert("comics", newValue, controlValue)

def nzblog(IssueID, NZBName, SARC=None, IssueArcID=None):
    myDB = db.DBConnection()

    newValue = {"NZBName":  NZBName}

    if IssueID is None or IssueID == 'None':
       #if IssueID is None, it's a one-off download from the pull-list.
       #give it a generic ID above the last one so it doesn't throw an error later.
       print "SARC detected as: " + str(SARC)
       if mylar.HIGHCOUNT == 0:
           IssueID = '900000'
       else: 
           IssueID = int(mylar.HIGHCOUNT) + 1
       
       if SARC:
           IssueID = 'S' + str(IssueArcID)
           newValue['SARC'] = SARC

    controlValue = {"IssueID": IssueID}
    #print controlValue
    #newValue['NZBName'] = NZBName
    #print newValue
    myDB.upsert("nzblog", newValue, controlValue)

def foundsearch(ComicID, IssueID, down=None):
    # When doing a Force Search (Wanted tab), the resulting search calls this to update.

    # this is all redudant code that forceRescan already does.
    # should be redone at some point so that instead of rescanning entire 
    # series directory, it just scans for the issue it just downloaded and
    # and change the status to Snatched accordingly. It is not to increment the have count
    # at this stage as it's not downloaded - just the .nzb has been snatched and sent to SAB.

    myDB = db.DBConnection()
    comic = myDB.action('SELECT * FROM comics WHERE ComicID=?', [ComicID]).fetchone()
    issue = myDB.action('SELECT * FROM issues WHERE IssueID=?', [IssueID]).fetchone()
    CYear = issue['IssueDate'][:4]

    if down is None:
        # update the status to Snatched (so it won't keep on re-downloading!)
        logger.fdebug("updating status to snatched")
        controlValue = {"IssueID":   IssueID}
        newValue = {"Status":    "Snatched"}
        myDB.upsert("issues", newValue, controlValue)

        # update the snatched DB
        snatchedupdate = {"IssueID":     IssueID,
                          "Status":      "Snatched"
                          }
        newsnatchValues = {"ComicName":       comic['ComicName'],
                           "ComicID":         ComicID,
                           "Issue_Number":    issue['Issue_Number'],
                           "DateAdded":       helpers.now(),
                           "Status":          "Snatched"
                           }
        myDB.upsert("snatched", newsnatchValues, snatchedupdate)
    else:
        snatchedupdate = {"IssueID":     IssueID,
                          "Status":      "Downloaded"
                          }
        newsnatchValues = {"ComicName":       comic['ComicName'],
                           "ComicID":         ComicID,
                           "Issue_Number":    issue['Issue_Number'],
                           "DateAdded":       helpers.now(),
                           "Status":          "Downloaded"
                           }
        myDB.upsert("snatched", newsnatchValues, snatchedupdate)


    #print ("finished updating snatched db.")
    logger.info(u"Updating now complete for " + comic['ComicName'] + " issue: " + str(issue['Issue_Number']))
    return

def forceRescan(ComicID,archive=None):
    myDB = db.DBConnection()
    # file check to see if issue exists
    rescan = myDB.action('SELECT * FROM comics WHERE ComicID=?', [ComicID]).fetchone()
    logger.info(u"Now checking files for " + rescan['ComicName'] + " (" + str(rescan['ComicYear']) + ") in " + str(rescan['ComicLocation']) )
    if archive is None:
        fc = filechecker.listFiles(dir=rescan['ComicLocation'], watchcomic=rescan['ComicName'], AlternateSearch=rescan['AlternateSearch'])
    else:
        fc = filechecker.listFiles(dir=archive, watchcomic=rescan['ComicName'], AlternateSearch=rescan['AlternateSearch'])
    iscnt = rescan['Total']
    havefiles = 0
    fccnt = int(fc['comiccount'])
    issnum = 1
    fcnew = []
    fn = 0
    issuedupechk = []
    issueexceptdupechk = []
    reissues = myDB.action('SELECT * FROM issues WHERE ComicID=?', [ComicID]).fetchall()
    while (fn < fccnt):  
        haveissue = "no"
        issuedupe = "no"
        try:
            tmpfc = fc['comiclist'][fn]
        except IndexError:
            break
        temploc= tmpfc['JusttheDigits'].replace('_', ' ')

#        temploc = tmpfc['ComicFilename'].replace('_', ' ')
        temploc = re.sub('[\#\']', '', temploc)
        logger.fdebug("temploc: " + str(temploc))
        if 'annual' not in temploc:
            #remove the extension here
            extensions = ('.cbr','.cbz')
            if temploc.lower().endswith(extensions):
                #logger.fdebug("removed extension for issue:" + str(temploc))
                temploc = temploc[:-4]
            deccnt = str(temploc).count('.')
            if deccnt > 1:
                #logger.fdebug("decimal counts are :" + str(deccnt))
                #if the file is formatted with '.' in place of spaces we need to adjust.
                #before replacing - check to see if digits on either side of decimal and if yes, DON'T REMOVE
                occur=1
                prevstart = 0
                digitfound = "no"
                decimalfound = "no"
                tempreconstruct = ''
                while (occur <= deccnt):
                    n = occur
                    start = temploc.find('.')
                    while start >=0 and n > 1:
                        start = temploc.find('.', start+len('.'))
                        n-=1
                    #logger.fdebug("occurance " + str(occur) + " of . at position: " + str(start))
                    if temploc[prevstart:start].isdigit():
                        if digitfound == "yes":
                            #logger.fdebug("this is a decimal, assuming decimal issue.")
                            decimalfound = "yes"
                            reconst = "." + temploc[prevstart:start] + " "
                        else:
                            #logger.fdebug("digit detected.")
                            digitfound = "yes"
                            reconst = temploc[prevstart:start]
                    else:
                        reconst = temploc[prevstart:start] + " "
                    #logger.fdebug("word: " + reconst)
                    tempreconstruct = tempreconstruct + reconst 
                    #logger.fdebug("tempreconstruct is : " + tempreconstruct)
                    prevstart = (start+1)
                    occur+=1
                #logger.fdebug("word: " + temploc[prevstart:])
                tempreconstruct = tempreconstruct + " " + temploc[prevstart:]
                #logger.fdebug("final filename to use is : " + str(tempreconstruct))
                temploc = tempreconstruct            
            #logger.fdebug("checking " + str(temploc))
            fcnew = shlex.split(str(temploc))            
            fcn = len(fcnew)
            n = 0
            while (n <= iscnt):
                som = 0
                try:
                    reiss = reissues[n]
                except IndexError:
                    break
                int_iss, iss_except = helpers.decimal_issue(reiss['Issue_Number'])
                issyear = reiss['IssueDate'][:4]
                old_status = reiss['Status']
                #logger.fdebug("integer_issue:" + str(int_iss) + " ... status: " + str(old_status))

                #if comic in format of "SomeSeries 5(c2c)(2013).cbr" whatever...it'll die.
                #can't distinguish the 5(c2c) to tell it's the issue #...
                fnd_iss_except = 'None'
                #print ("Issue, int_iss, iss_except: " + str(reiss['Issue_Number']) + "," + str(int_iss) + "," + str(iss_except))

                while (som < fcn):
                    #counts get buggered up when the issue is the last field in the filename - ie. '50.cbr'
                    #logger.fdebug("checking word - " + str(fcnew[som]))
                    if ".cbr" in fcnew[som].lower():
                        fcnew[som] = fcnew[som].replace(".cbr", "")
                    elif ".cbz" in fcnew[som].lower():
                        fcnew[som] = fcnew[som].replace(".cbz", "")
                    if "(c2c)" in fcnew[som].lower():
                        fcnew[som] = fcnew[som].replace("(c2c)", " ")
                        get_issue = shlex.split(str(fcnew[som]))
                        if fcnew[som] != " ":
                            fcnew[som] = get_issue[0]
                    if '.' in fcnew[som]:
                        #logger.fdebug("decimal detected...adjusting.")
                        try:
                            i = float(fcnew[som])
                        except ValueError, TypeError:
                            #not numeric
                            #logger.fdebug("NOT NUMERIC - new word: " + str(fcnew[som]))
                            fcnew[som] = fcnew[som].replace(".", "")
                        else:
                            #numeric
                            pass
                    if fcnew[som].isdigit():
                        #this won't match on decimal issues - need to fix.
                        #logger.fdebug("digit detected")
                        if int(fcnew[som]) > 0:
                            # fcdigit = fcnew[som].lstrip('0')
                            #fcdigit = str(int(fcnew[som]))
                            fcdigit = int(fcnew[som]) * 1000
                            if som+1 < len(fcnew) and 'au' in fcnew[som+1].lower():
                                if len(fcnew[som+1]) == 2:
                                    #if the 'AU' is in 005AU vs 005 AU it will yield different results.
                                    fnd_iss_except = 'AU'
                                    #logger.info("AU Detected - fnd_iss_except set.")
                        else: 
                            #fcdigit = "0"
                            fcdigit = 0
                    elif "." in fcnew[som]:
                        #this will match on decimal issues
                        IssueChk = fcnew[som]
                        #logger.fdebug("decimal detected...analyzing if issue")
                        isschk_find = IssueChk.find('.')
                        isschk_b4dec = IssueChk[:isschk_find]
                        isschk_decval = IssueChk[isschk_find+1:]
                        if isschk_b4dec.isdigit():
                            #logger.fdebug("digit detected prior to decimal.")
                            if isschk_decval.isdigit():
                                pass
                                #logger.fdebug("digit detected after decimal.")
                            else:
                                #logger.fdebug("not an issue - no digit detected after decimal")
                                break
                        else:
                            #logger.fdebug("not an issue - no digit detected prior to decimal")
                            break
                        #logger.fdebug("IssueNumber: " + str(IssueChk))
                        #logger.fdebug("..before decimal: " + str(isschk_b4dec))
                        #logger.fdebug("...after decimal: " + str(isschk_decval))
                        #--let's make sure we don't wipe out decimal issues ;)
                        if int(isschk_decval) == 0:
                            iss = isschk_b4dec
                            intdec = int(isschk_decval)
                        else:
                            if len(isschk_decval) == 1:
                                iss = isschk_b4dec + "." + isschk_decval
                                intdec = int(isschk_decval) * 10
                            else:
                                iss = isschk_b4dec + "." + isschk_decval.rstrip('0')
                                intdec = int(isschk_decval.rstrip('0')) * 10
                        fcdigit = (int(isschk_b4dec) * 1000) + intdec
                        #logger.fdebug("b4dec: " + str(isschk_b4dec))
                        #logger.fdebug("decval: " + str(isschk_decval))
                        #logger.fdebug("intdec: " + str(intdec))
                        #logger.fdebug("let's compare with this issue value: " + str(fcdigit))
                    elif 'au' in fcnew[som].lower():
                        #if AU is part of issue (5AU instead of 5 AU)
                        austart = fcnew[som].lower().find('au')
                        if fcnew[som][:austart].isdigit():
                            fcdigit = int(fcnew[som][:austart]) * 1000
                            fnd_iss_except = 'AU'
                            #logger.info("iss_except set to AU")
                    else:
                        # it's a word, skip it.
                        fcdigit = 19283838380101193
                    #logger.fdebug("fcdigit: " + str(fcdigit))
                    #logger.fdebug("int_iss: " + str(int_iss))
                    if "." in str(int_iss):
                         int_iss = helpers.decimal_issue(int_iss)
                    #logger.fdebug("this is the int issue:" + str(int_iss))
                    #logger.fdebug("this is the fcdigit:" + str(fcdigit))
                    if int(fcdigit) == int_iss:
                        #logger.fdebug("issue match")
                        #logger.fdebug("fnd_iss_except: " + str(fnd_iss_except))
                        #logger.fdebug("iss_except: " + str(iss_except))
                        if str(fnd_iss_except) != 'None' and str(iss_except) == 'AU':
                            if fnd_iss_except.lower() == iss_except.lower():
                                logger.fdebug("matched for AU")
                            else:
                                logger.fdebug("this is not an AU match..ignoring result.")
                                break                       
                        elif str(fnd_iss_except) == 'None' and str(iss_except) == 'AU':break
                        elif str(fnd_iss_except) == 'AU' and str(iss_except) == 'None':break
                        #if issyear in fcnew[som+1]:
                        #    print "matched on year:" + str(issyear)
                        #issuedupechk here.
                        #print ("fcdigit:" + str(fcdigit))
                        #print ("findiss_except:" + str(fnd_iss_except) + " = iss_except:" + str(iss_except))

                        #if int(fcdigit) in issuedupechk and str(fnd_iss_except) not in issueexceptdupechk: #str(fnd_iss_except) == str(iss_except):
                        for d in issuedupechk:
                            if int(d['fcdigit']) == int(fcdigit) and d['fnd_iss_except'] == str(fnd_iss_except):
                                logger.fdebug("duplicate issue detected - not counting this: " + str(tmpfc['ComicFilename']))
                                issuedupe = "yes"
                                break
                        if issuedupe == "no":
                            logger.fdebug("matched...issue: " + rescan['ComicName'] + "#" + str(reiss['Issue_Number']) + " --- " + str(int_iss))
                            havefiles+=1
                            haveissue = "yes"
                            isslocation = str(tmpfc['ComicFilename'])
                            issSize = str(tmpfc['ComicSize'])
                            logger.fdebug(".......filename: " + str(isslocation))
                            logger.fdebug(".......filesize: " + str(tmpfc['ComicSize'])) 
                            # to avoid duplicate issues which screws up the count...let's store the filename issues then 
                            # compare earlier...
                            issuedupechk.append({'fcdigit': int(fcdigit),
                                                 'fnd_iss_except': fnd_iss_except})
                        break
                        #else:
                        # if the issue # matches, but there is no year present - still match.
                        # determine a way to match on year if present, or no year (currently).

                    som+=1
                if haveissue == "yes": break
                n+=1
        #we have the # of comics, now let's update the db.
        #even if we couldn't find the physical issue, check the status.
        #if Archived, increase the 'Have' count.
        if archive:
            issStatus = "Archived"
        if haveissue == "no" and issuedupe == "no":
            isslocation = "None"
            if old_status == "Skipped":
                if mylar.AUTOWANT_ALL:
                    issStatus = "Wanted"
                else:
                    issStatus = "Skipped"
            elif old_status == "Archived":
                havefiles+=1
                issStatus = "Archived"
            elif old_status == "Downloaded":
                issStatus = "Archived"
                havefiles+=1
            elif old_status == "Wanted":
                issStatus = "Wanted"
            else:
                issStatus = "Skipped"
            controlValueDict = {"IssueID": reiss['IssueID']}
            newValueDict = {"Status":    issStatus }

        elif haveissue == "yes":
            issStatus = "Downloaded"
            controlValueDict = {"IssueID":  reiss['IssueID']}
            newValueDict = {"Location":           isslocation,
                            "ComicSize":          issSize,
                            "Status":             issStatus
                            }
        myDB.upsert("issues", newValueDict, controlValueDict)
        fn+=1


    logger.info("Total files located: " + str(havefiles))
    foundcount = havefiles
    arcfiles = 0
    # if filechecker returns 0 files (it doesn't find any), but some issues have a status of 'Archived'
    # the loop below won't work...let's adjust :)
    arcissues = myDB.action("SELECT count(*) FROM issues WHERE ComicID=? and Status='Archived'", [ComicID]).fetchall()
    if int(arcissues[0][0]) > 0:
        arcfiles = arcissues[0][0]
        havefiles = havefiles + arcfiles
        logger.fdebug("Adjusting have total to " + str(havefiles) + " because of this many archive files:" + str(arcfiles))


    #now that we are finished...
    #adjust for issues that have been marked as Downloaded, but aren't found/don't exist.
    #do it here, because above loop only cycles though found comics using filechecker.
    downissues = myDB.select("SELECT * FROM issues WHERE ComicID=? and Status='Downloaded'", [ComicID])
    if downissues is None:
        pass
    else:
        archivedissues = 0 #set this to 0 so it tallies correctly.
        for down in downissues:
            #print "downlocation:" + str(down['Location'])
            #remove special characters from 
            #temploc = rescan['ComicLocation'].replace('_', ' ')
            #temploc = re.sub('[\#\'\/\.]', '', temploc)
            #print ("comiclocation: " + str(rescan['ComicLocation']))
            #print ("downlocation: " + str(down['Location']))
            if down['Location'] is None:
                logger.fdebug("location doesn't exist which means file wasn't downloaded successfully, or was moved.")
                controlValue = {"IssueID":  down['IssueID']}
                newValue = {"Status":    "Archived"}
                myDB.upsert("issues", newValue, controlValue)
                archivedissues+=1
                pass
            else:
                comicpath = os.path.join(rescan['ComicLocation'], down['Location'])
                if os.path.exists(comicpath):
                    pass
                    #print "Issue exists - no need to change status."
                else:
                    #print "Changing status from Downloaded to Archived - cannot locate file"
                    controlValue = {"IssueID":   down['IssueID']}
                    newValue = {"Status":    "Archived"}
                    myDB.upsert("issues", newValue, controlValue)
                    archivedissues+=1 
        totalarc = arcfiles + archivedissues
        havefiles = havefiles + archivedissues  #arcfiles already tallied in havefiles in above segment
        logger.fdebug("I've changed the status of " + str(archivedissues) + " issues to a status of Archived, as I now cannot locate them in the series directory.")

        
    #let's update the total count of comics that was found.
    controlValueStat = {"ComicID":     rescan['ComicID']}
    newValueStat = {"Have":            havefiles
                   }

    myDB.upsert("comics", newValueStat, controlValueStat)
    logger.info(u"I've physically found " + str(foundcount) + " issues, and accounted for " + str(totalarc) + " in an Archived state. Total Issue Count: " + str(havefiles) + " / " + str(rescan['Total']))

    return

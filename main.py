#!/usr/bin/python2
# -*- coding: utf-8 -*-
from string import Template
import sys, getopt
import os.path
import re

import geocoder
class Settings:
    def __init__(self, vcardFileName, tempFilterRule, gpsCsvFileName, outputMRulesName, outputMScriptName ):
        self.tempFilterRule = tempFilterRule
        self.vcardFileName = vcardFileName
        self.gpsCsvFileName = gpsCsvFileName
        self.outputMScriptName = outputMScriptName
        self.outputMRulesName = outputMRulesName

class Address:
    def __init__(self, country, postcode, city, street, housenumber):
        self.country = country
        if country=='' or country == None:
            self.country = "Deutschland"

        self.postcode = postcode
        self.city = city
        self.street = street
        self.housenumber = housenumber
        if (street == '' or street == None):
            print >> sys.stderr, "ERROR: street missing on Contact "+name
        if (housenumber == '' or housenumber == None):
            print >> sys.stderr, "ERROR: "+name+" has no housenumber!"

    def toString(self):
        string = self.country
        if self.postcode != '' and self.postcode != None:
            string += ", "+str(self.postcode)
        if self.city != '' and self.city != None:
            string += ", "+str(self.city)
        if self.street != '' and self.street != None:
            string += ", "+str(self.street)
        if self.housenumber != '' and self.housenumber != None:
            string += ", "+str(self.housenumber)
        #return self.country+", "+str(self.postcode)+", "+self.city+", "+self.street+" "+str(self.housenumber)
        return string

    def lookupPosition(self):
        #g = geocoder.osm('Deutschland, 21379, Scharnebeck, Hülsenberg 6')
        print self.toString()
        g = geocoder.osm(self.toString())
        if (g.x == None)or(g.y == None):
            raise NameError("can't get lon/lat -> check your internet connection")
        return Position(g.x, g.y)

class Position:
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat

    def toString(self):
        return str(self.lat)+", "+ str(self.lon)

    #def toBbox(self, width, height):
    def toBbox(self):
        width = 0.005
        height = 0.0025
        top = self.lat+height/2
        bottom = self.lat-height/2
        left = self.lon-width/2
        right = self.lon+width/2
        return str(left)+","+str(bottom)+","+str(right)+","+str(top)

class Contact:
    def __init__(self, name, position, address):
        self.name = name

        # if no position is given - use the address to look one up
        if (position == None):
            print "has to lookup the address to get a gps position"
            self.position = address.lookupPosition()
        else:
            self.position = position
        self.address = address

    def toString(self):
        return self.name+" is from "+self.position.toString()

    def getPosition(self):
        return self.position


def createSingleContactRule(contact,settings):
    """
    creates a specific render rule to highlight the contact address building
    """
    filterTemplate = '(addr:housenumber=$housenumber AND addr:street="$street")'
    t = Template(filterTemplate)
    filter = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)

    file = "template.mrules"
    t = Template(open(file).read())
    new = t.substitute(filter=filter)
    out = open(settings.outputMRulesName, "w+").write(new)

def initFilter(contact,settings):
    """
    starts a filtering statement, to highlight multiple addresses
    """
    filterTemplate = '(addr:housenumber=$housenumber AND addr:street="$street")'
    t = Template(filterTemplate)
    new = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)
    out = open(settings.tempFilterRule, "w+").write(new)

def addFilter(contact,settings):
    """
    adds an address to a filtering statement, to highlight multiple addresses
    """
    filterTemplate = ' OR (addr:housenumber=$housenumber AND addr:street="$street")'
    t = Template(filterTemplate)
    new = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)
    out = open(settings.tempFilterRule, "a").write(new)

def finishMultiContactRule(settings):
    file = "template.mrules"
    filter = open(settings.tempFilterRule).read()
    t = Template(open(file).read())
    new = t.substitute(filter=filter)
    out = open(settings.outputMRulesName, "w+").write(new)
    #delete temporaty file
    os.remove(settings.tempFilterRule)


def createSingleContactScript(contact,settings):
    file = "template.mscript"
    t = Template(open(file).read())
    new = t.substitute(bbox= contact.position.toBbox(), rulename=contact.name, name=contact.name)
    out = open(settings.outputMScriptName, "w+").write(new)

def addToScript(contact, settings):
    file = "template.mscript"
    t = Template(open(file).read())
    new = t.substitute(bbox= contact.position.toBbox(),rulename=str(settings.outputMRulesName), name=contact.name)
    out = open(settings.outputMScriptName, "a+").write(new)

def getFirstHomeAddressFromRaw(text):
    pattern = re.compile('(?<=\nADR;TYPE=home:).*')
    match = pattern.search(text)
    if match:
        adrRaw = match.group(0).strip("\r").split(';')
        print adrRaw
        city = adrRaw[3]
        street = adrRaw[2]
        number = None
        try:
            street, number = street.rsplit(" ",1)
        except:
            number = None
        adr = Address(adrRaw[6],adrRaw[5],adrRaw[3],street,number)
        return adr
    return None

def getPositionFromRaw(text):
    pattern = re.compile('(?<=\nGEO:).*')
    match = pattern.search(text)
    if match:
        #extracts the prename name
        array = match.group(0).strip("\r").split(',')
        pos = Position(float(array[0]), float(array[1]))
        return pos
    return None

def getPreNameFromRaw(text):
    pattern = re.compile('(?<=\nN:).*')
    match = pattern.search(text)
    if match:
        #extracts the prename name
        return match.group(0).split(';')[1]
    return ""

def containsCategory(text,category):
    pattern = re.compile('\nCATEGORIES:.*'+category)
    match = pattern.search(text)
    if match:
        return True
    return False

def processSingleVCard(vcardText, settings):
    name = getPreNameFromRaw(vcardText)
    adr = getFirstHomeAddressFromRaw(vcardText)
    geo = getPositionFromRaw(vcardText)
    try:
        c = Contact(name, geo, adr)
    except:
        #TODO write fail log
        print >> sys.stderr, "ERROR: no location for "+name
        return None

    #log position:
    open(settings.gpsCsvFileName,"a+").write(c.name+", "+str(c.position.lat)+", "+str(c.position.lon)+"\n")

    if (os.path.exists(settings.tempFilterRule)):
        addFilter(c,settings)
        print "added filter for "+c.name
    else:
        initFilter(c, settings)
        print "initicialize filter with "+c.name

    addToScript(c, settings)
    print "added "+c.name+" to render script"

def processMultiVCard(settings):
    finishFlag = False

    vCardFile = open(settings.vcardFileName, 'r')

    idx = 0
    count = 0
    vcardStarted = False
    vcardBuffer = ""
    while True:
        line = vCardFile.readline()
        if not line:
            break

        if line.startswith('BEGIN:VCARD'):
            vcardStarted = True
            idx = idx + 1
            vcardBuffer = ""

        if vcardStarted:
            vcardBuffer += line

        if line.startswith('END:VCARD'):
            vcardStarted = False
            if containsCategory(vcardBuffer, 'Gast'):
                count = count + 1
                print "read vcard no: "+str(idx) + " gast count: "+str(count)
                print vcardBuffer
                processSingleVCard(vcardBuffer, settings)


    vCardFile.close()
    print '\nused ' + str(idx) + ' vCards';


def main(argv):

    vcardfilename = ""

    try:
        opts, args = getopt.getopt(argv,"?f:",["help","vcardfile="])
    except getopt.GetoptError:
        print 'main.py -f <vcard-file> [-?]'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-?', "help"):
            print 'main.py -f <vcard-file> [-?]'
            sys.exit()
        elif opt in ("-f", "--vcardfile"):
            vcardfilename = arg

    tempFileFilterRuleName = "temp.filter_rule"
    gpsCsvFileName = "posdb"
    outputMRulesName = str("Contacts.mrules")
    outputMScriptName = str("Contacts.mscritp")
    settings = Settings(vcardfilename,tempFileFilterRuleName, gpsCsvFileName, outputMRulesName, outputMScriptName)
    print "Processing VCard "+settings.vcardFileName
    processMultiVCard(settings)
    finishMultiContactRule(settings)

if __name__ == "__main__":
   main(sys.argv[1:])

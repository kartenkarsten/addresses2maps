#!/usr/bin/python2
# -*- coding: utf-8 -*-
from string import Template
import sys, getopt
import os.path
import re

import geocoder
class Address:
    def __init__(self, country, postcode, city, street, housenumber):
        self.country = country
        if country=='' or country == None:
            self.country = "Deutschland"

        self.postcode = postcode
        self.city = city
        self.street = street
        self.housenumber = housenumber

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




def createSingleContactRule(contact):
    """
    creates a specific render rule to highlight the contact address building
    """
    filterTemplate = '(addr:housenumber=$housenumber AND addr:street="$street")'
    t = Template(filterTemplate)
    filter = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)

    file = "template.mrules"
    t = Template(open(file).read())
    new = t.substitute(filter=filter)
    out = open(contact.name+".mrules", "w+").write(new)

def initFilter(contact):
    """
    starts a filtering statement, to highlight multiple addresses
    """
    filterTemplate = '(addr:housenumber=$housenumber AND addr:street="$street")'
    t = Template(filterTemplate)
    new = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)
    out = open("temp.filter_mrules", "w+").write(new)

def addFilter(contact):
    """
    adds an address to a filtering statement, to highlight multiple addresses
    """
    filterTemplate = ' OR (addr:housenumber=$housenumber AND addr:street="$street")'
    t = Template(filterTemplate)
    new = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)
    out = open("temp.filter_mrules", "a").write(new)

def finishMultiContactRule(rulename):
    file = "template.mrules"
    filter = open("temp.filter_mrules").read()
    t = Template(open(file).read())
    new = t.substitute(filter=filter)
    out = open(rulename+".mrule", "w+").write(new)
    #delete temporaty file
    os.remove("temp.filter_mrules")


def createSingleContactScript(contact):
    file = "template.mscript"
    t = Template(open(file).read())
    new = t.substitute(bbox= contact.position.toBbox(), rulename=contact.name, name=contact.name)
    out = open(contact.name+".mscript", "w+").write(new)

def addToScript(scriptName, ruleName, contact):
    file = "template.mscript"
    t = Template(open(file).read())
    new = t.substitute(bbox= contact.position.toBbox(),rulename=ruleName, name=contact.name)
    out = open(filename+".mscript", "a+").write(new)

def main(argv):
    p = Position(10.4951302,53.2929971)

#TODO parse name + addr parameter with getopt
    name = "Karsten"
    country = "Deutschland"
    postcode = "21379"
    city = "Scharnebeck"
    street = "Hülsenberg"
    housenumber = "6"

    finishFlag=False;
    multipleFlag=False;

    try:
        opts, args = getopt.getopt(argv,"?n:cp:i:s:h:fm",["name=","country=","postcode=","city=","street=","housenumber=","finish", "multiple"])
    except getopt.GetoptError:
        print 'main.py -n <name> -c <country> -p <postcode> -i <city> -s <street> -h <housenumber> [-?]'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-?':
            print 'main.py -n <name> -c <country> -p <postcode> -i <city> -s <street> -h <housenumber>'
            print '        [-m [-f] ]'
            print ' no real address data is needed for use with -f'
            sys.exit()
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-c", "--country"):
            country = arg
        elif opt in ("-p", "--postcode"):
            postcode = arg
        elif opt in ("-i", "--city"):
            city = arg
        elif opt in ("-s", "--street"):
            street = arg
        elif opt in ("-h", "--housenumber"):
            housenumber = arg
        elif opt in ("-f", "--finish"):
            finishFlag = True
        elif opt in ("-m", "--multiple"):
            multipleFlag = True

    print "Processing data for "+name

    addr = Address(country, postcode, city, street, housenumber)

    c = Contact(name, None, addr)
    print c.toString()

    if (multipleFlag == False):
        createSingleContactRule(c)
        print "render rule created"
        createSingleContactScript(c)
        print "render script created"
    else:
        multiRuleName = "Contacts.mrule"
        multiScriptName = "Contacts.mscript"
        if (finishFlag == True):
            finishMultiContactRule(multiRuleName)
        elif (os.path.exists("temp.filter_mrules")):
            addFilter(c)
            print "added filter for "+c.name
            addToScript(multiScriptName,multiRuleName, c)
            print "added "+c.name+" to render script"
        else:
            initFilter(c)
            print "initicialize filter with "+c.name
            addToScript(multiScriptName,multiRuleName, c)
            print "added "+c.name+" to render script"


def getFirstHomeAddressFromRaw(text):
    pattern = re.compile('(?<=\nADR;TYPE=home:).*')
    match = pattern.search(text)
    if match:
        adrRaw = match.group(0).split(';')
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

def getPreNameFromRaw(text):
    pattern = re.compile('(?<=\nN:).*')
    match = pattern.search(text)
    if match:
        #extracts the prename name
        return match.group(0).split(';')[1]
    return ""

def precheckContainsCategory(text,category):
    pattern = re.compile('\nCATEGORIES:.*'+category)
    match = pattern.search(text)
    if match:
        return True
    return False

def processMultiVCard(filename):
    finishFlag = False

    vCardFile = open(filename, 'r')

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
            if precheckContainsCategory(vcardBuffer, 'Gast'):
                count = count + 1
                print "read vcard no: "+str(idx) + " gast count: "+str(count)
                print vcardBuffer

                name = getPreNameFromRaw(vcardBuffer)
                adr = getFirstHomeAddressFromRaw(vcardBuffer)
                try:
                    c = Contact(name, None, adr)
                except:
                    count = count -1
                    #TODO write fail log
                    print >> sys.stderr, "ERROR: no location for "+name
                    continue

                #log position:
                open("posdb","a+").write(c.name+", "+str(c.position.lat)+", "+str(c.position.lon)+"\n")

                multiRuleName = "Contacts.mrule"
                multiScriptName = "Contacts.mscript"
                if (finishFlag == True):
                    finishMultiContactRule(multiRuleName)
                elif (os.path.exists("temp.filter_mrules")):
                    addFilter(c)
                    print "added filter for "+c.name
                    addToScript(multiScriptName,multiRuleName, c)
                    print "added "+c.name+" to render script"
                else:
                    initFilter(c)
                    print "initicialize filter with "+c.name
                    addToScript(multiScriptName,multiRuleName, c)
                    print "added "+c.name+" to render script"

    vCardFile.close()
    print '\nused ' + str(idx) + ' vCards';

#c = open("card.vcf").read()
filename = "Contacts.vcf"
#filename = "card.vcf"
processMultiVCard(filename)

#if __name__ == "__main__":
#   main(sys.argv[1:])

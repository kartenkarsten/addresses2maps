#!/usr/bin/python2
# -*- coding: utf-8 -*-
# uses geocoder, pycarddav
from string import Template
import geocoder
import vobject
import StringIO
import sys
#import models

class Contact:
    def __init__(self, name, position):
        self.name = name
        self.position = position
#        self.streetAndNumber = None
#        self.contry = None
#        self.city = None
#        self.postcode = None

    def toString(self):
        return self.name+" is from "+self.position.toString()

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

def getPosition(search):
    #g = geocoder.osm('Deutschland, 21379, Scharnebeck, Hülsenberg 6')
    g = geocoder.osm(search)
    #print g
    return Position(g.x, g.y)

def getAddr(vcard):
    try:
        print vcard.adr.value,"\n"
    except:
        print "fail"

#def openFile(location):
#    try:
#        f = open(location, 'r')
#        return f
#    except:
#        print "Error opening the file"

def getFileContent(fd):
    return fd.readlines()

def parseVcf(vcfStr):
    count = 0
    vcards_per_file = 0
    for line in vcfStr:
        if ("BEGIN:VCARD" in line):
            count += 1
        if (count <= vcards_per_file):
            results.append(line)

def createScript(contact):
    file = "template.mscript"
    t = Template(open(file).read())
#    template = open(file, "r").read()
#    template.replace("$$$bbox$$$", contact.position.toBbox)
#    template.replace("$$$name$$$", contact.name)
    new = t.substitute(bbox= contact.position.toBbox(), name=contact.name)
    out = open(contact.name+".mscript", "w+").write(new)
    return

def main(argv):
    p = Position(10.4951302,53.2929971)
    if (len(sys.argv) < 2):
        print "ERROR: too less parameter"
        return
    name = sys.argv[1]
    search = sys.argv[2]
    print "Processing data for "+name
    #location = getPosition(search)
    location = p
    c = Contact(name, location)
    print c.toString()
    createScript(c)
    print location.toString()
    print location.toBbox()

#    print "Vcard 2 lon lat"
#    card = "card.vcf"
#    vcards = dict()
#    fcard = open(card, "r")
#    try:
#        for vcard in vobject.readComponents(fcard):
#            name = vcard.fn.value
#            vcards[name] = vcard
#    except Exception, v:
#        print >> sys.stderr, "Warning, %s: %s" % (card, v)
#        fcard.close()
#        return
#    fcard.close()
#
#    for (name, vcard) in vcards.items():
#        print "->",name
#        getAddr(vcard)
#        print "\n"

#with open('Contacts.vcf', 'r') as content_file:
#    content = content_file.read()
#
#f = StringIO.StringIO(content)
#v = vobject.readOne( content )
#
##v2 = vobject.readComponents(f).next()
##print v2.component
#for v3 in vobject.readComponents(f):
#    getAddr(v3)
##v.prettyPrint()

if __name__ == "__main__":
   main(sys.argv[1:])

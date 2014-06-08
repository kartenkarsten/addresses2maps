#!/usr/bin/python2
# -*- coding: utf-8 -*-
from string import Template
import sys, getopt
import os.path
import re
#svg post processing
from pysvg.filter import *
from pysvg.gradient import *
from pysvg.linking import *
from pysvg.script import *
from pysvg.shape import *
from pysvg.structure import *
from pysvg.style import *
from pysvg.text import *
from pysvg.builders import *
import pysvg.parser

import geocoder
class Settings:
    def __init__(self, vcardFileName, outVCard, tempFilterRule, gpsCsvFileName, contactNameToExtract, outputMRulesName, outputMScriptName, outDir, logFile ):
        self.tempFilterRule = tempFilterRule
        self.vcardFileName = vcardFileName
        self.outVCard = outVCard
        self.gpsCsvFileName = gpsCsvFileName
        self.outputMScriptName = outputMScriptName
        self.outputMRulesName = outputMRulesName
        self.outDir = outDir
        self.logFile = logFile
        self.contactNameToExtract = contactNameToExtract

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
            self.street = None
            print >> sys.stderr, "ERROR: Address has no street!"
        if (housenumber == '' or housenumber == None):
            self.housenumber = None
            print >> sys.stderr, "ERROR: Address has no housenumber!"

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
        return Position(g.y, g.x)

class Position:
    def __init__(self, lat,lon):
        self.lon = lon
        self.lat = lat

    def toString(self):
        return str(self.lat)+";"+ str(self.lon)

    #def toBbox(self, width, height):
    def toBbox(self):
        width = 0.005
        height = 0.0015
        top = self.lat+height/2
        bottom = self.lat-height/2
        left = self.lon-width/2
        right = self.lon+width/2
        return str(left)+","+str(bottom)+","+str(right)+","+str(top)

class Contact:
    def __init__(self, name, position, address):
        self.name = name

        if address.housenumber is None or address.street is None:
            raise NameError("can not use this address :"+address.toString)

        # if no position is given - use the address to look one up
        if (position == None):
            print "has to lookup the address to get a gps position"
            self.position = address.lookupPosition()
            if self.position is None:
                raise NameError("could not find coordinates to this address :"+address.toString)
            print self.position.toString()
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
    filterTemplate = '(addr:housenumber="$housenumber" AND addr:street="$street")'
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
    filterTemplate = '(addr:housenumber="$housenumber" AND addr:street="$street")'
    t = Template(filterTemplate)
    new = t.substitute(street=contact.address.street, housenumber=contact.address.housenumber)
    out = open(settings.tempFilterRule, "w+").write(new)

def addFilter(contact,settings):
    """
    adds an address to a filtering statement, to highlight multiple addresses
    """
    filterTemplate = ' OR (addr:housenumber="$housenumber" AND addr:street="$street")'
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
    osmGetDataCommand= "download-osm-overpass"
    t = Template(open(file).read())
    new = t.substitute(bbox= contact.position.toBbox(), rulename=contact.name, name=contact.name, outputDir=settings.outDir, osmGetDataCommand=getDataCommand)
    out = open(settings.outputMScriptName, "w+").write(new)

def addToScript(contact, settings):
    file = "template.mscript"
    t = Template(open(file).read())
    #TODO put this in settings
    getDataCommand= 'load-source "/home/karsten/workspace/projekte/osm/tischkarten/'+contact.position.toString()+'.osm"'
    #osmGetDataCommand= "download-osm-overpass"
    new = t.substitute(bbox= contact.position.toBbox(), rulename=str(settings.outputMRulesName), name=contact.name, outputDir=settings.outDir, osmGetDataCommand=getDataCommand)
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
        array = match.group(0).strip("\r").split(';')
        pos = Position(float(array[0]), float(array[1]))
        return pos
    return None

def setGeoToRaw(text, position):
    #try search and replace
    if (getPositionFromRaw(text) is None):
        print "insert gps data"
        #get new line char
        nl = "\n"
        if re.search('(?<=\r\n)', text) is not None:
            nl = "\r\n"
        #insert it
        newText = re.sub('(?<=\n)()(?=END:VCARD)', "GEO:"+position.toString()+nl, text)
    else:
        print "update old gps data"
        newText = re.sub('(?<=\nGEO:)((\-?\d+(\.\d+)?);\s*(\-?\d+(\.\d+)?))(?=\r?)', position.toString(), text)
    return newText

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
        print >> sys.stderr, "ERROR: on parsing "+name+" incomlpete address or position lookup failed"
        try:
            addrString = adr.toString()
        except:
            addrString = "None"
        f = open(settings.logFile,"a+").write("ERROR: in "+settings.vcardFileName+" on "+name+" address incomplete or position lookup faild ("+addrString+")\n")
        return None

    if not (os.path.exists(c.position.toString()+".osm")):
        downloadOsmData(c.position.toBbox(),c.position.toString()+".osm")
    newVCardText = setGeoToRaw(vcardText, c.position)
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
    return newVCardText

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
            if inFilter(vcardBuffer, settings):
                count = count + 1
                print "read vcard no: "+str(idx) + " gast count: "+str(count)
                print vcardBuffer
                vcard = processSingleVCard(vcardBuffer, settings)
                if vcard is not None:
                    outFile = open(settings.outVCard, "a+").write(vcard)


    vCardFile.close()
    print '\nused ' + str(idx) + ' vCards';

def inFilter(vcardText, settings):
    allowed = False
    nameMatches = False
    categoryMatches = False
    if settings.contactNameToExtract is None:
        nameMatches = True
    elif getPreNameFromRaw(vcardText).lower == settings.contactNameToExtract.lower:
        nameMatches = True
    else:
        nameMatches = False

    categoryMatches = containsCategory(vcardText, 'Gast')

    allowed = nameMatches and categoryMatches
    return allowed

def svgAddName(filename, name):
    svg = pysvg.parser.parse(filename)
    h = float(svg.get_height())
    w = float(svg.get_width())
    print h
    oh = ShapeBuilder()
    leftOffset = 40
    charWidth = 20
    gap = 13
    #x1,y1,x2,y2
    for i in range(len(name)):
        svg.addElement(oh.createLine(leftOffset+i*(charWidth+gap), h*1/5, leftOffset+charWidth+i*(charWidth+gap), h*1/5, strokewidth=3, stroke="black"))
    svg.save("/tmp/test.svg")

def convertSvgToPng(filename):
    #TODO use filename
    outfile,extension = filename.rsplit(".",1)
    os.system("inkscape -f '"+filename+"' -z -e '"+outfile+".png' -w 1122 -h 531")

def convertSvgsInDir(path):
    for file in os.listdir(path):
        if file.endswith(".svg"):
            filename = path+"/"+file
            print filename
            convertSvgToPng(filename)

def convertPngsToPnggroups(path):
    groupCount = 0
    groups = []
    pngs = []
    for file in os.listdir(path):
        if file.endswith(".png"):
            filename = path+"/"+file
            print filename
            pngs.append(filename)
            if len(pngs) == 10:
                outFile = "/tmp/group_"+str(groupCount)+".png"
                files = '" "'.join(pngs)

                #merge 10 images to a big one
                command = 'montage "'+files+'" -tile 2x5 -geometry +0+10 '+outFile
                print command
                os.system(command)
                groups.append(outFile)
                groupCount = groupCount + 1
                pngs = []

    if len(pngs) != 0:
        outFile = "group_"+str(groupCount)+".png"

        #merge as well the last images to a big one
        command = 'montage "'+('" "'.join(pngs))+'" -tile 2x5 -geometry +0+10 '+outFile
        print command
        os.system(command)
        groups.append(outFile)
    return groups

def rmPnggroups(pnggroups):
    command = 'rm "'+('" "'.join(pnggroups))+'"'
    print command
    os.system(command)

def convertPnggroupsToPdf(pnggroups, outFile):
    command = 'convert "'+('" "'.join(pnggroups))+'" -repage 2480x3508+25+100 -units PixelsPerInch -density 300x300 '+outFile
    print command
    os.system(command)


def downloadOsmData(bboxOverpass,name):
#    server = "overpass.osm.rambler.ru/cgi/interpreter"
#    querry = "data=(node("+bboxOverpass+");rel(bn)->.x;way("+bboxOverpass+");node(w)->.x;rel(bw););out;"
    querry = "http://overpass-api.de/api/map?bbox="+bboxOverpass
    command = "wget -O '"+name+"' '"+querry+"'"
    print command
    os.system(command)

def usage():
    print 'main.py -f <vcard-file> [-h]'

def getSettings():
    tempFileFilterRuleName = "temp.filter_rule"
    gpsCsvFileName = "posdb"
    contactNameToExtract = None
    outputMRulesName = str("Contacts.mrules")
    outputMScriptName = str("Contacts.mscript")
    outVCard = "out.vcf"
    outDir = "/tmp/"#has to stop with /
    logFile = "log"
    return Settings(None, outVCard, tempFileFilterRuleName, gpsCsvFileName,contactNameToExtract, outputMRulesName, outputMScriptName, outDir, logFile)

def main(argv):

    try:
        opts, args = getopt.getopt(argv,"hf:cn:p",["help","vcardfile=","convert","contact-name=","convert2pdf"])
    except getopt.GetoptError as err:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    settings = getSettings()
    for opt, arg in opts:
        if opt in ('-?', "help",'-h'):
            usage()
            sys.exit()
        elif opt in ("-c", "--convert"):
            convertSvgsInDir("/tmp")
            return
        elif opt in ("-p", "--convert2pdf"):
            workingDir = "/tmp"
            print "starting to merge pngs..."
            pnggroups = convertPngsToPnggroups(workingDir)
            print "starting to convert merged pngs to pdf..."
            outFile = "mapsToPrint.pdf"
            convertPnggroupsToPdf(pnggroups, outFile)
            rmPnggroups(pnggroups)
            return
        elif opt in ("-n", "--name"):
            settings.contactNameToExtract = arg
        elif opt in ("-f", "--vcardfile"):
            settings.vcardFileName = arg
        else:
            assert False, "unhandled option"

    if settings.vcardFileName is None:
        print "No vcf File specified!"
        usage()
        sys.exit(2)


    if os.path.exists(settings.outVCard):
        os.remove(settings.outVCard)
    if os.path.exists(settings.outputMScriptName):
        os.remove(settings.outputMScriptName)
    if os.path.exists(settings.outVCard):
        os.remove(settings.outVCard)


    print "Processing VCard "+settings.vcardFileName
    processMultiVCard(settings)
    finishMultiContactRule(settings)

if __name__ == "__main__":
   main(sys.argv[1:])

#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# Known Bugs:
#  - downloaded osm-data are sometimes incomplete if there is a way without a point in that area
#  -> possible workaround - just use a bigger area for download or fix suspicious files with JOSM
#
# Licence:
#  The MIT License (MIT)
#  -> see LICENCE File
#
# TODO:
#  - use for each vcf-file a seperate temp dir
#  - let change filter by category with parameter
#  - split Code in multiple files
#  - improve svg post processing (to insert Contact name)
#  - add osm raw data pre processing (to set street and housnumber to the building)
#  - os independence

from string import Template
import sys, getopt
import os
import re
import csv
import geocoder
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

class Settings:
    def __init__(self, vcardFileName, csvFileName, outVCard, tempFilterRule, gpsCsvFileName, contactNamesToExtract, categoriesToExtract, outputMRulesName, outputMScriptName, dataDir, logFile ):
        self.tempFilterRule = tempFilterRule
        self.vcardFileName = vcardFileName
        self.csvFileName = csvFileName
        self.cacheDir = str(dataDir) + "cache/"
        if not os.path.exists(self.cacheDir):
            os.makedirs(self.cacheDir)
        self.outDir = str(dataDir) + "raw_svgs/"
        if not os.path.exists(self.outDir):
            os.makedirs(self.outDir)
        self.dataDir = str(dataDir)
        self.templateDir = str(dataDir)
        self.outVCard = str(self.outDir) + outVCard
        self.gpsCsvFileName = str(self.cacheDir) + gpsCsvFileName
        self.outputMScriptName = str(self.outDir) + outputMScriptName
        self.outputMRulesName = str(self.outDir) + outputMRulesName
        self.logFile = str(self.outDir) + logFile
        self.contactNamesToExtract = contactNamesToExtract
        self.categoriesToExtract = categoriesToExtract

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

    file = settings.templateDir + "template.mrules"
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
    file = settings.templateDir + "template.mrules"
    filter = open(settings.tempFilterRule).read()
    t = Template(open(file).read())
    new = t.substitute(filter=filter)
    out = open(settings.outputMRulesName, "w+").write(new)
    #delete temporaty file
    os.remove(settings.tempFilterRule)


def createSingleContactScript(contact,settings):
    file = settings.templateDir + "template.mscript"
    osmGetDataCommand= "download-osm-overpass"
    t = Template(open(file).read())
    new = t.substitute(bbox= contact.position.toBbox(), rulename=contact.name, name=contact.name, outputDir=settings.outDir, osmGetDataCommand=getDataCommand)
    out = open(settings.outputMScriptName, "w+").write(new)

def addToScript(contact, settings):
    file = settings.templateDir + "template.mscript"
    t = Template(open(file).read())
    #TODO put this in settings
    getDataCommand= 'load-source "'+settings.cacheDir+contact.position.toString()+'.osm"'
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

def getCategoriesFromRaw(text):
    pattern = re.compile('(?<=\nCATEGORIES:).*')
    match = pattern.search(text)
    if match:
        #extracts the prename name
        return match.group(0).strip("\r").split(',')
    return ""

def containsCategory(text,category):
    pattern = re.compile('\nCATEGORIES:.*'+category)
    match = pattern.search(text)
    if match:
        return True
    return False

# Contact, Settings
def processContact(c, settings):
    if not (os.path.exists(settings.cacheDir + c.position.toString()+".osm")):
        downloadOsmData(c.position.toBbox(), settings.cacheDir + c.position.toString()+".osm")
    #log position:
    open(settings.gpsCsvFileName,"a+").write(c.name+";"+c.address.street+";"+c.address.housenumber+";"+c.address.postcode+";"+c.address.city+";"+c.address.country+";"+str(c.position.lat)+"/"+str(c.position.lon)+"\n")
    if (os.path.exists(settings.tempFilterRule)):
        addFilter(c,settings)
        print "added filter for "+c.name
    else:
        initFilter(c, settings)
        print "initialize filter with "+c.name

    addToScript(c, settings)
    print "added "+c.name+" to render script"

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
        f = open(settings.logFile,"a+").write("ERROR: in "+settings.vcardFileName+" on "+name+" address incomplete or position lookup failed ("+addrString+")\n")
        return None

    newVCardText = setGeoToRaw(vcardText, c.position)
    processContact(c, settings)
    return newVCardText

def processCsv(settings):
    # reads csv file and calls processContact for each line
    with open(settings.csvFileName, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';')
        for row in csvreader:
            print(row)
            print("length; "+str(len(row)))
            assert len(row)==7
            # country, postcode, city, street, housenumber):
            adr = Address(row[5],row[3],row[4],row[1],row[2])
            if ("" == row[6]):
                c = Contact(row[0], adr.lookupPosition(), adr)
                processContact(c, settings)
            elif ('/' in row[6]):
                coordninates = row[6].split('/', 1)
                geo = Position(float(coordninates[0]),float(coordninates[1]))
                c = Contact(row[0], geo, adr)
                processContact(c, settings)
            else:
                raise NameError("ERROR: can invalid value for gps position in csv")

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
            if inContactFilter(vcardBuffer, settings):
                count = count + 1
                print "read vcard no: "+str(idx) + " gast count: "+str(count)
                print vcardBuffer
                vcard = processSingleVCard(vcardBuffer, settings)
                if vcard is not None:
                    outFile = open(settings.outVCard, "a+").write(vcard)


    vCardFile.close()
    print '\nused ' + str(idx) + ' vCards';

def inContactFilter(vcardText, settings):
    allowed = False

    if len(settings.contactNamesToExtract) is 0:
        #by default true
        nameMatches = True
    elif getPreNameFromRaw(vcardText).lower() in settings.contactNamesToExtract:
        nameMatches = True
    else:
        nameMatches = False

    #categoryMatches = containsCategory(vcardText, 'Gast')
    categories = getCategoriesFromRaw(vcardText)
    categoryMatches = len(set(categories).intersection(set(settings.categoriesToExtract)))!=0
    if len(settings.categoriesToExtract)==0:
        #by default true
        categoryMatches = True

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
    svg.save("/data/test.svg")

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
                outFile = "/data/group_"+str(groupCount)+".png"
                files = '" "'.join(pngs)

                #merge 10 images to a big one
                command = 'montage "'+files+'" -tile 2x6 -geometry +0+0 '+outFile
                print command
                os.system(command)
                groups.append(outFile)
                groupCount = groupCount + 1
                pngs = []

    if len(pngs) != 0:
        outFile = "group_"+str(groupCount)+".png"

        #merge as well the last images to a big one
        command = 'montage "'+('" "'.join(pngs))+'" -tile 2x6 -geometry +0+0 '+outFile
        print command
        os.system(command)
        groups.append(outFile)
    return groups

def renderMaps(mscriptFileName):
    command = "maperitive-bin `pwd`/Contacts.mscript"
    print command
    os.system(command)

def rmPnggroups(pnggroups):
    command = 'rm "'+('" "'.join(pnggroups))+'"'
    print command
    os.system(command)

def convertPnggroupsToPdf(pnggroups, outFile):
    command = 'convert "'+('" "'.join(pnggroups))+'" -repage 2480x3508+25+25 -units PixelsPerInch -density 300x300 '+outFile
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
    gpsCsvFileName = "addresses_with_coordinates.csv"
    contactNamesToExtract = []
    categoriesToExtract = []
    outputMRulesName = str("Contacts.mrules")
    outputMScriptName = str("Contacts.mscript")
    outVCard = "out.vcf"
    dataDir = "/data/"#has to stop with /
    defaultVcardName = dataDir+"addresses.vcf"
    defaultCsvName = dataDir+"addresses.csv"
    logFile = "log"
# todo create cache and out dir if not existent
    return Settings(defaultVcardName, defaultCsvName, outVCard, tempFileFilterRuleName, gpsCsvFileName,contactNamesToExtract, categoriesToExtract, outputMRulesName, outputMScriptName, dataDir, logFile)

def main(argv):

    try:
        opts, args = getopt.getopt(argv,"hf:cn:k:pr",["help","vcardfile=","convert","contact-name=","categories=","convert2pdf","render"])
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
            print "-------------------------------------------------------"
            print "to group the png-files and convert them to pdf run option -p"
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
        elif opt in ("-r", "--render"):
            renderMaps(settings.outputMScriptName)
            print "-------------------------------------------------------"
            print "first edit the svg-files if you like (but they will be overwritten after rerun with option -r)"
            print " -> run this script with option -c to convert to png-files"
            return
        elif opt in ("-n", "--names"):
            settings.contactNamesToExtract = arg.lower().split(";")
            print settings.contactNamesToExtract
        elif opt in ("-k", "--categories"):
            settings.categoriesToExtract = arg.split(";")
            print settings.categoriesToExtract
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


    #print "Processing VCard "+settings.vcardFileName
    #processMultiVCard(settings)
    print "Processing CSV "+settings.vcardFileName
    processCsv(settings)
    finishMultiContactRule(settings)
    #finishMultiContactScript
    open(settings.outputMScriptName, "a+").write("exit")
    print "-------------------------------------------------------"
    print "edit the osm-files if you like"
    print "see log file for errors"
    print "-> continue with option -r"

if __name__ == "__main__":
   main(sys.argv[1:])

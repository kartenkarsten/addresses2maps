#!/usr/bin/python3
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
#svg post processing
import pysvg.parser
from pysvg.builders import *
from pysvg.text import *
from pysvg.style import *

class Settings:
    def __init__(self, showNamePlaceholder, showIdx, idxOffset):
        self.inDir = "./raw_svgs/"
        self.outDir = "./out/"
        if not os.path.exists(self.outDir):
            os.makedirs(self.outDir)
        self.idxOffset = idxOffset
        self.showIdx = showIdx
        self.showNamePlaceholder = showNamePlaceholder

def getSettings():
    return Settings(True, True, 0)


def svgAddName(filename, name, idx, settings):
    svg = pysvg.parser.parse(filename)
    h = float(svg.get_height())
    w = float(svg.get_width())
    print("render '"+name+"' to "+filename)
    oh = ShapeBuilder()
    leftOffset = 40
    charWidth = 20*1.7
    charheight = charWidth*2.5
    gap = 13*1.7

    if settings.showNamePlaceholder:
        #x1,y1,x2,y2
        for i in range(len(name)):
            svg.addElement(oh.createRect(leftOffset+i*(charWidth+gap)-gap/4, h*1/5-(h*1/12), charWidth+gap/2, charheight, strokewidth=1, stroke='black', fill='white'))
            #svg.addElement(oh.createLine(leftOffset+i*(charWidth+gap), h*1/5, leftOffset+charWidth+i*(charWidth+gap), h*1/5, strokewidth=3, stroke="black"))
    
    if settings.showIdx:
        # Add the id to the top right corner
        myStyle = StyleBuilder()
        myStyle.setFontFamily(fontfamily="Times")
        myStyle.setFontSize('2em')
        myStyle.setFontStyle('italic')
        myStyle.setFontWeight('bold')
        text_element = Text("#"+str(idx), w-3*charWidth, 40 )
        text_element.set_style(myStyle.getStyle())
        svg.addElement(text_element)

    svg.save(settings.outDir+name+"_processed.svg")

def convertSvgToPng(filename):
    #TODO use filename
    outfile,extension = filename.rsplit(".",1)
    os.system("inkscape '"+filename+"' --export-type=png -o '"+outfile+".png' -w 1122 -h 531")

def preprocessSvgsInDir(settings):
    # delete id aszioation file
    if os.path.exists(settings.outDir+"ids.log"):
        os.remove(settings.outDir+"ids.log")

    idx = settings.idxOffset
    for file in os.listdir(settings.inDir):
        if file.endswith(".svg"):
            filename = settings.inDir+file
            name = file.split(".")[0].split("_")[0]
            idx = idx+1
            print("extracted name "+name+" from filename ("+file+") as #"+str(idx))
            open(settings.outDir+"ids.log","a+").write("extracted name "+name+" from filename ("+file+") as #"+str(idx)+"\n")
            svgAddName(filename, name, idx, settings)

def convertSvgsInDir(path):
    for file in os.listdir(path):
        if file.endswith(".svg"):
            filename = path+file
            print("convert "+filename+" to png")
            convertSvgToPng(filename)

def convertPngsToPnggroups(path):
    groupCount = 0
    groups = []
    pngs = []
    for file in os.listdir(path):
        if file.endswith(".png"):
            filename = path+file
            print(filename)
            pngs.append(filename)
            if len(pngs) == 10:
                outFile = outDir+"group_"+str(groupCount)+".png"
                files = '" "'.join(pngs)

                #merge 10 images to a big one
                command = 'montage "'+files+'" -tile 2x6 -geometry +0+0 '+outFile
                print(command)
                os.system(command)
                groups.append(outFile)
                groupCount = groupCount + 1
                pngs = []

    if len(pngs) != 0:
        outFile = "group_"+str(groupCount)+".png"

        #merge as well the last images to a big one
        command = 'montage "'+('" "'.join(pngs))+'" -tile 2x6 -geometry +0+0 '+outFile
        print(command)
        os.system(command)
        groups.append(outFile)
    return groups

def rmPnggroups(pnggroups):
    command = 'rm "'+('" "'.join(pnggroups))+'"'
    print(command)
    os.system(command)

def convertPnggroupsToPdf(pnggroups, outFile):
    command = 'convert "'+('" "'.join(pnggroups))+'" -repage 2480x3508+25+25 -units PixelsPerInch -density 300x300 '+outFile
    print(command)
    os.system(command)


def usage():
    print("This are the allowed options:")
    print('[-h|-?|help|--help] [--hide-idx] [--hide-name-placeholder] [--idx-offset=<a number>]')
    print("\nby using --idx-offset you can define at what number the index in the map starts to count up.")


def main(argv):
    try:
        opts, args = getopt.getopt(argv,"h",["help","hide-idx","hide-name-placeholder","idx-offset="])
    except getopt.GetoptError as err:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    settings = getSettings()
    for opt, arg in opts:
        if opt in ('-?', "help",'-h', "--help"):
            usage()
            sys.exit()
        elif opt in ("--hide-idx"):
            settings.showIdx=False
        elif opt in ("--hide-name-placeholder"):
            settings.showNamePlaceholder=False
        elif opt in ("--idx-offset"):
            settings.idxOffset = int(arg)
        else:
            assert False, "unhandled option"

    print("preprocess SVGs")
    preprocessSvgsInDir(settings)
    convertSvgsInDir(settings.outDir)
    print("-------------------------------------------------------")
    print("group the png-files and convert them to pdf")
    workingDir = settings.outDir
    print("starting to merge pngs...")
    pnggroups = convertPngsToPnggroups(workingDir)
    print("starting to convert merged pngs to pdf...")
    outFile = settings.outDir+"mapsToPrint.pdf"
    convertPnggroupsToPdf(pnggroups, outFile)
    rmPnggroups(pnggroups)


if __name__ == "__main__":
   main(sys.argv[1:])

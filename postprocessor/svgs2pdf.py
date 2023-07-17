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

inDir = "./raw_svgs/"
outDir = "./out/"
if not os.path.exists(outDir):
    os.makedirs(outDir)


def svgAddName(filename, name, idx, outDir):
    svg = pysvg.parser.parse(filename)
    h = float(svg.get_height())
    w = float(svg.get_width())
    print("render '"+name+"' to "+filename)
    oh = ShapeBuilder()
    leftOffset = 40
    charWidth = 20
    gap = 13

    #x1,y1,x2,y2
    for i in range(len(name)):
        svg.addElement(oh.createLine(leftOffset+i*(charWidth+gap), h*1/5, leftOffset+charWidth+i*(charWidth+gap), h*1/5, strokewidth=3, stroke="black"))
    
    # Add the id to the top right corner
    myStyle = StyleBuilder()
    myStyle.setFontFamily(fontfamily="Times")
    myStyle.setFontSize('2em')
    myStyle.setFontStyle('italic')
    myStyle.setFontWeight('bold')
    text_element = Text("#"+str(idx), "90%", "10%")
    text_element.set_style(myStyle.getStyle())
    svg.addElement(text_element)

    svg.save(outDir+name+"_processed.svg")

def convertSvgToPng(filename):
    #TODO use filename
    outfile,extension = filename.rsplit(".",1)
    os.system("inkscape '"+filename+"' --export-type=png -o '"+outfile+".png' -w 1122 -h 531")

def preprocessSvgsInDir(inpath, outpath):
    # delete id aszioation file
    if os.path.exists(outDir+"ids.log"):
        os.remove(outDir+"ids.log")

    idx = 0
    for file in os.listdir(inpath):
        if file.endswith(".svg"):
            filename = inpath+file
            name = file.split(".")[0].split("_")[0]
            idx = idx+1
            print("extracted name "+name+" from filename ("+file+") as #"+str(idx))
            open(outDir+"ids.log","a+").write("extracted name "+name+" from filename ("+file+") as #"+str(idx)+"\n")
            svgAddName(filename, name, idx, outpath)

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
    print('TODO')


def main(argv):

    print("convert to png")
    preprocessSvgsInDir(inDir, outDir)
    convertSvgsInDir(outDir)
    print("-------------------------------------------------------")
    print("group the png-files and convert them to pdf")
    workingDir = outDir
    print("starting to merge pngs...")
    pnggroups = convertPngsToPnggroups(workingDir)
    print("starting to convert merged pngs to pdf...")
    outFile = outDir+"mapsToPrint.pdf"
    convertPnggroupsToPdf(pnggroups, outFile)
    rmPnggroups(pnggroups)


if __name__ == "__main__":
   main(sys.argv[1:])

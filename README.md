addresses2maps
==========

parses an addressbook (csv-file) to render a small OSM-map (4.5cm x 9.5cm 300dpi) of some contacts
![This is the rendered map from the example vcard](https://raw.githubusercontent.com/kartenkarsten/vcard2maps/master/John.png "example map")

# Usecase
You want awesome table name cards on your next anniversary

# Features
- parses a CSV file containing your addresses
- if coordinates are provided they are used as map center
- without coordinates it uses [Nominatim](http://wiki.openstreetmap.org/wiki/Nominatim) for geocoding of address information
- downloads the OpenstreetMap raw data with the [Overpass-API](http://wiki.openstreetmap.org/wiki/Overpass_API)
- generates a [Maperitive](http://maperitive.net/) render rule based on [Cadastre Style](http://wiki.openstreetmap.org/wiki/User:Nakaner/Cadastre_Style)
- the houses of our contacts will be highlited and in the center of each map
- generates a Maperitive script to do the rendering
- converts svg maps with [inkscape](http://www.inkscape.org/de/) to pngs
- merges 12 pngs to a big one with [ImageMagick montage](http://www.imagemagick.org/script/montage.php) and converts to Din-A4 sized pdf with [ImageMagick convert](http://www.imagemagick.org/script/convert.php) 

# Dependencies
everything is dockerized to avoid the dependency hell of this outdated code

# Usage

Use the template folder as starting point.
Replace the addresses.csv with your addresses e.g. by saving a libreoffice calc table with the columns name, street, housenumber, postcode, city, country, optional geo position as csv file.
If you are familiar with Maperitive you could adjust the template as well to create custom maps.

## build images

```
cd preprocessor
docker build -t preprocessor .
cd ../maperitive
docker build -t maperitive .
cd ../postprocessor
docker build -t postprocessor .
cd ..
```

## render svg

```
# parses addresses, looks up geo position if not present, downloads osm files for each address and prepares the maperitiv script (used for svg rendering)
# expects a mounted folder at /data containing at least 3 files () optinal it could contain cached downloads
# creates a script for Maperitive at /data/raw_svgs/Contacts.mscript (and referenced osm files)
docker run --user "$(id -u):$(id -g)" --mount type=bind,source=$(pwd)/template,target=/data preprocessor

# executes the rendered maperative script and places creates svgs depending on the provided maperitive script
docker run -it --user "$(id -u):$(id -g)" --mount type=bind,source=$(pwd)/template,target=/data -v /tmp/.X11-unix:/tmp/.X11-unix -v /run/user/1000/gdm/Xauthority:/root/.Xauthority -e DISPLAY=:0 --network host --privileged maperitive /data/raw_svgs/Contacts.mscript

# expects /data/
docker run -it --user "$(id -u):$(id -g)" --mount type=bind,source=$(pwd)/template,target=/data postprocessor
```

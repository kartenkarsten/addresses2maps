vcard2maps
==========

parses an addressbook (vcf-file) to render a small OSM-map (4.5cm x 9.5cm 300dpi) of some contacts
![This is the rendered map from the example vcard](https://raw.githubusercontent.com/kartenkarsten/vcard2maps/master/John.png "example map")

# Usecase
You want awesome table name cards on your next anniversary

# Features
- parses [vcards (vcf-files)](http://de.wikipedia.org/wiki/Vcard)
- filters contacts by name and or category
- uses [Nominatim](http://wiki.openstreetmap.org/wiki/Nominatim) for geocoding of address information
- downloads the OpenstreetMap raw data with the [Overpass-API](http://wiki.openstreetmap.org/wiki/Overpass_API)
- generates a [Maperitive](http://maperitive.net/) render rule based on [Cadastre Style](http://wiki.openstreetmap.org/wiki/User:Nakaner/Cadastre_Style)
- the hoses of our contacts will be highlited and in the center of each map
- generates a Maperitive script to do the rendering
- converts svg maps with [inkscape](http://www.inkscape.org/de/) to pngs
- merges 12 pngs to a big one with [ImageMagick montage](http://www.imagemagick.org/script/montage.php) and converts to Din-A4 sized pdf with [ImageMagick convert](http://www.imagemagick.org/script/convert.php) 

# Dependencies
it's running under Linux - others might be difficult right now because of heavy commandline usage

- wget
- convert (imagemagick)
- montage (imagemagick)
- Inkscape
- Maperitive 

## for python install with pip
- pysvg
- geocoder

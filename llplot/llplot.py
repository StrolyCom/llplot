from __future__ import absolute_import

import json
import math
import os
import requests
import urllib
import warnings

from collections import namedtuple

from llplot.color_dicts import mpl_color_map, html_color_codes
from llplot.google_maps_templates import SYMBOLS, CIRCLE


Symbol = namedtuple('Symbol', ['symbol', 'lat', 'long', 'size'])


class InvalidSymbolError(Exception):
    pass


def safe_iter(var):
    try:
        return iter(var)
    except TypeError:
        return [var]


DEFAULT_ATTRIBUTION = 'CC-BY-SA. Imagery Mapbox'

class LeafletPlotter(object):

    def __init__(self, tile_url, center_lat, center_lng, zoom, apikey='',
                 attribution=DEFAULT_ATTRIBUTION):
        self.tile_url = tile_url
        self.center = (float(center_lat), float(center_lng))
        self.zoom = int(zoom)
        self.apikey = str(apikey)
        self.attribution = attribution
        self.grids = None
        self.paths = []
        self.shapes = []
        self.points = []
        self.circles = []
        self.symbols = []
        self.heatmap_points = []
        self.ground_overlays = []
        self.radpoints = []
        self.gridsetting = None
        self.bounding_box = None
        self.coloricon = os.path.join(os.path.dirname(__file__), 'markers/%s.png')
        self.color_dict = mpl_color_map
        self.html_color_codes = html_color_codes

    @classmethod
    def from_geocode(cls, location_string, zoom=13):
        lat, lng = cls.geocode(location_string)
        return cls(lat, lng, zoom)

    @classmethod
    def geocode(self, location_string):
        q_string = urllib.parse.urlencode({'q': location_string,
                                           'format': 'json',
                                           'addressdetails': 1,
                                           })
        request_url = 'https://nominatim.openstreetmap.org/?%s' % q_string

        geocode = requests.get(request_url)
        geocode = geocode.json()

        try:
            return geocode[0]['lat'], geocode[0]['lon'], 13
        except:
            print(geocode)

    def grid(self, slat, elat, latin, slng, elng, lngin):
        self.gridsetting = [slat, elat, latin, slng, elng, lngin]

    def marker(self, lat, lng, color='#FF0000', c=None, title="no implementation"):
        if c:
            color = c
        color = self.color_dict.get(color, color)
        color = self.html_color_codes.get(color, color)
        self.points.append((lat, lng, color[1:], title))

    def scatter(self, lats, lngs, color=None, size=None, marker=True, c=None, s=None, symbol='o', **kwargs):
        color = color or c
        size = size or s or 40
        kwargs["color"] = color
        kwargs["size"] = size
        settings = self._process_kwargs(kwargs)
        for lat, lng in zip(lats, lngs):
            if marker:
                self.marker(lat, lng, settings['color'])
            else:
                self._add_symbol(Symbol(symbol, lat, lng, size), **settings)

    def _add_symbol(self, symbol, color=None, c=None, **kwargs):
        color = color or c
        kwargs.setdefault('face_alpha', 0.5)
        kwargs.setdefault('face_color', "#000000")
        kwargs.setdefault("color", color)
        settings = self._process_kwargs(kwargs)
        self.symbols.append((symbol, settings))

    def circle(self, lat, lng, radius, color=None, c=None, **kwargs):
        color = color or c
        kwargs.setdefault('face_alpha', 0.5)
        kwargs.setdefault('face_color', "#000000")
        kwargs.setdefault("color", color)
        settings = self._process_kwargs(kwargs)
        self.circles.append(((lat, lng, radius), settings))

    def _process_kwargs(self, kwargs):
        settings = dict()
        settings["edge_color"] = kwargs.get("color", None) or \
                                 kwargs.get("edge_color", None) or \
                                 kwargs.get("ec", None) or \
                                 "#000000"

        settings["edge_alpha"] = kwargs.get("alpha", None) or \
                                 kwargs.get("edge_alpha", None) or \
                                 kwargs.get("ea", None) or \
                                 1.0
        settings["edge_width"] = kwargs.get("edge_width", None) or \
                                 kwargs.get("ew", None) or \
                                 1.0
        settings["face_alpha"] = kwargs.get("alpha", None) or \
                                 kwargs.get("face_alpha", None) or \
                                 kwargs.get("fa", None) or \
                                 0.3
        settings["face_color"] = kwargs.get("color", None) or \
                                 kwargs.get("face_color", None) or \
                                 kwargs.get("fc", None) or \
                                 "#000000"

        settings["color"] = kwargs.get("color", None) or \
                            kwargs.get("c", None) or \
                            settings["edge_color"] or \
                            settings["face_color"]

        settings["stroke"] = 0 if kwargs.get('stroke') == False else 1
        settings["fill"] = 0 if kwargs.get('fill') == False else 1
        settings["fill_color"] = kwargs.get('fill_color')
        settings["opacity"] = kwargs.get('opacity') or 1.0
        settings["weight"] = kwargs.get('weight') or 3
        settings["line_cap"] = kwargs.get('line_cap') or "round"
        settings["line_join"] = kwargs.get('line_join') or "round"
        settings["dash_array"] = kwargs.get('dash_array') or ""
        settings["dash_offset"] = kwargs.get('dash_offset') or ""
        settings["fill_opacity"] = kwargs.get('fill_opacity') or 0.2
        settings["fill_rule"] = kwargs.get('fill_rule') or "evenodd"
        settings["fill_rule"] = 0 if kwargs.get('fill_rule') == False else 1

        # Need to replace "plum" with "#DDA0DD" and "c" with "#00FFFF" (cyan).
        for key, color in settings.items():
            if 'color' in key:
                color = self.color_dict.get(color, color)
                color = self.html_color_codes.get(color, color)
                settings[key] = color

        settings["closed"] = kwargs.get("closed", None)
        return settings

    def plot(self, lats, lngs, color=None, c=None, **kwargs):
        color = color or c
        kwargs.setdefault("color", color)
        settings = self._process_kwargs(kwargs)
        path = zip(lats, lngs)
        self.paths.append((path, settings))

    def heatmap(self, lats, lngs, threshold=10, radius=10, gradient=None, opacity=0.6, maxIntensity=1, dissipating=True):
        """
        :param lats: list of latitudes
        :param lngs: list of longitudes
        :param maxIntensity:(int) max frequency to use when plotting. Default (None) uses max value on map domain.
        :param threshold:
        :param radius: The hardest param. Example (string):
        :return:
        """
        settings = {}
        # Try to give anyone using threshold a heads up.
        if threshold != 10:
            warnings.warn("The 'threshold' kwarg is deprecated, replaced in favor of maxIntensity.")
        settings['threshold'] = threshold
        settings['radius'] = radius
        settings['gradient'] = gradient
        settings['opacity'] = opacity
        settings['maxIntensity'] = maxIntensity
        settings['dissipating'] = dissipating
        settings = self._process_heatmap_kwargs(settings)

        heatmap_points = []
        for lat, lng in zip(lats, lngs):
            heatmap_points.append((lat, lng))
        self.heatmap_points.append((heatmap_points, settings))


    def fit_bounds(self, nelat, nelng, swlat, swlng):
        self.bounding_box = [nelat, nelng, swlat, swlng]

    def _process_heatmap_kwargs(self, settings_dict):
        settings_string = ''
        settings_string += "heatmap.set('threshold', %d);\n" % settings_dict['threshold']
        settings_string += "heatmap.set('radius', %d);\n" % settings_dict['radius']
        settings_string += "heatmap.set('maxIntensity', %d);\n" % settings_dict['maxIntensity']
        settings_string += "heatmap.set('opacity', %f);\n" % settings_dict['opacity']

        dissipation_string = 'true' if settings_dict['dissipating'] else 'false'
        settings_string += "heatmap.set('dissipating', %s);\n" % (dissipation_string)

        gradient = settings_dict['gradient']
        if gradient:
            gradient_string = "var gradient = [\n"
            for r, g, b, a in gradient:
                gradient_string += "\t" + "'rgba(%d, %d, %d, %d)',\n" % (r, g, b, a)
            gradient_string += '];' + '\n'
            gradient_string += "heatmap.set('gradient', gradient);\n"

            settings_string += gradient_string

        return settings_string

    def ground_overlay(self, url, bounds_dict):
        '''
        :param url: Url of image to overlay
        :param bounds_dict: dict of the form  {'north': , 'south': , 'west': , 'east': }
        setting the image container
        :return: None
        Example use:
        import llplot
        gmap = llplot.GoogleMapPlotter(37.766956, -122.438481, 13)
        bounds_dict = {'north':37.832285, 'south': 37.637336, 'west': -122.520364, 'east': -122.346922}
        gmap.ground_overlay('http://explore.museumca.org/creeks/images/TopoSFCreeks.jpg', bounds_dict)
        gmap.draw("my_map.html")
        Google Maps API documentation
        https://developers.google.com/maps/documentation/javascript/groundoverlays#introduction
        '''

        bounds_string = self._process_ground_overlay_image_bounds(bounds_dict)
        self.ground_overlays.append((url, bounds_string))

    def _process_ground_overlay_image_bounds(self, bounds_dict):
        bounds_string = 'var imageBounds = {'
        bounds_string += "north:  %.4f,\n" % bounds_dict['north']
        bounds_string += "south:  %.4f,\n" % bounds_dict['south']
        bounds_string += "east:  %.4f,\n" % bounds_dict['east']
        bounds_string += "west:  %.4f};\n" % bounds_dict['west']

        return bounds_string

    def polygon(self, lats, lngs, color=None, c=None, **kwargs):
        color = color or c
        kwargs.setdefault("color", color)
        settings = self._process_kwargs(kwargs)
        shape = zip(lats, lngs)
        self.shapes.append((shape, settings))

    def draw(self, htmlfile, img_path=None, header=None, footer=None):
        """Create the html file which include one google map and all points and paths. If
        no string is provided, return the raw html.
        """
        f = open(htmlfile, 'w')
        f.write('<html>\n')
        f.write('<head>\n')
        f.write(
            '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.3.4/dist/leaflet.css" '
            'integrity="sha512-puBpdR0798OZvTTbP4A8Ix/l+A4dHDD0DGqYW6RQ+9jxkRFclaxxQb/SJAWZfWAkuyeQUytO7+7N4QKrDh+drA==" '
            'crossorigin=""/>\n')
        f.write(
            '<script src="https://unpkg.com/leaflet@1.3.4/dist/leaflet.js"'
            'integrity="sha512-nMMmRyTVoLYqjP9hrbed9S+FzjZHW5gY1TWCHA5ckwXZBadntCNs8kEqAWdrb9O7rxbCaA4lKTIWjDXZxflOcA=="'
            'crossorigin=""></script>'
        )
        f.write(
            '<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>\n')
        f.write('<title>Leaflet - llplot </title>\n')
        # if self.apikey:
        #     f.write('<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?libraries=visualization&sensor=true_or_false&key=%s"></script>\n' % self.apikey )
        # else:
        #     f.write('<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?libraries=visualization&sensor=true_or_false"></script>\n' )
        f.write('<script type="text/javascript">\n')
        f.write('\tvar llMap;\n')
        f.write('\tfunction initialize() {\n')
        self.write_map(f)
        # self.write_grids(f)
        self.write_points(f)
        self.write_paths(f)
        self.write_circles(f)
        # self.write_symbols(f)
        # self.write_shapes(f)
        # self.write_heatmap(f)
        # self.write_ground_overlay(f)
        self.write_fitbounds(f)
        f.write('\t}\n')
        f.write('</script>\n')
        f.write('</head>\n')
        f.write(
            '<body style="margin:0px; padding:0px;" onload="initialize()">\n')

        if header:
            f.write('\t<h2>'+header+'</h2>')
        f.write(
            '\t<div id="container" style="overflow: hidden; padding: 20px;">\n')
        # f.write(
        #     '\t\t<div id="map_canvas" style="width: 512px; height: 512px; float:left; padding-right: 20px;"></div>\n')

        f.write(
            '\t\t<div id="mapid" style="width: 512px; height: 512px; float:left; padding-right: 20px;"></div>'
        )

        if img_path:
            f.write(
                '\t\t<div id="image" height: 512px; overflow: hidden; padding-left: 20px;">')
            f.write('\t\t\t<img src="'+img_path+'" alt="mapimage" height="512">')
            f.write('\t\t</div>\n')
        f.write(
            '\t</div>\n')

        if footer:
            f.write('\t<div>'+footer+'</div>')
        f.write('</body>\n')
        f.write('</html>\n')
        f.close()

    #############################################
    # # # # # # Low level Map Drawing # # # # # #
    #############################################

    def write_grids(self, f):
        if self.gridsetting is None:
            return
        slat = self.gridsetting[0]
        elat = self.gridsetting[1]
        latin = self.gridsetting[2]
        slng = self.gridsetting[3]
        elng = self.gridsetting[4]
        lngin = self.gridsetting[5]
        self.grids = []

        r = [
            slat + float(x) * latin for x in range(0, int((elat - slat) / latin))]
        for lat in r:
            self.grids.append(
                [(lat + latin / 2.0, slng + lngin / 2.0), (lat + latin / 2.0, elng + lngin / 2.0)])

        r = [
            slng + float(x) * lngin for x in range(0, int((elng - slng) / lngin))]
        for lng in r:
            self.grids.append(
                [(slat + latin / 2.0, lng + lngin / 2.0), (elat + latin / 2.0, lng + lngin / 2.0)])

        for line in self.grids:
            settings = self._process_kwargs({"color": "#000000"})
            self.write_polyline(f, line, settings)

    def write_points(self, f):
        for id, point in enumerate(self.points):
            self.write_point(f, point[0], point[1], point[2], point[3], id)

    def write_circles(self, f):
        for circle, settings in self.circles:
            self.write_circle(f, circle[0], circle[1], circle[2], settings)

    def write_symbols(self, f):
        for symbol, settings in self.symbols:
            self.write_symbol(f, symbol, settings)

    def write_paths(self, f):
        for path, settings in self.paths:
            self.write_polyline(f, path, settings)

    def write_shapes(self, f):
        for shape, settings in self.shapes:
            self.write_polygon(f, shape, settings)

    # TODO: Add support for mapTypeId: google.maps.MapTypeId.SATELLITE
    def write_map(self,  f):
        f.write('\t\tvar MarkerIcon = L.Icon.extend({\n'
                '\t\t\toptions: {\n'
                '\t\t\t\ticonSize:     [21, 34],\n'
                '\t\t\t\ticonAnchor:   [22, 34],\n'
                '\t\t\t\tpopupAnchor:  [-11, -34]\n'
                '\t\t\t}});\n')
        f.write('\t\tattribution = "%s";\n' % (self.attribution.replace('"', "'")))
        f.write('\t\tvar baseLayer = L.tileLayer("%s", {\n' %
                (self.tile_url))
        f.write('\t\t\tattribution, \n\t\t\tmapid: "streets"});\n')
        f.write('\t\tllMap = L.map("mapid", {\n')
        f.write('\t\t\tzoomSnap: 0,\n')
        f.write('\t\t\tmaxZoom: 18\n')
        f.write('\t\t\t}).setView([%f, %f], %d);\n' %
                (self.center[0], self.center[1], self.zoom))
        f.write('\t\tbaseLayer.addTo(llMap);\n')

    def write_point(self, f, lat, lon, color, title, id):
        f.write('\t\tvar latlng = [%f, %f];\n' %
                (lat, lon))
        f.write('\t\tvar img = new MarkerIcon({iconUrl: \'%s\'});\n' %
                (self.coloricon % color))
        f.write('\t\tvar marker'+str(id)+' = L.marker(latlng, {\n')
        f.write('\t\ttitle: "%s",\n' % title)
        f.write('\t\ticon: img,\n')
        f.write('\t\t});\n')

        if title != "no implementation":
            f.write('\t\tmarker'+str(id)+'.bindPopup("'+title+'");\n')

        f.write('\t\tmarker'+str(id)+'.addTo(llMap);\n')
        f.write('\n')

    def write_symbol(self, f, symbol, settings):
        strokeColor = settings.get('color') or settings.get('edge_color')
        strokeOpacity = settings.get('edge_alpha')
        strokeWeight = settings.get('edge_width')
        fillColor = settings.get('face_color')
        fillOpacity = settings.get('face_alpha')
        try:
            template = SYMBOLS[symbol.symbol]
        except KeyError:
            raise InvalidSymbolError("Symbol %s is not implemented" % symbol.symbol)

        f.write(template.format(lat=symbol.lat, long=symbol.long, size=symbol.size, strokeColor=strokeColor,
                                strokeOpacity=strokeOpacity, strokeWeight=strokeWeight,
                                fillColor=fillColor, fillOpacity=fillOpacity))


    def write_circle(self, f, lat, lng, radius, settings):

        stroke = 0 if settings.get('stroke') == False else 1
        fill = 0 if settings.get('fill') == False else 1
        strokeColor = settings.get('color') or settings.get('edge_color')
        strokeOpacity = settings.get('opacity') or 1.0
        strokeWeight = settings.get('weight') or 3
        lineCap = settings.get('line_cap') or 'round'
        lineJoin = settings.get('line_join') or 'round'
        dashArray = settings.get('dash_array') or ''
        dashOffset = settings.get('dash_offset') or ''
        fillColor = settings.get('fill_color') or strokeColor
        fillOpacity = settings.get('fill_opacity') or 0.2
        fillRule = settings.get('fill_rule') or "evenodd"
        bubblingMouseEvents = 0 if settings.get('bubbling_mouse_events') == False else 1
        f.write(CIRCLE.format(latlng=[lat, lng], radius=radius, strokeColor=strokeColor,
                              strokeOpacity=strokeOpacity, strokeWeight=strokeWeight,fill=fill,
                              lineCap=lineCap, lineJoin=lineJoin, dashArray=dashArray,
                              dashOffset=dashOffset, fillRule=fillRule, bubblingMouseEvents=bubblingMouseEvents,
                              fillColor=fillColor, fillOpacity=fillOpacity, stroke=stroke))

    def write_polyline(self, f, path, settings):
        # clickable = False
        # geodesic = True
        strokeColor = settings.get('color') or settings.get('edge_color')
        strokeOpacity = settings.get('edge_alpha')
        strokeWeight = settings.get('edge_width')

        f.write('var PolylineCoordinates = [\n')
        for coordinate in path:
            f.write('[%f, %f],\n' %
                    (coordinate[0], coordinate[1]))
        f.write('];\n')
        f.write('\n')

        f.write('var Path = L.polyline( PolylineCoordinates, {\n')
        # f.write('clickable: %s,\n' % (str(clickable).lower()))
        # f.write('geodesic: %s,\n' % (str(geodesic).lower()))
        f.write('color: "%s",\n' % (strokeColor))
        f.write('opacity: %f,\n' % (strokeOpacity))
        f.write('weight: %d\n' % (strokeWeight))
        f.write('}).addTo(llMap);\n')
        f.write('\n\n')

    def write_polygon(self, f, path, settings):
        clickable = False
        geodesic = True
        strokeColor = settings.get('edge_color') or settings.get('color')
        strokeOpacity = settings.get('edge_alpha')
        strokeWeight = settings.get('edge_width')
        fillColor = settings.get('face_color') or settings.get('color')
        fillOpacity= settings.get('face_alpha')
        f.write('var coords = [\n')
        for coordinate in path:
            f.write('new google.maps.LatLng(%f, %f),\n' %
                    (coordinate[0], coordinate[1]))
        f.write('];\n')
        f.write('\n')

        f.write('var polygon = new google.maps.Polygon({\n')
        f.write('clickable: %s,\n' % (str(clickable).lower()))
        f.write('geodesic: %s,\n' % (str(geodesic).lower()))
        f.write('fillColor: "%s",\n' % (fillColor))
        f.write('fillOpacity: %f,\n' % (fillOpacity))
        f.write('paths: coords,\n')
        f.write('strokeColor: "%s",\n' % (strokeColor))
        f.write('strokeOpacity: %f,\n' % (strokeOpacity))
        f.write('strokeWeight: %d\n' % (strokeWeight))
        f.write('});\n')
        f.write('\n')
        f.write('polygon.setMap(map);\n')
        f.write('\n\n')

    def write_heatmap(self, f):
        for heatmap_points, settings_string in self.heatmap_points:
            f.write('var heatmap_points = [\n')
            for heatmap_lat, heatmap_lng in heatmap_points:
                f.write('new google.maps.LatLng(%f, %f),\n' %
                        (heatmap_lat, heatmap_lng))
            f.write('];\n')
            f.write('\n')
            f.write('var pointArray = new google.maps.MVCArray(heatmap_points);' + '\n')
            f.write('var heatmap;' + '\n')
            f.write('heatmap = new google.maps.visualization.HeatmapLayer({' + '\n')
            f.write('\n')
            f.write('data: pointArray' + '\n')
            f.write('});' + '\n')
            f.write('heatmap.setMap(map);' + '\n')
            f.write(settings_string)

    def write_ground_overlay(self, f):

        for url, bounds_string in self.ground_overlays:
            f.write(bounds_string)
            f.write('var groundOverlay;' + '\n')
            f.write('groundOverlay = new google.maps.GroundOverlay(' + '\n')
            f.write('\n')
            f.write("'" + url + "'," + '\n')
            f.write('imageBounds);' + '\n')
            f.write('groundOverlay.setMap(map);' + '\n')

    def write_fitbounds(self, f):
        if self.bounding_box is None:
            return
        nelat = self.bounding_box[0]
        nelng = self.bounding_box[1]
        swlat = self.bounding_box[2]
        swlng = self.bounding_box[3]

        f.write('var bounds = [[%f, %f], [%f, %f]];\n' %
                (self.bounding_box[0], self.bounding_box[1],
                 self.bounding_box[2], self.bounding_box[3]))
        f.write('llMap.fitBounds(bounds);\n')



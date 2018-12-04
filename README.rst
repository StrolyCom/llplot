gmplot -> llplot
================

Plotting data on a Leaflet map (instead of GoogleMap), the easy way. A matplotlib-like
interface to generate the HTML and javascript to render all the
data you'd like on top of Leaflet. Several plotting methods
make creating exploratory map views effortless. Here's a crash course:

::

    from gmplot import gmplot

    mapbox_token = "<your token>"
    # Place map
    gmap = gmplot.LeafletPlotter(
        "https://{s}.tiles.mapbox.com/v4/mapbox.{mapid}/{z}/{x}/{y}@2x.png?"
        "access_token=" + mapbox_token,
        37.766956, -122.438481, 13
    )

    # Polygon
    golden_gate_park_lats, golden_gate_park_lons = zip(*[
        (37.771269, -122.511015),
        (37.773495, -122.464830),
        (37.774797, -122.454538),
        (37.771988, -122.454018),
        (37.773646, -122.440979),
        (37.772742, -122.440797),
        (37.771096, -122.453889),
        (37.768669, -122.453518),
        (37.766227, -122.460213),
        (37.764028, -122.510347),
        (37.771269, -122.511015)
        ])
    gmap.plot(golden_gate_park_lats, golden_gate_park_lons, 'cornflowerblue', edge_width=10)

    # Marker
    hidden_gem_lat, hidden_gem_lon = 37.770776, -122.461689
    gmap.marker(hidden_gem_lat, hidden_gem_lon, 'cornflowerblue')

    # Draw
    gmap.draw("my_map.html")

.. image:: https://i.imgur.com/12KXJS3.png

About this fork
---------------

This is a fork of `gmplot <https://github.com/vgm64/gmplot/>`_ to show a map using `Leaflet <https://leafletjs.com/>`_
instead of Google Maps (hence the name llplot). The main difference at creation is that it needs
the base URL of the tiles you are going to display on leaflet.

NOTE: Not all the write functions have been migrated from Google Maps to Leaflet. Please check the open issues list if you want to contribute.


.. code-block:: python:

    mapbox_token = "<your token>"
    # Create map
    map = gmplot.LeafletPlotter(
        "https://{s}.tiles.mapbox.com/v4/mapbox.{mapid}/{z}/{x}/{y}@2x.png?"
        "access_token=" + mapbox_token,
        37.766956, -122.438481, 13
    )

    # Added three new optional arguments for draw:
    # image_path: the path of an image to show before the map
    # header and footer: html strings to draw before and after the map
    map.draw("map.html",
             img_path="./images/image.png",
             header="This is the header",
             footer="<PRE>And the footer</pre>")

    # Call to fit_bounds
    # https://developers.google.com/maps/documentation/javascript/reference/map#Map.fitBounds
    map.fit_bounds(north, east, south, west)

    # also, by default if a marker has title it is shown as a pop-up


Geocoding
---------

NOTE: NOT MIGRATE YET

``gmplot`` contains a simple wrapper around Google's geocoding service enabling
map initilization to the location of your choice. Rather than providing latitude,
longitude, and zoom level during initialization, grab your gmplot instance with
a location:

::

    gmap = gmplot.GoogleMapPlotter.from_geocode("San Francisco")

Plot types
----------

* Polygons with fills - ``plot`` # DONE
* Drop pins. - ``marker`` # DONE
* Scatter points. - ``scatter`` # TO DO
* Grid lines. - ``grid`` # TO DO
* Heatmaps. - ``heatmap`` # TO DO

.. image:: https://i.imgur.com/ETxECMW.png

Misc.
-----

Install easily with ``pip install git+https://github.com/StrolyCom/gmplot.git#egg=gmplot`` directly from this repo.

Inspired by Yifei Jiang's (jiangyifei@gmail.com) pygmaps_ module.

.. _pygmaps: http://code.google.com/p/pygmaps/

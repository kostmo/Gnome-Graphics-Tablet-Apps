#!/usr/bin/env python
############################################################################
##
## Copyright (C) 2007 Alexander Macdonald. All rights reserved.
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License version 2
##
## Gnome Panel Pressure Applet
##
############################################################################

import sys
import pygtk
pygtk.require('2.0')
import gtk
import gobject
import gnomeapplet

bar = gtk.ProgressBar()
image = gtk.Image()
hbox = gtk.HBox()

def Update():
	pressure = 0.0
	for dev in gtk.gdk.devices_list():
		p = dev.get_axis(dev.get_state(hbox.window)[0], gtk.gdk.AXIS_PRESSURE)
		if p != None:
			if p > pressure:
				pressure = p
	bar.set_fraction(pressure)
	return True

def PressureAppletFactory(applet, iid):
	image.set_from_file("/usr/share/pressure-applet/input-tablet.png")
	bar.set_size_request(50,-1)
	
	hbox.add(image)
	hbox.add(bar)
	applet.add(hbox)
	applet.show_all()
	applet.set_extension_events(gtk.gdk.EXTENSION_EVENTS_ALL)
	gobject.timeout_add(75, Update)
	return True

if len(sys.argv) == 2 and sys.argv[1] == "debug":
	main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	main_window.set_title("Pressure Applet")
	main_window.connect("delete_event", gtk.main_quit)
	app = gnomeapplet.Applet()
	PressureAppletFactory(app, None)
	app.reparent(main_window)
	main_window.show_all()
	gtk.main()
	sys.exit()
		
gnomeapplet.bonobo_factory("OAFIID:GNOME_PressureApplet_Factory", gnomeapplet.Applet.__gtype__, "Display tablet device pressure", "1.0", PressureAppletFactory)


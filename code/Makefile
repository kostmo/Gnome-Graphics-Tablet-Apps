install:
	mkdir -p /usr/share/pressure-applet
	cp pressure-applet.py /usr/bin/
	cp pressure-applet.server /usr/lib/bonobo/servers/
	mkdir -p /usr/share/tablet-capplet
	cp tablet-capplet.glade /usr/share/tablet-capplet/
	cp tablet-capplet.py /usr/bin/
	cp tablet-capplet.desktop /usr/share/applications/
uninstall:
	rm -rf /usr/share/pressure-applet/
	rm /usr/bin/presure-applet.py
	rm /usr/lib/bonobo/servers/pressure-applet.server
	rm -rf /usr/share/tablet-capplet/
	rm /usr/bin/tablet-capplet.py
	rm /usr/share/applications/tablet-capplet.desktop
clean:
	rm -f *~

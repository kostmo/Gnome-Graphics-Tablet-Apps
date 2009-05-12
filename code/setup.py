#!/usr/bin/python

if __name__ == "__main__":

	from distutils.core import setup

	setup(name="tabletconfig",
		description="Gnome panel and control center applets to configure and monitor graphics tablet devices.",
		long_description="""The gnome wacom applet is a small gnome panel applet that shows how much pressure is being applied to your wacom tablet by the current device. Clicking on the panel icon brings up a dialog allowing you to select a different device and check what pressure and tilt information is being recieved from it. This dialog also contains a small drawing test area to give your pen a quick test.""",
		author="Alex Mac",
#		author_email="kostmo@gmail.com",
		url="http://www.alexmac.cc/tablet-apps/",
		version="0.4.0-alpha1",
		scripts=["tabletconfig"],
		data_files=[
			("share/tablet-apps", ["tabletconfig.glade"])
		]
	)



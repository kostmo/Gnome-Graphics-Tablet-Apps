#!/usr/bin/env python

'''This setup script only installs the tablet-config application, not the panel applet.'''

if __name__ == "__main__":

    from distutils.core import setup
    from tablet_apps import tablet_prog_info

    setup(name=tablet_prog_info.NAME,
        description="Gnome panel and control center applets to configure and monitor graphics tablet devices.",
        long_description="""The Gnome Wacom applet is a small Gnome panel applet that shows how much pressure is being applied to your wacom tablet by the current device. Clicking on the panel icon brings up a dialog allowing you to select a different device and check what pressure and tilt information is being received from it. This dialog also contains a small drawing test area to give your pen a quick test.""",
        author=tablet_prog_info.AUTHOR,
        author_email=tablet_prog_info.EMAIL,
        url=tablet_prog_info.WEBSITE,
        version=tablet_prog_info.VERSION,
#        scripts=["tablet-config"],
        classifiers=["Intended Audience :: End Users/Desktop",
                     "Development Status :: 4 - Beta",
                     "Environment :: X11 Applications :: Gnome",
                     "Operating System :: POSIX :: Linux",
                     "Topic :: System :: Hardware"],
        packages=["tablet_apps"],
        data_files=[
            ("share/tablet-config", ["tablet-config.glade", "input-tablet.png", "input-tablet.svg"])
        ]
    )

#!/usr/bin/env python
############################################################################
##
## Copyright (C), all rights reserved:
##      2007-2009 Alexander Macdonald
##      2008 Juho Vepsalainen
##      2009 Thomas Iorns <yobbobandana@yahoo.co.nz>
##      2011 Karl Ostmo <kostmo@gmail.com>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License version 2
##
## Graphics Tablet Applet
##
############################################################################

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import cairo
import sys
import os
import subprocess
import math

bool_options = [
    "TPCButton",
    ]

int_options = [
    "Mode",
    "ToolID",
    "ClickForce",
    ]

def xswGetDefault(devicename, propertyname, *args):
    ''' Get the default value for some option using xsetwacom.
    '''
    try:
        cmd = ['xsetwacom']
        cmd.extend(args)
        cmd.extend(['getdefault', devicename, propertyname])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()[0]
        return output.strip()
    except:
        return None

def xswGet(devicename, propertyname, *args):
    ''' Get the current value for some option using xsetwacom.
    '''
    try:
        cmd = ['xsetwacom']
        cmd.extend(args)
        cmd.extend(['get', devicename, propertyname])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()[0].strip()
        if not output:
            return None
        if propertyname in bool_options:
            return bool(int(output))
        elif propertyname in int_options:
            return int(output)
        return output
    except:
        return None

def xswSet(devicename, propertyname, value, *args):
    ''' Set an option using xsetwacom.
    '''
    try:
        if value is True:
            value = "on"
        elif value is False:
            value = "off"
        elif value is None:
            value = xswGetDefault(devicename, propertyname)
        cmd = ['xsetwacom']
        cmd.extend(args)
        cmd.extend(['set', devicename, propertyname, str(value)])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()[0]
        return output.strip()
    except:
        return None

def GetPressCurve(devicename):
    ''' Get the pressure curve of a device using xsetwacom
    '''
    try:
        output = subprocess.Popen(["xsetwacom", "-x", "get", devicename, "PressCurve"], stdout=subprocess.PIPE).communicate()[0]
        bits = output.split()
        if bits[1] == "\"PressCurve\"":
            return [float(x) for x in bits[2].strip("\"").split(",")]
    except:
        return None

def SetPressCurve(devicename, points):
    ''' Set the pressure curve of a device using xsetwacom
    '''
    try:
        output = subprocess.Popen(["xsetwacom", "set", devicename, "PressCurve", str(points[0]), str(points[1]), str(points[2]), str(points[3])])
    except:
        return None

def GetClickForce(devicename):
    ''' Get the ClickForce of a device using xsetwacom.
        Values are in the range 1 - 21.
    '''
    return xswGet(devicename, "ClickForce")

def SetClickForce(devicename, force):
    ''' Set the ClickForce of a device using xsetwacom.
        Values are in the range 1 - 21.
    '''
    if force == None:
        force = xswGetDefault(devicename, "ClickForce")
    elif force > 21:
        force = 21
    elif force < 1:
        force = 1

    return xswSet(devicename, "ClickForce", force)

def GetMode(devicename):
    ''' Get the device Mode using xsetwacom.
    '''
    try:
        output = subprocess.Popen(["xsetwacom", "get", devicename, "Mode"], stdout=subprocess.PIPE).communicate()[0]
        return int(output.strip())
    except:
        return None

def SetMode(devicename, m):
    ''' Set the device Mode using xsetwacom.
    '''
    try:
        output = subprocess.Popen(["xsetwacom", "set", devicename, "Mode", str(m)])
        return int(output.strip())
    except:
        return None

class PressureCurveWidget(gtk.DrawingArea):
    ''' A widget for displaying and modifying the pressure curve (PressCurve)
        for a wacom-compatible drawing tablet. The curve may be
        modified by dragging the control point.
    '''
    def __init__(self):

        gtk.DrawingArea.__init__(self)

        self.Pressure = 0.0
        self.CP = None
        self.ClickForceLine = None

        self.Radius = 5.0
        self.ControlPointStroke = 2.0
        self.ControlPointDiameter = (self.Radius * 2) + self.ControlPointStroke
        self.WindowSize = None
        self.Scale = None

        self.DeviceName = ""

        self.DraggingCP = False
        self.DraggingCF = False

        self.set_events(gtk.gdk.POINTER_MOTION_MASK  | gtk.gdk.BUTTON_MOTION_MASK | gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON2_MOTION_MASK | gtk.gdk.BUTTON3_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK)

        self.connect("configure-event", self.ConfigureEvent)
        self.connect("expose-event", self.ExposeEvent)
        self.connect("motion-notify-event", self.MotionEvent)
        self.connect("button-press-event", self.ButtonPress)
        self.connect("button-release-event", self.ButtonRelease)
        self.set_size_request(100,100)

    def GetPoints(self):
        ''' Return the control points as xsetwacom would like them.
        '''
        if not self.CP:
            return None
        points = []
        points.append(int(self.ClampValue(self.CP[0]) * 100.0))
        points.append(int(self.ClampValue(1.0 - self.CP[1]) * 100.0))
        points.append(100 - points[1])
        points.append(100 - points[0])
        return points

    def SetDevice(self, name):
        ''' Change or refresh the current device.
        '''
        self.DeviceName = name
        cf = GetClickForce(name)

        if cf == None:
            self.ClickForceLine = None
        else:
            self.ClickForceLine = self.ClampValue((cf - 1) / 20.0)

        points = GetPressCurve(name)
        if points == None:
            self.CP = None
        else:
            self.CP = [points[0] / 100.0, 1.0 - (points[1] / 100.0)]
            self.Pressure = 0.0

        self.Update()

    def Update(self):
        self.queue_draw()

    def ClampValue(self, v):
        ''' Make sure v is between 0.0 and 1.0 inclusive.
        '''
        if v < 0.0:
            return 0.0
        elif v > 1.0:
            return 1.0
        else:
            return v

    def ConfigureEvent(self, widget, event):
        ''' Handle widget resize.
        '''
        self.WindowSize = self.window.get_size()
        xscale = self.WindowSize[0] - self.ControlPointDiameter
        yscale = self.WindowSize[1] - self.ControlPointDiameter
        self.Scale = (xscale, yscale)

    def MotionEvent(self, widget, event):
        ''' Handle motion notify events.
        '''
        pos = event.get_coords()
        pos = (pos[0] / self.Scale[0], pos[1] / self.Scale[1])

        if self.CP == None:
            return

        if self.DraggingCP:
            self.CP[0] = self.ClampValue(pos[0])
            self.CP[1] = self.ClampValue(pos[1])
            self.Update()

        elif self.DraggingCF:
            cf = int(pos[0] * 20)
            self.ClickForceLine = self.ClampValue(cf / 20.0)

    def ButtonPress(self, widget, event):
        ''' Handle button press events.
        '''
        if self.CP == None:
            return

        if self.DraggingCP or self.DraggingCF:
            self.DragFinished()
        else:
            pos = event.get_coords()
            pos = (pos[0] / self.Scale[0], pos[1] / self.Scale[1])

            dx = abs(pos[0] - self.CP[0]) * self.Scale[0]
            dy = abs(pos[1] - self.CP[1]) * self.Scale[1]

            if dx < self.ControlPointDiameter and dy < self.ControlPointDiameter:
                self.DraggingCP = True
                return

            if self.ClickForceLine == None:
                return

            dx = abs(pos[0] - self.ClickForceLine) * self.Scale[0]

            if dx < self.ControlPointDiameter:
                self.DraggingCF = True
                return

    def ButtonRelease(self, widget, event):
        ''' Handle button release events.
        '''
        self.DragFinished()
        self.Update()

    def DragFinished(self):
        ''' Clean up after finished drag.
        '''
        self.DraggingCP = False
        self.DraggingCF = False

        if self.ClickForceLine != None:
            SetClickForce(self.DeviceName, int(self.ClickForceLine * 20.0) + 1)

        points = self.GetPoints()
        if points != None:
            SetPressCurve(self.DeviceName, points)

    def DrawGrid(self, cr):
        ''' Draw a 10 by 10 grid.
        '''
        cr.set_line_width(0.5)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.25)
        cr.save()
        cr.scale(self.Scale[0], self.Scale[1])
        cr.new_path()
        for x in range(11):
            cr.move_to(x * 0.1, 0.0)
            cr.line_to(x * 0.1, 1.0)
        for y in range(11):
            cr.move_to(0.0, y * 0.1)
            cr.line_to(1.0, y * 0.1)
        cr.restore()
        cr.stroke()

    def DrawLinear(self, cr):
        ''' Draw a line to indicate the default (linear) pressure curve.
        '''
        cr.set_line_width(1.0)
        cr.save()
        cr.scale(self.Scale[0], self.Scale[1])
        cr.new_path()
        cr.move_to(0.0, 1.0)
        cr.line_to(1.0, 0.0)
        cr.restore()
        cr.stroke()

    def DrawClickForce(self, cr):
        ''' Draw a vertical line indicating the current click force.
        '''
        if self.ClickForceLine == None:
            return
        cr.set_line_width(1.0)
        cr.set_source_rgba(1.0, 0.0, 0.0, 0.25)
        cr.save()
        cr.scale(self.Scale[0], self.Scale[1])
        cr.new_path()
        cr.move_to(self.ClickForceLine, 0.0)
        cr.line_to(self.ClickForceLine, 1.0)
        cr.restore()
        cr.stroke()

    def DrawPressure(self, cr, x0, y0, x1, y1, click=True):
        ''' Draw the current pressure.
        '''
        if not self.Pressure:
            return
        pmin = 0.0
        if self.ClickForceLine != None:
            pmin = self.ClickForceLine * 20 / 100.0

        cr.save()
        cr.scale(self.Scale[0], self.Scale[1])
        cr.rectangle(0.0, 0.0, self.Pressure, 1.0)
        cr.clip()
        cr.new_path()
        if self.Pressure >= pmin:
            cr.set_source_rgba(114.0 / 255.0, 159.0 / 255.0, 207.0 / 255.0, 0.5)
        else:
            cr.set_source_rgba(207.0 / 255.0, 114.0 / 255.0, 114.0 / 255.0, 0.5)
        cr.move_to(0.0,1.0)
        cr.curve_to(x0, y0, x1, y1, 1.0, 0.0)
        cr.line_to(1.0, 1.0)
        cr.fill()
        cr.restore()

    def DrawPressureCurve(self, cr, x0, y0, x1, y1):
        ''' Draw the active pressure curve.
        '''
        cr.set_line_width(2.0)
        cr.set_source_rgba(32.0 / 255.0, 74.0 / 255.0, 135.0 / 255.0, 1.0)
        cr.save()
        cr.scale(self.Scale[0], self.Scale[1])
        cr.new_path()
        cr.move_to(0.0, 1.0)
        cr.curve_to(x0, y0, x1, y1, 1.0, 0.0)
        cr.restore()
        cr.stroke()

    def ExposeEvent(self, widget, event):
        ''' Draw the widget.
        '''
        cr = widget.window.cairo_create()
        cr.set_line_cap(cairo.LINE_CAP_ROUND);

        cr.save()
        cr.translate(self.ControlPointDiameter / 2.0, self.ControlPointDiameter / 2.0)

        self.DrawGrid(cr)

        if self.Pressure == None:
            cr.restore()
            return

        self.DrawLinear(cr)

        x0 = 0.0
        y0 = 1.0
        x1 = 1.0
        y1 = 0.0

        if self.CP:
            x0 = self.CP[0]
            y0 = self.CP[1]
            x1 = self.CP[1]
            y1 = self.CP[0]

        self.DrawPressure(cr, x0, y0, x1, y1)
        self.DrawPressureCurve(cr, x0, y0, x1, y1)


        if self.CP == None:
            cr.restore()
            return

        cr.set_line_width(2.0)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5)

        cr.save()
        cr.scale(self.Scale[0], self.Scale[1])
        cr.move_to(0.0, 1.0)
        cr.line_to(x0, y0)
        cr.restore()

        cr.stroke()

        # Control Points
        cr.set_line_width(2.0)

        cr.save()
        cr.arc(x0 * self.Scale[0], y0 * self.Scale[1], self.Radius, 0.0, 2.0 * math.pi);
        cr.set_source_rgba(237.0 / 255.0, 212.0 / 255.0, 0.0, 0.5)
        cr.fill_preserve()
        cr.set_source_rgba(239.0 / 255.0, 41.0 / 255.0, 41.0 / 255.0, 1.0)
        cr.stroke()
        cr.restore()

        cr.restore()

class DrawingTestWidget(gtk.DrawingArea):
    ''' A widget for testing the pressure sensitivity of an input device.
    '''
    def __init__(self):

        gtk.DrawingArea.__init__(self)

        self.Device = 0
        self.Radius = 5.0
        self.Drawing = False
        self.WindowSize = None
        self.Raster = None
        self.RasterCr = None

        self.set_events(gtk.gdk.POINTER_MOTION_MASK  | gtk.gdk.BUTTON_MOTION_MASK | gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON2_MOTION_MASK | gtk.gdk.BUTTON3_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK)
        self.set_extension_events(gtk.gdk.EXTENSION_EVENTS_ALL)

        self.connect("configure-event", self.ConfigureEvent)
        self.connect("expose-event", self.ExposeEvent)
        self.connect("motion-notify-event", self.MotionEvent)
        self.connect("button-press-event", self.ButtonPress)
        self.connect("button-release-event", self.ButtonRelease)
        self.set_size_request(100,100)

    def ConfigureEvent(self, widget, event):
        ''' Handle widget resize.
        '''
        self.WindowSize = self.window.get_size()
        self.Raster = self.window.cairo_create().get_target().create_similar(cairo.CONTENT_COLOR, self.WindowSize[0], self.WindowSize[1])
        self.RasterCr = cairo.Context(self.Raster)
        self.RasterCr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        self.RasterCr.rectangle(0.0, 0.0, self.WindowSize[0], self.WindowSize[1])
        self.RasterCr.fill()

    def GetPressure(self):
        ''' Return the current device pressure.
        '''
        dev = gtk.gdk.devices_list()[self.Device]
        state = dev.get_state(self.window)
        return dev.get_axis(state[0], gtk.gdk.AXIS_PRESSURE)

    def MotionEvent(self, widget, event):
        ''' Handle motion events.
        '''
        if self.Drawing:
            pos = event.get_coords()
            p = self.GetPressure()
            if p == None:
                p = 0.0
            r =  p * 50 + 5
            self.RasterCr.set_line_width(2)
            self.RasterCr.set_source_rgba(p, 1.0, 0.0, 0.5)
            if p:
                self.RasterCr.arc(pos[0], pos[1],r, 0.0, 2 * math.pi);
            else:
                # draw something to indicate no pressure
                self.RasterCr.move_to(pos[0] - 4, pos[1] - 4)
                self.RasterCr.line_to(pos[0] + 4, pos[1] + 4)
                self.RasterCr.move_to(pos[0] - 4, pos[1] + 4)
                self.RasterCr.line_to(pos[0] + 4, pos[1] - 4)

            self.RasterCr.fill_preserve()
            self.RasterCr.set_source_rgba(0.5, 0.2, p, 0.5)
            self.RasterCr.stroke()
            reg = gtk.gdk.Region()
            reg.union_with_rect((int(pos[0] - r - 2), int(pos[1] - r - 2), int(2 * (r + 2)), int(2 * (r + 2))))
            self.window.invalidate_region(reg, False)

    def ButtonPress(self, widget, event):
        ''' Handle button press events.
        '''
        self.Drawing = True

    def ButtonRelease(self, widget, event):
        ''' Handle button release events.
        '''
        self.Drawing = False

    def ExposeEvent(self, widget, event):
        ''' Draw the widget.
        '''
        cr = widget.window.cairo_create()
        cr.set_source_surface(self.Raster, 0.0, 0.0)
        cr.paint()
        cr.set_line_width(2)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.25)
        cr.rectangle(0.0, 0.0, self.WindowSize[0], self.WindowSize[1])
        cr.stroke()

class GraphicsTabletApplet:
    ''' GUI for configuring wacom-compatible drawing tablets.
    '''
    def __init__(self, gladefile, statusicon):

        self.WidgetTree = gtk.glade.XML(gladefile)
        self.StatusIcon = statusicon

        self.MainWindow = self.WidgetTree.get_widget("MainWindow")
        self.MainWindow.connect("destroy", self.destroy)
        
        self.DeviceCombo = self.WidgetTree.get_widget("DeviceCombo")
        self.ModeCombo = self.WidgetTree.get_widget("ModeCombo")
        self.XTilt = self.WidgetTree.get_widget("xtilt")
        self.YTilt = self.WidgetTree.get_widget("ytilt")
        self.Wheel = self.WidgetTree.get_widget("wheel")
        self.ToolID = self.WidgetTree.get_widget("ToolID")
        self.TPCRadioButton = self.WidgetTree.get_widget("tpcbutton")
        self.ClickForceScale = self.WidgetTree.get_widget("ClickForceScale")
        self.ClickForceFrame = self.WidgetTree.get_widget("ClickForceFrame")
        self.SideSwitchFrame = self.WidgetTree.get_widget("SideSwitchFrame")
        self.TiltFrame = self.WidgetTree.get_widget("TiltFrame")
        self.WheelFrame = self.WidgetTree.get_widget("WheelFrame")

        self.Curve = PressureCurveWidget()
        self.Curve.show()
        self.WidgetTree.get_widget("PressureVBox").add(self.Curve)
        self.WidgetTree.get_widget("imagemenuitemAbout").connect("activate", self.show_about)
        self.WidgetTree.get_widget("menuitemQuit").connect("activate", self.destroy)

        self.DrawingArea = DrawingTestWidget()
        self.DrawingArea.show()
        self.WidgetTree.get_widget("DrawingAlignment").add(self.DrawingArea)

        self.Device = 0
        self.DeviceMode = None
        self.DeviceName = None

        self.DeviceCombo.connect("changed", self.DeviceSelected)
        self.ModeCombo.connect("changed", self.ModeChanged)
        self.ClickForceScale.connect("value-changed", self.ClickForceChanged)
        self.TPCRadioButton.connect("toggled", self.TPCButtonToggled)

        self.DeviceList = gtk.ListStore(str)
        self.DeviceCell = gtk.CellRendererText()
        self.DeviceCombo.pack_start(self.DeviceCell, True)
        self.DeviceCombo.add_attribute(self.DeviceCell, 'text', 0)
        self.DeviceCombo.set_model(self.DeviceList)

        self.ClickForce = None
        self.TPCButton = None
        self.destroying = False

    def show_about(self, widget):
        
        import tablet_prog_info
        about = gtk.AboutDialog()
        about.set_name(tablet_prog_info.NAME)
        about.set_version(tablet_prog_info.VERSION)
        about.set_website(tablet_prog_info.WEBSITE)
        about.set_website_label("Source code on GitHub")
        about.set_authors([tablet_prog_info.AUTHOR, "Alexander Macdonald", "Thomas Iorns", "Juho Vepsalainen"])
        response = about.run()
        about.hide()

    def destroy(self, widget, data=None):
        self.destroying = True
        gtk.main_quit()

    def Run(self):
        ''' Set up device list and start main window app.
        '''
        
        devices_list = gtk.gdk.devices_list()
        print "How many items in devices list?", len(devices_list)
        for d in devices_list:
            devicename = str(d.name)
            self.DeviceList.append([devicename])
            toolID = xswGet(devicename, "ToolID")
            if toolID >= 0: # valid wacom device
                self.Device = max(len(self.DeviceList) - 1, 0)
            else:
                pass

        self.DeviceCombo.set_active(self.Device)
        self.DeviceName = gtk.gdk.devices_list()[self.Device].name
        self.UpdateChildren()
        gobject.idle_add(self.Update)


        self.MainWindow.show()
#        self.MainWindow.hide()
        gtk.main()

    def GetPressure(self):
        ''' Return current device pressure.
        '''
        dev = gtk.gdk.devices_list()[self.Device]
        state = dev.get_state(self.DrawingArea.window)
        return dev.get_axis(state[0], gtk.gdk.AXIS_PRESSURE)

    def GetTilt(self):
        ''' Return current device tilt as (xtilt, ytilt).
        '''
        dev = gtk.gdk.devices_list()[self.Device]
        state = dev.get_state(self.DrawingArea.window)
        try:
            x = float(dev.get_axis(state[0], gtk.gdk.AXIS_XTILT))
            y = float(dev.get_axis(state[0], gtk.gdk.AXIS_YTILT))
            if x != x or y != y:
                return None
            else:
                return (x, y)
        except:
            return None

    def GetWheel(self):
        ''' Return current device wheel state.
        '''
        dev = gtk.gdk.devices_list()[self.Device]
        state = dev.get_state(self.DrawingArea.window)
        try:
            wheel = dev.get_axis(state[0], gtk.gdk.AXIS_WHEEL)
            if wheel != wheel:
                return None
            else:
                return wheel
        except:
            return None

    def ModeChanged(self, widget):
        ''' Set changed mode using xsetwacom.
        '''
        xswSet(self.DeviceName, "Mode", widget.get_active())

    def ClickForceChanged(self, widget):
        ''' Do callback for ClickForce slider "value-changed" event.
        '''
        cf = widget.get_value()
        self.Curve.ClickForceLine = (cf - 1) / 20.0
        SetClickForce(self.DeviceName, cf)

    def TPCButtonToggled(self, widget):
        ''' Handle "toggled" event from the TPCButton radio button.
        '''
        if self.TPCButton == widget.get_active():
            return
        self.TPCButton = widget.get_active()
        xswSet(self.DeviceName, "TPCButton", self.TPCButton)

    def UpdateDeviceMode(self):
        ''' Update the device mode combo box.
        '''
        self.DeviceMode = xswGet(self.DeviceName, "Mode")
        if self.DeviceMode == None:
            self.ModeCombo.set_sensitive(False)
        else:
            self.ModeCombo.set_sensitive(True)
            self.ModeCombo.set_active(self.DeviceMode)

    def UpdateClickForce(self):
        ''' Update the click force slider.
        '''
        self.ClickForce = GetClickForce(self.DeviceName)
        if self.ClickForce == None:
            self.ClickForceFrame.hide()
        else:
            self.ClickForceFrame.show()
            self.ClickForceScale.set_value(self.ClickForce)

    def UpdateTPCButton(self):
        ''' Update the TPCButton radio button group.
        '''
        self.TPCButton = xswGet(self.DeviceName, "TPCButton")

        if self.TPCButton == None:
            self.SideSwitchFrame.hide()
            return

        self.SideSwitchFrame.show()
        self.TPCButton = bool(self.TPCButton)

        if self.TPCButton == self.TPCRadioButton.get_active():
            return

        if self.TPCButton:
            self.TPCRadioButton.set_active(True)
            return

        for button in self.TPCRadioButton.get_group():
            if button != self.TPCRadioButton:  # there's only one other
                button.set_active(True)
                return

    def UpdateChildren(self):
        ''' Update the child widgets to reflect current settings.
        '''
        self.UpdateDeviceMode()
        self.UpdateClickForce()
        self.UpdateTPCButton()

    def DeviceSelected(self, widget):
        ''' Update the various parts of the applet for a new device.
        '''
        self.Device = widget.get_active()
        self.DrawingArea.Device = self.Device
        self.DeviceName = gtk.gdk.devices_list()[self.Device].name
        self.Curve.SetDevice(self.DeviceName)
        self.UpdateChildren()

    def Update(self):
        if self.destroying:
            return False

        p = self.GetPressure()

        if p == None:
            self.Curve.Pressure = None
            self.Curve.Update()
        else:
            self.Curve.Pressure = p
            self.Curve.Update()

        t = self.GetTilt()

        if t == None:
            self.TiltFrame.hide()
        else:
            self.TiltFrame.show()
            self.XTilt.set_adjustment(gtk.Adjustment(t[0], -1.0, 1.0))
            self.YTilt.set_adjustment(gtk.Adjustment(t[1], -1.0, 1.0))

        w = self.GetWheel()

        if w == None:
            self.WheelFrame.hide()
        else:
            self.WheelFrame.show()
            self.Wheel.set_adjustment(gtk.Adjustment(w, -1.0, 1.0))

        id = xswGet(self.DeviceName, "ToolID")

        if id == None:
            id = ""

        self.ToolID.set_label(str(id))

        return True


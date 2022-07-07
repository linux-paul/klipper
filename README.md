---------------------------------------------------

The beginning is made :)

This is a Kipper MOD for use on the Tellboard especially for the use of a WZL.
For this, changes in Klipper had purely missing in other versions or possibly not work.
Simply adding a module was not possible because you can not simply assign a different end stop to the axes.
A config template is in the conf directory

This is still a test version, it can be that not all GCODES are mapped.
If something is missing you can solve it with a Klipper macro, see doc.
There are also some things I want to change, like driving the steppers on "push of a button".

Why Klipper? Klipper is very good extendable e.g. for the UseCase Tillboard, using the pins of the Raspberry
and it has proven itself in 3D printing as FW for stepper control.

- current extensions;

Config:
[mpcnc]
WZL here as normally open contact
[spindle]
The spindle example is for the Maffell.
[estlcam]
Translates G00, G01, G02, G03, M00, M03, M05 to G0, G1, G2, G3, PAUSE, M3, M5

GCODE:
"HOME_WZL" : "Homed" Z additionally down, sets GCode coordinates to 0 and recalculates limit 
"G3 S<rpm>" : Spindle on with speed <rpm>.
"G5" : spindle off

"ENABLE_TP"/"DISABLE_TP"
Use of a touch plate, inclusion of TP offsets at HOME_WZL.

"PARK_TOOL"

"SET_MESHCONFIG VALUE=min_x,min_y,max_x,max_y,count_x,count_y" (SET_MESHCONFIG VALUE=1,1,49,49,5,5)
Surface sampling
For understanding please read MPCNC.md.
"CREATE_MESH"
Executes the leveling.

- Structure:
Klipper needs mandatory limit switches because you always have to homen Klipper before you can "print".
For this it seems more practical to use the Z end stop at the top of the axis.

- Marlin GCODE:
Klipper understands Marlin GCODE like G1, G2, ... G01 or G02 as it comes from Estlcam does not.
By the way, so far no slicer generates G01,... in Marlin mode. 

- Flashing:
Chips like the Nano with OldBootloader have to be flashed with 57000 Boud, if necessary you have to flash manually, e.g.
avrdude -C/etc/arduino/avrdude.conf -v -patmega328p -carduino -b57000 -P/dev/ttyUSB0 -D -Uflash:w:out/klipper.elf.hex:i
Support for the atmega328p doesn't seem to be around that long, it sometimes pinches when flashing.

- UI:
Octoprint and Repetier work as UI. Pronterface unfortunately only conditionally, since it does not recognize the Klipper GCODE Commands as GCODE and does not send through.

- Surface scanning:
Please read MPCNC.md for understanding.

People with interest/experience in programming klipper extensions (C/Python) are welcome to contact me, I'm also just a hobbyist in this corner.

---------------------------------------------------

Welcome to the Klipper project!

[![Klipper](docs/img/klipper-logo-small.png)](https://www.klipper3d.org/)

https://www.klipper3d.org/

Klipper is a 3d-Printer firmware. It combines the power of a general
purpose computer with one or more micro-controllers. See the
[features document](https://www.klipper3d.org/Features.html) for more
information on why you should use Klipper.

To begin using Klipper start by
[installing](https://www.klipper3d.org/Installation.html) it.

Klipper is Free Software. See the [license](COPYING) or read the
[documentation](https://www.klipper3d.org/Overview.html).

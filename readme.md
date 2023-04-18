# HA Switches AutoOff

The purpose of this app is to turn off a light or switches after a certain amount of time after motion or occupancy
sensors
stopped signalling the zone is occupied.

In standard HA setup there is a couple options of how lights are working.

1. You can turn on it manually and have to turn it off manually.
2. You can create motion-assisted light.

However, there is no option to have a light or switches that turns off automatically after a certain amount of time
after occupancy is gone.

* Some switches should be turned on manually.
* Some switches should be kept on when some other zone is occupied, but they should not be triggered by that zone
  occupancy. Example: kitchen lights must be turned on when kitchen is occupied, but should be kept on till the hall is
  occupied as well.

This app closes this gap.
After couple years of using HA I found that I need this feature in my setup because some lights or switches has to be
turned manually.
The blueprints didn't solve this in efficient way.
Such way will ease the setup of the lights and will make it more convenient to use.

It supports HA templating as well.
Typical use case for templating:
1. Auto off timeout for the night lights to be 1 minute at night and for a longer period of time during the day.
2. Kitchen lights should have timeout of 1 minute when projector in hall is on, but should have longer timeout when
   projector is off.


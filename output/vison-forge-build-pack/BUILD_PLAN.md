# Build Plan

1. Read the linked controller documentation and confirm the board pin labels.
2. Lay out the controller and one component without power; compare every connection to the wiring table.
3. Test one input or output at a time using USB power only.
4. Add the remaining components only after each prior test passes.
5. Run the failure tests and record results in the build journal.

## Wiring Blueprint

- Connect soil-sensor output to GPIO 34; connect sensor power according to its datasheet.
- Connect the relay input to a free digital pin; relay VCC/GND must match its module documentation.
- Power the 5V pump from its separate 5V supply through the relay contacts; do not draw pump current from a controller pin.
- Keep all electronics dry and test the circuit before placing tubing near it.
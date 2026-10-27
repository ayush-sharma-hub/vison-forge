# Build Plan

1. Read the linked controller documentation and confirm the board pin labels.
2. Lay out the controller and one component without power; compare every connection to the wiring table.
3. Test one input or output at a time using USB power only.
4. Add the remaining components only after each prior test passes.
5. Run the failure tests and record results in the build journal.

## Wiring Blueprint

- ESP32 5V Pin -> Breadboard + Rail
- ESP32 GND Pin -> Breadboard - Rail
- Servo VCC (Red) -> Breadboard + Rail (5V)
- Servo GND (Brown) -> Breadboard - Rail (GND)
- Servo Signal (Orange/Yellow) -> ESP32 GPIO 18
- HC-SR04 VCC -> Breadboard + Rail (5V)
- HC-SR04 GND -> Breadboard - Rail (GND)
- HC-SR04 Trig -> ESP32 GPIO 5
- HC-SR04 Echo -> ESP32 GPIO 18 (Note: Use voltage divider or resistor network if strict 3.3V tolerance is needed, though many HC-SR04s tolerate 5V echo input poorly; safer to use a voltage divider for Echo back to ESP32)
# Test Plan

- Subsystem test: verify microcontroller logic on USB power before connecting actuators.
- Power rail test: verify external voltage rail under load before connecting signal wires.
- Emergency stop: confirm software failsafe kills motor/actuator power if signal is lost.

## Risks

- Servo jerks, resets the ESP32, or fails to move when commanded. — Insufficient current from USB or shared ground loops causing brown-out resets due to high inrush current of the servo motor.
- Current mismatch between controller GPIO pins and external actuators.
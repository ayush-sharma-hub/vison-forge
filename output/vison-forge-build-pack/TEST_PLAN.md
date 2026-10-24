# Test Plan

- Dry-sensor test: confirm the measured value changes when the sensor moves from dry air to water-free damp soil.
- Pump test: with water disconnected, trigger the relay for two seconds and confirm the controller remains powered.
- Fail-safe test: disconnect the sensor and confirm the pump does not run continuously.

## Risks

- Sensor readings drift; calibrate with dry and damp soil.
- Pump current can reset the controller; use separate low-voltage pump power.
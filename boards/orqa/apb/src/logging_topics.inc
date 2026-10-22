// APB UART profile, instance 0 only. Intervals are milliseconds.
// Included inside LoggedTopics::initialize_logged_topics(). Do not add
// unbounded-rate topics: scripts/check_apb_logging.py checks generated sizes.
add_topic("vehicle_attitude", 100);
add_topic("vehicle_angular_velocity", 100);
add_topic("vehicle_local_position", 200);
add_topic("vehicle_global_position", 500);
add_topic("vehicle_gps_position", 1000);
add_topic("battery_status", 1000);
add_topic("vehicle_status", 500);
add_topic("vehicle_control_mode", 500);
add_topic("actuator_armed", 500);
add_topic("failsafe_flags", 500);
add_topic("manual_control_setpoint", 200);
add_topic("actuator_outputs", 200);
add_topic("vehicle_attitude_setpoint", 200);
add_topic("vehicle_rates_setpoint", 200);
add_topic("estimator_status", 1000);
add_topic("estimator_status_flags", 1000);
add_topic("sensor_combined", 200);

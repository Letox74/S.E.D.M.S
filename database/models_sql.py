CREATE_DEVICES_SQL = """
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            firmware_version TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'online',
            location TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            has_battery BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, location)
        );
"""
# both timestamps are UTC time

CREATE_DEVICE_STATUS_LOG_SQL = """
        CREATE TABLE IF NOT EXISTS device_status_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# for the analytic data (to check last_reset and operation_hours)

CREATE_TELEMETRY_SQL = """
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            voltage REAL NOT NULL,
            current REAL NOT NULL, 
            signal_strength REAL NOT NULL,
            frequency REAL NOT NULL,
            temperature REAL NOT NULL,
            current_battery_percentage REAL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# current: the current (in amperes)
# voltage: the electric voltage (in volts)
# power can be calculated: voltage * current
# resistence can be calculated: voltage / current

CREATE_ANALYTICS_SQL = """
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            avg_power REAL NOT NULL DEFAULT 0,
            peak_power REAL NOT NULL DEFAULT 0,
            min_power REAL NOT NULL DEFAULT 0,
            std_power REAL NOT NULL DEFAULT 0,
            avg_voltage REAL NOT NULL DEFAULT 0,
            peak_voltage REAL NOT NULL DEFAULT 0,
            min_voltage REAL NOT NULL DEFAULT 0,
            std_voltage REAL NOT NULL DEFAULT 0,
            avg_current REAL NOT NULL DEFAULT 0,
            peak_current REAL NOT NULL DEFAULT 0,
            min_current REAL NOT NULL DEFAULT 0,
            std_current REAL NOT NULL DEFAULT 0,
            avg_signal_strength REAL NOT NULL DEFAULT 0,
            peak_signal_strength REAL NOT NULL DEFAULT 0,
            min_signal_strength REAL NOT NULL DEFAULT 0,
            std_signal_strength REAL NOT NULL DEFAULT 0,
            avg_temperature REAL NOT NULL DEFAULT 0,
            peak_temperature REAL NOT NULL DEFAULT 0,
            min_temperature REAL NOT NULL DEFAULT 0,
            std_temperature REAL NOT NULL DEFAULT 0,
            avg_battery_percentage REAL NOT NULL DEFAULT 0,
            min_battery_percentage REAL NOT NULL DEFAULT 0,
            operation_hours REAL NOT NULL DEFAULT 0,
            efficiency_score REAL NOT NULL DEFAULT 0,
            energy_consumption REAL NOT NULL DEFAULT 0,
            last_reset DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# energy_consumption: watt hours (Wh)
# watt hours: W * hours (example: Device runs 24h with 30W -> 30 * 24 = 720 Wh)

CREATE_PREDICTIONS_SQL = """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            predicted_load REAL NOT NULL,
            actual_load REAL,
            prediction_error REAL,
            anomaly_score REAL NOT NULL,
            is_anomaly BOOLEAN NOT NULL,
            confidence REAL NOT NULL,
            prediction_horizon_minutes INTEGER NOT NULL,
            model_version TEXT NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# anomaly_score: atypical of a datapoint
# predicted_load: is in watt (in 30 min the device will use 30W)

CREATE_INDICIES_SQL = """
        CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);
        CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);
"""
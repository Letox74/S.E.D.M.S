CREATE_DEVICES_SQL = """
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            firmware_version TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
"""

CREATE_TELEMETRY_SQL = """
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            voltage REAL NOT NULL,
            current REAL NOT NULL, 
            signal_strengh REAL NOT NULL,
            frequency REAL NOT NULL,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# current: the current (in amperes)
# voltage: the electric voltage (in volts)

CREATE_ANALYTICS_SQL = """
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            avg_power REAL NOT NULL DEFAULT 0,
            peak_power REAL NOT NULL DEFAULT 0,
            min_power REAL NOT NULL DEFAULT 0,
            variance_power REAL NOT NULL DEFAULT 0,
            operation_hours REAL NOT NULL DEFAULT 0,
            efficiency_score REAL NOT NULL DEFAULT 0,
            energy_consumption REAL NOT NULL DEFAULT 0,
            last_reset DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# energy_consumption: watt hours

CREATE_PREDICTIONS_SQL = """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            predicted_load REAL NOT NULL,
            anomaly_score REAL NOT NULL,
            is_anomaly BOOLEAN NOT NULL,
            feature_importance TEXT NOT NULL,
            predicton_horizon_minutes INTEGER DEFAULT 0,
            model_version TEXT NOT NULL,
            FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
        );
"""
# anomaly_score: atypical of a datapoint
# predicted_load: is in watt (in 30 min the device will use 30W)
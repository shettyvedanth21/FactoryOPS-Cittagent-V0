-- Create all required databases for FactoryOPS
-- Per HLD §2.1 and LLD §1.3

CREATE DATABASE IF NOT EXISTS energy_device_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS energy_rule_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS energy_analytics_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS energy_reporting_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS energy_export_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Grant privileges to root user for all databases
GRANT ALL PRIVILEGES ON energy_device_db.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON energy_rule_db.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON energy_analytics_db.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON energy_reporting_db.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON energy_export_db.* TO 'root'@'%';

FLUSH PRIVILEGES;

"""App configuration, loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "embedwatch/sensors"

    database_url: str = "sqlite:///./embedwatch.db"

    # How often a simulated sensor takes a reading, in seconds.
    sensor_interval_seconds: float = 2.0

    # Battery level below which the power manager switches to a longer
    # sleep interval to conserve energy.
    low_battery_threshold: float = 20.0


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "torneo_futbol5"
    db_admin_user: str = "usuario_admin"
    db_admin_password: str = ""
    db_planillero_user: str = "usuario_planillero"
    db_planillero_password: str = ""
    db_auth_user: str = "usuario_auth"      # lo usa el módulo de login
    db_auth_password: str = ""
    jwt_secret: str
    jwt_expire_hours: int = 8

settings = Settings()
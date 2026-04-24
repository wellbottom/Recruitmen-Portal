from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "Smart Recruitment Portal API"
    raw_database_url: str | None = Field(default=None, alias="database_url")
    user: str | None = None
    password: str | None = None
    host: str | None = None
    port: int = 5432
    dbname: str | None = None
    db_sslmode: str = "require"

    clerk_issuer: str | None = None
    clerk_jwks_url: str | None = None

    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def database_url(self) -> str:
        if self.raw_database_url:
            raw_url = self.raw_database_url.strip()
            if raw_url.startswith("postgres://"):
                return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
            if raw_url.startswith("postgresql://") and not raw_url.startswith(
                "postgresql+"
            ):
                return raw_url.replace(
                    "postgresql://", "postgresql+psycopg://", 1
                )
            return raw_url

        required_parts = {
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "dbname": self.dbname,
        }
        missing_parts = [name for name, value in required_parts.items() if not value]
        if missing_parts:
            missing = ", ".join(missing_parts)
            raise ValueError(
                "Database configuration is incomplete. "
                f"Missing: {missing}. Set database_url or the individual connection fields."
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.dbname,
            query={"sslmode": self.db_sslmode},
        ).render_as_string(hide_password=False)


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    linkedin_access_token: str = ""
    linkedin_author_urn: str = ""
    linkedin_api_version: str = "202609"
    mastodon_base_url: str = "https://mastodon.social"
    mastodon_access_token: str = ""
    bluesky_handle: str = ""
    bluesky_app_password: str = ""
    wordpress_base_url: str = ""
    wordpress_username: str = ""
    wordpress_app_password: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

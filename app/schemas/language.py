from pydantic import BaseModel

class LanguageUpdate(BaseModel):
    user_id: int
    lang: str  # "ru", "en", "uk"

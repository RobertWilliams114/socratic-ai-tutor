## Configuration for Socratic

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

## Load environment variables
load_dotenv()

## The application settings
class Settings(BaseSettings):

    ## LLM Configuration
    llm_provider: Literal["ollama", "lm_studio", "openrouter"] = Field(
        default="ollama", env="LLM_PROVIDER"
    )
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    lm_studio_base_url: str = Field(default="http://localhost:1234", env="LM_STUDIO_BASE_URL")
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")

    ## Model Configuration
    model_name: str = Field(default="qwen2.5:latest", env="MODEL_NAME")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")

    ## Database Configuration
    mongo_uri: str = Field(default="mongodb://localhost:27017", env="MONGO_URI")
    mongo_db_name: str = Field(default="socratic_tutor", env="MONGO_DB_NAME")
    use_file_storage: bool = Field(default=True, env="USE_FILE_STORAGE")

    ## GraphRAG Configuration
    graph_storage_path: Path = Field(default=Path("./data/graph"), env="GRAPH_STORAGE_PATH")
    max_context_length: int = Field(default=8192, env="MAX_CONTEXT_LENGTH")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")

    ## Data Ingestion
    course_website_url: str = Field(
        default="https://pantelis.github.io/aiml-common/", env="COURSE_WEBSITE_URL"
    )
    data_dir: Path = Field(default=Path("./data/raw"), env="DATA_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = False

    ## This function gets the LLM base URL based on the provider
    def get_llm_base_url(self) -> str:
        if self.llm_provider == "ollama":
            return f"{self.ollama_base_url}/v1"
        elif self.llm_provider == "lm_studio":
            return self.lm_studio_base_url
        elif self.llm_provider == "openrouter":
            return "https://openrouter.ai/api/v1"
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    ## This function gets an api key from the user if you wanna use openrouter
    def get_api_key(self) -> str | None:
        if self.llm_provider == "openrouter":
            return self.openrouter_api_key
        return None


## Global settings instance
settings = Settings()

"""
Configuration settings for the resume parser application.
"""

import os
from typing import List, Set
from pydantic_settings import BaseSettings
from pydantic import Field


class AppSettings(BaseSettings):
    """Application configuration settings."""
    
    # File upload settings
    MAX_FILE_SIZE_MB: int = Field(default=10, description="Maximum file size in MB")
    SUPPORTED_EXTENSIONS: Set[str] = Field(
        default={".pdf", ".docx", ".doc", ".txt", ".html", ".htm"},
        description="Supported file extensions"
    )
    SUPPORTED_MIME_TYPES: Set[str] = Field(
        default={
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "text/html",
            "application/octet-stream"  # Fallback for some file types
        },
        description="Supported MIME types"
    )
    
    # OpenAI settings
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="OpenAI model to use")
    OPENAI_MAX_TOKENS: int = Field(default=4000, description="Maximum tokens for OpenAI response")
    OPENAI_TEMPERATURE: float = Field(default=0.1, description="Temperature for OpenAI model")
    
    # Processing settings
    ENABLE_DEBUG_MODE: bool = Field(default=False, env="DEBUG")
    PROCESSING_TIMEOUT_SECONDS: int = Field(default=120, description="Processing timeout")
    
    # UI settings
    APP_TITLE: str = Field(default="Intelligent Resume Parser", description="Application title")
    APP_DESCRIPTION: str = Field(
        default="Upload resumes in multiple formats and get structured JSON output using AI",
        description="Application description"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env file


# Global settings instance
settings = AppSettings()


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is supported."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in settings.SUPPORTED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """Check if file size is within limits."""
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size <= max_size_bytes


def get_file_type_from_extension(filename: str) -> str:
    """Get file type description from extension."""
    ext = os.path.splitext(filename.lower())[1]
    type_mapping = {
        ".pdf": "PDF Document",
        ".docx": "Word Document (DOCX)",
        ".doc": "Word Document (DOC)",
        ".txt": "Text Document",
        ".html": "HTML Document",
        ".htm": "HTML Document"
    }
    return type_mapping.get(ext, "Unknown Document Type")

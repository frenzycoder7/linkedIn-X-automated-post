import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv


load_dotenv()


@dataclass
class AppConfig:
    openai_api_key: str

    reddit_client_id: Optional[str]
    reddit_client_secret: Optional[str]
    reddit_user_agent: Optional[str]

    x_bearer_token: Optional[str]
    x_api_key: Optional[str]
    x_api_secret: Optional[str]
    x_access_token: Optional[str]
    x_access_token_secret: Optional[str]

    # OAuth2 (user context) optional fields
    x_client_id: Optional[str]
    x_client_secret: Optional[str]
    x_oauth2_access_token: Optional[str]
    x_oauth2_refresh_token: Optional[str]
    x_redirect_uri: Optional[str]
    x_scopes: Optional[str]

    linkedin_access_token: Optional[str]
    linkedin_person_urn: Optional[str]
    linkedin_organization_urn: Optional[str]

    keywords: List[str]


DEFAULT_KEYWORDS = [
    "tech",
    "technology",
    "software",
    "software engineering",
    "software development",
    "developers",
    "programming",
    "coding",
    "computer science",
    "systems design",
    "backend",
    "frontend",
    "full stack",
    "api",
    "microservices",
    "cloud",
    "aws",
    "azure",
    "gcp",
    "kubernetes",
    "docker",
    "devops",
    "sre",
    "observability",
    "performance",
    "security",
    "cybersecurity",
    "data engineering",
    "data platform",
    "streaming",
    "apache kafka",
    "spark",
    "mlops",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "ai",
    "ai agents",
    "genai",
    "llm",
    "gpt",
    "open ai",
    "openai",
    "langchain",
    "rag",
    "vector database",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "clickhouse",
    "python",
    "javascript",
    "typescript",
    "node.js",
    "react",
    "next.js",
    "vue",
    "svelte",
    "go",
    "golang",
    "rust",
    "java",
    "spring",
    ".net",
    "c#",
    "cpp",
    "c++",
    "robotics",
    "automation",
    "nvidia",
    "microsoft",
    "google",
    "amazon",
    "meta",
    "anthropic",
    "databricks",
    "snowflake",
    "hugging face",
    "windsurf",
    "cursor",
    "ai agents",
    "ai agent",
    "ai agentic",
    "ai agentic systems",
    "ai agentic systems engineering",
    "ai agentic systems engineering",
    "go",
    "golang",
    "rust",
    "python",
    "javascript",
    "typescript",
    "node.js",
    "react",
    "next.js",
    "vue",
    "svelte",
    "go",
    "golang",
    "rust",
    "python",
    "javascript",
    "typescript",
    "node.js",
    "react",
]


def read_config() -> AppConfig:
    keywords_env = os.getenv("KEYWORDS", None)
    if keywords_env:
        keywords = [k.strip() for k in keywords_env.split(",") if k.strip()]
    else:
        keywords = DEFAULT_KEYWORDS

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "linkedin-x-autoposter/1.0"),
        x_bearer_token=os.getenv("X_BEARER_TOKEN"),
        x_api_key=os.getenv("X_API_KEY"),
        x_api_secret=os.getenv("X_API_SECRET"),
        x_access_token=os.getenv("X_ACCESS_TOKEN"),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        x_client_id=os.getenv("X_CLIENT_ID"),
        x_client_secret=os.getenv("X_CLIENT_SECRET"),
        x_oauth2_access_token=os.getenv("X_OAUTH2_ACCESS_TOKEN"),
        x_oauth2_refresh_token=os.getenv("X_OAUTH2_REFRESH_TOKEN"),
        x_redirect_uri=os.getenv("X_REDIRECT_URI"),
        x_scopes=os.getenv("X_SCOPES"),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
        linkedin_person_urn=os.getenv("LINKEDIN_PERSON_URN"),
        linkedin_organization_urn=os.getenv("LINKEDIN_ORGANIZATION_URN"),
        keywords=keywords,
    )

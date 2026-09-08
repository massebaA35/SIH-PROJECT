"""Optional production integrations with deterministic local fallbacks."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationStatus:
    postgres: str
    neo4j: str
    nlp: str


def integration_status() -> IntegrationStatus:
    postgres = "configured" if os.getenv("DATABASE_URL") else "synthetic-fallback"
    neo4j = "configured" if os.getenv("NEO4J_URI") else "synthetic-fallback"
    nlp = "transformers" if os.getenv("NLP_MODEL") else "rule-based-fallback"
    return IntegrationStatus(postgres=postgres, neo4j=neo4j, nlp=nlp)


def get_graph_client():
    """Return a Neo4j driver only when explicitly configured."""
    uri = os.getenv("NEO4J_URI")
    if not uri:
        return None
    from neo4j import GraphDatabase
    return GraphDatabase.driver(uri, auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "change-me")))


def get_database_connection():
    """Return a PostgreSQL connection only when explicitly configured."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    import psycopg
    return psycopg.connect(url)
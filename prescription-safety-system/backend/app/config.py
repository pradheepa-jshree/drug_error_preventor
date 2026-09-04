import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://admin:demo@localhost:5432/lasa_guardian"
)

LASA_MIN_CONFIDENCE = float(
    os.getenv("LASA_MIN_CONFIDENCE", "55")
)

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONVariant = JSON().with_variant(JSONB(), "postgresql")

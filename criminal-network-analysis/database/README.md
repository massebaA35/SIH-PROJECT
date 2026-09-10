# database/

`schema.sql` is the authoritative table structure, **generated from the SQLAlchemy
models** in `backend/app/models/` (which is the actual source of truth — this file is
a read-only reference, not something to hand-edit). See `../docs/DATABASE.md` for the
full schema walkthrough, the entity-id convention, and the PostgreSQL migration path.

Regenerate `schema.sql` any time after changing a model:

```bash
cd backend
python -c "
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import sqlite
from app.database import Base
import app.models  # noqa: registers every table on Base.metadata

for table in Base.metadata.sorted_tables:
    print(str(CreateTable(table).compile(dialect=sqlite.dialect())).strip() + ';\n')
" > ../database/schema.sql
```

No migration tool (Alembic) is set up for this prototype — `seed/seed_db.py` calls
`Base.metadata.create_all()`, which creates any missing table but does not alter an
existing one. For iterative schema changes during development, use
`python -m seed.seed_db --reset` to drop and recreate everything from the current
models, then reseed.

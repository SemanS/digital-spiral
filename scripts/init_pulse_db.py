#!/usr/bin/env python3
"""Initialize database tables for Executive Work Pulse."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import db
from orchestrator import pulse_models  # noqa: F401 - Import to register models


def init_pulse_tables():
    """Create all Pulse tables in the database."""
    
    print("Initializing Executive Work Pulse database tables...")
    
    # Create all tables
    db.Base.metadata.create_all(bind=db.engine)
    
    print("✅ Database tables created successfully!")
    print("\nCreated tables:")
    for table_name in db.Base.metadata.tables.keys():
        print(f"  - {table_name}")


if __name__ == "__main__":
    init_pulse_tables()


# backend/app/services/seed.py
"""Demo data seeding utilities.

The ``seed_demo_data`` function is called on application startup (see ``main.py``).
It populates the SQLite database with a minimal set of campus blocks, cameras,
responders, and a demo admin user. The function is idempotent – if any block
already exists the seeding is skipped.
"""

from sqlalchemy.orm import Session
from ..models import CampusBlock, Camera, Responder, User, UserRole

DEMO_BLOCKS = [
    {"name": "Block A", "description": "Engineering block"},
    {"name": "Block B", "description": "Science block"},
    {"name": "Library", "description": "Main library"},
    {"name": "Laboratory", "description": "Research labs"},
    {"name": "Cafeteria", "description": "Food services"},
    {"name": "Hostel", "description": "Student residence"},
    {"name": "Main Gate", "description": "Entrance"},
]


def seed_demo_data(db: Session) -> None:
    """Insert demo records if the database is empty.

    The function is deliberately simple – it does not use bulk inserts to keep
    the code readable for a hackathon demo. All objects are added one‑by‑one and
    committed after each logical group.
    """
    # Bail out early if blocks already exist
    if db.query(CampusBlock).first():
        return

    # Create campus blocks
    block_objs = []
    for blk in DEMO_BLOCKS:
        block = CampusBlock(name=blk["name"], description=blk["description"])
        db.add(block)
        block_objs.append(block)
    db.commit()
    for blk in block_objs:
        db.refresh(blk)

    # Create two demo cameras per block
    for blk in block_objs:
        for i in range(1, 3):
            cam = Camera(
                name=f"Camera {blk.name} #{i}",
                block_id=blk.id,
                is_available=True,
                processing_status="idle",
            )
            db.add(cam)
    db.commit()

    # Create responders: primary Security Officer and Backup Responder
    for blk in block_objs:
        primary = Responder(name=f"Officer {blk.name}", role="Security Officer", block_id=blk.id)
        backup = Responder(name=f"Backup {blk.name}", role="Backup Responder", block_id=blk.id)
        db.add_all([primary, backup])
    db.commit()

    # Create a demo admin user (plain password for demo only)
    admin_user = User(
        username="admin",
        full_name="Admin User",
        hashed_password="admin",  # NOTE: In a real app you would store a hashed pwd
        role=UserRole.ADMIN,
    )
    db.add(admin_user)
    db.commit()

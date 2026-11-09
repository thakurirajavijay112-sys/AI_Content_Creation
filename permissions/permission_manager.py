"""
Permissions Manager
====================
Enforces content usage rights for the Streamer Clipper engine.
Every piece of footage must have an AUTHORISED or CREATOR_PROVIDED
status before it can proceed to rendering or publishing.

Permission States:
    AUTHORISED       — Creator explicitly granted reuse rights (documented)
    CREATOR_PROVIDED — Creator directly provided the footage
    PENDING          — Awaiting creator response
    NOT_AUTHORISED   — No permission granted (default for all discovered clips)
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from core.logger import get_logger

logger = get_logger(__name__)


class PermissionStatus(str, Enum):
    AUTHORISED = "AUTHORISED"
    CREATOR_PROVIDED = "CREATOR_PROVIDED"
    PENDING = "PENDING"
    NOT_AUTHORISED = "NOT_AUTHORISED"


class PermissionManager:
    """
    Central permission manager.
    All engines must check permissions before processing any external content.
    """

    def __init__(self):
        from database.db_manager import db
        self.db = db

    def get_permission(self, entity_type: str, entity_id: int) -> PermissionStatus:
        """
        Returns the current permission status for a clip, session, or streamer.

        Args:
            entity_type: "clip", "session", or "streamer"
            entity_id: Database ID of the entity

        Returns:
            PermissionStatus enum value
        """
        row = self.db.fetchone(
            "SELECT status FROM permissions WHERE entity_type=:type AND entity_id=:id "
            "ORDER BY created_at DESC LIMIT 1",
            {"type": entity_type, "id": entity_id}
        )
        if row:
            try:
                return PermissionStatus(row["status"])
            except ValueError:
                return PermissionStatus.NOT_AUTHORISED
        return PermissionStatus.NOT_AUTHORISED

    def is_authorised(self, entity_type: str, entity_id: int) -> bool:
        """
        Returns True only if the entity is AUTHORISED or CREATOR_PROVIDED.
        This is the gate that all rendering and publishing must pass.
        """
        status = self.get_permission(entity_type, entity_id)
        authorised = status in (PermissionStatus.AUTHORISED, PermissionStatus.CREATOR_PROVIDED)
        if not authorised:
            logger.warning(
                f"Permission denied for {entity_type} #{entity_id}: status={status.value}"
            )
        return authorised

    def grant_permission(
        self,
        entity_type: str,
        entity_id: int,
        status: PermissionStatus,
        granted_by: str,
        notes: str = "",
        evidence_path: Optional[str] = None,
    ) -> int:
        """
        Records a permission grant in the database.

        Args:
            entity_type: "clip", "session", or "streamer"
            entity_id: Database ID
            status: The permission level being granted
            granted_by: Who granted it (username, email, or "creator_provided")
            notes: Optional notes about the permission
            evidence_path: Path to screenshot/email/document proving permission

        Returns:
            New permission record ID
        """
        now = datetime.utcnow().isoformat()
        self.db.execute("""
            INSERT INTO permissions (entity_type, entity_id, status, granted_by, notes, evidence_path, created_at, updated_at)
            VALUES (:type, :id, :status, :by, :notes, :evidence, :now, :now)
        """, {
            "type": entity_type,
            "id": entity_id,
            "status": status.value,
            "by": granted_by,
            "notes": notes,
            "evidence": evidence_path,
            "now": now,
        })
        logger.info(f"Permission granted: {entity_type} #{entity_id} → {status.value} by {granted_by}")

        # Also update the entity's permission field
        if entity_type == "clip":
            self.db.execute(
                "UPDATE clips SET permission=:status WHERE id=:id",
                {"status": status.value, "id": entity_id}
            )
        elif entity_type == "streamer":
            self.db.execute(
                "UPDATE streamers SET permission=:status WHERE id=:id",
                {"status": status.value, "id": entity_id}
            )

        row = self.db.fetchone("SELECT last_insert_rowid() as rid")
        return row["rid"] if row else -1

    def revoke_permission(self, entity_type: str, entity_id: int, reason: str = ""):
        """
        Revokes permission — sets status to NOT_AUTHORISED.
        Any queued jobs for this entity should be cancelled.
        """
        self.grant_permission(
            entity_type, entity_id,
            PermissionStatus.NOT_AUTHORISED,
            granted_by="system_revocation",
            notes=reason,
        )
        logger.warning(f"Permission revoked: {entity_type} #{entity_id}. Reason: {reason}")

    def get_all_permissions(self) -> list:
        """Returns all permission records (for dashboard display)."""
        return self.db.fetchall("""
            SELECT p.*, 
                   CASE p.entity_type 
                     WHEN 'clip' THEN c.title
                     WHEN 'streamer' THEN s.username
                     ELSE 'unknown'
                   END as entity_name
            FROM permissions p
            LEFT JOIN clips c ON p.entity_type='clip' AND p.entity_id=c.id
            LEFT JOIN streamers s ON p.entity_type='streamer' AND p.entity_id=s.id
            ORDER BY p.created_at DESC
        """)


# Singleton
permission_manager = PermissionManager()

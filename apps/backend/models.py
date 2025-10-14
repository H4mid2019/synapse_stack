from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(
        db.String(255), unique=True, nullable=False
    )  # e.g., "auth0|123456"
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    picture = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Relationships
    files = db.relationship(
        "FileSystemItem",
        backref="owner",
        lazy=True,
        foreign_keys="FileSystemItem.owner_id",
    )
    shared_with_me = db.relationship(
        "FilePermission",
        backref="user",
        lazy=True,
        foreign_keys="FilePermission.user_id",
    )

    def to_dict(self):
        return {
            "id": str(self.id),  # Convert to string for JavaScript compatibility
            "auth0_id": self.auth0_id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"


class FileSystemItem(db.Model):
    __tablename__ = "filesystem_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum("folder", "file", name="item_type"), nullable=False)
    parent_id = db.Column(
        db.Integer, db.ForeignKey("filesystem_items.id"), nullable=True
    )
    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # NEW: Owner
    size = db.Column(db.BigInteger, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    path = db.Column(db.String(1000), nullable=True)
    is_public = db.Column(db.Boolean, default=False)  # NEW: Public access
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    # Self-referential relationship for parent-child
    parent = db.relationship("FileSystemItem", remote_side=[id], backref="children")

    # Relationships
    permissions = db.relationship(
        "FilePermission", backref="item", lazy=True, cascade="all, delete-orphan"
    )

    # Ensure unique names per location per owner
    __table_args__ = (
        db.UniqueConstraint(
            "name", "parent_id", "owner_id", name="unique_name_per_location_per_owner"
        ),
    )

    def to_dict(self, include_owner=False):
        data = {
            "id": str(self.id),  # Convert to string for JavaScript compatibility
            "name": self.name,
            "type": self.type,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "owner_id": str(self.owner_id),
            "size": self.size,
            "mime_type": self.mime_type,
            "path": self.path,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_owner and self.owner:
            data["owner"] = {
                "id": str(self.owner.id),
                "email": self.owner.email,
                "name": self.owner.name,
            }

        return data

    def __repr__(self):
        return f"<FileSystemItem {self.name} ({self.type})>"


class FilePermission(db.Model):
    """Manages file/folder sharing between users"""

    __tablename__ = "file_permissions"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("filesystem_items.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    permission = db.Column(
        db.Enum("read", "write", "admin", name="permission_type"),
        nullable=False,
        default="read",
    )
    granted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    granted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Ensure unique user-item pairs
    __table_args__ = (
        db.UniqueConstraint("item_id", "user_id", name="unique_item_user_permission"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "item_id": str(self.item_id),
            "user_id": str(self.user_id),
            "permission": self.permission,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "granted_by": str(self.granted_by) if self.granted_by else None,
        }

    def __repr__(self):
        return f"<FilePermission item={self.item_id} user={self.user_id} perm={self.permission}>"

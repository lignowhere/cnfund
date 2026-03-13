from pydantic import BaseModel, Field


class BackupListItemDTO(BaseModel):
    backup_id: str
    backup_type: str
    created_at: str
    metadata: dict


class RestoreBackupRequest(BaseModel):
    backup_id: str = Field(min_length=1, max_length=255, pattern=r"^[\w\-\.]+$")
    backup_date: str | None = None
    confirm_phrase: str = ""
    create_safety_backup: bool = True

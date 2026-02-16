from pydantic import BaseModel


class BackupListItemDTO(BaseModel):
    backup_id: str
    backup_type: str
    created_at: str
    metadata: dict


class RestoreBackupRequest(BaseModel):
    backup_id: str
    backup_date: str | None = None
    confirm_phrase: str = ""
    create_safety_backup: bool = True

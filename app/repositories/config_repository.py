"""
配置仓储
"""
from typing import Optional, List, Dict, Any, Iterable
from sqlalchemy.orm import Session
from app.models.config import SystemConfig, UserConfig, ConfigHistory
import json


def _to_json_str(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json_str(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


class ConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- 系统/租户级 ----------
    def upsert_system_configs(self, tenant_id: Optional[str], items: Iterable[dict], operator_id: Optional[str]):
        for item in items:
            category = item["category"]
            key = item["key"]
            value = _to_json_str(item["value"])
            status = item.get("status", True)

            existing = (
                self.db.query(SystemConfig)
                .filter(SystemConfig.tenant_id == tenant_id, SystemConfig.category == category, SystemConfig.key == key)
                .first()
            )
            if existing:
                old_value = existing.value
                existing.value = value
                existing.status = status
                self._add_history("tenant" if tenant_id else "system", tenant_id, category, key, old_value, value, operator_id)
            else:
                cfg = SystemConfig(
                    tenant_id=tenant_id,
                    category=category,
                    key=key,
                    value=value,
                    status=status,
                    created_by=operator_id,
                )
                self.db.add(cfg)
                self._add_history("tenant" if tenant_id else "system", tenant_id, category, key, None, value, operator_id)

    def list_system_configs(self, tenant_id: Optional[str] = None) -> List[SystemConfig]:
        query = self.db.query(SystemConfig)
        if tenant_id is None:
            query = query.filter(SystemConfig.tenant_id.is_(None))
        else:
            query = query.filter(SystemConfig.tenant_id == tenant_id)
        return query.all()

    def delete_system_config(self, tenant_id: Optional[str], category: str, key: str, operator_id: Optional[str]):
        """删除系统/租户级配置"""
        existing = (
            self.db.query(SystemConfig)
            .filter(SystemConfig.tenant_id == tenant_id, SystemConfig.category == category, SystemConfig.key == key)
            .first()
        )
        if existing:
            old_value = existing.value
            self.db.delete(existing)
            self._add_history("tenant" if tenant_id else "system", tenant_id, category, key, old_value, None, operator_id)

    # ---------- 用户级 ----------
    def upsert_user_configs(self, user_id: str, items: Iterable[dict], operator_id: Optional[str]):
        for item in items:
            category = item["category"]
            key = item["key"]
            value = _to_json_str(item["value"])
            status = item.get("status", True)

            existing = (
                self.db.query(UserConfig)
                .filter(UserConfig.user_id == user_id, UserConfig.category == category, UserConfig.key == key)
                .first()
            )
            if existing:
                old_value = existing.value
                existing.value = value
                existing.status = status
                self._add_history("user", user_id, category, key, old_value, value, operator_id)
            else:
                cfg = UserConfig(
                    user_id=user_id,
                    category=category,
                    key=key,
                    value=value,
                    status=status,
                    created_by=operator_id,
                )
                self.db.add(cfg)
                self._add_history("user", user_id, category, key, None, value, operator_id)

    def list_user_configs(self, user_id: str) -> List[UserConfig]:
        return (
            self.db.query(UserConfig)
            .filter(UserConfig.user_id == user_id)
            .all()
        )

    # ---------- 历史 ----------
    def _add_history(
        self,
        scope_type: str,
        scope_id: Optional[str],
        category: str,
        key: str,
        old_value: Optional[str],
        new_value: Optional[str],
        operator_id: Optional[str],
    ):
        history = ConfigHistory(
            scope_type=scope_type,
            scope_id=scope_id,
            category=category,
            key=key,
            old_value=old_value,
            new_value=new_value,
            operator_id=operator_id,
        )
        self.db.add(history)

    def list_history(
        self,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        category: Optional[str] = None,
        key: Optional[str] = None,
    ) -> List[ConfigHistory]:
        query = self.db.query(ConfigHistory)
        if scope_type:
            query = query.filter(ConfigHistory.scope_type == scope_type)
        if scope_id is not None:
            query = query.filter(ConfigHistory.scope_id == scope_id)
        if category:
            query = query.filter(ConfigHistory.category == category)
        if key:
            query = query.filter(ConfigHistory.key == key)
        return query.order_by(ConfigHistory.created_at.desc()).all()

    # ---------- 合并逻辑辅助 ----------
    def to_dict(self, configs: List[SystemConfig]) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for cfg in configs:
            if not cfg.status:
                continue
            if cfg.category not in result:
                result[cfg.category] = {}
            result[cfg.category][cfg.key] = _from_json_str(cfg.value)
        return result

    def to_dict_user(self, configs: List[UserConfig]) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for cfg in configs:
            if not cfg.status:
                continue
            if cfg.category not in result:
                result[cfg.category] = {}
            result[cfg.category][cfg.key] = _from_json_str(cfg.value)
        return result

    # ---------- 事务辅助 ----------
    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()


"""
配置领域服务（对象化配置 + 敏感字段加密/脱敏）
"""
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from app.repositories.config_repository import ConfigRepository
from app.schemas.config import ConfigUpdateRequest
from app.core.config_definitions import CONFIG_DEFINITIONS
import numbers
import base64
import copy


class ConfigService:
    def __init__(self, config_repo: ConfigRepository):
        self.config_repo = config_repo

    # -------- 获取配置 --------
    def get_effective_config(self, tenant_id: Optional[str], user_id: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取有效配置（系统 -> 租户 -> 用户 覆盖），敏感字段脱敏
        """
        system_cfg = self._decrypt_and_mask(self.config_repo.to_dict(self.config_repo.list_system_configs(None)))
        tenant_cfg = (
            self._decrypt_and_mask(self.config_repo.to_dict(self.config_repo.list_system_configs(tenant_id)))
            if tenant_id
            else {}
        )
        user_cfg = (
            self._decrypt_and_mask(self.config_repo.to_dict_user(self.config_repo.list_user_configs(user_id)))
            if user_id
            else {}
        )

        merged: Dict[str, Dict[str, Any]] = {}
        self._merge_config(merged, system_cfg)
        self._merge_config(merged, tenant_cfg)
        self._merge_config(merged, user_cfg)
        return merged

    def list_scope_configs(self, scope: str, scope_id: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """
        按作用域列出配置（不合并），敏感字段脱敏
        """
        if scope == "system":
            cfg = self._decrypt_and_mask(self.config_repo.to_dict(self.config_repo.list_system_configs(None)))
        elif scope == "tenant":
            if scope_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 tenant_id")
            cfg = self._decrypt_and_mask(self.config_repo.to_dict(self.config_repo.list_system_configs(scope_id)))
        elif scope == "user":
            if scope_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 user_id")
            cfg = self._decrypt_and_mask(self.config_repo.to_dict_user(self.config_repo.list_user_configs(scope_id)))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scope 必须是 system/tenant/user")
        return cfg

    # -------- 更新配置 --------
    def update_system_config(self, items: ConfigUpdateRequest, operator_id: Optional[str]):
        enc_items = self._validate_and_encrypt(items)
        try:
            self.config_repo.upsert_system_configs(None, enc_items, operator_id)
            self.config_repo.commit()
        except Exception as e:
            self.config_repo.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新系统配置失败: {e}")

    def _is_config_value_empty(self, value: Any) -> bool:
        """检查配置值是否为空（空对象或所有字段都为空）"""
        if not value:
            return True
        if not isinstance(value, dict):
            return False
        if len(value) == 0:
            return True
        # 检查所有字段是否都为空
        for v in value.values():
            if v is not None and v != "" and v != []:
                return False
        return True

    def update_tenant_config(self, tenant_id: str, items: ConfigUpdateRequest, operator_id: Optional[str]):
        """
        更新租户级配置
        如果配置项为空或所有字段都为空，则删除该配置项（回退到系统级默认值）
        """
        # 先验证配置项（如果为空则跳过验证）
        non_empty_items = []
        items_to_delete = []
        
        for item in items.items:
            # 检查配置值是否为空
            if self._is_config_value_empty(item.value):
                # 配置值为空，标记为删除
                items_to_delete.append(item)
            else:
                # 配置值不为空，需要验证
                non_empty_items.append(item)
        
        # 验证非空配置项
        if non_empty_items:
            non_empty_request = ConfigUpdateRequest(items=non_empty_items)
            enc_items = self._validate_and_encrypt(non_empty_request)
            try:
                self.config_repo.upsert_system_configs(tenant_id, enc_items, operator_id)
            except Exception as e:
                self.config_repo.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新租户配置失败: {e}")
        
        # 删除空配置项
        for item in items_to_delete:
            try:
                self.config_repo.delete_system_config(tenant_id, item.category, item.key, operator_id)
            except Exception as e:
                self.config_repo.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除租户配置失败: {e}")
        
        try:
            self.config_repo.commit()
        except Exception as e:
            self.config_repo.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新租户配置失败: {e}")

    def update_user_config(self, user_id: str, items: ConfigUpdateRequest, operator_id: Optional[str]):
        enc_items = self._validate_and_encrypt(items)
        try:
            self.config_repo.upsert_user_configs(user_id, enc_items, operator_id)
            self.config_repo.commit()
        except Exception as e:
            self.config_repo.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新用户配置失败: {e}")

    # -------- 历史 --------
    def list_history(
        self,
        scope_type: Optional[str],
        scope_id: Optional[str],
        category: Optional[str],
        key: Optional[str],
    ):
        return self.config_repo.list_history(scope_type, scope_id, category, key)

    # -------- 校验 --------
    def validate_items(self, items: ConfigUpdateRequest):
        self._validate_items(items)
        return {"valid": True, "message": "校验通过"}

    # -------- 内部辅助 --------
    def _merge_config(self, target: Dict[str, Dict[str, Any]], source: Dict[str, Dict[str, Any]]):
        for category, kv in source.items():
            if category not in target:
                target[category] = {}
            target[category].update(kv)

    def _validate_items(self, items: ConfigUpdateRequest):
        for item in items.items:
            category = item.category
            key = item.key
            value = item.value

            if not category or not key:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="category/key 不能为空")

            if category not in CONFIG_DEFINITIONS:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的配置类别: {category}")
            if key not in CONFIG_DEFINITIONS[category]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的配置键: {category}.{key}")

            field_defs = CONFIG_DEFINITIONS[category][key]
            self._validate_object_fields(f"{category}.{key}", value, field_defs)

        # 跨字段校验：doc.chunk.overlap < doc.chunk.size
        temp: Dict[str, Dict[str, Any]] = {}
        for item in items.items:
            temp.setdefault(item.category, {})[item.key] = item.value
        if "doc" in temp and "chunk" in temp["doc"]:
            chunk = temp["doc"]["chunk"]
            size = chunk.get("size")
            overlap = chunk.get("overlap")
            if size is not None and overlap is not None and overlap >= size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="doc.chunk.overlap 必须小于 doc.chunk.size",
                )

    def _validate_object_fields(self, prefix: str, obj: Any, field_defs: Dict[str, Any]):
        if not isinstance(obj, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{prefix} 必须是对象")
        for field_name, rule in field_defs.items():
            if rule.get("required") and field_name not in obj:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{prefix}.{field_name} 为必填项")
            if field_name not in obj:
                continue
            val = obj[field_name]
            expected_type = rule.get("type")
            if expected_type and not isinstance(val, expected_type):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{prefix}.{field_name} 类型应为 {expected_type}",
                )
            if isinstance(val, numbers.Number):
                if "min" in rule and val < rule["min"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{prefix}.{field_name} 最小值为 {rule['min']}",
                    )
                if "max" in rule and val > rule["max"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{prefix}.{field_name} 最大值为 {rule['max']}",
                    )
            if "allowed_values" in rule and val is not None:
                if isinstance(val, list):
                    invalid = [v for v in val if v not in rule["allowed_values"]]
                    if invalid:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"{prefix}.{field_name} 包含不支持的值: {invalid}",
                        )
                else:
                    if val not in rule["allowed_values"]:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"{prefix}.{field_name} 仅支持 {rule['allowed_values']}",
                        )

    def _validate_and_encrypt(self, items: ConfigUpdateRequest) -> List[dict]:
        self._validate_items(items)
        encrypted_items: List[dict] = []
        for item in items.items:
            new_item = copy.deepcopy(item.dict())
            category = new_item["category"]
            key = new_item["key"]
            value = new_item["value"]
            field_defs = CONFIG_DEFINITIONS[category][key]
            new_item["value"] = self._encrypt_object_fields(value, field_defs)
            encrypted_items.append(new_item)
        return encrypted_items

    def _encrypt_object_fields(self, obj: Any, field_defs: Dict[str, Any]):
        if not isinstance(obj, dict):
            return obj
        new_obj = {}
        for k, v in obj.items():
            rule = field_defs.get(k, {})
            if rule.get("sensitive") and isinstance(v, str):
                new_obj[k] = self._encrypt(v)
            elif isinstance(v, dict) and "type" not in rule:
                new_obj[k] = self._encrypt_object_fields(v, rule)
            else:
                new_obj[k] = v
        return new_obj

    def _decrypt_and_mask(self, cfg: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for category, kv in cfg.items():
            result[category] = {}
            for key, value in kv.items():
                if category not in CONFIG_DEFINITIONS or key not in CONFIG_DEFINITIONS[category]:
                    result[category][key] = value
                    continue
                field_defs = CONFIG_DEFINITIONS[category][key]
                result[category][key] = self._decrypt_object_fields(value, field_defs)
        return result

    def _decrypt_object_fields(self, obj: Any, field_defs: Dict[str, Any]):
        if not isinstance(obj, dict):
            return obj
        new_obj = {}
        for k, v in obj.items():
            rule = field_defs.get(k, {})
            if rule.get("sensitive") and isinstance(v, str):
                decrypted = self._decrypt(v)
                new_obj[k] = self._mask(decrypted)
            elif isinstance(v, dict) and "type" not in rule:
                new_obj[k] = self._decrypt_object_fields(v, rule)
            else:
                new_obj[k] = v
        return new_obj

    def _encrypt(self, text: str) -> str:
        return "ENC:" + base64.b64encode(text.encode("utf-8")).decode("utf-8")

    def _decrypt(self, text: str) -> str:
        if text.startswith("ENC:"):
            try:
                return base64.b64decode(text[4:].encode("utf-8")).decode("utf-8")
            except Exception:
                return text
        return text

    def _mask(self, text: str) -> str:
        if not text:
            return ""
        if len(text) <= 8:
            return text[0] + "*" * max(0, len(text) - 2) + text[-1]
        return text[:4] + "*" * (len(text) - 8) + text[-4]


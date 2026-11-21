"""
Unit tests for WeComConfig
"""

import os
from pathlib import Path
from wechat_common.config import WeComConfig, get_config


def test_wecom_config_defaults():
    cfg = WeComConfig()
    assert cfg.corp_id == "ww3ee9feeacefff47d"
    assert cfg.bot_id == "aibHijIfgjxior5g9W-WFBdeoqN8QhnrSh_"
    assert cfg.last_chat_id == "LuoYuXun"


def test_wecom_config_save_and_load(tmp_path: Path):
    cfg_file = tmp_path / "custom_config.json"
    cfg = WeComConfig(
        corp_id="corp_abc",
        bot_id="bot_123",
        bot_secret="sec_xyz",
        last_chat_id="user_test",
        config_file_path=cfg_file
    )
    cfg.save()
    assert cfg_file.exists()

    loaded = get_config(config_path=cfg_file)
    assert loaded.corp_id == "corp_abc"
    assert loaded.bot_id == "bot_123"
    assert loaded.last_chat_id == "user_test"


def test_wecom_config_env_override(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("WECOM_BOT_ID", "env_bot_id")
    monkeypatch.setenv("WECOM_DEFAULT_CHAT_ID", "env_chat_id")
    
    cfg = get_config(config_path=tmp_path / "non_existent.json")
    assert cfg.bot_id == "env_bot_id"
    assert cfg.last_chat_id == "env_chat_id"

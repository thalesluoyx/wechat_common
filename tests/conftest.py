"""
Pytest global fixtures for wechat_common (Strict Mocking & Isolation)
"""

import sys
from pathlib import Path

# Ensure src is in python path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from unittest.mock import AsyncMock, MagicMock
from wechat_common.config import WeComConfig


@pytest.fixture
def dummy_config(tmp_path: Path) -> WeComConfig:
    """Fixture providing an isolated temporary configuration."""
    cfg_file = tmp_path / "test_wecom_config.json"
    return WeComConfig(
        corp_id="test_corp_id",
        bot_id="test_bot_id",
        bot_secret="test_bot_secret",
        last_chat_id="test_user_id",
        config_file_path=cfg_file
    )


@pytest.fixture
def mock_ws_client():
    """Fixture providing a strictly mocked WSClient for offline testing."""
    client = MagicMock()
    client.is_connected = True
    client.is_authenticated = True
    client.connect_async = AsyncMock(return_value=None)
    client.disconnect = AsyncMock(return_value=None)
    
    mock_res = MagicMock()
    mock_res.errcode = 0
    mock_res.errmsg = "ok"
    client.send_message = AsyncMock(return_value=mock_res)
    client.reply_stream = AsyncMock(return_value=mock_res)
    client.on = MagicMock()
    return client

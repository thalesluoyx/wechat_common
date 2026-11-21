"""
Unit tests for WeComNotifier (Strict Mocking / 100% Offline)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from wechat_common.notifier import WeComNotifier, send_wecom_message
from wechat_common.config import WeComConfig


@pytest.mark.asyncio
async def test_wecom_notifier_send_async_success(dummy_config, mock_ws_client):
    notifier = WeComNotifier(config=dummy_config)

    with patch("wechat_common.notifier.WSClient", return_value=mock_ws_client):
        success = await notifier.send_async(
            content="Hello Test",
            chat_id="user_123",
            msg_type="markdown"
        )
        assert success is True
        mock_ws_client.connect_async.assert_called_once()
        mock_ws_client.send_message.assert_called_once()
        mock_ws_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_wecom_notifier_send_async_missing_target(dummy_config):
    dummy_config.last_chat_id = ""
    notifier = WeComNotifier(config=dummy_config)

    success = await notifier.send_async(content="Hello", chat_id=None)
    assert success is False


def test_send_wecom_message_sync(dummy_config, mock_ws_client):
    with patch("wechat_common.notifier.WSClient", return_value=mock_ws_client):
        result = send_wecom_message(
            content="Sync Test",
            config=dummy_config
        )
        assert result is True

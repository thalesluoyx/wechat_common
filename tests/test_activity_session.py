"""
Unit tests for DailyActivitySession (Strict Mocking / 100% Offline)
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from wechat_common.activity_session import DailyActivitySession


@pytest.fixture
def activity_session(tmp_path: Path):
    session_file = tmp_path / "test_session.json"
    session = DailyActivitySession(session_file=session_file)
    return session


@pytest.mark.asyncio
async def test_handle_greeting(activity_session):
    mock_frame = MagicMock()
    with patch.object(activity_session, "_send_to_ai_session", return_value=None):
        reply = await activity_session.handle_user_message("hi", "user_123", mock_frame)
        assert "日常运动_Session" in reply or "打卡" in reply
        assert len(activity_session.history) == 2


@pytest.mark.asyncio
async def test_handle_gym_rejection(activity_session):
    mock_frame = MagicMock()
    reply = await activity_session.handle_user_message("今天深蹲 80kg 3组", "user_123", mock_frame)
    assert "本会话为【日常运动_Session】" in reply
    assert "健身私教" in reply


@pytest.mark.asyncio
async def test_handle_walk_recording(activity_session):
    mock_frame = MagicMock()
    with patch.object(activity_session, "_send_to_ai_session", return_value=None):
        with patch.object(activity_session, "_execute_record_js", return_value="Recorded walk successfully"):
            reply = await activity_session.handle_user_message("今天散步 7500步", "user_123", mock_frame)
            assert "散步记录成功" in reply
            assert "7500" in reply


@pytest.mark.asyncio
async def test_handle_meditation_recording(activity_session):
    mock_frame = MagicMock()
    with patch.object(activity_session, "_send_to_ai_session", return_value=None):
        with patch.object(activity_session, "_execute_record_js", return_value="Recorded meditation successfully"):
            reply = await activity_session.handle_user_message("刚才内观 30分钟 观呼吸 平静", "user_123", mock_frame)
            assert "内观记录成功" in reply
            assert "30" in reply


@pytest.mark.asyncio
async def test_handle_ai_session_success(activity_session):
    mock_frame = MagicMock()
    with patch.object(activity_session, "_send_to_ai_session", return_value="AI回复：散步8000步已成功记录！"):
        reply = await activity_session.handle_user_message("散步 8000步", "user_123", mock_frame)
        assert "AI回复" in reply
        assert "8000步" in reply

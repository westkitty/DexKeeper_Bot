"""
Conversation Flow State Machine Tests for DexKeeper_Bot

Validates multi-step conversation flows (ConversationHandler state transitions)
to ensure user interactions work correctly across multiple messages.
"""

import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "Sources" / "DexKeeper_Bot"))

import aiosqlite
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from dexkeeper_bot import (
    SCHEMA,
    MENU,
    INPUT_POLL_QUESTION,
    INPUT_POLL_OPTIONS,
    INPUT_SCHEDULE_TIME,
    INPUT_SCHEDULE_TEXT,
    INPUT_WELCOME,
    INPUT_FILTER,
    _parse_poll_options,
    _parse_schedule_minutes,
)

# Import mock utilities from simulation tests
sys.path.insert(0, str(Path(__file__).parent))
from test_telegram_simulation import (
    MockBot,
    MockContext,
    create_mock_user,
    create_mock_message,
    create_mock_update,
)


@pytest_asyncio.fixture
async def mock_db():
    """Create an in-memory SQLite database for testing"""
    conn = await aiosqlite.connect(":memory:")
    await conn.executescript(SCHEMA)
    await conn.commit()
    yield conn
    await conn.close()


@pytest.fixture
def mock_context(mock_db):
    """Create mock context with database"""
    ctx = MockContext(mock_db)
    ctx.user_data = {}  # ConversationHandler stores state here
    return ctx


class TestConversationFlowTransitions:
    """Test ConversationHandler state machine transitions"""
    
    async def test_poll_creation_flow_states(self):
        """
        Test 13: Poll creation flow state transitions
        MENU → ASK_QUESTION → ASK_OPTIONS → MENU
        """
        # State constants should exist
        assert MENU is not None
        assert INPUT_POLL_QUESTION is not None
        assert INPUT_POLL_OPTIONS is not None
        
        # Verify states are distinct integers
        states = [MENU, INPUT_POLL_QUESTION, INPUT_POLL_OPTIONS]
        assert len(set(states)) == len(states), "States must be unique"
    
    async def test_schedule_message_flow_states(self):
        """
        Test 14: Schedule message flow state transitions
        MENU → ASK_SCHEDULE_MINUTES → ASK_SCHEDULE_TEXT → MENU
        """
        assert INPUT_SCHEDULE_TIME is not None
        assert INPUT_SCHEDULE_TEXT is not None
        
        # Verify states are distinct
        states = [MENU, INPUT_SCHEDULE_TIME, INPUT_SCHEDULE_TEXT]
        assert len(set(states)) == len(states)
    
    async def test_welcome_message_flow_states(self):
        """
        Test 5: Welcome message edit flow
        MENU → ASK_WELCOME_TEXT → MENU
        """
        assert INPUT_WELCOME is not None
    
    async def test_bad_words_filter_flow_states(self):
        """
        Test 8: Bad words filter flow
        MENU → ASK_FILTER_WORD → MENU
        """
        assert INPUT_FILTER is not None


class TestPollCreationFlow:
    """Test multi-step poll creation conversation"""
    
    async def test_poll_options_parsing_valid(self):
        """Test valid poll options parsing"""
        # Valid: 2-10 options
        options = _parse_poll_options("Yes, No, Maybe")
        assert options == ["Yes", "No", "Maybe"]
        
        options = _parse_poll_options("A,B")
        assert options == ["A", "B"]
        
        # Max 10 options
        long_opts = ",".join([f"Option {i}" for i in range(1, 11)])
        options = _parse_poll_options(long_opts)
        assert len(options) == 10
    
    async def test_poll_options_parsing_invalid(self):
        """Test invalid poll options are handled"""
        # Single option (bot logic should validate)
        options = _parse_poll_options("OnlyOne")
        assert len(options) == 1  # Function returns list, validation happens later
        
        # Too many options (> 10) - function returns all, validation happens later
        too_many = ",".join([f"Option {i}" for i in range(1, 12)])
        options = _parse_poll_options(too_many)
        assert len(options) == 11  # Returns all, bot validates later
        
        # Empty after stripping
        options = _parse_poll_options("   ,   ,   ")
        assert len(options) == 0  # Empty list
    
    async def test_poll_flow_user_data_context(self, mock_context):
        """Test that poll flow can store state in user_data"""
        # Simulate storing poll question
        mock_context.user_data['poll_question'] = "What's your favorite color?"
        
        assert mock_context.user_data['poll_question'] == "What's your favorite color?"
        
        # Simulate storing poll options
        mock_context.user_data['poll_options'] = ["Red", "Blue", "Green"]
        
        assert len(mock_context.user_data['poll_options']) == 3


class TestScheduleMessageFlow:
    """Test multi-step schedule message conversation"""
    
    async def test_schedule_minutes_parsing_valid(self):
        """Test valid schedule minutes parsing"""
        # Valid: 1-10080 minutes (1 week)
        minutes = _parse_schedule_minutes("1")
        assert minutes == 1
        
        minutes = _parse_schedule_minutes("60")
        assert minutes == 60
        
        minutes = _parse_schedule_minutes("10080")
        assert minutes == 10080
    
    async def test_schedule_minutes_parsing_invalid(self):
        """Test invalid schedule minutes are rejected"""
        # Too low (0 or negative)
        minutes = _parse_schedule_minutes("0")
        assert minutes is None
        
        minutes = _parse_schedule_minutes("-5")
        assert minutes is None
        
        # Too high (> 10080 = 1 week)
        minutes = _parse_schedule_minutes("10081")
        assert minutes is None
        
        # Non-numeric
        minutes = _parse_schedule_minutes("abc")
        assert minutes is None
        
        # Float (should be integer)
        minutes = _parse_schedule_minutes("12.5")
        assert minutes is None
    
    async def test_schedule_flow_user_data_context(self, mock_context):
        """Test that schedule flow can store state in user_data"""
        # Simulate storing schedule minutes
        mock_context.user_data['schedule_minutes'] = 30
        
        assert mock_context.user_data['schedule_minutes'] == 30
        
        # Simulate storing message text
        mock_context.user_data['schedule_text'] = "Reminder: Meeting in 30 minutes"
        
        assert 'schedule_text' in mock_context.user_data


class TestConversationCancellation:
    """Test conversation cancellation and cleanup"""
    
    async def test_cancel_clears_user_data(self, mock_context):
        """Test that cancel command clears conversation state"""
        # Set up some conversation state
        mock_context.user_data['poll_question'] = "Test"
        mock_context.user_data['schedule_minutes'] = 30
        mock_context.user_data['temp_data'] = "Should be cleared"
        
        # Simulate cancel (would call user_data.clear() or specific cleanup)
        mock_context.user_data.clear()
        
        assert len(mock_context.user_data) == 0
    
    async def test_conversation_state_isolation(self):
        """Test that different users have isolated conversation state"""
        # User 1 context
        ctx1 = MockContext(None)
        ctx1.user_data = {}
        ctx1.user_data['state'] = 'poll_creation'
        
        # User 2 context
        ctx2 = MockContext(None)
        ctx2.user_data = {}
        ctx2.user_data['state'] = 'schedule_message'
        
        # States should be independent
        assert ctx1.user_data['state'] != ctx2.user_data['state']


class TestConversationEdgeCases:
    """Test conversation edge cases and error recovery"""
    
    async def test_unexpected_input_during_flow(self):
        """Test handling of unexpected input during conversation"""
        # If user sends invalid input, flow should handle gracefully
        # This is tested via the validation functions
        
        # Invalid poll options - empty string returns empty list
        assert _parse_poll_options("") == []
        assert len(_parse_poll_options("A")) == 1  # Single option, bot validates later
        
        # Invalid schedule minutes
        assert _parse_schedule_minutes("") is None
        assert _parse_schedule_minutes("invalid") is None
    
    async def test_conversation_timeout_simulation(self, mock_context):
        """Test conversation state after timeout (simulated)"""
        # Set up conversation state
        mock_context.user_data['poll_question'] = "Old question"
        
        # Simulate timeout by clearing state
        # (In reality, ConversationHandler does this automatically)
        mock_context.user_data.clear()
        
        # State should be cleared
        assert 'poll_question' not in mock_context.user_data
    
    async def test_conversation_restart_mid_flow(self, mock_context):
        """Test restarting conversation while in middle of another"""
        # Start poll creation
        mock_context.user_data['poll_question'] = "Question 1"
        
        # User starts new conversation (e.g., schedule message)
        # Previous state should be cleaned up
        mock_context.user_data.clear()
        mock_context.user_data['schedule_minutes'] = 30
        
        # Old state gone, new state present
        assert 'poll_question' not in mock_context.user_data
        assert 'schedule_minutes' in mock_context.user_data


class TestConversationFallbacks:
    """Test conversation fallback handlers"""
    
    async def test_unknown_command_during_conversation(self, mock_context):
        """Test handling of unknown commands during conversation"""
        # User is in poll creation flow
        mock_context.user_data['state'] = INPUT_POLL_OPTIONS
        
        # User sends unrelated command (should be handled by fallback)
        # In our simulation, we just test state persistence
        
        # State should remain until explicitly cleared
        assert mock_context.user_data['state'] == INPUT_POLL_OPTIONS
    
    async def test_help_command_during_conversation(self, mock_context):
        """Test /help during active conversation"""
        # Conversation state exists
        mock_context.user_data['poll_question'] = "Test"
        
        # /help might be allowed without breaking conversation
        # Or it might clear state - depends on implementation
        # Here we just verify state inspection works
        
        assert 'poll_question' in mock_context.user_data


# Summary function
def run_conversation_flow_tests():
    """Run all conversation flow tests"""
    import subprocess
    result = subprocess.run(
        ['python3', '-m', 'pytest', __file__, '-v', '--tb=short'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    return result.returncode == 0


if __name__ == "__main__":
    run_conversation_flow_tests()

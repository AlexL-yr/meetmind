from unittest.mock import patch, MagicMock

def test_get_llm():
    with patch("src.core.llm.ChatGoogleGenerativeAI") as mock_chat:
        mock_chat.return_value = MagicMock()

        from src.core.llm import get_llm as core_get_llm

        core_get_llm.cache_clear()
        llm = core_get_llm()

        assert llm is not None
        mock_chat.assert_called()
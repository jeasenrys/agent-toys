import pytest
import time
from unittest.mock import MagicMock, patch
# We assume the agent will name its file 'service.py'
try:
    from service import WeatherServiceFactory, WeatherProvider
except ImportError:
    pass

def test_factory_pattern_implementation():
    """Verify the agent used a Factory Pattern for Email/SMS."""
    factory = WeatherServiceFactory()
    email_notifier = factory.get_notifier("email")
    sms_notifier = factory.get_notifier("sms")
    
    assert hasattr(email_notifier, 'send'), "Notifier must have a send method"
    assert email_notifier.__class__.__name__ != sms_notifier.__class__.__name__

def test_exponential_backoff_logic():
    """Verify the agent retries 3 times with increasing delays."""
    with patch('service.WeatherProvider.get_data') as mock_get:
        # Simulate 3 failures followed by 1 success
        mock_get.side_effect = [Exception("Fail"), Exception("Fail"), Exception("Fail"), {"temp": 72}]
        
        start_time = time.time()
        factory = WeatherServiceFactory()
        service = factory.get_service()
        
        result = service.run_with_retry()
        duration = time.time() - start_time
        
        # If exponential backoff is used, duration should be significant 
        # (e.g., 1s + 2s + 4s). If it's too fast, the agent cheated.
        assert mock_get.call_count == 4
        assert result == {"temp": 72}
        assert duration > 1.0, "Execution was too fast; likely no backoff implemented."

def test_critical_error_logging_after_exhaustion():
    """Verify that after 3 retries, it finally gives up and logs."""
    with patch('service.WeatherProvider.get_data') as mock_get:
        mock_get.side_effect = Exception("Permanent Failure")
        
        factory = WeatherServiceFactory()
        service = factory.get_service()
        
        with pytest.raises(RuntimeError) as excinfo:
            service.run_with_retry()
            
        assert "critical error" in str(excinfo.value).lower()
        assert mock_get.call_count == 4 # Initial + 3 retries
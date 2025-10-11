"""
Test configuration and fixtures for the mix-shift-dashboard tests.
"""
import pytest
from flask import Flask
from kyros_plotly_common.core.cache import cache


@pytest.fixture(scope="session", autouse=True)
def setup_cache():
    """
    Set up the cache for testing by creating a test Flask app and initializing the cache.
    This ensures that the cache object has the required 'app' attribute during tests.
    """
    # Create a test Flask app
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    test_app.config['DEBUG'] = False
    
    # Initialize the cache with the test app
    cache.init_app(
        test_app,
        config={
            "CACHE_TYPE": "SimpleCache",  # Use simple cache for testing
            "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes for tests
        }
    )
    
    # Yield to allow tests to run
    yield
    
    # Clean up
    cache.clear() 
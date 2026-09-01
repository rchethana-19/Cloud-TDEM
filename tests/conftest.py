"""
Pytest configuration and shared fixtures for TDEM tests
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment to test
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["STORAGE_PATH"] = "./data/test/storage"
os.environ["METADATA_PATH"] = "./data/test/metadata"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment"""
    import tempfile
    from pathlib import Path
    
    # Create test data directory
    test_data_dir = Path("./data/test")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    (test_data_dir / "storage").mkdir(exist_ok=True)
    (test_data_dir / "metadata").mkdir(exist_ok=True)
    (test_data_dir / "metadata" / "audit").mkdir(exist_ok=True)
    
    yield
    
    # Cleanup could go here if needed

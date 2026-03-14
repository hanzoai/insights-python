#!/usr/bin/env python3
"""
Simple test script for Insights remote config endpoint.
"""

import hanzo_insights

# Initialize Insights client
hanzo_insights.api_key = "phc_..."
hanzo_insights.personal_api_key = "phs_..."  # or "phx_..."
hanzo_insights.host = "http://localhost:8000"  # or "https://us.insights.hanzo.ai"
hanzo_insights.debug = True


def test_remote_config():
    """Test remote config payload retrieval."""
    print("Testing remote config endpoint...")

    # Test feature flag key - replace with an actual flag key from your project
    flag_key = "unencrypted-remote-config-setting"

    try:
        # Get remote config payload
        payload = hanzo_insights.get_remote_config_payload(flag_key)
        print(f"✅ Success! Remote config payload for '{flag_key}': {payload}")

    except Exception as e:
        print(f"❌ Error getting remote config: {e}")


if __name__ == "__main__":
    test_remote_config()

"""
Feature Extraction Module
Converts backend request data into AI model features.
"""

def extract_features(request_data):

    features = {

        "login_hour": request_data["login_hour"],

        "trusted_device": request_data["trusted_device"],

        "country": request_data["country"],

        "ip_reputation": request_data["ip_reputation"],

        "vpn_detected": request_data["vpn_detected"],

        "failed_login_attempts": request_data["failed_login_attempts"],

        "browser": request_data["browser"],

        "access_frequency": request_data["access_frequency"],

        "file_sensitivity": request_data["file_sensitivity"],

        "refresh_frequency": request_data["refresh_frequency"]

    }

    return features
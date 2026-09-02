from major_project.feature_extractor import extract_features

backend_request = {

    "user_id": "RITHIKA001",

    "device_id": "DEVICE123",

    "ip_address": "192.8.1.45",

    "login_hour": 22,

    "trusted_device": 0,

    "country": "India",

    "ip_reputation": 0.42,

    "vpn_detected": 1,

    "failed_login_attempts": 4,

    "browser": "Chrome",

    "access_frequency": 7,

    "file_sensitivity": "High",

    "refresh_frequency": 5

}

features = extract_features(backend_request)

print(features)
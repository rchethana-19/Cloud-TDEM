from major_project.service import evaluate_request

request = {

    "user_id": "RITHIKA001",

    "device_id": "DEVICE001",

    "ip_address": "192.168.1.15",

    "login_hour": 2,

    "trusted_device": 0,

    "country": "Unknown",

    "ip_reputation": 0.15,

    "vpn_detected": 1,

    "failed_login_attempts": 8,

    "browser": "Firefox",

    "access_frequency": 14,

    "file_sensitivity": "High",

    "refresh_frequency": 9

}

print(evaluate_request(request))
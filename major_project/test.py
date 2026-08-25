from risk_engine import calculate_risk
from explain import generate_explanation

user = {
    "login_hour": 2,
    "trusted_device": 0,
    "country": "Unknown",
    "ip_reputation": 0.12,
    "vpn_detected": 1,
    "failed_login_attempts": 8,
    "browser": "Firefox",
    "access_frequency": 15,
    "file_sensitivity": "High",
    "refresh_frequency": 9
}

result = calculate_risk(user)

print(result)

explanation = generate_explanation(
    user,
    result["decision"]
)

print("\nExplanation")
print("----------------")

print("Decision :", explanation["decision"])

for reason in explanation["reasons"]:
    print("•", reason)
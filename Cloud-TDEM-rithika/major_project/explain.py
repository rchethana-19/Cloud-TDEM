def generate_explanation(features, decision):

    reasons = []

    # Login Time
    if features["login_hour"] < 6 or features["login_hour"] > 22:
        reasons.append("Login at unusual hour")

    # Device
    if features["trusted_device"] == 0:
        reasons.append("Unknown or untrusted device")

    # VPN
    if features["vpn_detected"] == 1:
        reasons.append("VPN detected")

    # Failed Logins
    if features["failed_login_attempts"] >= 3:
        reasons.append("Multiple failed login attempts")

    # IP Reputation
    if features["ip_reputation"] < 0.40:
        reasons.append("Low IP reputation")

    # Refresh Frequency
    if features["refresh_frequency"] > 5:
        reasons.append("High refresh request frequency")

    # File Sensitivity
    if features["file_sensitivity"] == "High":
        reasons.append("Accessing highly sensitive file")

    if not reasons:
        reasons.append("Normal user behaviour detected")

    return {
        "decision": decision,
        "reasons": reasons
    }
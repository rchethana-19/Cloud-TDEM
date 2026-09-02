import pandas as pd
import random

NUM_RECORDS = 3000

countries = ["India", "USA", "Germany", "UK", "Canada", "Unknown"]
browsers = ["Chrome", "Firefox", "Edge", "Safari"]
sensitivities = ["Low", "Medium", "High"]

data = []

for _ in range(NUM_RECORDS):

    category = random.choices(
        ["Normal", "Suspicious", "Attack"],
        weights=[70, 20, 10]
    )[0]

    if category == "Normal":

        login_hour = random.randint(8, 18)
        trusted_device = 1
        country = "India"
        ip_reputation = round(random.uniform(0.80, 1.00), 2)
        vpn_detected = 0
        failed_login_attempts = random.randint(0, 1)
        access_frequency = random.randint(1, 5)
        refresh_frequency = random.randint(0, 2)
        file_sensitivity = random.choice(["Low", "Medium"])

    elif category == "Suspicious":

        login_hour = random.choice(
            list(range(0, 6)) + list(range(20, 24))
        )
        trusted_device = random.choice([0, 1])
        country = random.choice(["USA", "Germany", "India"])
        ip_reputation = round(random.uniform(0.40, 0.79), 2)
        vpn_detected = random.choice([0, 1])
        failed_login_attempts = random.randint(2, 5)
        access_frequency = random.randint(5, 10)
        refresh_frequency = random.randint(2, 6)
        file_sensitivity = random.choice(["Medium", "High"])

    else:

        login_hour = random.randint(1, 4)
        trusted_device = 0
        country = random.choice(["Unknown", "Russia", "China"])
        ip_reputation = round(random.uniform(0.00, 0.30), 2)
        vpn_detected = 1
        failed_login_attempts = random.randint(6, 10)
        access_frequency = random.randint(10, 20)
        refresh_frequency = random.randint(6, 10)
        file_sensitivity = "High"

    browser = random.choice(browsers)

    data.append([
        login_hour,
        trusted_device,
        country,
        ip_reputation,
        vpn_detected,
        failed_login_attempts,
        browser,
        access_frequency,
        file_sensitivity,
        refresh_frequency,
        category
    ])

columns = [
    "login_hour",
    "trusted_device",
    "country",
    "ip_reputation",
    "vpn_detected",
    "failed_login_attempts",
    "browser",
    "access_frequency",
    "file_sensitivity",
    "refresh_frequency",
    "label"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv("dataset.csv", index=False)

print("Dataset generated successfully!")
print(df.head())
print(df.shape)
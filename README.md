# Garmin Training Automation 🏃‍♂️📈

This project automates the collection and visualization of running data from Garmin Connect using AWS services. It’s built to support my training for the 42K Palma Marathon (October 2025) — providing weekly insights on key metrics through serverless infrastructure.

---

## 🚀 Features

- 🕒 Weekly Garmin data update via AWS Lambda
- ☁️ Stores structured `.csv` data in Amazon S3
- 📊 Generates progress graphs with `matplotlib`
- 📬 Sends visual summary by email using Amazon SES
- 🔄 Automatically triggered every Monday at 14:00 (Madrid time) using EventBridge

---

## 🛠️ Tech Stack

- Python (`pandas`, `matplotlib`, `boto3`, `garminconnect`)
- AWS Lambda (2 functions)
- Amazon S3
- Amazon SES
- Amazon EventBridge (CRON scheduler)
- IAM (scoped roles)
- Git & GitHub

---

## 📁 Folder Structure
Marathon_Training_With_Garmin/
├── lambda/
│   ├── GarminUpdate/               # Lambda that fetches Garmin data and updates S3
│   │   └── lambda_function.py
│   ├── EmailSender/                # Lambda that plots data and sends email
│   │   └── lambda_function.py
├── data/
│   └── weekly_collected_data.csv   # Sample training data
├── docs/
│   └── progress_graph_example.png  # Screenshot of email graph
├── requirements.txt
├── LICENSE
├── README.md

## 📬 Sample Output

📧 This is the kind of email I receive each Monday:

![Weekly Progress Graph](docs/progress_graph_example.png)

---

## 🎯 Why I Built It

I'm training for the Palma Marathon (Oct 2025) with a goal of finishing under 3:30h.  
This project helps me track progress on:

- VO2 Max
- Pace (min/km)
- Cadence
- Stride Length
- Heart Rate
- BMI

It also serves as a full-stack serverless data project in my portfolio — showcasing cloud automation, clean data pipelines, and real-time feedback delivery.

---

## 📄 License

MIT — see `LICENSE` for details.

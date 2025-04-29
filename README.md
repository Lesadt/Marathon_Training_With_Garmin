# Garmin Training Automation 🏃‍♂️📈

This project automates the collection and visualization of running data from Garmin Connect using AWS. Every week, it fetches new training data, updates a CSV file in S3, generates progress graphs, and emails a visual report automatically.

## 🛠 Tech Stack

- AWS Lambda (x2)
- Amazon S3
- Amazon SES
- Amazon EventBridge
- Python (pandas, matplotlib, boto3)

## 📦 Folder Structure
import os
import boto3
import pandas as pd
import logging
from garminconnect import Garmin
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# === Graph and Email Helper Functions ===

def plot_update(df):
    goals = {'VO2_Max': 60, 'Pace': 5.00, 'BMI': 23.37, 'Cadence': 178, 'Stride': 1.20, 'Heart_Rate': 145.0}
    fig, axs = plt.subplots(6, 1, figsize=(10, 20), sharex=True)

    def annotate_distance(ax, y_values):
        for i in range(len(df)):
            ax.annotate(f"{df['Distance (km)'][i]}km", (df['Date'][i], y_values[i]),
                        textcoords="offset points", xytext=(0, 10), ha='center')

    df["Date"] = pd.to_datetime(df["Date"])  # Ensure correct format
    metrics = [("Cadence (spm)", None), ("Pace (min/km)", None), ("Stride (m)", None),
               ("Heart Rate (bpm)", None), ("VO2 Max", 'green'), ("BMI", 'purple')]
    goals_keys = ["Cadence", "Pace", "Stride", "Heart_Rate", "VO2_Max", "BMI"]

    for i, (metric, color) in enumerate(metrics):
        axs[i].plot(df["Date"], df[metric], marker='o', label=metric, color=color)
        axs[i].axhline(goals[goals_keys[i]], color='r', linestyle='--', label="Goal")
        annotate_distance(axs[i], df[metric])
        axs[i].set_ylabel(metric)
        axs[i].set_title(f"{metric} vs Goal", pad=15)
        axs[i].legend()
        if metric == "Pace (min/km)":
            axs[i].invert_yaxis()

    axs[-1].set_xlabel("Week")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

def send_email_with_graph(image_buf):
    ses = boto3.client('ses', region_name='eu-north-1')  # Change if needed
    sender = os.environ['EMAIL_SENDER']
    recipient = os.environ['EMAIL_RECIPIENT']

    msg = MIMEMultipart()
    msg['Subject'] = "Weekly Garmin Progress Report"
    msg['From'] = sender
    msg['To'] = recipient

    html_body = MIMEText("""
        <html>
            <body>
                <p>Hey! Here's your updated running progress 📈</p>
                <img src="cid:progress_graph">
            </body>
        </html>
    """, 'html')
    msg.attach(html_body)

    img = MIMEImage(image_buf.read(), name="progress.png")
    img.add_header('Content-ID', '<progress_graph>')
    img.add_header('Content-Disposition', 'inline', filename="progress.png")
    msg.attach(img)

    response = ses.send_raw_email(Source=sender, Destinations=[recipient],
                                  RawMessage={'Data': msg.as_string()})
    return response

# === MAIN Lambda Function ===

def lambda_handler(event, context):
    try:
        # Login to Garmin
        email = os.environ['GARMIN_EMAIL']
        password = os.environ['GARMIN_PASSWORD']
        client = Garmin(email, password)
        client.login()

        today = datetime.today().strftime("%Y-%m-%d")
        a_week_ago = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

        # Latest activity and body metrics
        activities = client.get_activities(0, 1)
        activity = activities[0]
        date = activity['startTimeLocal'].split(' ')[0]
        distance = round(activity['distance'] / 1000, 2)
        total_time = round(activity['duration'] / 60, 2)
        total_ascent = round(activity['elevationGain'])
        max_altitude = round(activity['maxElevation'], 2)
        weight = client.get_body_composition(a_week_ago, today)['dateWeightList'][0]['weight'] / 1000
        bmi = round(weight / (1.85 ** 2), 2)
        vo2_max = 51.0  # TODO: Replace with real VO2 Max when available
        pace = round(total_time / distance, 2)
        cadence = round(activity['averageRunningCadenceInStepsPerMinute'], 2)
        stride = round(activity['avgStrideLength'] / 100, 2)
        heart_rate = activity['averageHR']

        new_activity = (date, distance, total_time, total_ascent, max_altitude,
                        weight, bmi, vo2_max, pace, cadence, stride, heart_rate)

        # Read & update CSV in S3
        s3 = boto3.client('s3')
        bucket = 'my-garmin-data-csv'
        key = 'weekly_collected_data.csv'

        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(response['Body'])
        except s3.exceptions.NoSuchKey:
            df = pd.DataFrame(columns=["Date", "Distance (km)", "Total Time (min)", "Total Ascent (m)",
                                       "Max Altitude (m)", "Weight (kg)", "BMI", "VO2 Max", "Pace (min/km)",
                                       "Cadence (spm)", "Stride (m)", "Heart Rate (bpm)"])

        # Add row only if not already logged
        if df.empty or df['Date'].iloc[-1] != date:
            df.loc[len(df)] = new_activity
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())

        # Generate graph + send email
        image_buf = plot_update(df)
        send_email_with_graph(image_buf)

        return {'statusCode': 200, 'body': f'Data updated & emailed for {date}'}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {'statusCode': 500, 'body': str(e)}
import os
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

def lambda_handler(event, context):
    try:
        # Load updated Garmin data
        df = load_csv_from_s3()
        image_buf = plot_update(df)
        send_email_with_graph(image_buf)
        return {'statusCode': 200, 'body': 'Weekly progress email sent!'}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {'statusCode': 500, 'body': str(e)}

def load_csv_from_s3():
    s3 = boto3.client('s3')
    bucket = 'my-garmin-data-csv'
    key = 'weekly_collected_data.csv'
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj['Body'])
    df["Date"] = pd.to_datetime(df["Date"])
    return df

def plot_update(df):
    goals = {'VO2_Max': 60, 'Pace': 5.00, 'BMI': 23.37, 'Cadence': 178, 'Stride': 1.20, 'Heart_Rate': 145.0}
    fig, axs = plt.subplots(6, 1, figsize=(10, 20), sharex=True)

    def annotate_distance(ax, y_values):
        for i in range(len(df)):
            ax.annotate(f"{df['Distance (km)'][i]}km", (df['Date'][i], y_values[i]),
                        textcoords="offset points", xytext=(0, 10), ha='center')

    metrics = [
        ("Cadence (spm)", "Cadence", None),
        ("Pace (min/km)", "Pace", None),
        ("Stride (m)", "Stride", None),
        ("Heart Rate (bpm)", "Heart_Rate", None),
        ("VO2 Max", "VO2_Max", 'green'),
        ("BMI", "BMI", 'purple'),
    ]

    for i, (label, key, color) in enumerate(metrics):
        axs[i].plot(df["Date"], df[label], marker='o', label=label, color=color)
        axs[i].axhline(goals[key], color='r', linestyle='--', label="Goal")
        annotate_distance(axs[i], df[label])
        axs[i].set_ylabel(label)
        axs[i].set_title(f"{label} vs Goal", pad=15)
        axs[i].legend()
        if label == "Pace (min/km)":
            axs[i].invert_yaxis()

    axs[-1].set_xlabel("Week")
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

def send_email_with_graph(image_buf):
    ses = boto3.client('ses', region_name='eu-north-1')  # Your region
    sender = os.environ['EMAIL_SENDER']
    recipient = os.environ['EMAIL_RECIPIENT']

    msg = MIMEMultipart()
    msg['Subject'] = "Weekly Garmin Progress Report"
    msg['From'] = sender
    msg['To'] = recipient

    # Email HTML body
    html = """
        <html>
            <body>
                <h2>Your Weekly Garmin Progress 📈</h2>
                <p>See how you're progressing toward your goals!</p>
                <img src="cid:progress_graph" alt="Progress Graph" />
            </body>
        </html>
    """
    msg.attach(MIMEText(html, 'html'))

    # Attach image as inline content
    img = MIMEImage(image_buf.read(), name="progress.png")
    img.add_header('Content-ID', '<progress_graph>')
    img.add_header('Content-Disposition', 'inline', filename="progress.png")
    msg.attach(img)

    # Send email
    ses.send_raw_email(
        Source=sender,
        Destinations=[recipient],
        RawMessage={'Data': msg.as_string()}
    )


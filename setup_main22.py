import datetime
import base64
import os
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.events'
]

def get_google_services():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds), build('gmail', 'v1', credentials=creds)

def inject_baseline_calendar(calendar_service, start_date, end_date):
    print("📅 מזריק חלונות בסיס קבועים לטווח החדש (30/06-03/07)...")
    current_date = start_date
    while current_date <= end_date:
        slots = [
            {"summary": "פתיחת יום 🌅", "sh": 8, "sm": 0, "eh": 8, "em": 30, "color": "2"},       # ירוק Sage
            {"summary": "ארוחת צהריים 🍱", "sh": 12, "sm": 0, "eh": 13, "em": 0, "color": "5"},     # צהוב Banana
            {"summary": "סוף יום ומעבר על מטלות 🧘‍♂️", "sh": 17, "sm": 0, "eh": 18, "em": 0, "color": "4"} # שחור Graphite
        ]
        for slot in slots:
            start_dt = datetime.datetime.combine(current_date, datetime.time(slot["sh"], slot["sm"], 0)).isoformat()
            end_dt = datetime.datetime.combine(current_date, datetime.time(slot["eh"], slot["em"], 0)).isoformat()
            event = {
                'summary': slot['summary'],
                'start': {'dateTime': start_dt, 'timeZone': 'Asia/Jerusalem'},
                'end': {'dateTime': end_dt, 'timeZone': 'Asia/Jerusalem'},
                'colorId': slot['color']
            }
            calendar_service.events().insert(calendarId='primary', body=event).execute()
        current_date += datetime.timedelta(days=1)
    print("✅ חלונות בסיס קבועים עודכנו בהצלחה.")

def send_trigger_email(gmail_service, subject, body_text):
    my_email = "saharmoshe5293@gmail.com"
    message = MIMEText(body_text, 'plain', 'utf-8')
    message['to'] = my_email
    message['from'] = my_email
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    gmail_service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f"📧 נשלח מייל טריגר: {subject}")

if __name__ == '__main__':
    calendar_service, gmail_service = get_google_services()
    start_date = datetime.date(2026, 6, 30)
    end_date = datetime.date(2026, 7, 3)
    
    inject_baseline_calendar(calendar_service, start_date, end_date)
    
    print("\n📩 שולח 6 מיילים עם דרישות שונות לתיבה שלך...")
    triggers = [
        {"sub": "בקשת פגישה: פרויקט ניהול", "body": "היי סהר, פגישה מורכבת לעבור על המאמר האקדמי ב-30/06. דורש ריכוז גבוה."},
        {"sub": "בקשת פגישה: עדכון קצר", "body": "שלום, פגישה קלילה של 20 דקות לעדכן לגבי הרכב ב-01/07 באחה\"צ."},
        {"sub": "דחוף: פגישה בצהריים", "body": "חייב לפגוש אותך דחוף ב-02/07 בדיוק ב-12:00 בצהריים על פרויקט הרכב!"},
        {"sub": "ביטול פגישה: פרויקט ניהול", "body": "היי סהר, תבטל את הפגישה על הפרויקט שקבענו."},
        {"sub": "בקשת פגישה: שיחת צוות", "body": "אהלן, בוא נארגן שיחת סיעור מוחות של כל הצוות ב-03/07 בשעה 11:00."},
        {"sub": "עדכון לו\"ז: הזזת ארוחת צהריים", "body": "סהר, בבקשה תזיז את חלון ארוחת הצהריים ב-30.6 משעה 12:00 לשעה 13:00."}
    ]
    for t in triggers:
        send_trigger_email(gmail_service, t["sub"], t["body"])
    print("\n🏁 שלב ההכנה הסתיים בהצלחה!")
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
    print("📅 שלב א': מזריק חלונות בסיס קבועים ליומן...")
    current_date = start_date
    while current_date <= end_date:
        slots = [
            {"summary": "פתיחת יום 🌅", "start": 8, "end": 8.5, "color": "2"},    # ירוק Sage
            {"summary": "ארוחת צהריים 🥗", "start": 12, "end": 13, "color": "5"},  # צהוב Banana
            {"summary": "סוף יום ומעבר על מטלות 🧘‍♂️", "start": 17, "end": 18, "color": "4"} # שחור/אפור כהה
        ]
        
        for slot in slots:
            sh_h, sh_m = int(slot["start"]), int((slot["start"] % 1) * 60)
            eh_h, eh_m = int(slot["end"]), int((slot["end"] % 1) * 60)
            
            start_dt = datetime.datetime.combine(current_date, datetime.time(sh_h, sh_m, 0)).isoformat()
            end_dt = datetime.datetime.combine(current_date, datetime.time(eh_h, eh_m, 0)).isoformat()
            
            event = {
                'summary': slot['summary'],
                'start': {'dateTime': start_dt, 'timeZone': 'Asia/Jerusalem'},
                'end': {'dateTime': end_dt, 'timeZone': 'Asia/Jerusalem'},
                'colorId': slot['color']
            }
            calendar_service.events().insert(calendarId='primary', body=event).execute()
        print(f"  ✅ נקבעו חלונות קבועים עבור {current_date.strftime('%d/%m')}")
        current_date += datetime.timedelta(days=1)

def send_trigger_email(gmail_service, subject, body_text):
    my_email = "saharmoshe5293@gmail.com"
    message = MIMEText(body_text, 'plain', 'utf-8')
    message['to'] = my_email
    message['from'] = my_email
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    # שליחה עצמית יוצרת מייל שלא נקרא בתיבה
    gmail_service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f"📧 נשלח מייל טריגר: {subject}")

def setup_all_demo_triggers():
    calendar_service, gmail_service = get_google_services()
    
    start_date = datetime.date(2026, 6, 30)
    end_date = datetime.date(2026, 7, 3)
    
    # 1. הקמת הלו"ז ביומן
    inject_baseline_calendar(calendar_service, start_date, end_date)
    
    # 2. שליחת 6 מיילים עם דרישות שונות (טריגרים ל-main18)
    print("\n📩 שלב ב': שולח 6 מיילי טריגר מורכבים לתיבה...")
    
    triggers = [
        {
            "sub": "בקשת פגישה: פרויקט ניהול",
            "body": "היי סהר, צריך לקבוע פגישה מורכבת לעבור על המאמר האקדמי ב-30/06. דורש ריכוז גבוה."
        },
        {
            "sub": "בקשת פגישה: עדכון קצר",
            "body": "שלום, פגישה קלילה של 20 דקות לעדכן לגבי הרכב החדש בתאריך 01/07 באחה\"צ."
        },
        {
            "sub": "דחוף: פגישה בצהריים",
            "body": "סהר זה דחוף ביותר! פיצוץ בפרויקט, חייב לפגוש אותך ב-02/07 בדיוק ב-12:00 בצהריים!"
        },
        {
            "sub": "ביטול פגישה: פרויקט ניהול",
            "body": "היי סהר, תבטל את הפגישה על הפרויקט שקבענו, התפנה לי הזמן."
        },
        {
            "sub": "בקשת פגישה: שיחת צוות",
            "body": "אהלן, בוא נארגן שיחת סיעור מוחות של כל הצוות ב-03/07 בשעה 11:00."
        },
        {
            "sub": "עדכון לו\"ז: הזזת ארוחת צהריים",
            "body": "סהר, בבקשה תזיז את חלון ארוחת הצהריים שלי ב-30.6 משעה 12:00 לשעה 13:00."
        }
    ]
    
    for t in triggers:
        send_trigger_email(gmail_service, t["sub"], t["body"])
        
    print("\n🏁 התשתית מוכנה! היומן מאוכלס בבלוקים, ו-6 מיילים מחכים בתיבה כ-Unread. עכשיו אפשר להריץ את main18.py!")

if __name__ == '__main__':
    setup_all_demo_triggers()
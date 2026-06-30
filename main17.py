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

def clean_and_reset_calendar(calendar_service, gmail_service):
    emails_to_notify = ["saharmoshe5293@gmail.com", "tonywolf2go@gmail.com"]
    
    # הגדרת הטווח החדש כולל ה-26 לחודש
    start_date = datetime.date(2026, 6, 21)
    end_date = datetime.date(2026, 6, 26)
    
    print(f"🧹 מוחק את כל האירועים ביומן מ-{start_date.strftime('%d/%m')} עד {end_date.strftime('%d/%m')}...")
    time_min = datetime.datetime.combine(start_date, datetime.time(0, 0, 0)).isoformat() + "Z"
    time_max = datetime.datetime.combine(end_date, datetime.time(23, 59, 59)).isoformat() + "Z"
    
    # שליפת כל האירועים הקיימים בטווח
    events_result = calendar_service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy='startTime'
    ).execute()
    existing_events = events_result.get('items', [])
    
    # מחיקת האירועים שנמצאו
    deleted_count = 0
    for event in existing_events:
        event_id = event['id']
        calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
        deleted_count += 1
    print(f"🗑️ נמחקו {deleted_count} אירועים ישנים מהיומן.")

    print("🟢 מזריק את מופעי ארוחת הצהריים החדשים (12:00-13:00)...")
    current_date = start_date
    created_events = []
    
    while current_date <= end_date:
        slot_start = datetime.datetime.combine(current_date, datetime.time(12, 0, 0)).isoformat()
        slot_end = datetime.datetime.combine(current_date, datetime.time(13, 0, 0)).isoformat()
        
        event_body = {
            'summary': 'ארוחת צהריים 🥗',
            'start': {'dateTime': slot_start, 'timeZone': 'Asia/Jerusalem'},
            'end': {'dateTime': slot_end, 'timeZone': 'Asia/Jerusalem'},
            'colorId': '2'  # צבע ירוק (Sage)
        }
        
        calendar_service.events().insert(calendarId='primary', body=event_body).execute()
        created_events.append(current_date.strftime('%d/%m/%Y'))
        print(f"✅ נוצר מופע ארוחת צהריים עבור {current_date.strftime('%d/%m')}")
        
        current_date += datetime.timedelta(days=1)
        
    # שליחת המייל החגיגי והמעוצב
    send_fancy_update_email(gmail_service, emails_to_notify, start_date, end_date, deleted_count)

def send_fancy_update_email(service, recipients, start, end, deleted_count):
    subject = "🚀 עדכון סוכן AI: יומן מנוקה ולו''ז חדש עודכן! ✨"
    
    body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; background-color: #f4f7f6; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-top: 8px solid #2ecc71;">
            
            <div style="text-align: center; margin-bottom: 25px;">
                <span style="font-size: 50px;">👋✨</span>
                <h2 style="color: #27ae60; margin-top: 10px;">היי סהר וטוני!</h2>
                <p style="font-size: 16px; color: #7f8c8d;">הסוכן החכם שלכם השלים אופטימיזציה מלאה ללו"ז!</p>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            
            <div style="background-color: #f9f9f9; border-right: 4px solid #e74c3c; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                <p style="margin: 0; font-size: 15px;">🧹 <b>ניקוי יומן גורף:</b> כל {deleted_count} המופעים שהיו קיימים בין התאריכים <b>{start.strftime('%d/%m')} ל-{end.strftime('%d/%m')}</b> נמחקו בהצלחה כדי להתחיל דף חלק לחלוטין!</p>
            </div>
            
            <h3 style="color: #2c3e50; font-size: 18px; margin-top: 25px;">🥗 מה הוכנס ללו"ז החדש שלכם?</h3>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background-color: #fdfefe; border: 1px solid #eab308; border-radius: 6px;">
                <tr style="background-color: #2ecc71; color: white; text-align: center;">
                    <th style="padding: 12px; font-size: 15px;">📅 טווח תאריכים</th>
                    <th style="padding: 12px; font-size: 15px;">⏰ שעות קבועות</th>
                    <th style="padding: 12px; font-size: 15px;">🎨 סטטוס ויזואלי</th>
                </tr>
                <tr style="text-align: center; background-color: #f9fdfa;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">{start.strftime('%d/%m')} - {end.strftime('%d/%m')}/2026</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #27ae60;">12:00 - 13:00</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">🟢 ירוק מרגיע (Sage)</td>
                </tr>
            </table>
            
            <div style="margin-top: 25px; padding: 15px; background-color: #ebf5fb; border-radius: 6px; text-align: center;">
                <p style="margin: 0; color: #2980b9; font-size: 15px;">🍽️ <b>חלון ארוחת הצהריים שלכם נעול ומאובטח כעת מפני התנגשויות!</b></p>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
            
            <p style="font-size: 12px; color: #95a5a6; text-align: center; margin: 0;">
                הופק ועודכן אוטומטית על ידי מערכת הניהול הניהולית של סוכן ה-AI שלכם 🦾🤖
            </p>
        </div>
    </body>
    </html>
    """
    
    to_header = ", ".join(recipients)
    message = MIMEText(body, 'html', 'utf-8')
    message['to'] = to_header
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"📧 המייל החגיגי נשלח בהצלחה לכל הנמענים!")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")

if __name__ == '__main__':
    print("🚀 מאתחל חיבורים לגוגל עבור קובץ main17.py...")
    calendar_service, gmail_service = get_google_services()
    print("⚡ מתחיל תהליך איפוס והזרקת לו''ז חדש...")
    clean_and_reset_calendar(calendar_service, gmail_service)
    print("🏁 הפעולה הסתיימה בהצלחה מרובה!")
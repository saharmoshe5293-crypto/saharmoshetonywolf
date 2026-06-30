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
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.events'
]

def get_google_services():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                if os.path.exists('token.json'):
                    os.remove('token.json')
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds), build('gmail', 'v1', credentials=creds)

def send_fancy_response(gmail_service, to_email, subject, title, html_content, border_color="#3498db"):
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right; background-color: #f4f7f6; padding: 15px;">
        <div style="max-width: 550px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-top: 6px solid {border_color};">
            <h3 style="color: #2c3e50;">{title}</h3>
            {html_content}
            <br>
            <p style="font-size: 11px; color: #7f8c8d; border-top: 1px solid #eee; padding-top: 10px;">הופק אוטומטית על ידי סוכן ה-AI של סהר וטוני 🦾🤖</p>
        </div>
    </body>
    </html>
    """
    message = MIMEText(body, 'html', 'utf-8')
    message['to'] = to_email
    message['subject'] = f"🤖 מענה אוטומטי: {subject}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    gmail_service.users().messages().send(userId='me', body={'raw': raw}).execute()

def clean_and_inject_baseline(calendar_service):
    # 🧼 1. מחיקה מוחלטת של טווח הניסוי הישן (21-26/06)
    print("🧹 מנקה אירועים ישנים מטווח הניסויים הקודם (21-26/06)...")
    t1_min = "2026-06-21T00:00:00Z"
    t1_max = "2026-06-26T23:59:59Z"
    res1 = calendar_service.events().list(calendarId='primary', timeMin=t1_min, timeMax=t1_max, singleEvents=True).execute()
    for e in res1.get('items', []):
        calendar_service.events().delete(calendarId='primary', eventId=e['id']).execute()
        
    # 🧼 2. ניקוי מקדים של הטווח החדש (30/06-03/07) למניעת כפילויות
    print("🧹 מנקה אירועים קיימים בטווח החדש (30/06-03/07) כדי לבנות בסיס נקי...")
    t2_min = "2026-06-30T00:00:00Z"
    t2_max = "2026-07-03T23:59:59Z"
    res2 = calendar_service.events().list(calendarId='primary', timeMin=t2_min, timeMax=t2_max, singleEvents=True).execute()
    for e in res2.get('items', []):
        calendar_service.events().delete(calendarId='primary', eventId=e['id']).execute()

    # 📅 3. הזרקת חלונות הבסיס הקבועים בצבעים המבוקשים לטווח החדש
    print("📅 מזריק חלונות בסיס קבועים (פתיחה, צהריים, סיום) לטווח החדש...")
    start_date = datetime.date(2026, 6, 30)
    end_date = datetime.date(2026, 7, 3)
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
    print("✅ בסיס היומן החדש מוכן ומעוצב!")

def process_smart_agent_emails(calendar_service, gmail_service):
    date_mapping = {
        "30/06": datetime.date(2026, 6, 30),
        "30.6": datetime.date(2026, 6, 30),
        "01/07": datetime.date(2026, 7, 1),
        "02/07": datetime.date(2026, 7, 2),
        "03/07": datetime.date(2026, 7, 3)
    }
    
    print("🔍 סורק את תיבת ה-Gmail ומחפש טריגרים חדשים שלא נקראו...")
    results = gmail_service.users().messages().list(userId='me', maxResults=15, q="is:unread").execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("💡 לא נמצאו מיילים חדשים שלא נקראו בתיבה. ודא שהרצת קודם את setup_demo.py!")
        return

    for msg in messages:
        m_id = msg['id']
        full_msg = gmail_service.users().messages().get(userId='me', id=m_id, format='full').execute()
        headers = full_msg['payload']['headers']
        
        subject, sender = "", ""
        for h in headers:
            if h['name'] == 'Subject': subject = h['value']
            if h['name'] == 'From': sender = h['value']

        # 🎯 מקרה 1: פגישת פרויקט (מאמץ גבוה -> אדום בבוקר ב-30/06)
        if "בקשת פגישה: פרויקט ניהול" in subject:
            print(f"🧠 מזהה משימת פוקוס קשה מ: {sender}")
            t_date = date_mapping["30/06"]
            start = datetime.datetime.combine(t_date, datetime.time(9, 0, 0)).isoformat()
            end = datetime.datetime.combine(t_date, datetime.time(11, 0, 0)).isoformat()
            event = {'summary': '[HIGH] פרויקט ניהול 🧠', 'start': {'dateTime': start, 'timeZone': 'Asia/Jerusalem'}, 'end': {'dateTime': end, 'timeZone': 'Asia/Jerusalem'}, 'colorId': '11'}
            calendar_service.events().insert(calendarId='primary', body=event).execute()
            send_fancy_response(gmail_service, sender, subject, "✅ הפגישה שובצה בהצלחה!", "<p>הסוכן זיהה משימה בעלת מאמץ קוגניטיבי גבוה ושיבץ אותה בבוקר (09:00-11:00) בצבע אדום לפוקוס מקסימלי!</p>", "#e74c3c")

        # 🎯 מקרה 2: עדכון קצר (מאמץ נמוך -> ירוק אחה"צ ב-01/07)
        elif "בקשת פגישה: עדכון קצר" in subject:
            print(f"✉️ מזהה משימה קלה מ: {sender}")
            t_date = date_mapping["01/07"]
            start = datetime.datetime.combine(t_date, datetime.time(14, 0, 0)).isoformat()
            end = datetime.datetime.combine(t_date, datetime.time(15, 0, 0)).isoformat()
            event = {'summary': '[LOW] עדכון קצר ✉️', 'start': {'dateTime': start, 'timeZone': 'Asia/Jerusalem'}, 'end': {'dateTime': end, 'timeZone': 'Asia/Jerusalem'}, 'colorId': '2'}
            calendar_service.events().insert(calendarId='primary', body=event).execute()
            send_fancy_response(gmail_service, sender, subject, "✅ הפגישה הקלה שובצה!", "<p>הסוכן שיבץ את המשימה בחלון אחה''צ (14:00) בצבע ירוק, המיועד למשימות אדמיניסטרטיביות קלות.</p>", "#2ecc71")

        # 🎯 מקרה 3: ניסיון דריסת צהריים ב-02/07 (משא ומתן אוטומטי)
        elif "דחוף: פגישה בצהריים" in subject:
            print(f"🚨 זיהוי ניסיון דריסה של ארוחת צהריים מ: {sender}")
            html_content = """<p style='color: #c0392b; font-weight: bold;'>חלון זמן זה (12:00-13:00) מוגן ונעול לארוחת צהריים ומנוחה.</p>
            <p><b>🤝 הצעת אלטרנטיבה של הסוכן:</b> נשמח להציע לך להיפגש במקום זאת בשעה <b>14:00</b> או <b>15:00</b>. השב למייל זה עם השעה המועדפת!</p>"""
            send_fancy_response(gmail_service, sender, subject, "⚠️ חסימת התנגשות והצעת חלופות", html_content, "#e67e22")

        # 🎯 מקרה 4: ביטול פגישה אוטומטי
        elif "ביטול פגישה: פרויקט ניהול" in subject:
            print(f"🗑️ מזהה בקשת ביטול מ: {sender}")
            events = calendar_service.events().list(calendarId='primary', q='פרויקט ניהול').execute().get('items', [])
            for e in events:
                calendar_service.events().delete(calendarId='primary', eventId=e['id']).execute()
            send_fancy_response(gmail_service, sender, subject, "🗑️ הפגישה בבוטלה והוסרה מהיומן", "<p>לבקשתך, הסוכן איתר את הפגישה ביומן והסיר אותה לחלוטין כדי לפנות לך זמן פנוי.</p>", "#95a5a6")

        # 🎯 מקרה 5: שיחת צוות (מאמץ בינוני -> טורקיז ב-03/07)
        elif "בקשת פגישה: שיחת צוות" in subject:
            print(f"👥 מזהה שיחת צוות מ: {sender}")
            t_date = date_mapping["03/07"]
            start = datetime.datetime.combine(t_date, datetime.time(11, 0, 0)).isoformat()
            end = datetime.datetime.combine(t_date, datetime.time(12, 0, 0)).isoformat()
            event = {'summary': '[MEDIUM] שיחת צוות 👥', 'start': {'dateTime': start, 'timeZone': 'Asia/Jerusalem'}, 'end': {'dateTime': end, 'timeZone': 'Asia/Jerusalem'}, 'colorId': '7'}
            calendar_service.events().insert(calendarId='primary', body=event).execute()
            send_fancy_response(gmail_service, sender, subject, "✅ שיחת הצוות עודכנה", "<p>הסוכן שיבץ שיחת אינטראקציה וצוות בצבע טורקיז בשעה 11:00.</p>", "#1abc9c")

        # 🎯 מקרה 6: הזזת ארוחת צהריים דינמית ב-30/06
        elif 'עדכון לו"ז: הזזת ארוחת צהריים' in subject:
            print(f"🔄 מזהה בקשת עדכון שעה לארוחת צהריים מ: {sender}")
            t_date = date_mapping["30.6"]
            events = calendar_service.events().list(calendarId='primary', timeMin=f"{t_date}T00:00:00Z", timeMax=f"{t_date}T23:59:59Z", q='ארוחת צהריים').execute().get('items', [])
            for e in events:
                calendar_service.events().delete(calendarId='primary', eventId=e['id']).execute()
            start = datetime.datetime.combine(t_date, datetime.time(13, 0, 0)).isoformat()
            end = datetime.datetime.combine(t_date, datetime.time(14, 0, 0)).isoformat()
            event = {'summary': 'ארוחת צהריים (מוזזת) 🥗', 'start': {'dateTime': start, 'timeZone': 'Asia/Jerusalem'}, 'end': {'dateTime': end, 'timeZone': 'Asia/Jerusalem'}, 'colorId': '5'}
            calendar_service.events().insert(calendarId='primary', body=event).execute()
            send_fancy_response(gmail_service, sender, subject, "🔄 ארוחת הצהריים הוזזה בהצלחה!", "<p>הסוכן פינה את החלון המקורי והזיז את ארוחת הצהריים לשעה 13:00 לבקשתך.</p>", "#f1c40f")

        # סימון המייל כנקרא
        gmail_service.users().messages().batchModify(userId='me', body={'ids': [m_id], 'removeLabelIds': ['UNREAD']}).execute()

if __name__ == '__main__':
    print("🚀 מאתחל את סוכן ה-Multi-Trigger העל (main20.py)...")
    calendar_service, gmail_service = get_google_services()
    clean_and_inject_baseline(calendar_service)
    process_smart_agent_emails(calendar_service, gmail_service)
    print("🏁 הסוכן סיים את הפעולה המלאה בהצלחה מרובה!")
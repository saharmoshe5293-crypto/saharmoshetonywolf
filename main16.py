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

def run_advanced_calendar_flow(calendar_service, gmail_service):
    emails_to_notify = ["saharmoshe5293@gmail.com", "tonywolf2go@gmail.com"]
    start_date = datetime.date(2026, 6, 21)
    end_date = datetime.date(2026, 6, 25)
    
    print("🧹 Scanning existing events...")
    time_min = datetime.datetime.combine(start_date, datetime.time(0, 0, 0)).isoformat() + "Z"
    time_max = datetime.datetime.combine(end_date, datetime.time(23, 59, 59)).isoformat() + "Z"
    
    # התיקון כאן: שימוש ב-calendarId במקום calendar_id
    events_result = calendar_service.events().list(
        calendarId='primary', timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy='startTime'
    ).execute()
    existing_events = events_result.get('items', [])
    
    total_hours_busy = 0
    long_events_count = 0
    conflicts_found = []
    daily_load = {str(start_date + datetime.timedelta(days=i)): 0 for i in range((end_date - start_date).days + 1)}
    
    for event in existing_events:
        start_str = event['start'].get('dateTime')
        end_str = event['end'].get('dateTime')
        if start_str and end_str:
            start_dt = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_dt = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            total_hours_busy += duration_hours
            if duration_hours > 4:
                long_events_count += 1
            day_key = str(start_dt.date())
            if day_key in daily_load:
                daily_load[day_key] += duration_hours

    slots_to_create = [
        {"title": "מעבר על היומן ופתיחת יום", "start_h": 8, "end_h": 10, "color": "2"},
        {"title": "ארוחת צהרים - נעול", "start_h": 12, "end_h": 13, "color": "9"},
        {"title": "סוף יום, מעבר ותחקיר יומי", "start_h": 17, "end_h": 18, "color": "5"}
    ]
    
    current_date = start_date
    while current_date <= end_date:
        for slot in slots_to_create:
            slot_start = datetime.datetime.combine(current_date, datetime.time(slot["start_h"], 0, 0)).isoformat()
            slot_end = datetime.datetime.combine(current_date, datetime.time(slot["end_h"], 0, 0)).isoformat()
            
            has_conflict = False
            conflicting_with = ""
            for event in existing_events:
                e_start_str = event['start'].get('dateTime')
                e_end_str = event['end'].get('dateTime')
                if e_start_str and e_end_str:
                    e_start = datetime.datetime.fromisoformat(e_start_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    e_end = datetime.datetime.fromisoformat(e_end_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    s_start_check = datetime.datetime.combine(current_date, datetime.time(slot["start_h"], 0, 0))
                    s_end_check = datetime.datetime.combine(current_date, datetime.time(slot["end_h"], 0, 0))
                    if (s_start_check < e_end) and (s_end_check > e_start):
                        has_conflict = True
                        conflicting_with = event.get('summary', 'מופע ללא שם')
                        break
            
            if has_conflict:
                alert_msg = f"Conflict on {current_date.strftime('%d/%m')} for '{slot['title']}' with '{conflicting_with}'"
                conflicts_found.append(alert_msg)
                print(f"⚠️ {alert_msg}")
                send_conflict_email(gmail_service, emails_to_notify, current_date, slot['title'], conflicting_with)
            else:
                event_body = {
                    'summary': slot['title'],
                    'start': {'dateTime': slot_start, 'timeZone': 'Asia/Jerusalem'},
                    'end': {'dateTime': slot_end, 'timeZone': 'Asia/Jerusalem'},
                    'colorId': slot['color']
                }
                # כאן משתמשים ב-calendarId מיושר רשמית
                calendar_service.events().insert(calendarId='primary', body=event_body).execute()
                print(f"✅ Created event: {slot['title']} for {current_date}")
                daily_load[str(current_date)] += (slot["end_h"] - slot["start_h"])
                total_hours_busy += (slot["end_h"] - slot["start_h"])
        current_date += datetime.timedelta(days=1)
        
    send_summary_report(gmail_service, emails_to_notify, daily_load, total_hours_busy, long_events_count, conflicts_found)

def send_conflict_email(service, recipients, date, new_slot, existing_slot):
    subject = f"🚨 התראה דחופה: התנגשות לו''ז ביומן סהר וטוני ({date.strftime('%d/%m')})"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
        <h2 style="color: #d9534f;">⚠️ נמצאה התנגשות לו"ז חסומה!</h2>
        <p>הסוכן זיהה חפיפה ביומן ולא הזין את המופע:</p>
        <ul>
            <li><b>התאריך:</b> {date.strftime('%d/%m/%Y')}</li>
            <li><b>המופע שבוקש:</b> {new_slot}</li>
            <li><b>האירוע החוסם:</b> <span style="color: red;">{existing_slot}</span></li>
        </ul>
    </body>
    </html>
    """
    send_raw_email(service, recipients, subject, body)

def send_summary_report(service, recipients, daily_load, total_hours, long_events, conflicts):
    subject = "📊 דוח אנליטי ומפת חום: סיכום פעילות סוכן AI"
    heatmap_html = ""
    for date, hours in daily_load.items():
        if hours > 8: color = "#ff4d4d"
        elif hours > 5: color = "#ffa64d"
        else: color = "#99ff99"
        heatmap_html += f"""
        <tr style="background-color: {color}; text-align: center;">
            <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{hours:.1f} שעות</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{"🔥 עמוס" if hours > 8 else "✅ תקין"}</td>
        </tr>
        """
    conflicts_list = "".join([f"<li>❌ {c}</li>" for c in conflicts]) if conflicts else "<li>✅ לא נמצאו התנגשויות!</li>"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right; padding: 20px;">
        <h2>📋 דוח ביצועים אנליטי ומפת חום</h2>
        <h3>🌡️ מפת חום ועומס יומי (21-25/06):</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #34495e; color: white;">
                <th style="padding: 10px;">תאריך</th><th style="padding: 10px;">שעות מנוצלות</th><th style="padding: 10px;">סטטוס</th>
            </tr>
            {heatmap_html}
        </table>
        <h3>🧠 מדדי קיבולת:</h3>
        <ul>
            <li>⏳ <b>סך שעות פנויות משוער:</b> {120 - total_hours:.1f} שעות</li>
            <li>⚠️ <b>פגישות מעל 4 שעות רצופות:</b> {long_events} מופעים</li>
        </ul>
        <h3>🛑 התנגשויות:</h3><ul>{conflicts_list}</ul>
    </body>
    </html>
    """
    send_raw_email(service, recipients, subject, body)

def send_raw_email(service, recipients, subject, html_body):
    to_header = ", ".join(recipients)
    message = MIMEText(html_body, 'html', 'utf-8')
    message['to'] = to_header
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"📧 המייל '{subject}' נשלח בהצלחה!")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")

if __name__ == '__main__':
    print("🚀 מאתחל חיבורים לגוגל...")
    calendar_service, gmail_service = get_google_services()
    print("⚡ מתחיל הרצת לוגיקה מתקדמת...")
    run_advanced_calendar_flow(calendar_service, gmail_service)
    print("🏁 הסוכן סיים את הפעולה בהצלחה!")
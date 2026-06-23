import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
import google_services

def check_conflict_and_create_event(calendar_service, gmail_service):
    # הגדרת זמן הזימון המדויק: 23 ליוני 2026, בין 21:30 ל-22:00 (שעון ישראל GMT+3)
    start_iso = "2026-06-23T21:30:00+03:00"
    end_iso = "2026-06-23T22:00:00+03:00"
    
    print(f"🔍 בודק אם יש אירועים מתנגשים ביומן בין 21:30 ל-22:00...")
    
    # שאילתה לגוגל לבדיקת אירועים קיימים בטווח הזמן הזה
    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin="2026-06-23T18:30:00Z", # המרה ל-UTC (פחות 3 שעות משעון ישראל)
        timeMax="2026-06-23T19:00:00Z",
        singleEvents=True
    ).execute()
    
    existing_events = events_result.get('items', [])
    has_conflict = len(existing_events) > 0
    
    # קביעת שם האירוע לפי קיום התנגשות
    if has_conflict:
        event_title = "שיעור AI - מתנגש עם מופע אחר"
        print("⚠️ נמצאה התנגשות ביומן!")
    else:
        event_title = "שיעור AI - חדש נכנס"
        print("✅ הטווח פנוי! אין התנגשויות.")
        
    # יצירת הזימון ביומן
    event = {
        "summary": event_title,
        "description": "נוצר באופן אוטומטי על ידי סוכן ה-AI של סהר",
        "start": {"dateTime": start_iso, "timeZone": "Asia/Jerusalem"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Jerusalem"},
    }
    
    calendar_service.events().insert(calendarId="primary", body=event).execute()
    print(f"🎉 האירוע '{event_title}' נוצר בהצלחה בלוח השנה!")
    
    # אם יש התנגשות - שולחים מייל אמיתי ומיידי לנמענים
    if has_conflict:
        send_conflict_email(gmail_service)

def send_conflict_email(gmail_service):
    print("📧 מכין ושולח מייל התראה על התנגשות...")
    msg = EmailMessage()
    
    # הגדרת השולח והנמענים
    msg["From"] = "saharmoshe5293@gmail.com"
    msg["To"] = "saharmoshe5293@gmail.com, tonywolf2go@gmail.com"
    msg["Subject"] = "טעות טעות טעות - שגיאה בהכנסת הזימון"
    
    # תוכן המייל המדויק שביקשת
    email_content = "שלום, הבקשה להכנסת מופע חדש ליומן נתקלה בטעות עקב מופע מתנגש, בברכה, סהר"
    msg.set_content(email_content)
    
    # קידוד ושליחה ישירה לתיבת הדואר (הודעה מיידית, לא טיוטה)
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body = {"raw": raw_message}
    
    gmail_service.users().messages().send(userId="me", body=body).execute()
    print("✉️ המייל נשלח בהצלחה ל-saharmoshe5293@gmail.com ו-tonywolf2go@gmail.com!")

def main():
    print("🤖 סוכן ה-AI מתחיל לעבוד על המשימה המבוקשת...")
    gmail_service = google_services.get_gmail_service()
    calendar_service = google_services.get_calendar_service()
    
    check_conflict_and_create_event(calendar_service, gmail_service)
    print("\n✅ הפעולה הושלמה בהצלחה!")

if __name__ == "__main__":
    main()
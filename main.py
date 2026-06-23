import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
import google_services

def create_test_calendar_event(calendar_service):
    now = datetime.utcnow()
    start_time = now + timedelta(hours=4)
    end_time = start_time + timedelta(hours=1)
    
    start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    event = {
        "summary": "AI Agent - Test Meeting",
        "description": "אירוע בדיקה אוטומטי שנוצר על ידי סוכן ה-AI של סהר",
        "start": {"dateTime": start_iso, "timeZone": "UTC"},
        "end": {"dateTime": end_iso, "timeZone": "UTC"},
    }
    calendar_service.events().insert(calendarId="primary", body=event).execute()
    print("🎉 [תוצאה 3] האירוע נוצר בהצלחה בלוח השנה לעוד 4 שעות!")

def create_gmail_draft(gmail_service):
    msg = EmailMessage()
    # כאן עודכן המייל האמיתי שלך כדי למנוע את שגיאת ה-Invalid To header
    msg["To"] = "saharmoshe5293@gmail.com"  
    msg["Subject"] = "סטטוס סוכן AI - בדיקת מערכת"
    msg.set_content("שלום,\n\nהודעה זו נוצרה באופן אוטומטי כטיוטה ב-Gmail.\n\nבברכה,\nהסוכן שלך.")
    
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body = {"message": {"raw": raw_message}}
    gmail_service.users().drafts().create(userId="me", body=body).execute()
    print("✉️ [תוצאה 2] טיוטה חדשה נוצרה בהצלחה ב-Gmail!")

def main():
    print("🤖 סוכן ה-AI מתחיל לעבוד...")
    gmail_service = google_services.get_gmail_service()
    calendar_service = google_services.get_calendar_service()
    
    create_test_calendar_event(calendar_service)
    create_gmail_draft(gmail_service)
    print("\n✅ כל מדדי ההצלחה של ד\"ר סגל הושלמו בהצלחה!")

if __name__ == "__main__":
    main()
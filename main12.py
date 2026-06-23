import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
import google_services

def find_free_slot_and_schedule(calendar_service, gmail_service):
    # רשימת הימים שביקשת (24, 25, 26 ביוני 2026)
    days_to_check = ["2026-06-24", "2026-06-25", "2026-06-26"]
    
    print("🤖 סוכן המצטיינים מתחיל לסרוק את היומן למציאת חלונות פנויים להפסקת אוכל...")

    for day in days_to_check:
        print(f"\n📅 בודק את יום {day}...")
        
        # הגדרת טווח יום העבודה באותו יום בשעון מקומי לצורך הלולאה
        work_start = datetime.fromisoformat(f"{day}T08:00:00")
        work_end = datetime.fromisoformat(f"{day}T18:00:00")
        
        # המרה לפורמט שגוגל דורש בשאילתה (כולל ה-Offset של שעון ישראל +03:00)
        time_min_str = f"{day}T08:00:00+03:00"
        time_max_str = f"{day}T18:00:00+03:00"
        
        # שליפת כל האירועים הקיימים בטווח יום העבודה מגוגל
        events_result = calendar_service.events().list(
            calendarId='primary',
            timeMin=time_min_str,
            timeMax=time_max_str,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # מציאת חלון פנוי של שעה אחת
        slot_found = None
        current_time = work_start
        
        while current_time + timedelta(hours=1) <= work_end:
            potential_end = current_time + timedelta(hours=1)
            has_conflict = False
            
            # בדיקה האם החלון הנוכחי מתנגש עם אירוע קיים כלשהו
            for event in events:
                event_start_str = event['start'].get('dateTime') or event['start'].get('date')
                event_end_str = event['end'].get('dateTime') or event['end'].get('date')
                
                # ניקוי פורמט הזמן של גוגל לצורך השוואה פשוטה ויציבה
                ev_start = datetime.fromisoformat(event_start_str.split('+')[0].split('Z')[0])
                ev_end = datetime.fromisoformat(event_end_str.split('+')[0].split('Z')[0])
                
                # בדיקת חפיפה בזמנים
                if not (potential_end <= ev_start or current_time >= ev_end):
                    has_conflict = True
                    break
            
            if not has_conflict:
                slot_found = (current_time, potential_end)
                break
            
            # התקדמות של 30 דקות קדימה כדי לבדוק את החלון הבא
            current_time += timedelta(minutes=30)
            
        # אם מצאנו חלון פנוי - משבצים ביומן ושולחים מייל
        if slot_found:
            start_slot, end_slot = slot_found
            start_iso = f"{day}T{start_slot.strftime('%H:%M:%S')}+03:00"
            end_iso = f"{day}T{end_slot.strftime('%H:%M:%S')}+03:00"
            
            event_title = "הפסקה :) נא לאכול !"
            
            event = {
                "summary": event_title,
                "description": "הפסקת אוכל יומית ששובצה אוטומטית על ידי סוכן המצטיינים של סהר",
                "start": {"dateTime": start_iso, "timeZone": "Asia/Jerusalem"},
                "end": {"dateTime": end_iso, "timeZone": "Asia/Jerusalem"},
            }
            
            calendar_service.events().insert(calendarId="primary", body=event).execute()
            print(f"🎉 הצלחה! שובצה הפסקה ביום {day} בין השעות {start_slot.strftime('%H:%M')} ל-{end_slot.strftime('%H:%M')}")
            
            # שליחת המייל לנמענים שביקשת
            send_success_email(gmail_service, day, start_slot.strftime('%H:%M'), end_slot.strftime('%H:%M'))
        else:
            print(f"❌ לא נמצא חלון פנוי של שעה שלמה ביום העבודה של {day}.")

def send_success_email(gmail_service, day, start_time, end_time):
    msg = EmailMessage()
    msg["From"] = "saharmoshe5293@gmail.com"
    msg["To"] = "saharmoshe5293@gmail.com, tonywolf2go@gmail.com"
    msg["Subject"] = f"🍱 עדכון סוכן: שובצה הפסקת אוכל ליום {day}!"
    
    content = f"""שלום סהר וטוני,

סוכן ה-AI סרק את היומן ומצא חלון פנוי להפסקת אוכל!

📋 פרטי המופע שנכנס:
📅 יום: {day}
⏰ שעה: {start_time} - {end_time}
✨ כותרת המופע: הפסקה :) נא לאכול !

בתיאבון,
הסוכן החכם של סהר 🤖"""
    
    msg.set_content(content)
    
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body = {"raw": raw_message}
    
    gmail_service.users().messages().send(userId="me", body=body).execute()
    print(f"📧 מייל עדכון נשלח בהצלחה לסהר וטוני!")

def main():
    gmail_service = google_services.get_gmail_service()
    calendar_service = google_services.get_calendar_service()
    find_free_slot_and_schedule(calendar_service, gmail_service)
    print("\n✅ סוכן המצטיינים סיים את פעולתו בהצלחה!")

if __name__ == "__main__":
    main()
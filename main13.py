import base64
import os
from datetime import datetime, timedelta
from email.message import EmailMessage
import google_services

# ספרייה לייצור גרפים
import matplotlib.pyplot as plt

def analyze_burnout_and_report(calendar_service, gmail_service):
    start_date_str = "2026-06-28"
    end_date_str = "2026-07-11"
    
    print(f"🕵️‍♂️ סוכן ה-AI מתחיל בניתוח עומסים מורכב לשעות העבודה (08:00-18:00) בין התאריכים {start_date_str} ל-{end_date_str}...")
    
    # המרה לטווח זמנים שגוגל מבין (UTC)
    time_min = f"{start_date_str}T00:00:00Z"
    time_max = f"{end_date_str}T23:59:59Z"
    
    events_result = calendar_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    # יצירת מילון של כל הימים בטווח ואיפוס שעות הפגישות
    start_date = datetime.date(datetime.fromisoformat(start_date_str))
    end_date = datetime.date(datetime.fromisoformat(end_date_str))
    
    daily_hours = {}
    current_day = start_date
    while current_day <= end_date:
        # בודק רק ימי חול (ללא סופי שבוע שבת ראשון - אופציונלי, כרגע כולל הכל)
        daily_hours[current_day.strftime("%m-%d")] = 0.0
        current_day += timedelta(days=1)
        
    # חישוב שעות הפגישות לכל יום - אך ורק בתוך שעות העבודה (08:00-18:00)
    for event in events:
        start_str = event['start'].get('dateTime') or event['start'].get('date')
        end_str = event['end'].get('dateTime') or event['end'].get('date')
        
        if 'T' in start_str:
            ev_start = datetime.fromisoformat(start_str.split('+')[0].split('Z')[0])
            ev_end = datetime.fromisoformat(end_str.split('+')[0].split('Z')[0])
            
            # הגדרת גבולות יום העבודה באותו היום
            day_str = ev_start.strftime("%Y-%m-%d")
            work_start = datetime.fromisoformat(f"{day_str}T08:00:00")
            work_end = datetime.fromisoformat(f"{day_str}T18:00:00")
            
            # חיתוך הפגישה כך שתיספר רק אם היא בתוך שעות העבודה
            actual_start = max(ev_start, work_start)
            actual_end = min(ev_end, work_end)
            
            if actual_start < actual_end:
                duration = (actual_end - actual_start).total_seconds() / 3600.0
                day_key = ev_start.strftime("%m-%d")
                if day_key in daily_hours:
                    daily_hours[day_key] += duration

    # ניתוח נתונים ומדדים (KPIs) מתוך יום עבודה של 10 שעות
    total_days = len(daily_hours)
    busy_days_count = sum(1 for h in daily_hours.values() if h >= 5.0) # 5 שעות ומעלה זה חצי מיום העבודה
    burnout_percentage = (busy_days_count / total_days) * 100
    
    max_day_key = max(daily_hours, key=daily_hours.get)
    max_hours = daily_hours[max_day_key]
    
    # חישוב ממוצע ניצול הלו"ז בשעות העבודה
    avg_hours = sum(daily_hours.values()) / total_days
    avg_utilization = (avg_hours / 10.0) * 100 # 10 שעות עבודה ביום

    print(f"📊 סיכום ניתוח: אחוז ימי שחיקה: {burnout_percentage:.1f}%. ניצול ממוצע: {avg_utilization:.1f}%")

    # חסימת זמן שקט בימי עומס קריטיים (מעל 5 שעות פגישות)
    for day_key, hours in daily_hours.items():
        if hours >= 5.0:
            full_date_str = f"2026-{day_key}"
            block_start = f"{full_date_str}T17:00:00+03:00"
            block_end = f"{full_date_str}T18:00:00+03:00"
            
            protection_event = {
                "summary": "זמן שקט לחשוב 🧘‍♂️ (סוכן AI)",
                "description": "ננעל אוטומטית עקב עומס פגישות של מעל 50% מיום העבודה למניעת שחיקה.",
                "start": {"dateTime": block_start, "timeZone": "Asia/Jerusalem"},
                "end": {"dateTime": block_end, "timeZone": "Asia/Jerusalem"},
            }
            try:
                calendar_service.events().insert(calendarId="primary", body=protection_event).execute()
                print(f"🧘‍♂️ הגנת שחיקה הופעלה! נחסמה שעה ביומן בתאריך {full_date_str}")
            except Exception as e:
                print(f"הערה: חסימת הזמן בתאריך {full_date_str} כבר קיימת או נכשלה.")

    # ייצור גרף עמודות ושמירתו כתמונה
    plt.figure(figsize=(11, 5))
    plt.bar(daily_hours.keys(), daily_hours.values(), color='#34A853', edgecolor='#137333') # צבע ירוק ניהולי
    plt.axhline(y=5.0, color='red', linestyle='--', label='רף שחיקה (5 שעות - 50% מיום העבודה)')
    plt.title('ניתוח עומס פגישות בשעות העבודה (08:00-18:00) - סוכן ה-AI', fontsize=13, fontweight='bold')
    plt.xlabel('תאריך (חודש-יום)', fontsize=11)
    plt.ylabel('שעות פגישות בפועל', fontsize=11)
    plt.ylim(0, 10) # מקסימום 10 שעות עבודה ביום
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    
    graph_filename = "burnout_analysis.png"
    plt.savefig(graph_filename)
    plt.close()
    print(f"📉 הגרף הוויזואלי נוצר ונשמר בהצלחה בשם {graph_filename}!")

    # בניית מייל מורכב ושליחתו
    send_report_email(gmail_service, burnout_percentage, max_day_key, max_hours, avg_utilization, graph_filename)

def send_report_email(gmail_service, burnout_pct, max_day, max_hours, avg_util, attachment_path):
    print("📧 מנסח ושולח את דו''ח המנכ''לים המורכב לסהר וטוני...")
    msg = EmailMessage()
    msg["From"] = "saharmoshe5293@gmail.com"
    msg["To"] = "saharmoshe5293@gmail.com, tonywolf2go@gmail.com"
    msg["Subject"] = "📊 דו''ח ניתוח עומסי עבודה ומדדי שחיקה (שעות 08:00-18:00)"
    
    email_content = f"""שלום סהר וטוני,

להלן דו''ח אנליטיקה מתקדמת המבוסס על שעות העבודה המוגדרות (08:00 - 18:00) לשבועיים הקרובים (28/06 - 11/07):

📈 מדדי ביצוע מרכזיים וניצול לו''ז (KPIs):
--------------------------------------------------
⏱️ שעות עבודה פוטנציאליות ביום: 10 שעות
📊 מדד ניצול הלו''ז הממוצע: {avg_util:.1f}% מיום העבודה מנוצל לפגישות.
🔥 אחוז ימי השחיקה (מעל 5 שעות פגישות): {burnout_pct:.1f}% מהימים.
📅 היום העמוס ביותר שנמצא: {max_day}
⏳ שיא שעות פגישות ביום העמוס: {max_hours:.1f} שעות.

🛡️ פעולות מנע אוטומטיות:
בימים שבהם זוהה עומס קריטי החוצה את רף ה-5 שעות (50% מיום העבודה), הסוכן נעל אוטומטית את השעה האחרונה של יום העבודה (17:00-18:00) תחת הכותרת "זמן שקט לחשוב 🧘‍♂️" למניעת עומס יתר.

📊 קובץ הגרף האנליטי מצורף להודעה זו.

בברכה,
סוכן ה-AI הניהולי שלך 🤖"""
    
    msg.set_content(email_content)
    
    # הצמדת קובץ הגרף
    with open(attachment_path, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='image', subtype='png', filename=attachment_path)

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    body = {"raw": raw_message}
    
    gmail_service.users().messages().send(userId="me", body=body).execute()
    print("✉️ הדו''ח והגרף המעודכנים נשלחו בהצלחה במייל!")
    
    if os.path.exists(attachment_path):
        os.remove(attachment_path)

def main():
    gmail_service = google_services.get_gmail_service()
    calendar_service = google_services.get_calendar_service()
    analyze_burnout_and_report(calendar_service, gmail_service)
    print("\n✅ פרויקט המצטיינים המשודרג הושלם בהצלחה מרובה!")

if __name__ == "__main__":
    main()
import datetime
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build

def run_advanced_calendar_flow(calendar_service, gmail_service):
    # הגדרת המיילים להפצה - סהר וטוני
    emails_to_notify = ["saharmoshe5293@gmail.com", "tony.wolf.biu@gmail.com"]
    
    start_date = datetime.date(2026, 6, 21)
    end_date = datetime.date(2026, 6, 25)
    
    print("🧹 סורק אירועים קיימים ביומן לטובת מפת חום ובדיקת התנגשויות...")
    time_min = datetime.datetime.combine(start_date, datetime.time(0, 0, 0)).isoformat() + "Z"
    time_max = datetime.datetime.combine(end_date, datetime.time(23, 59, 59)).isoformat() + "Z"
    
    events_result = calendar_service.events().list(
        calendar_id='primary', timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy='startTime'
    ).execute()
    existing_events = events_result.get('items', [])
    
    # משתנים לאנליטיקה
    total_hours_busy = 0
    long_events_count = 0  # מעל 4 שעות
    conflicts_found = []
    daily_load = {str(start_date + datetime.timedelta(days=i)): 0 for i in range((end_date - start_date).days + 1)}
    
    # ניתוח לו"ז קיים למפת החום
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

    # הגדרת 3 המופעים היומיים המבוקשים והצבעים שלהם (ירוק, כחול, שחור)
    slots_to_create = [
        {"title": "מעבר על היומן ופתיחת יום", "start_h": 8, "end_h": 10, "color": "2"},  # ירוק Sage
        {"title": "ארוחת צהרים - נעול", "start_h": 12, "end_h": 13, "color": "9"},       # כחול Blueberry
        {"title": "סוף יום, מעבר ותחקיר יומי", "start_h": 17, "end_h": 18, "color": "5"} # שחור Graphite
    ]
    
    current_date = start_date
    while current_date <= end_date:
        for slot in slots_to_create:
            slot_start = datetime.datetime.combine(current_date, datetime.time(slot["start_h"], 0, 0))
            slot_end = datetime.datetime.combine(current_date, datetime.time(slot["end_h"], 0, 0))
            
            # בדיקת התנגשויות בזמן אמת
            has_conflict = False
            conflicting_with = ""
            for event in existing_events:
                e_start_str = event['start'].get('dateTime')
                e_end_str = event['end'].get('dateTime')
                if e_start_str and e_end_str:
                    e_start = datetime.datetime.fromisoformat(e_start_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    e_end = datetime.datetime.fromisoformat(e_end_str.replace('Z', '+00:00')).replace(tzinfo=None)
                    
                    if (slot_start < e_end) and (slot_end > e_start):
                        has_conflict = True
                        conflicting_with = event.get('summary', 'מופע ללא שם')
                        break
            
            if has_conflict:
                alert_msg = f"התנגשות ביום {current_date.strftime('%d/%m')} בין '{slot['title']}' לבין האירוע הקיים '{conflicting_with}'"
                conflicts_found.append(alert_msg)
                print(f"⚠️ {alert_msg}")
                # שליחת מייל התראה מיידי עם אייקונים
                send_conflict_email(gmail_service, emails_to_notify, current_date, slot['title'], conflicting_with)
            else:
                # יצירת המופע במידה ואין התנגשות
                event_body = {
                    'summary': slot['title'],
                    'start': {'dateTime': slot_start.isoformat() + 'Z', 'timeZone': 'UTC'},
                    'end': {'dateTime': slot_end.isoformat() + 'Z', 'timeZone': 'UTC'},
                    'colorId': slot['color']
                }
                calendar_service.events().insert(calendar_id='primary', body=event_body).execute()
                daily_load[str(current_date)] += (slot["end_h"] - slot["start_h"])
                total_hours_busy += (slot["end_h"] - slot["start_h"])
                
        current_date += datetime.timedelta(days=1)
        
    # הפצת מייל הסיכום האנליטי ומפת החום בסיום הריצה
    send_summary_report(gmail_service, emails_to_notify, daily_load, total_hours_busy, long_events_count, conflicts_found)

# ✉️ פונקציה לשליחת מייל התנגשות לו"ז דחופה
def send_conflict_email(service, recipients, date, new_slot, existing_slot):
    subject = f"🚨 התראה דחופה: התנגשות לו''ז ביומן סהר וטוני ({date.strftime('%d/%m')})"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right;">
        <h2 style="color: #d9534f;">⚠️ נמצאה התנגשות לו"ז חסומה!</h2>
        <p>הסוכן החכם ניסה לשריין משבצת קבועה אך זיהה חפיפה ביומן:</p>
        <ul>
            <li><b>התאריך:</b> {date.strftime('%d/%m/%Y')}</li>
            <li><b>המופע שרצינו להכניס:</b> {new_slot}</li>
            <li><b>האירוע הקיים שחוסם:</b> <span style="color: red;">{existing_slot}</span></li>
        </ul>
        <p>🚨 נא לעדכן את הלו"ז באופן ידני בהקדם האפשרי על מנת למנוע כפילויות.</p>
    </body>
    </html>
    """
    send_raw_email(service, recipients, subject, body)

# 📊 פונקציה לשליחת דוח סיכום ומפת חום מלאה ב-HTML
def send_summary_report(service, recipients, daily_load, total_hours, long_events, conflicts):
    subject = "📊 דוח אנליטי ומפת חום: סיכום פעילות סוכן AI"
    
    heatmap_html = ""
    for date, hours in daily_load.items():
        if hours > 8: color = "#ff4d4d"  # עומס כבד - אדום
        elif hours > 5: color = "#ffa64d"  # עומס בינוני - כתום
        else: color = "#99ff99"  # פנוי - ירוק
        
        heatmap_html += f"""
        <tr style="background-color: {color}; text-align: center;">
            <td style="padding: 8px; border: 1px solid #ddd;">{date}</td>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{hours:.1f} שעות</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{"🔥 עמוס מאוד" if hours > 8 else "✅ תקין"}</td>
        </tr>
        """
        
    conflicts_list = "".join([f"<li>❌ {c}</li>" for c in conflicts]) if conflicts else "<li>✅ לא נמצאו התנגשויות חדשות!</li>"
    total_available_hours = 120 - total_hours
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; direction: rtl; text-align: right; background-color: #f9f9f9; padding: 20px;">
        <div style="background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">📋 דוח ביצועים אנליטי ומפת חום - סוכן חכם</h2>
            
            <h3>🌡️ מפת חום ועומס יומי (21-25/06):</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #34495e; color: white;">
                        <th style="padding: 10px; border: 1px solid #ddd;">תאריך</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">סך שעות מנוצלות</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">סטטוס עומס</th>
                    </tr>
                </thead>
                <tbody>
                    {heatmap_html}
                </tbody>
            </table>
            
            <h3>🧠 נתונים אנליטיים ומדדי קיבולת:</h3>
            <ul>
                <li>⏳ <b>סך הכל זמן פנוי משוער ברוטו:</b> {total_available_hours:.1f} שעות</li>
                <li>⚠️ <b>פגישות חריגות (מעל 4 שעות רצופות):</b> {long_events} מופעים</li>
            </ul>
            
            <h3>🛑 סיכום התנגשויות שנמצאו:</h3>
            <ul style="color: #c0392b;">
                {conflicts_list}
            </ul>
            
            <p style="font-size: 12px; color: #7f8c8d; margin-top: 30px; text-align: center;">הופק אוטומטית על ידי סוכן ה-AI הניהולי שלכם 🚀</p>
        </div>
    </body>
    </html>
    """
    send_raw_email(service, recipients, subject, body)

# פונקציית עזר גנרית לשליחת מייל דרך ה-API של Gmail
def send_raw_email(service, recipients, subject, html_body):
    to_header = ", ".join(recipients)
    message = MIMEText(html_body, 'html', 'utf-8')
    message['to'] = to_header
    message['subject'] = subject
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f" המייל '{subject}' נשלח בהצלחה!")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")
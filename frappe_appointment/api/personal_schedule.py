import frappe
from frappe_appointment.api.personal_meet import get_schedular_link

def create_user_appointment_availability(
    candidate_email, duration, user_id="info@mbwcloud.com", app_type="Avi"
):
    try:
        calendar_name = f"Lịch phỏng vấn ứng viên"
        google_calendar_id = None
        google_calendar_docs = frappe.get_all(
            "Google Calendar",
            filters={"user": user_id, "calendar_name": calendar_name},
            fields=["name"]
        )
        if len(google_calendar_docs) > 0:
            google_calendar_id = google_calendar_docs[0].name
        else:
            google_calendar_doc = frappe.get_doc(
                {"doctype": "Google Calendar", "user": user_id, "calendar_name": calendar_name}
            ).insert()
            google_calendar_id = google_calendar_doc.name

        user_appointment_availability_doc = frappe.get_doc(
            {
                "doctype": "User Appointment Availability",
                "user": user_id,
                "google_calendar": google_calendar_id,
                "appointment_time_slot": [
                    {"day": "Monday", "start_time": "09:00:00", "end_time": "22:00:00"},
                    {"day": "Tuesday", "start_time": "09:00:00", "end_time": "22:00:00"},
                    {"day": "Wednesday", "start_time": "09:00:00", "end_time": "22:00:00"},
                    {"day": "Thursday", "start_time": "09:00:00", "end_time": "22:00:00"},
                    {"day": "Friday", "start_time": "09:00:00", "end_time": "22:00:00"},
                    {"day": "Saturday", "start_time": "09:00:00", "end_time": "22:00:00"},
                    {"day": "Sunday", "start_time": "09:00:00", "end_time": "22:00:00"},
                ],
                "enable_scheduling": 1,
                "slug": f"{app_type.lower()}-{candidate_email.replace('@', '_').replace('.', '_')}",
                "available_durations": [{"title": calendar_name, "duration": duration * 60}],
                "app_type": app_type,
            }
        )
        user_appointment_availability_doc.insert()
        return user_appointment_availability_doc
    except Exception as e:
        frappe.throw(str(e))

def get_user_appointment_availability(candidate_email, app_type="Avi"):
    try:
        user_appointment_availability = None
        user_appointment_availability_docs = frappe.get_all(
            "User Appointment Availability",
            filters={  
                "slug": f"{app_type.lower()}-{candidate_email.replace('@', '_').replace('.', '_')}",
            },
            fields=["name"]
        )
        if len(user_appointment_availability_docs) > 0:
            user_appointment_availability_doc = user_appointment_availability_docs[0]
            user_appointment_availability = frappe.get_doc("User Appointment Availability", user_appointment_availability_doc.name)
        
        return user_appointment_availability
    except Exception as e:
        frappe.throw(str(e))

def get_schedular_link_by_name(name, email_candidate: str = None, fullname_candidate: str = None, task_id: str = None, type_app: str = None):
    return get_schedular_link(name, email_candidate, fullname_candidate, task_id, type_app)
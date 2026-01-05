import frappe


def setup_default_user_availability():
    """
    Create a default User Appointment Availability record for Administrator
    with predefined time slots and duration settings.
    """
    try:
        # Check if a User Appointment Availability already exists for Administrator
        integration_third_doc = frappe.get_single("Integration Third Platform")
        integration_third_doc.async_google_calendar = 0
        integration_third_doc.save(ignore_permissions=True)
        
        existing = frappe.db.exists(
            "User Appointment Availability",
            {"user": "Administrator"}
        )
        
        if existing:
            print("ℹ️ User Appointment Availability for Administrator already exists. Skipping creation.")
            return
        
        # Create the User Appointment Availability document
        availability_doc = frappe.get_doc({
            "doctype": "User Appointment Availability",
            "user": "Administrator",
            "enable_scheduling": 1,
            # Time slots for Monday to Friday, 9:00 AM to 4:00 PM
            "appointment_time_slot": [
                {
                    "day": "Monday",
                    "start_time": "09:00:00",
                    "end_time": "16:00:00"
                },
                {
                    "day": "Tuesday",
                    "start_time": "09:00:00",
                    "end_time": "16:00:00"
                },
                {
                    "day": "Wednesday",
                    "start_time": "09:00:00",
                    "end_time": "16:00:00"
                },
                {
                    "day": "Thursday",
                    "start_time": "09:00:00",
                    "end_time": "16:00:00"
                },
                {
                    "day": "Friday",
                    "start_time": "09:00:00",
                    "end_time": "16:00:00"
                }
            ],
            # Available duration: 30 minutes for candidate interviews
            "available_durations": [
                {
                    "title": "Phỏng vấn ứng viên",
                    "duration": 1800
                }
            ]
        })
        
        availability_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("✅ Default User Appointment Availability created for Administrator")
        
    except Exception as e:
        print(f"⚠️ Error creating default User Appointment Availability: {e}")
        frappe.log_error(
            message=str(e),
            title="Setup Default User Availability Error"
        )

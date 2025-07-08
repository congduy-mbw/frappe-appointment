# Copyright (c) 2023, rtCamp and contributors
# For license information, please see license.txt

from datetime import datetime
from functools import cmp_to_key

import frappe
from frappe import _
from frappe.integrations.doctype.google_calendar.google_calendar import (
    get_google_calendar_object,
)
from frappe.model.document import Document

from frappe_appointment.helpers.utils import (
    compare_end_time_slots,
    convert_timezone_to_utc,
    get_today_min_max_time,
)


class AppointmentTimeSlot(Document):
    pass


class GoogleBadRequest(Exception):
    pass


def get_all_unavailable_google_calendar_slots_for_day(
    member_time_slots: object,
    starttime: datetime,
    endtime: datetime,
    date: datetime,
    appointment_group: object,
) -> list:
    """Get all google time slots of the given memebers

    Args:
    member_time_slots (object): list  of members
    starttime (datetime): start time for slot
    endtime (datetime): end time for slot
    date (datetime): data for which need to fetch the data
    appointment_group (object): object

    Returns:
    list: List of all google time slots of members
    """
    cal_slots = []
    
    if frappe.db.get_single_value("Integration Third Platform", "async_google_calendar") == 0:
        return cal_slots

    for member in member_time_slots:
        google_calendar_slots = get_google_calendar_slots_member(member, starttime, endtime, date, appointment_group)

        if google_calendar_slots == False:  # noqa: E712
            return False

        cal_slots = cal_slots + google_calendar_slots

    cal_slots.sort(key=cmp_to_key(compare_end_time_slots))

    return remove_duplicate_slots(cal_slots)


def get_google_calendar_slots_member(
    member: str,
    starttime: datetime,
    endtime: datetime,
    date: datetime,
    appointment_group: object,
) -> list:
    """Fetch the google slots data for given memebr/user

    Args:
    member (str): member email
    starttime (datetime): Start time
    endtime (datetime): end time
    date (datetime): date
    appointment_group (object): object

    Returns:
    list: list of slots of user
    """

    if not member:
        return None

    google_calendar_id = frappe.get_value("User Appointment Availability", member, "google_calendar")

    if not google_calendar_id:
        return None

    google_calendar = frappe.get_doc("Google Calendar", google_calendar_id)

    try:
        google_calendar_api_obj, account = get_google_calendar_object(google_calendar.name)
    except Exception:
        raise GoogleBadRequest(_("Google Calendar - Could not create Google Calendar API object."))

    events = []

    try:
        time_max, time_min = get_today_min_max_time(date)

        events = (
            google_calendar_api_obj.events()
            .list(
                calendarId=google_calendar.google_calendar_id,
                maxResults=2000,
                singleEvents=True,
                timeMax=time_max,
                timeMin=time_min,
                orderBy="startTime",
            )
            .execute()
        )

        # Fetch availability
        # ref: https://github.com/rtCamp/frappe-appointment/issues/67
        # availability = (
        #     google_calendar_api_obj.freebusy()
        #     .query(
        #         body={
        #             "timeMin": time_min,
        #             "timeMax": time_max,
        #             "items": [{"id": google_calendar.google_calendar_id}],
        #         }
        #     )
        #     .execute()
        # )
    except Exception as err:
        frappe.throw(
            _("Google Calendar - Could not fetch event from Google Calendar, error code {0}.").format(err.resp.status)
        )

    events_items = events["items"]
    range_events = []

    for event in events_items:
        try:
            creator = event.get("creator", {}).get("email")
            if creator != member:
                attendees = event.get("attendees", [])
                filtered_attendees = [attendee for attendee in attendees if attendee.get("self", False)]

                if len(filtered_attendees) > 0:
                    attendee = filtered_attendees[0]

                    if attendee.get("responseStatus") == "declined":
                        continue
                else:
                    continue

            if check_if_datetime_in_range(
                convert_timezone_to_utc(event["start"]["dateTime"], event["start"]["timeZone"]),
                convert_timezone_to_utc(event["end"]["dateTime"], event["end"]["timeZone"]),
                starttime,
                endtime,
            ):
                range_events.append(event)
        except Exception:
            if "timeZone" not in event["start"] and google_calendar.custom_ignore_all_day_events:
                pass
            else:
                return False

    return range_events


def remove_duplicate_slots(cal_slots: list):
    """Remove duplicate from google slots

    Args:
    cal_slots (list): List of time slots

    Returns:
    _type_: List of time slots
    """
    if len(cal_slots) <= 1:
        return cal_slots

    current = 1
    last = 0
    remove_duplicate_time_slots = []

    remove_duplicate_time_slots.append(cal_slots[last])

    while current < len(cal_slots):
        last_start = convert_timezone_to_utc(cal_slots[last]["start"]["dateTime"], cal_slots[last]["start"]["timeZone"])
        last_end = convert_timezone_to_utc(cal_slots[last]["end"]["dateTime"], cal_slots[last]["end"]["timeZone"])
        current_start = convert_timezone_to_utc(
            cal_slots[current]["start"]["dateTime"],
            cal_slots[current]["start"]["timeZone"],
        )
        current_end = convert_timezone_to_utc(
            cal_slots[current]["end"]["dateTime"], cal_slots[current]["end"]["timeZone"]
        )

        if current_start == last_start and current_end == last_end:
            current += 1
            continue

        remove_duplicate_time_slots.append(cal_slots[current])
        last = current
        current += 1

    return remove_duplicate_time_slots


def is_busy_event(event: object, availability: object, user: str):
    if (
        not availability.get("calendars")
        or not availability["calendars"].get(user)
        or availability["calendars"][user].get("errors")
    ):
        # If error then assume the slot as busy only
        return True

    busy_array = availability["calendars"][user]["busy"]

    start_utc = convert_timezone_to_utc(event["start"]["dateTime"], event["start"]["timeZone"])
    end_utc = convert_timezone_to_utc(event["end"]["dateTime"], event["end"]["timeZone"])

    for busy in busy_array:
        if datetime.fromisoformat(busy["start"]) == start_utc and datetime.fromisoformat(busy["end"]) == end_utc:
            return True

    return False


def check_if_datetime_in_range(
    start_datetime: datetime,
    end_datetime: datetime,
    lower_datetime: datetime,
    upper_datetime: datetime,
):
    """Check if [start_datetime, end_datetime] (s1) has an intersection with [lower_datetime, upper_datetime] (r1).

    Args:
    start_datetime (datetime): Start Datetime
    end_datetime (datetime): End Datetime
    lower_datetime (datetime): Lower Datetime (Start time of range)
    upper_datetime (datetime): Upper Datetime (End time of range)

    Returns:
    bool: True if s1 has overlap with r1, False otherwise.
    """

    # if lower_datetime <= start_datetime and end_datetime <= upper_datetime:
    # 	return True

    # if end_datetime > lower_datetime and lower_datetime > start_datetime:
    # 	return True

    # if start_datetime < upper_datetime and upper_datetime < end_datetime:
    # 	return True

    if lower_datetime > end_datetime or upper_datetime < start_datetime:
        return False

    return True

import os
import datetime
import pytz
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

class GoogleCalendarService:
    def __init__(self):
        self.scopes = config.SCOPES
        self.timezone_str = config.TIMEZONE
        self.tz = pytz.timezone(self.timezone_str)
        self.creds: Optional[Credentials] = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticates with Google Calendar API using OAuth2 (supports local file & cloud env vars)."""
        token_path = config.GOOGLE_TOKEN_FILE
        creds_path = config.GOOGLE_CREDENTIALS_FILE

        # 1. Try loading token from environment variable (useful for cloud servers like Render/Koyeb)
        token_env = os.getenv("GOOGLE_TOKEN_JSON")
        if token_env:
            try:
                import json
                info = json.loads(token_env)
                self.creds = Credentials.from_authorized_user_info(info, self.scopes)
            except Exception as e:
                print(f"[Warning] Failed to load token from GOOGLE_TOKEN_JSON env: {e}")
                self.creds = None

        # 2. Try loading token from local token.json file
        if not self.creds and os.path.exists(token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(str(token_path), self.scopes)
            except Exception as e:
                print(f"[Warning] Failed to load token.json: {e}")
                self.creds = None

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"[Warning] Failed to refresh token: {e}")
                    self.creds = None

            if not self.creds:
                if not os.path.exists(creds_path):
                    print("[Warning] No valid token or credentials.json found. Set GOOGLE_TOKEN_JSON environment variable for cloud deployment.")
                    return
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), self.scopes)
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"[Warning] Could not run local server auth: {e}")
                    return

            if self.creds and os.path.exists(token_path):
                try:
                    with open(token_path, "w", encoding="utf-8") as token_file:
                        token_file.write(self.creds.to_json())
                except Exception:
                    pass

        if self.creds:
            self.service = build("calendar", "v3", credentials=self.creds)

    def add_event(
        self,
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        details: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adds a new event to the primary Google Calendar.
        
        Args:
            title: Title of the event
            start_time: Start datetime string in ISO format (e.g., '2026-07-24T14:00:00')
            end_time: Optional end datetime string in ISO format. Defaults to 1 hour after start_time.
            details: Optional detailed description for the event.
        """
        try:
            if not self.service:
                self._authenticate()
                if not self.service:
                    return {"status": "error", "message": "Google Calendar avtorizatsiyasi mavjud emas. GOOGLE_TOKEN_JSON environment variable kiritilganini tekshiring."}

            # Parse start time
            try:
                dt_start = datetime.datetime.fromisoformat(start_time)
            except ValueError:
                return {"status": "error", "message": f"Noto'g'ri boshlanish vaqti formati: '{start_time}'. ISO format kerak."}

            if dt_start.tzinfo is None:
                dt_start = self.tz.localize(dt_start)

            # Calculate end time if not provided
            if end_time:
                try:
                    dt_end = datetime.datetime.fromisoformat(end_time)
                    if dt_end.tzinfo is None:
                        dt_end = self.tz.localize(dt_end)
                except ValueError:
                    dt_end = dt_start + datetime.timedelta(hours=1)
            else:
                dt_end = dt_start + datetime.timedelta(hours=1)

            event_body = {
                "summary": title,
                "description": details or "",
                "start": {
                    "dateTime": dt_start.isoformat(),
                    "timeZone": self.timezone_str,
                },
                "end": {
                    "dateTime": dt_end.isoformat(),
                    "timeZone": self.timezone_str,
                },
            }

            event = self.service.events().insert(calendarId="primary", body=event_body).execute()
            return {
                "status": "success",
                "event_id": event.get("id"),
                "summary": event.get("summary"),
                "start": dt_start.strftime("%Y-%m-%d %H:%M"),
                "end": dt_end.strftime("%Y-%m-%d %H:%M"),
                "html_link": event.get("htmlLink"),
                "message": f"✅ '{title}' tasdiqlandi va kalendarga qo'shildi!"
            }

        except HttpError as err:
            return {"status": "error", "message": f"Google Calendar API xatosi: {err}"}
        except Exception as err:
            return {"status": "error", "message": f"Xatolik yuz berdi: {err}"}

    def get_upcoming_events(self, limit: int = 10, start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves upcoming events from the primary calendar.
        
        Args:
            limit: Maximum number of events to fetch (default 10)
            start_date: Optional ISO format date to start fetching from. Defaults to now.
        """
        try:
            if start_date:
                try:
                    dt_start = datetime.datetime.fromisoformat(start_date)
                    if dt_start.tzinfo is None:
                        dt_start = self.tz.localize(dt_start)
                except ValueError:
                    dt_start = datetime.datetime.now(self.tz)
            else:
                dt_start = datetime.datetime.now(self.tz)

            time_min = dt_start.isoformat()

            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=time_min,
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])
            formatted_events = []
            
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                formatted_events.append({
                    "id": event["id"],
                    "summary": event.get("summary", "Sarlavhasiz"),
                    "start": start,
                    "end": end,
                    "description": event.get("description", ""),
                    "link": event.get("htmlLink")
                })

            return {
                "status": "success",
                "count": len(formatted_events),
                "events": formatted_events
            }

        except HttpError as err:
            return {"status": "error", "message": f"Google Calendar API xatosi: {err}"}
        except Exception as err:
            return {"status": "error", "message": f"Xatolik yuz berdi: {err}"}

    def delete_event(self, event_id: str) -> Dict[str, Any]:
        """
        Deletes an event from the primary calendar by ID.
        """
        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
            return {
                "status": "success",
                "event_id": event_id,
                "message": f"🗑 Event (ID: {event_id}) muvaffaqiyatli o'chirildi."
            }
        except HttpError as err:
            return {"status": "error", "message": f"O'chirishda Google Calendar API xatosi: {err}"}
        except Exception as err:
            return {"status": "error", "message": f"Xatolik yuz berdi: {err}"}

# Global singleton instance for easy import
_calendar_instance: Optional[GoogleCalendarService] = None

def get_calendar_service() -> GoogleCalendarService:
    global _calendar_instance
    if _calendar_instance is None:
        _calendar_instance = GoogleCalendarService()
    return _calendar_instance

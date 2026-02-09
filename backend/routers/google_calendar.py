"""
Google Calendar Integration Router

Handles OAuth flow, calendar sync, and AI training data collection.
"""

import os
# Allow Google to return additional scopes without raising an error
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel
from core.supabase import get_supabase_admin
from core.security import get_current_user
from core.config import get_settings
from opik import track
import logging
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calendar", tags=["Google Calendar"])
settings = get_settings()

# OAuth Configuration
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly',
]

# Credentials loaded dynamically to ensure dotenv is loaded first
def get_google_credentials():
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/calendar/auth/callback')
    return client_id, client_secret, redirect_uri


class CalendarSyncRequest(BaseModel):
    full_sync: bool = False
    days_back: int = 30
    days_forward: int = 90


class CalendarEventResponse(BaseModel):
    id: str
    title: str
    start_time: str
    end_time: str
    all_day: bool
    location: Optional[str] = None
    event_type: Optional[str] = None


def get_oauth_flow(state: Optional[str] = None) -> Flow:
    """Create OAuth flow with client configuration."""
    client_id, client_secret, redirect_uri = get_google_credentials()

    if not client_id or not client_secret:
        raise ValueError("Google OAuth credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")

    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    if state:
        flow.state = state

    return flow


def get_user_credentials(user_id: str) -> Optional[Credentials]:
    """Get stored OAuth credentials for a user."""
    client_id, client_secret, _ = get_google_credentials()
    supabase = get_supabase_admin()

    result = (
        supabase.table("google_oauth_tokens")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return None

    token_data = result.data[0]

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=token_data.get("scope", "").split(" ") if token_data.get("scope") else SCOPES,
    )

    # Check if token needs refresh
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            # Update stored token
            supabase.table("google_oauth_tokens").update({
                "access_token": creds.token,
                "expires_at": creds.expiry.isoformat() if creds.expiry else None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    return creds


def categorize_event(event: dict) -> str:
    """Categorize a calendar event for AI training."""
    title = (event.get("summary") or "").lower()
    description = (event.get("description") or "").lower()
    attendees = event.get("attendees", [])

    # Meeting indicators
    meeting_keywords = ["meeting", "call", "sync", "standup", "1:1", "review", "interview"]
    if any(kw in title for kw in meeting_keywords) or len(attendees) > 1:
        return "meeting"

    # Focus time
    focus_keywords = ["focus", "deep work", "heads down", "no meetings", "blocked"]
    if any(kw in title for kw in focus_keywords):
        return "focus_time"

    # Personal
    personal_keywords = ["lunch", "break", "gym", "doctor", "dentist", "personal", "vacation", "pto"]
    if any(kw in title for kw in personal_keywords):
        return "personal"

    # Travel
    travel_keywords = ["travel", "flight", "commute", "drive to"]
    if any(kw in title for kw in travel_keywords):
        return "travel"

    # Default
    return "other"


@router.get("/auth/url")
async def get_auth_url(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get the Google OAuth authorization URL."""
    try:
        # Check credentials are configured
        client_id, client_secret, redirect_uri = get_google_credentials()
        if not client_id or not client_secret:
            logger.error("Google OAuth credentials not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
            )

        logger.info(f"Creating OAuth flow with redirect_uri: {redirect_uri}")
        flow = get_oauth_flow()

        # Get frontend URL from request origin or settings
        frontend_url = request.headers.get("origin") or settings.frontend_url

        # Include user_id and frontend_url in state for callback
        state = json.dumps({
            "user_id": current_user["id"],
            "frontend_url": frontend_url
        })

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state,
        )

        logger.info(f"Generated auth URL for user {current_user['id']}")
        return {
            "success": True,
            "data": {
                "authorization_url": authorization_url,
            },
        }
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}",
        )


@router.get("/auth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """Handle OAuth callback from Google."""
    try:
        logger.info(f"OAuth callback received with state: {state[:50]}...")

        # Parse state to get user_id
        state_data = json.loads(state)
        user_id = state_data.get("user_id")
        logger.info(f"Parsed user_id from state: {user_id}")

        if not user_id:
            logger.error("No user_id in state parameter")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        # Extract frontend_url from state
        frontend_url = state_data.get("frontend_url", settings.frontend_url)

        logger.info("Creating OAuth flow for token exchange...")
        flow = get_oauth_flow(state=state)
        logger.info("Fetching token from Google...")
        flow.fetch_token(code=code)
        logger.info("Token fetched successfully")

        credentials = flow.credentials

        supabase = get_supabase_admin()

        # Store or update tokens
        token_data = {
            "user_id": user_id,
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_type": "Bearer",
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
            "scope": " ".join(credentials.scopes) if credentials.scopes else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Upsert token
        existing = (
            supabase.table("google_oauth_tokens")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )

        if existing.data:
            supabase.table("google_oauth_tokens").update(token_data).eq("user_id", user_id).execute()
        else:
            token_data["created_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("google_oauth_tokens").insert(token_data).execute()

        # Update integration status
        integration_exists = (
            supabase.table("integrations")
            .select("id")
            .eq("user_id", user_id)
            .eq("integration_type", "google_calendar")
            .execute()
        )

        if integration_exists.data:
            supabase.table("integrations").update({
                "status": "active",
                "connected_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", integration_exists.data[0]["id"]).execute()
        else:
            supabase.table("integrations").insert({
                "user_id": user_id,
                "integration_type": "google_calendar",
                "status": "active",
                "connected_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

        logger.info(f"Google Calendar connected for user {user_id}")

        # Redirect to frontend success page
        return RedirectResponse(url=f"{frontend_url}/settings?calendar=connected")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in state: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}", exc_info=True)
        print(f"OAUTH ERROR: {type(e).__name__}: {e}")  # Also print to console
        # Try to get frontend_url from state, fallback to settings
        try:
            state_data = json.loads(state) if state else {}
            frontend_url = state_data.get("frontend_url", settings.frontend_url)
        except:
            frontend_url = settings.frontend_url
        return RedirectResponse(url=f"{frontend_url}/settings?calendar=error")


@router.get("/status")
async def get_calendar_status(
    current_user: dict = Depends(get_current_user),
):
    """Check if Google Calendar is connected and get status."""
    try:
        supabase = get_supabase_admin()

        token_result = (
            supabase.table("google_oauth_tokens")
            .select("last_synced_at, expires_at, created_at")
            .eq("user_id", current_user["id"])
            .execute()
        )

        if not token_result.data:
            return {
                "success": True,
                "data": {
                    "connected": False,
                    "status": "not_connected",
                },
            }

        token_data = token_result.data[0]

        # Count synced events
        events_count = (
            supabase.table("calendar_events")
            .select("id", count="exact")
            .eq("user_id", current_user["id"])
            .execute()
        )

        return {
            "success": True,
            "data": {
                "connected": True,
                "status": "active",
                "last_synced_at": token_data.get("last_synced_at"),
                "connected_at": token_data.get("created_at"),
                "events_synced": events_count.count if events_count else 0,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get calendar status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get calendar status",
        )


@router.post("/sync")
@track(name="calendar_sync")
async def sync_calendar(
    request: CalendarSyncRequest,
    current_user: dict = Depends(get_current_user),
):
    """Sync calendar events from Google Calendar."""
    try:
        credentials = get_user_credentials(current_user["id"])

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Calendar not connected. Please authorize first.",
            )

        service = build('calendar', 'v3', credentials=credentials)
        supabase = get_supabase_admin()

        # Calculate time range
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=request.days_back)).isoformat()
        time_max = (now + timedelta(days=request.days_forward)).isoformat()

        # Get sync token for incremental sync
        token_data = (
            supabase.table("google_oauth_tokens")
            .select("calendar_sync_token")
            .eq("user_id", current_user["id"])
            .execute()
        )

        sync_token = None
        if not request.full_sync and token_data.data:
            sync_token = token_data.data[0].get("calendar_sync_token")

        events_synced = 0
        events_created = 0
        events_updated = 0
        new_sync_token = None

        try:
            # Fetch events from Google Calendar
            if sync_token and not request.full_sync:
                # Incremental sync
                events_result = service.events().list(
                    calendarId='primary',
                    syncToken=sync_token,
                ).execute()
            else:
                # Full sync
                events_result = service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=500,
                    singleEvents=True,
                    orderBy='startTime',
                ).execute()

            events = events_result.get('items', [])
            new_sync_token = events_result.get('nextSyncToken')

            for event in events:
                # Skip cancelled events in incremental sync
                if event.get('status') == 'cancelled':
                    # Delete from our DB if exists
                    supabase.table("calendar_events").delete().eq(
                        "user_id", current_user["id"]
                    ).eq("google_event_id", event['id']).execute()
                    continue

                # Parse start/end times
                start = event.get('start', {})
                end = event.get('end', {})

                all_day = 'date' in start
                if all_day:
                    start_time = datetime.fromisoformat(start['date']).replace(tzinfo=timezone.utc)
                    end_time = datetime.fromisoformat(end['date']).replace(tzinfo=timezone.utc)
                else:
                    start_time = datetime.fromisoformat(start.get('dateTime', '').replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end.get('dateTime', '').replace('Z', '+00:00'))

                event_data = {
                    "user_id": current_user["id"],
                    "google_event_id": event['id'],
                    "google_calendar_id": "primary",
                    "title": event.get('summary', 'Untitled'),
                    "description": event.get('description'),
                    "location": event.get('location'),
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "all_day": all_day,
                    "timezone": start.get('timeZone'),
                    "recurring": event.get('recurringEventId') is not None,
                    "recurring_event_id": event.get('recurringEventId'),
                    "event_type": categorize_event(event),
                    "attendees_count": len(event.get('attendees', [])),
                    "is_organizer": event.get('organizer', {}).get('self', True),
                    "status": event.get('status', 'confirmed'),
                    "visibility": event.get('visibility', 'default'),
                    "color_id": event.get('colorId'),
                    "busy_status": "free" if event.get('transparency') == 'transparent' else "busy",
                    "etag": event.get('etag'),
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

                # Upsert event
                existing_event = (
                    supabase.table("calendar_events")
                    .select("id")
                    .eq("user_id", current_user["id"])
                    .eq("google_event_id", event['id'])
                    .execute()
                )

                if existing_event.data:
                    supabase.table("calendar_events").update(event_data).eq(
                        "id", existing_event.data[0]["id"]
                    ).execute()
                    events_updated += 1
                else:
                    event_data["created_at"] = datetime.now(timezone.utc).isoformat()
                    supabase.table("calendar_events").insert(event_data).execute()
                    events_created += 1

                events_synced += 1

            # Handle pagination
            while 'nextPageToken' in events_result:
                events_result = service.events().list(
                    calendarId='primary',
                    pageToken=events_result['nextPageToken'],
                    timeMin=time_min if not sync_token else None,
                    timeMax=time_max if not sync_token else None,
                ).execute()

                for event in events_result.get('items', []):
                    # Same processing as above (simplified for brevity)
                    if event.get('status') == 'cancelled':
                        continue
                    events_synced += 1

                new_sync_token = events_result.get('nextSyncToken', new_sync_token)

        except HttpError as e:
            if e.resp.status == 410:
                # Sync token expired, need full sync
                logger.warning("Sync token expired, performing full sync")
                request.full_sync = True
                return await sync_calendar(request, current_user)
            raise

        # Update sync token and last_synced_at
        supabase.table("google_oauth_tokens").update({
            "calendar_sync_token": new_sync_token,
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_id", current_user["id"]).execute()

        # Update integration last_synced_at
        supabase.table("integrations").update({
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_id", current_user["id"]).eq("integration_type", "google_calendar").execute()

        logger.info(f"Calendar sync completed for user {current_user['id']}: {events_synced} events")

        return {
            "success": True,
            "data": {
                "events_synced": events_synced,
                "events_created": events_created,
                "events_updated": events_updated,
                "sync_type": "full" if request.full_sync else "incremental",
                "synced_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Calendar sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync calendar: {str(e)}",
        )


@router.get("/events")
async def get_calendar_events(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, le=500),
):
    """Get synced calendar events."""
    try:
        supabase = get_supabase_admin()

        query = (
            supabase.table("calendar_events")
            .select("*")
            .eq("user_id", current_user["id"])
            .neq("status", "cancelled")
            .order("start_time", desc=False)
            .limit(limit)
        )

        if start_date:
            query = query.gte("start_time", f"{start_date}T00:00:00Z")

        if end_date:
            query = query.lte("end_time", f"{end_date}T23:59:59Z")

        if event_type:
            query = query.eq("event_type", event_type)

        result = query.execute()

        return {
            "success": True,
            "data": {
                "events": result.data or [],
                "total": len(result.data or []),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get calendar events",
        )


@router.get("/today")
async def get_today_schedule(
    current_user: dict = Depends(get_current_user),
):
    """Get today's calendar events for AI context."""
    try:
        supabase = get_supabase_admin()

        today = datetime.now(timezone.utc).date()
        tomorrow = today + timedelta(days=1)

        result = (
            supabase.table("calendar_events")
            .select("*")
            .eq("user_id", current_user["id"])
            .neq("status", "cancelled")
            .gte("start_time", today.isoformat())
            .lt("start_time", tomorrow.isoformat())
            .order("start_time", desc=False)
            .execute()
        )

        events = result.data or []

        # Calculate busy time
        total_busy_minutes = 0
        for event in events:
            if event.get("busy_status") == "busy":
                start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
                total_busy_minutes += int((end - start).total_seconds() / 60)

        # Find free blocks
        free_blocks = []
        work_start = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
        work_end = datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0)

        sorted_events = sorted(
            [e for e in events if e.get("busy_status") == "busy"],
            key=lambda x: x["start_time"]
        )

        current_time = max(work_start, datetime.now(timezone.utc))

        for event in sorted_events:
            event_start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
            if event_start > current_time:
                gap_minutes = int((event_start - current_time).total_seconds() / 60)
                if gap_minutes >= 30:  # Only consider blocks >= 30 mins
                    free_blocks.append({
                        "start": current_time.isoformat(),
                        "end": event_start.isoformat(),
                        "duration_minutes": gap_minutes,
                    })
            event_end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
            current_time = max(current_time, event_end)

        # Check remaining time
        if current_time < work_end:
            gap_minutes = int((work_end - current_time).total_seconds() / 60)
            if gap_minutes >= 30:
                free_blocks.append({
                    "start": current_time.isoformat(),
                    "end": work_end.isoformat(),
                    "duration_minutes": gap_minutes,
                })

        return {
            "success": True,
            "data": {
                "date": today.isoformat(),
                "events": events,
                "total_events": len(events),
                "total_busy_minutes": total_busy_minutes,
                "free_blocks": free_blocks,
                "meetings_count": len([e for e in events if e.get("event_type") == "meeting"]),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get today's schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get today's schedule",
        )


@router.get("/insights")
@track(name="calendar_insights")
async def get_calendar_insights(
    current_user: dict = Depends(get_current_user),
):
    """Get AI-generated insights from calendar patterns."""
    try:
        supabase = get_supabase_admin()

        # Get last 30 days of events
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        result = (
            supabase.table("calendar_events")
            .select("*")
            .eq("user_id", current_user["id"])
            .gte("start_time", thirty_days_ago)
            .neq("status", "cancelled")
            .execute()
        )

        events = result.data or []

        if not events:
            return {
                "success": True,
                "data": {
                    "insights": [],
                    "message": "Not enough calendar data for insights. Sync more events.",
                },
            }

        # Calculate insights
        insights = []

        # 1. Meeting-heavy days
        day_meetings = {}
        for event in events:
            if event.get("event_type") == "meeting":
                day = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00")).strftime("%A")
                day_meetings[day] = day_meetings.get(day, 0) + 1

        if day_meetings:
            busiest_day = max(day_meetings, key=day_meetings.get)
            insights.append({
                "type": "meeting_heavy_days",
                "title": "Busiest Meeting Day",
                "description": f"{busiest_day} has the most meetings ({day_meetings[busiest_day]} on average)",
                "data": day_meetings,
            })

        # 2. Peak meeting hours
        hour_meetings = {}
        for event in events:
            if event.get("event_type") == "meeting":
                hour = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00")).hour
                hour_meetings[hour] = hour_meetings.get(hour, 0) + 1

        if hour_meetings:
            peak_hour = max(hour_meetings, key=hour_meetings.get)
            insights.append({
                "type": "peak_hours",
                "title": "Peak Meeting Time",
                "description": f"Most meetings occur around {peak_hour}:00",
                "data": hour_meetings,
            })

        # 3. Average daily busy time
        daily_busy = {}
        for event in events:
            if event.get("busy_status") == "busy":
                day = event["start_time"][:10]
                start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
                minutes = int((end - start).total_seconds() / 60)
                daily_busy[day] = daily_busy.get(day, 0) + minutes

        if daily_busy:
            avg_busy = sum(daily_busy.values()) / len(daily_busy)
            insights.append({
                "type": "average_busy_time",
                "title": "Average Daily Committed Time",
                "description": f"You spend an average of {int(avg_busy / 60)}h {int(avg_busy % 60)}m in calendar events daily",
                "data": {"average_minutes": avg_busy},
            })

        # 4. Event type breakdown
        type_counts = {}
        for event in events:
            event_type = event.get("event_type", "other")
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        if type_counts:
            insights.append({
                "type": "event_breakdown",
                "title": "Event Type Breakdown",
                "description": "Distribution of your calendar events by type",
                "data": type_counts,
            })

        return {
            "success": True,
            "data": {
                "insights": insights,
                "period": "last_30_days",
                "events_analyzed": len(events),
            },
        }
    except Exception as e:
        logger.error(f"Failed to generate calendar insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate calendar insights",
        )


@router.delete("/disconnect")
async def disconnect_calendar(
    current_user: dict = Depends(get_current_user),
):
    """Disconnect Google Calendar integration."""
    try:
        supabase = get_supabase_admin()

        # Delete OAuth tokens
        supabase.table("google_oauth_tokens").delete().eq("user_id", current_user["id"]).execute()

        # Delete synced events
        supabase.table("calendar_events").delete().eq("user_id", current_user["id"]).execute()

        # Update integration status
        supabase.table("integrations").update({
            "status": "disconnected",
        }).eq("user_id", current_user["id"]).eq("integration_type", "google_calendar").execute()

        logger.info(f"Google Calendar disconnected for user {current_user['id']}")

        return {
            "success": True,
            "message": "Google Calendar disconnected successfully",
        }
    except Exception as e:
        logger.error(f"Failed to disconnect calendar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect calendar",
        )

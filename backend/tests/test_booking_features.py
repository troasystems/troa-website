"""Tests for amenity booking features:
1. Today/tomorrow only
2. No consecutive day same slot
3. Edit existing booking (PUT)
4. Peak hours 18-20: only 60-min slots
"""
import os
import asyncio
import secrets
from datetime import datetime, timedelta, date as date_type

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / '.env')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://websocket-app-3.preview.emergentagent.com').rstrip('/')
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'troa_residence')

AMENITY_ID = '69bec999-30e1-4127-845d-dc6dff3e2057'
AMENITY_NAME = 'Sports Courts'
ADMIN_EMAIL = 'troa.systems@gmail.com'

TODAY = date_type.today().strftime('%Y-%m-%d')
TOMORROW = (date_type.today() + timedelta(days=1)).strftime('%Y-%m-%d')
DAY_AFTER = (date_type.today() + timedelta(days=2)).strftime('%Y-%m-%d')


# ---------- Session fixture ----------
@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def session_token(event_loop):
    """Insert a temp admin session in Mongo, return token."""
    token = 'testtok_' + secrets.token_urlsafe(16)

    async def _setup():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await db.sessions.insert_one({
            'token': token,
            'user': {'email': ADMIN_EMAIL, 'role': 'admin', 'name': 'Admin'},
            'expires': datetime.utcnow() + timedelta(hours=2),
        })
        client.close()

    async def _teardown():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await db.sessions.delete_many({'token': {'$regex': '^testtok_'}})
        # cleanup any test bookings for the admin user
        await db.bookings.delete_many({
            'booked_by_email': ADMIN_EMAIL,
            'amenity_id': AMENITY_ID,
            'booking_date': {'$in': [TODAY, TOMORROW, DAY_AFTER]},
        })
        client.close()

    event_loop.run_until_complete(_setup())
    # Pre-clean any leftover bookings from prior runs
    event_loop.run_until_complete(_teardown_helper())
    yield token
    event_loop.run_until_complete(_teardown())


async def _teardown_helper():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.bookings.delete_many({
        'booked_by_email': ADMIN_EMAIL,
        'amenity_id': AMENITY_ID,
        'booking_date': {'$in': [TODAY, TOMORROW, DAY_AFTER]},
    })
    client.close()


@pytest.fixture
def headers(session_token):
    return {'X-Session-Token': f'Bearer {session_token}', 'Content-Type': 'application/json'}


@pytest.fixture(autouse=True)
def clean_bookings(event_loop):
    """Clean test bookings before each test"""
    event_loop.run_until_complete(_teardown_helper())
    yield
    event_loop.run_until_complete(_teardown_helper())


def _booking_payload(date, start_time, duration=60):
    return {
        'amenity_id': AMENITY_ID,
        'amenity_name': AMENITY_NAME,
        'booking_date': date,
        'start_time': start_time,
        'duration_minutes': duration,
        'guests': [],
        'additional_guests': [],
    }


# ============ Feature 1: today/tomorrow only ============
class TestFeature1DateRange:
    def test_book_today_succeeds(self, headers):
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TODAY, '08:00', 60), headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()['booking_date'] == TODAY

    def test_book_tomorrow_succeeds(self, headers):
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '08:00', 60), headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()['booking_date'] == TOMORROW

    def test_book_day_after_tomorrow_fails(self, headers):
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(DAY_AFTER, '08:00', 60), headers=headers)
        assert r.status_code == 400, r.text
        assert 'today or tomorrow' in r.json()['detail'].lower()


# ============ Feature 2: consecutive-day same slot ============
class TestFeature2ConsecutiveDay:
    def test_same_slot_two_days_fails(self, headers):
        r1 = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TODAY, '10:00', 60), headers=headers)
        assert r1.status_code == 200, r1.text
        r2 = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '10:00', 60), headers=headers)
        assert r2.status_code == 400, r2.text
        assert 'consecutive' in r2.json()['detail'].lower()

    def test_different_slot_tomorrow_succeeds(self, headers):
        r1 = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TODAY, '10:00', 60), headers=headers)
        assert r1.status_code == 200, r1.text
        r2 = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '14:00', 60), headers=headers)
        assert r2.status_code == 200, r2.text


# ============ Feature 3: edit (PUT) ============
class TestFeature3Edit:
    def test_edit_time_succeeds(self, headers):
        # Use 16:00 to ensure we have room to bump to 17:00 later (today/future hour)
        # Use far-future hours from current to avoid past-booking errors
        # Pick a fixed time that's safely in the future regardless of current time:
        # We'll use TOMORROW so it's always in the future.
        c = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '09:00', 60), headers=headers)
        assert c.status_code == 200, c.text
        bid = c.json()['id']
        u = requests.put(
            f'{BASE_URL}/api/bookings/{bid}',
            json={'booking_date': TOMORROW, 'start_time': '11:00', 'duration_minutes': 60, 'guests': []},
            headers=headers,
        )
        assert u.status_code == 200, u.text
        assert u.json()['start_time'] == '11:00'

    def test_edit_to_day_after_tomorrow_fails(self, headers):
        c = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '09:00', 60), headers=headers)
        assert c.status_code == 200, c.text
        bid = c.json()['id']
        u = requests.put(
            f'{BASE_URL}/api/bookings/{bid}',
            json={'booking_date': DAY_AFTER, 'start_time': '11:00', 'duration_minutes': 60, 'guests': []},
            headers=headers,
        )
        assert u.status_code == 400, u.text
        assert 'today or tomorrow' in u.json()['detail'].lower()

    def test_edit_to_peak_30min_fails(self, headers):
        c = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '09:00', 60), headers=headers)
        assert c.status_code == 200, c.text
        bid = c.json()['id']
        u = requests.put(
            f'{BASE_URL}/api/bookings/{bid}',
            json={'booking_date': TOMORROW, 'start_time': '18:00', 'duration_minutes': 30, 'guests': []},
            headers=headers,
        )
        assert u.status_code == 400, u.text
        assert 'peak' in u.json()['detail'].lower()


# ============ Feature 4: peak hours (18-20) ============
class TestFeature4PeakHours:
    def test_30min_at_18_fails(self, headers):
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '18:00', 30), headers=headers)
        assert r.status_code == 400, r.text
        assert 'peak' in r.json()['detail'].lower()

    def test_60min_at_18_succeeds(self, headers):
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '18:00', 60), headers=headers)
        assert r.status_code == 200, r.text

    def test_30min_at_1930_fails(self, headers):
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '19:30', 30), headers=headers)
        assert r.status_code == 400, r.text
        assert 'peak' in r.json()['detail'].lower()

    def test_30min_at_1730_succeeds_no_overlap(self, headers):
        # 17:30 + 30 = 18:00; slot_end == peak_start -> does NOT overlap; should succeed
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '17:30', 30), headers=headers)
        assert r.status_code == 200, r.text

    def test_30min_at_20_succeeds(self, headers):
        # 20:00 is outside peak window (peak_end exclusive)
        r = requests.post(f'{BASE_URL}/api/bookings', json=_booking_payload(TOMORROW, '20:00', 30), headers=headers)
        assert r.status_code == 200, r.text

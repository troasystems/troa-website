"""Admin/manager override tests for booking edit/cancel + GET /manage/bookings."""
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
USER_EMAIL = 'TEST_overrideuser@example.com'

TODAY = date_type.today().strftime('%Y-%m-%d')
TOMORROW = (date_type.today() + timedelta(days=1)).strftime('%Y-%m-%d')
DAY_AFTER = (date_type.today() + timedelta(days=2)).strftime('%Y-%m-%d')
THREE_DAYS = (date_type.today() + timedelta(days=3)).strftime('%Y-%m-%d')


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def tokens(event_loop):
    admin_tok = 'testtok_admin_' + secrets.token_urlsafe(12)
    user_tok = 'testtok_user_' + secrets.token_urlsafe(12)

    async def _setup():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        now = datetime.utcnow()
        await db.sessions.insert_many([
            {'token': admin_tok,
             'user': {'email': ADMIN_EMAIL, 'role': 'admin', 'name': 'Admin'},
             'expires': now + timedelta(hours=2)},
            {'token': user_tok,
             'user': {'email': USER_EMAIL, 'role': 'user', 'name': 'Test User'},
             'expires': now + timedelta(hours=2)},
        ])
        client.close()

    async def _teardown():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await db.sessions.delete_many({'token': {'$regex': '^testtok_'}})
        await db.bookings.delete_many({
            'booked_by_email': {'$in': [USER_EMAIL, ADMIN_EMAIL]},
            'amenity_id': AMENITY_ID,
        })
        client.close()

    event_loop.run_until_complete(_setup())
    event_loop.run_until_complete(_clean_test_bookings())
    yield {'admin': admin_tok, 'user': user_tok}
    event_loop.run_until_complete(_teardown())


async def _clean_test_bookings():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    await db.bookings.delete_many({
        'booked_by_email': {'$in': [USER_EMAIL, ADMIN_EMAIL]},
        'amenity_id': AMENITY_ID,
    })
    client.close()


@pytest.fixture(autouse=True)
def clean_each(event_loop):
    event_loop.run_until_complete(_clean_test_bookings())
    yield
    event_loop.run_until_complete(_clean_test_bookings())


def _hdr(tok):
    return {'X-Session-Token': f'Bearer {tok}', 'Content-Type': 'application/json'}


def _create_user_booking(event_loop, date=TOMORROW, start='09:00', duration=60):
    """Insert a booking directly owned by USER_EMAIL."""
    import uuid
    bid = str(uuid.uuid4())
    end_h, end_m = int(start.split(':')[0]), int(start.split(':')[1]) + duration
    end_h += end_m // 60
    end_m = end_m % 60
    end_time = f'{end_h:02d}:{end_m:02d}'

    async def _ins():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await db.bookings.insert_one({
            'id': bid,
            'amenity_id': AMENITY_ID,
            'amenity_name': AMENITY_NAME,
            'booked_by_email': USER_EMAIL,
            'booked_by_name': 'Test User',
            'booked_by_villa': '999',
            'booking_date': date,
            'start_time': start,
            'end_time': end_time,
            'duration_minutes': duration,
            'guests': [],
            'additional_guests': [],
            'total_guest_charges': 0.0,
            'status': 'confirmed',
            'availed_status': 'pending',
            'audit_log': [],
            'created_at': datetime.utcnow(),
        })
        client.close()

    event_loop.run_until_complete(_ins())
    return bid


def _get_booking(event_loop, bid):
    async def _g():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        b = await db.bookings.find_one({'id': bid}, {'_id': 0})
        client.close()
        return b
    return event_loop.run_until_complete(_g())


# ============ Admin Cancel Override ============
class TestAdminCancelOverride:
    def test_admin_can_cancel_user_booking(self, tokens, event_loop):
        bid = _create_user_booking(event_loop)
        r = requests.delete(f'{BASE_URL}/api/bookings/{bid}', headers=_hdr(tokens['admin']))
        assert r.status_code == 200, r.text
        # verify status changed in DB
        b = _get_booking(event_loop, bid)
        assert b['status'] == 'cancelled'
        # audit log must mention admin override
        audit = b.get('audit_log', [])
        assert any('admin' in (e.get('details', '').lower()) for e in audit), audit

    def test_user_cannot_cancel_others_booking(self, tokens, event_loop):
        bid = _create_user_booking(event_loop)
        # create a second user session distinct from owner
        other_tok = 'testtok_other_' + secrets.token_urlsafe(8)

        async def _ins():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            await db.sessions.insert_one({
                'token': other_tok,
                'user': {'email': 'TEST_other@example.com', 'role': 'user', 'name': 'Other'},
                'expires': datetime.utcnow() + timedelta(hours=2),
            })
            client.close()
        event_loop.run_until_complete(_ins())

        r = requests.delete(f'{BASE_URL}/api/bookings/{bid}', headers=_hdr(other_tok))
        assert r.status_code == 403, r.text


# ============ Admin Edit Override ============
class TestAdminEditOverride:
    def test_admin_can_edit_user_booking_to_far_future(self, tokens, event_loop):
        bid = _create_user_booking(event_loop, date=TOMORROW, start='09:00')
        r = requests.put(
            f'{BASE_URL}/api/bookings/{bid}',
            json={'booking_date': THREE_DAYS, 'start_time': '10:00', 'duration_minutes': 60, 'guests': []},
            headers=_hdr(tokens['admin']),
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body['booking_date'] == THREE_DAYS
        assert body['start_time'] == '10:00'
        # audit must contain override note
        b = _get_booking(event_loop, bid)
        audit_details = ' '.join(e.get('details', '') for e in b.get('audit_log', []))
        assert 'Override by admin' in audit_details, audit_details

    def test_admin_edit_skips_consecutive_day_check(self, tokens, event_loop):
        # owner has another booking on TODAY same slot — consecutive-day would block a regular user
        # We pre-create a TODAY 10:00 booking for the same user (as a fixture)
        existing = _create_user_booking(event_loop, date=TODAY, start='10:00', duration=60)
        target = _create_user_booking(event_loop, date=DAY_AFTER, start='09:00', duration=60)
        # admin tries to move 'target' to TOMORROW 10:00 — that would be consecutive with TODAY 10:00 for the owner
        r = requests.put(
            f'{BASE_URL}/api/bookings/{target}',
            json={'booking_date': TOMORROW, 'start_time': '10:00', 'duration_minutes': 60, 'guests': []},
            headers=_hdr(tokens['admin']),
        )
        assert r.status_code == 200, r.text
        # cleanup helper
        _ = existing

    def test_admin_edit_still_enforces_peak_30min(self, tokens, event_loop):
        bid = _create_user_booking(event_loop, date=TOMORROW, start='09:00', duration=60)
        r = requests.put(
            f'{BASE_URL}/api/bookings/{bid}',
            json={'booking_date': TOMORROW, 'start_time': '18:00', 'duration_minutes': 30, 'guests': []},
            headers=_hdr(tokens['admin']),
        )
        assert r.status_code == 400, r.text
        assert 'peak' in r.json()['detail'].lower()

    def test_user_cannot_edit_others_booking(self, tokens, event_loop):
        bid = _create_user_booking(event_loop)
        other_tok = 'testtok_otheredit_' + secrets.token_urlsafe(8)

        async def _ins():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            await db.sessions.insert_one({
                'token': other_tok,
                'user': {'email': 'TEST_otheredit@example.com', 'role': 'user', 'name': 'Other'},
                'expires': datetime.utcnow() + timedelta(hours=2),
            })
            client.close()
        event_loop.run_until_complete(_ins())

        r = requests.put(
            f'{BASE_URL}/api/bookings/{bid}',
            json={'booking_date': TOMORROW, 'start_time': '11:00', 'duration_minutes': 60, 'guests': []},
            headers=_hdr(other_tok),
        )
        assert r.status_code == 403, r.text


# ============ /manage/bookings ============
class TestManageBookings:
    def test_admin_can_list_all(self, tokens, event_loop):
        _create_user_booking(event_loop, date=TOMORROW, start='09:00')
        r = requests.get(f'{BASE_URL}/api/manage/bookings', headers=_hdr(tokens['admin']))
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # at least the booking we just made should appear
        assert any(b['booked_by_email'] == USER_EMAIL for b in data), [b.get('booked_by_email') for b in data[:5]]

    def test_manage_bookings_date_filter(self, tokens, event_loop):
        _create_user_booking(event_loop, date=TOMORROW, start='09:00')
        _create_user_booking(event_loop, date=TODAY, start='11:00')
        r = requests.get(
            f'{BASE_URL}/api/manage/bookings',
            params={'date_from': TOMORROW, 'date_to': TOMORROW},
            headers=_hdr(tokens['admin']),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        for b in data:
            assert b['booking_date'] == TOMORROW, b

    def test_regular_user_cannot_access_manage(self, tokens):
        r = requests.get(f'{BASE_URL}/api/manage/bookings', headers=_hdr(tokens['user']))
        assert r.status_code == 403, r.text

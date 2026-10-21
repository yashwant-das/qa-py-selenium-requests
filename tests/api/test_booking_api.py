# tests/api/test_booking_api.py
import pytest
from jsonschema import FormatChecker, validate

from src.utils.data_generator import fake
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Schema for a booking object (adjust based on Restful-booker's actual response)
BOOKING_SCHEMA = {
    "type": "object",
    "properties": {
        "firstname": {"type": "string"},
        "lastname": {"type": "string"},
        "totalprice": {"type": "integer"},
        "depositpaid": {"type": "boolean"},
        "bookingdates": {
            "type": "object",
            "properties": {
                "checkin": {"type": "string", "format": "date"},
                "checkout": {"type": "string", "format": "date"},
            },
            "required": ["checkin", "checkout"],
        },
        "additionalneeds": {"type": ["string", "null"]},
    },
    "required": ["firstname", "lastname", "totalprice", "depositpaid", "bookingdates"],
}

# Schema for the POST response which includes bookingid
CREATED_BOOKING_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {"bookingid": {"type": "integer"}, "booking": BOOKING_SCHEMA},
    "required": ["bookingid", "booking"],
}


@pytest.fixture
def authenticated_client(booking_service_client):
    if not booking_service_client.auth_token:
        assert booking_service_client.authenticate(), (
            "API authentication failed. Check BOOKER_USERNAME, BOOKER_PASSWORD, and API connectivity."
        )
    return booking_service_client


@pytest.fixture
def booking_payload():
    return {
        "firstname": fake.first_name(),
        "lastname": fake.last_name(),
        "totalprice": fake.random_int(min=50, max=1000),
        "depositpaid": fake.boolean(),
        "bookingdates": {
            "checkin": fake.date_between(start_date="-1y", end_date="today").strftime("%Y-%m-%d"),
            "checkout": fake.date_between(start_date="today", end_date="+1y").strftime("%Y-%m-%d"),
        },
        "additionalneeds": "Breakfast",
    }


@pytest.fixture
def created_booking(authenticated_client, booking_payload):
    response = authenticated_client.create_booking(booking_payload)
    assert response.status_code == 200, f"Create booking failed: {response.status_code}"
    data = response.json()
    booking_id = data["bookingid"]
    try:
        validate(instance=data, schema=CREATED_BOOKING_RESPONSE_SCHEMA, format_checker=FormatChecker())
        yield booking_id, data["booking"]
    finally:
        # Restful-booker returns 405 for a repeated DELETE; verify absence with GET.
        cleanup = authenticated_client.delete_booking(booking_id)
        if cleanup.status_code != 201:
            remaining = authenticated_client.get_booking_details(booking_id)
            assert remaining.status_code == 404, f"Booking cleanup failed: {cleanup.status_code}"


@pytest.mark.api
@pytest.mark.regression
class TestBookingAPI:
    @pytest.mark.smoke
    def test_health_check(self, booking_service_client):
        response = booking_service_client.health_check()
        assert response.status_code == 201
        assert response.text == "Created"

    @pytest.mark.smoke
    def test_authentication(self, booking_service_client):
        assert booking_service_client.authenticate(), (
            "API authentication failed. Check BOOKER_USERNAME, BOOKER_PASSWORD, and API connectivity."
        )
        assert booking_service_client.auth_token

    @pytest.mark.smoke
    def test_create_booking(self, created_booking, booking_payload):
        booking_id, booking = created_booking
        assert isinstance(booking_id, int)
        assert booking == booking_payload

    def test_get_booking_details(self, booking_service_client, created_booking):
        booking_id, booking = created_booking
        response = booking_service_client.get_booking_details(booking_id)
        assert response.status_code == 200
        validate(instance=response.json(), schema=BOOKING_SCHEMA, format_checker=FormatChecker())
        assert response.json() == booking

    def test_update_booking(self, authenticated_client, created_booking, booking_payload):
        booking_id, _ = created_booking
        payload = {**booking_payload, "firstname": "UpdatedName", "additionalneeds": "Late checkout"}
        response = authenticated_client.update_booking(booking_id, payload)
        assert response.status_code == 200
        assert response.json() == payload
        assert authenticated_client.get_booking_details(booking_id).json() == payload

    def test_partial_update_booking(self, authenticated_client, created_booking):
        booking_id, original = created_booking
        response = authenticated_client.partial_update_booking(booking_id, {"firstname": "PatchedName"})
        assert response.status_code == 200
        expected = {**original, "firstname": "PatchedName"}
        assert response.json() == expected
        assert authenticated_client.get_booking_details(booking_id).json() == expected

    def test_delete_created_booking(self, authenticated_client, created_booking):
        booking_id, _ = created_booking
        response = authenticated_client.delete_booking(booking_id)
        assert response.status_code == 201
        assert authenticated_client.get_booking_details(booking_id).status_code == 404

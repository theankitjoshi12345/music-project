from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from .throttles import OwnerRateThrottle


class TinyOwnerThrottle(OwnerRateThrottle):
    rate = "2/minute"


class OwnerThrottleTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()

    def request(self, subject):
        request = self.factory.get("/api/scores/")
        request.session = {"google_sub": subject}
        return request

    def test_limit_is_scoped_to_verified_google_subject(self):
        throttle = TinyOwnerThrottle()
        self.assertTrue(throttle.allow_request(self.request("alice"), None))
        self.assertTrue(throttle.allow_request(self.request("alice"), None))
        self.assertFalse(throttle.allow_request(self.request("alice"), None))
        self.assertTrue(TinyOwnerThrottle().allow_request(self.request("bob"), None))

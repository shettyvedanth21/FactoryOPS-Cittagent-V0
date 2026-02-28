import pytest
from shared.response import success_response, error_response


class TestResponseEnvelope:
    """Test standard response envelope per LLD §2.2."""
    
    def test_success_response_structure(self):
        """Success response should have correct structure."""
        resp = success_response({"test": "data"})
        
        assert "success" in resp
        assert "data" in resp
        assert "pagination" in resp
        assert "timestamp" in resp
        assert "request_id" in resp
        assert resp["success"] is True
        assert resp["data"] == {"test": "data"}
    
    def test_success_response_with_pagination(self):
        """Success response with pagination should work."""
        resp = success_response(
            data=[1, 2, 3],
            pagination={"page": 1, "limit": 10, "total": 3}
        )
        
        assert resp["pagination"]["page"] == 1
        assert resp["pagination"]["total"] == 3
    
    def test_error_response_structure(self):
        """Error response should have correct structure."""
        resp = error_response("TEST_ERROR", "Test message")
        
        assert "success" in resp
        assert "error" in resp
        assert "timestamp" in resp
        assert "request_id" in resp
        assert resp["success"] is False
        assert resp["error"]["code"] == "TEST_ERROR"
        assert resp["error"]["message"] == "Test message"
    
    def test_error_response_with_details(self):
        """Error response with details should work."""
        resp = error_response(
            "TEST_ERROR",
            "Test message",
            details=[{"field": "value"}]
        )
        
        assert len(resp["error"]["details"]) == 1
    
    def test_timestamp_is_iso_format(self):
        """Timestamp should be in ISO 8601 format."""
        resp = success_response({})
        
        assert "T" in resp["timestamp"]
        assert "+" in resp["timestamp"] or "Z" in resp["timestamp"]
    
    def test_request_id_is_uuid(self):
        """request_id should be a valid UUID."""
        import uuid
        
        resp = success_response({})
        
        uuid.UUID(resp["request_id"])

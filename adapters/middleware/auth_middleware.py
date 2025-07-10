from functools import wraps
from flask import request, jsonify
import requests
import os
from typing import Optional, Dict, Any, Callable

class AuthMiddleware:
    """Middleware for validating JWT tokens"""
    
    def __init__(self, auth_service_url: Optional[str] = None):
        self.auth_service_url = auth_service_url or os.getenv(
            'AUTH_SERVICE_URL', 
            'http://localhost:5001/auth/validate-token'
        )
    
    def _extract_token(self) -> Optional[str]:
        """Extracts the JWT token from the Authorization header"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        # Check that the header follows the "Bearer <token>" format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]
    
    def _validate_token(self, token: str) -> Dict[str, Any]:
        """Validates the token against the authentication service"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                self.auth_service_url,
                headers=headers,
                timeout=5  # 5-second timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"valid": False, "error": f"Auth service returned {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return {"valid": False, "error": f"Auth service unavailable: {str(e)}"}
    
    def require_auth(self, f: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that requires a valid authentication token"""
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Extract token
            token = self._extract_token()
            if not token:
                return jsonify({
                    "error": "Authorization token required",
                    "message": "You must provide a Bearer token in the Authorization header"
                }), 401
            
            # Validate token
            validation_result = self._validate_token(token)
            
            if not validation_result.get("valid", False):
                error_message = validation_result.get("error", "Invalid token")
                return jsonify({
                    "error": "Invalid token",
                    "message": error_message
                }), 401
            
            # Add user info to Flask's global context for later use
            from flask import g
            g.user_id = validation_result.get("user_id")
            g.auth_data = validation_result
            
            return f(*args, **kwargs)
        
        return decorated_function

# Global instance of the middleware
auth_middleware = AuthMiddleware()

# Convenience decorator
def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    """Convenience decorator to require authentication"""
    return auth_middleware.require_auth(f)

from src.services.auth_service.auth import AuthEndpoints

auth_endpoints = AuthEndpoints()
auth_router = auth_endpoints.router

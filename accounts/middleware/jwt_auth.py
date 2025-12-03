class CookieJWTToHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # ❗ Skip Google login endpoint — token is NOT a JWT yet
        if request.path == "/api/accounts/auth/google-login/":
            return self.get_response(request)

        access = request.COOKIES.get("access")
        if access and "authorization" not in request.headers:
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {access}"

        return self.get_response(request)

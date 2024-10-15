from django.contrib import admin

from payment.models import Payment


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "get_user_email",
        "status",
        "type",
        "borrowing",
        "short_session_url",
        "short_session_id",
        "money",
    )
    list_filter = ("borrowing__user__email", "status", "type", "money")
    search_fields = ("borrowing__user__email", "money")

    def get_user_email(self, obj):
        return obj.borrowing.user.email

    get_user_email.short_description = "User Email"

    def short_session_url(self, obj):
        # Return only the first 20 characters of the session URL
        return (
            obj.session_url[:20] + "..."
            if len(obj.session_url) > 20
            else obj.session_url
        )

    def short_session_id(self, obj):
        # Return only the first 20 characters of the session ID
        return (
            obj.session_id[:20] + "..." if len(obj.session_id) > 20 else obj.session_id
        )

    short_session_url.short_description = "Session ID"


admin.site.register(Payment, PaymentAdmin)

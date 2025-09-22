from rest_framework import serializers


class ForecastQuery(serializers.Serializer):
    # OWM query fields
    city = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    lang = serializers.CharField(required=False, default="zh_tw")
    units = serializers.ChoiceField(
        choices=["metric", "imperial"], required=False, default="metric"
    )

    # CWA query fields
    locationName = serializers.CharField(required=False)

    # Provider selector
    provider = serializers.ChoiceField(choices=["owm", "cwa"], required=False)

    def validate(self, attrs):
        provider = attrs.get("provider")

        if provider == "cwa":
            if not attrs.get("locationName"):
                raise serializers.ValidationError(
                    "locationName is required when provider=cwa"
                )
        elif provider == "owm":
            if not attrs.get("city") or not attrs.get("country"):
                raise serializers.ValidationError(
                    "city and country are required when provider=owm"
                )
        else:
            # Provider optional; require at least one supported location input
            has_cwa = bool(attrs.get("locationName"))
            has_owm = bool(attrs.get("city") and attrs.get("country"))
            if not (has_cwa or has_owm):
                raise serializers.ValidationError(
                    "Provide locationName (CWA) or city+country (OWM)."
                )

        return attrs

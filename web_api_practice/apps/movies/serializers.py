from rest_framework import serializers


class MoviesSearchQuery(serializers.Serializer):
    query = serializers.CharField(required=True)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    provider = serializers.ChoiceField(choices=["tmdb", "omdb"], required=False)
    lang = serializers.CharField(required=False, default="zh-TW")

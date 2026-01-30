from rest_framework import serializers
from .models import ScraperJob, ScrapedData

class ScrapedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapedData
        fields = '__all__'

class ScraperJobSerializer(serializers.ModelSerializer):
    data = ScrapedDataSerializer(many=True, read_only=True)

    class Meta:
        model = ScraperJob
        fields = '__all__'
        read_only_fields = ('user', 'status', 'created_at', 'updated_at')

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class TaskStatusView(APIView):
    def get(self, request, task_id):
        # Logic to check task status
        return Response({"task_id": task_id, "status": "PENDING"})

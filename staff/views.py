# staff/views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import StaffService
from .models import StaffProfile, StaffTask


class CreateStaffView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        staff = StaffService.create_staff(request.data)
        return Response({
            "message": "Staff created",
            "staff_id": staff.id,
            "role": staff.role
        }, status=status.HTTP_201_CREATED)


class AssignTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task = StaffService.assign_task(request.data)
        return Response({
            "message": "Task assigned",
            "task_id": task.id
        }, status=status.HTTP_201_CREATED)


class ListStaffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        staff = StaffProfile.objects.values(
            "id", "user__username", "role", "active", "user__email"
        )
        return Response(list(staff))


class ListTasksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = StaffTask.objects.values(
            "id", "title", "status", "staff__user__username", "room__room_number"
        )
        return Response(list(tasks))

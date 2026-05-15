from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import create_audit_log

from .serializers import SafetyReportCreateSerializer, SafetyReportSerializer
from .services import create_safety_report, get_user_reports


class SafetyReportCreateView(APIView):
    def post(self, request):
        serializer = SafetyReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = create_safety_report(
            user=request.user,
            message_id=serializer.validated_data['message_id'],
            category=serializer.validated_data['category'],
            description=serializer.validated_data.get('description', ''),
        )
        create_audit_log(
            user=request.user,
            event_type='safety_report_created',
            request=request,
            object_type='SafetyReport',
            object_id=report.id,
            metadata={'category': report.category},
        )
        return Response(SafetyReportSerializer(report).data, status=status.HTTP_201_CREATED)


class MySafetyReportsView(APIView):
    def get(self, request):
        reports = get_user_reports(request.user)
        return Response(SafetyReportSerializer(reports, many=True).data)

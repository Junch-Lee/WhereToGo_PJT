from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Topic

from .serializers import TopicSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topics(request):
    queryset = Topic.objects.filter(is_active=True).order_by("id")
    serializer = TopicSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

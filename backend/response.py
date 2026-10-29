from rest_framework.response import Response
from rest_framework import status

def success_response(message,success=True, data=None, status_code=status.HTTP_200_OK):
    return Response({
        "success": success,
        "message": message,
        "data": data if data is not None else {}
    }, status=status_code)
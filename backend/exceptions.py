
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, DatabaseError
from django.http import Http404

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import APIException


def custom_exception_handler(exc, context):

    # =========================================================
    # 1. DRF built-in exceptions
    # =========================================================

    response = exception_handler(exc, context)

    if response is not None:

        return Response(
            {
                "success": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": flatten_errors(response.data),
                },
            },
            status=response.status_code,
        )

    # =========================================================
    # 2. Object Does Not Exist / 404
    # =========================================================

    if isinstance(exc, (ObjectDoesNotExist, Http404)):

        return _error_response(
            error_type="NotFound",
            message="Object not found.",
            status_code=404,
        )

    # =========================================================
    # 3. Permission Error
    # =========================================================

    if isinstance(exc, PermissionError):

        return _error_response(
            error_type="PermissionError",
            message="Permission denied.",
            status_code=403,
        )

    # =========================================================
    # 4. Database Integrity Error
    # =========================================================

    if isinstance(exc, IntegrityError):

        return _error_response(
            error_type="IntegrityError",
            message="Database constraint violation.",
            status_code=400,
        )

    # =========================================================
    # 5. General Database Error
    # =========================================================

    if isinstance(exc, DatabaseError):

        return _error_response(
            error_type="DatabaseError",
            message="A database error occurred.",
            status_code=500,
        )

    # =========================================================
    # 6. API Exception fallback
    # =========================================================

    if isinstance(exc, APIException):

        return _error_response(
            error_type=exc.__class__.__name__,
            message=flatten_errors(exc.detail),
            status_code=exc.status_code,
        )

    # =========================================================
    # 7. Unknown Exception
    # =========================================================

    return _error_response(
        error_type="ServerError",
        message="Something went wrong.",
        status_code=500,
    )


# =============================================================
# Standard Error Response
# =============================================================

def _error_response(error_type, message, status_code):

    return Response(
        {
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
            },
        },
        status=status_code,
    )


# =============================================================
# Flatten Validation Errors
# =============================================================

def flatten_errors(errors):

    messages = []

    # Dictionary
    if isinstance(errors, dict):

        for field, value in errors.items():

            if isinstance(value, dict):

                nested_message = flatten_errors(value)

                if nested_message:
                    messages.append(nested_message)

            elif isinstance(value, list):

                for item in value:

                    if isinstance(item, dict):

                        nested_message = flatten_errors(item)

                        if nested_message:
                            messages.append(nested_message)

                    else:
                        messages.append(str(item))

            else:

                messages.append(str(value))

    # List
    elif isinstance(errors, list):

        for item in errors:

            if isinstance(item, dict):

                nested_message = flatten_errors(item)

                if nested_message:
                    messages.append(nested_message)

            else:

                messages.append(str(item))

    # String / Other
    else:

        messages.append(str(errors))

    return "; ".join(messages)
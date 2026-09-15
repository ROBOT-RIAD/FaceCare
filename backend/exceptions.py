
# import logging
# #
# from django.core.exceptions import ObjectDoesNotExist
# from django.conf import settings
# from django.db import IntegrityError, DatabaseError
# from django.http import Http404

# from rest_framework.views import exception_handler
# from rest_framework.response import Response
# from rest_framework.exceptions import APIException


# logger = logging.getLogger(__name__)


# def custom_exception_handler(exc, context):

#     # =========================================================
#     # 1. DRF built-in exceptions
#     # =========================================================

#     response = exception_handler(exc, context)

#     if response is not None:

#         return Response(
#             {
#                 "success": False,
#                 "error": {
#                     "type": exc.__class__.__name__,
#                     "message": flatten_errors(response.data),
#                 },
#             },
#             status=response.status_code,
#         )

#     # =========================================================
#     # 2. Object Does Not Exist / 404
#     # =========================================================

#     if isinstance(exc, (ObjectDoesNotExist, Http404)):

#         return _error_response(
#             error_type="NotFound",
#             message="Object not found.",
#             status_code=404,
#         )

#     # =========================================================
#     # 3. Permission Error
#     # =========================================================

#     if isinstance(exc, PermissionError):

#         return _error_response(
#             error_type="PermissionError",
#             message="Permission denied.",
#             status_code=403,
#         )

#     # =========================================================
#     # 4. Database Integrity Error
#     # =========================================================

#     if isinstance(exc, IntegrityError):

#         logger.exception(
#                 "DATABASE INTEGRITY ERROR in %s",
#                 context.get("view").__class__.__name__
#                 if context.get("view")
#                 else "unknown view",
#             )

#         return _error_response(
#             error_type="IntegrityError",
#             message="Database constraint violation.",
#             status_code=400,
#         )

#     # =========================================================
#     # 5. General Database Error
#     # =========================================================

#     if isinstance(exc, DatabaseError):

#         logger.exception(
#             "DATABASE ERROR in %s",
#             context.get("view").__class__.__name__
#             if context.get("view")
#             else "unknown view",
#         )

#         return _error_response(
#             error_type="DatabaseError",
#             message="A database error occurred.",
#             status_code=500,
#         )

#     # =========================================================
#     # 6. API Exception fallback
#     # =========================================================

#     if isinstance(exc, APIException):

#         return _error_response(
#             error_type=exc.__class__.__name__,
#             message=flatten_errors(exc.detail),
#             status_code=exc.status_code,
#         )

#     # =========================================================
#     # 7. Unknown Exception
#     # =========================================================

#     view = context.get("view")
#     logger.exception(
#         "Unhandled exception in %s",
#         view.__class__.__name__ if view else "unknown view",
#         exc_info=exc,
#     )

#     if settings.DEBUG:
#         return _error_response(
#             error_type=exc.__class__.__name__,
#             message=str(exc),
#             status_code=500,
#         )

#     return _error_response(
#         error_type="ServerError",
#         message="Something went wrong.",
#         status_code=500,
#     )


# # =============================================================
# # Standard Error Response
# # =============================================================

# def _error_response(error_type, message, status_code):

#     return Response(
#         {
#             "success": False,
#             "error": {
#                 "type": error_type,
#                 "message": message,
#             },
#         },
#         status=status_code,
#     )


# # =============================================================
# # Flatten Validation Errors
# # =============================================================

# def flatten_errors(errors):

#     messages = []

#     # Dictionary
#     if isinstance(errors, dict):

#         for field, value in errors.items():

#             if isinstance(value, dict):

#                 nested_message = flatten_errors(value)

#                 if nested_message:
#                     messages.append(nested_message)

#             elif isinstance(value, list):

#                 for item in value:

#                     if isinstance(item, dict):

#                         nested_message = flatten_errors(item)

#                         if nested_message:
#                             messages.append(nested_message)

#                     else:
#                         messages.append(str(item))

#             else:

#                 messages.append(str(value))

#     # List
#     elif isinstance(errors, list):

#         for item in errors:

#             if isinstance(item, dict):

#                 nested_message = flatten_errors(item)

#                 if nested_message:
#                     messages.append(nested_message)

#             else:

#                 messages.append(str(item))

#     # String / Other
#     else:

#         messages.append(str(errors))

#     return "; ".join(messages)



import logging

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import IntegrityError, DatabaseError
from django.http import Http404

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import APIException


logger = logging.getLogger(__name__)


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

    # if isinstance(exc, IntegrityError):

    #     view = context.get("view")

    #     logger.exception(
    #         "DATABASE INTEGRITY ERROR in %s",
    #         view.__class__.__name__ if view else "unknown view",
    #     )

    #     # -----------------------------------------------------
    #     # PostgreSQL diagnostic information
    #     # -----------------------------------------------------

    #     cause = getattr(exc, "__cause__", None)
    #     diag = getattr(cause, "diag", None)

    #     sqlstate = getattr(diag, "sqlstate", None)
    #     constraint_name = getattr(diag, "constraint_name", None)
    #     table_name = getattr(diag, "table_name", None)
    #     column_name = getattr(diag, "column_name", None)

    #     # -----------------------------------------------------
    #     # PostgreSQL UNIQUE violation
    #     # SQLSTATE: 23505
    #     # -----------------------------------------------------

    #     if sqlstate == "23505":

    #         constraint_messages = {

    #             # User email
    #             "account_user_email_key":
    #                 "Email is already in use.",

    #             # Profile OneToOne
    #             "account_profile_user_id_key":
    #                 "Profile already exists for this user.",

    #             # Cloudinary public ID
    #             "account_profile_cloudinary_public_id_key":
    #                 "This Cloudinary image is already associated with another profile.",
    #         }

    #         message = constraint_messages.get(
    #             constraint_name
    #         )

    #         # -------------------------------------------------
    #         # Known constraint
    #         # -------------------------------------------------

    #         if message:

    #             return _error_response(
    #                 error_type="ValidationError",
    #                 message=message,
    #                 status_code=400,
    #             )

    #         # -------------------------------------------------
    #         # Unknown UNIQUE constraint
    #         # -------------------------------------------------

    #         if column_name:

    #             return _error_response(
    #                 error_type="ValidationError",
    #                 message=(
    #                     f"{column_name.replace('_', ' ').capitalize()} "
    #                     "already exists."
    #                 ),
    #                 status_code=400,
    #             )

    #         return _error_response(
    #             error_type="ValidationError",
    #             message="A value already exists.",
    #             status_code=400,
    #         )

    #     # -----------------------------------------------------
    #     # PostgreSQL FOREIGN KEY violation
    #     # SQLSTATE: 23503
    #     # -----------------------------------------------------

    #     if sqlstate == "23503":

    #         return _error_response(
    #             error_type="ValidationError",
    #             message="Related object does not exist.",
    #             status_code=400,
    #         )

    #     # -----------------------------------------------------
    #     # PostgreSQL NOT NULL violation
    #     # SQLSTATE: 23502
    #     # -----------------------------------------------------

    #     if sqlstate == "23502":

    #         if column_name:

    #             return _error_response(
    #                 error_type="ValidationError",
    #                 message=(
    #                     f"{column_name.replace('_', ' ').capitalize()} "
    #                     "is required."
    #                 ),
    #                 status_code=400,
    #             )

    #         return _error_response(
    #             error_type="ValidationError",
    #             message="A required field is missing.",
    #             status_code=400,
    #         )

    #     # -----------------------------------------------------
    #     # PostgreSQL CHECK constraint violation
    #     # SQLSTATE: 23514
    #     # -----------------------------------------------------

    #     if sqlstate == "23514":

    #         return _error_response(
    #             error_type="ValidationError",
    #             message="Invalid value.",
    #             status_code=400,
    #         )

    #     # -----------------------------------------------------
    #     # Other IntegrityError
    #     # -----------------------------------------------------

    #     return _error_response(
    #         error_type="IntegrityError",
    #         message="Database constraint violation.",
    #         status_code=400,
    #     )
    if isinstance(exc, IntegrityError):

        view = context.get("view")

        logger.exception(
            "DATABASE INTEGRITY ERROR in %s",
            view.__class__.__name__ if view else "unknown view",
        )

        cause = getattr(exc, "__cause__", None)
        diag = getattr(cause, "diag", None)

        sqlstate = getattr(diag, "sqlstate", None)
        constraint_name = getattr(diag, "constraint_name", None)
        table_name = getattr(diag, "table_name", None)
        column_name = getattr(diag, "column_name", None)

        # -----------------------------------------------------
        # PostgreSQL UNIQUE violation (23505)
        # -----------------------------------------------------
        if sqlstate == "23505":

            # 1. Known constraints (highest priority)
            known_messages = {
                "account_user_email_key": "Email is already in use.",
                "account_profile_user_id_key": "Profile already exists for this user.",
                "account_profile_cloudinary_public_id_key": "This Cloudinary image is already associated with another profile.",
            }

            if constraint_name in known_messages:
                return _error_response(
                    error_type="ValidationError",
                    message=known_messages[constraint_name],
                    status_code=400,
                )

            # 2. Dynamic message based on column_name (most reliable fallback)
            if column_name:
                human_column = column_name.replace("_", " ").capitalize()
                return _error_response(
                    error_type="ValidationError",
                    message=f"{human_column} already exists.",
                    status_code=400,
                )

            # 3. Dynamic message based on constraint_name (good fallback)
            if constraint_name:
                # Try to extract meaningful name from constraint
                # e.g. "account_user_email_key" → "Email"
                # e.g. "account_profile_user_id_key" → "User id"
                name = constraint_name

                # Remove common suffixes
                for suffix in ["_key", "_uniq", "_unique", "_idx"]:
                    if name.endswith(suffix):
                        name = name[: -len(suffix)]
                        break

                # Take the last meaningful part
                parts = name.split("_")
                if len(parts) >= 2:
                    human_name = parts[-1].replace("_", " ").capitalize()
                else:
                    human_name = name.replace("_", " ").capitalize()

                return _error_response(
                    error_type="ValidationError",
                    message=f"{human_name} already exists.",
                    status_code=400,
                )

            # 4. Ultimate fallback
            return _error_response(
                error_type="ValidationError",
                message="A value already exists.",
                status_code=400,
            )

        # -----------------------------------------------------
        # FOREIGN KEY (23503)
        # -----------------------------------------------------
        if sqlstate == "23503":
            return _error_response(
                error_type="ValidationError",
                message="Related object does not exist.",
                status_code=400,
            )

        # -----------------------------------------------------
        # NOT NULL (23502)
        # -----------------------------------------------------
        if sqlstate == "23502":
            if column_name:
                human_column = column_name.replace("_", " ").capitalize()
                return _error_response(
                    error_type="ValidationError",
                    message=f"{human_column} is required.",
                    status_code=400,
                )
            return _error_response(
                error_type="ValidationError",
                message="A required field is missing.",
                status_code=400,
            )

        # -----------------------------------------------------
        # CHECK constraint (23514)
        # -----------------------------------------------------
        if sqlstate == "23514":
            return _error_response(
                error_type="ValidationError",
                message="Invalid value.",
                status_code=400,
            )

        # -----------------------------------------------------
        # Other IntegrityError
        # -----------------------------------------------------
        return _error_response(
            error_type="IntegrityError",
            message="Database constraint violation.",
            status_code=400,
        )
    # =========================================================
    # 5. General Database Error
    # =========================================================

    # if isinstance(exc, DatabaseError):

    #     view = context.get("view")

    #     logger.exception(
    #         "DATABASE ERROR in %s",
    #         view.__class__.__name__ if view else "unknown view",
    #     )

    #     error_type = exc.__class__.__name__

    #     database_messages = {
    #         "OperationalError": "Database service is temporarily unavailable.",
    #         "ProgrammingError": "A database operation could not be completed.",
    #         "DataError": "Invalid data was provided for the database.",
    #         "NotSupportedError": "This database operation is not supported.",
    #         "InternalError": "An internal database error occurred.",
    #     }

    #     message = database_messages.get(
    #         error_type,
    #         "A database error occurred."
    #     )

    #     return _error_response(
    #         error_type="DatabaseError",
    #         message=message,
    #         status_code=500,
    #     )

    # 
    # 

    if isinstance(exc, DatabaseError):

        view = context.get("view")

        logger.exception(
            "DATABASE ERROR in %s",
            view.__class__.__name__ if view else "unknown view",
        )

        error_type = exc.__class__.__name__
        error_message = str(exc).lower()

        # -------------------------------------------------
        # Specific OperationalError messages
        # -------------------------------------------------
        if error_type == "OperationalError":

            if "too many clients" in error_message:
                return _error_response(
                    error_type="DatabaseError",
                    message="Database is currently overloaded. Please try again in a moment.",
                    status_code=503,  # Service Unavailable
                )

            if "connection" in error_message and (
                "refused" in error_message
                or "not accepting" in error_message
                or "is the server running" in error_message
            ):
                return _error_response(
                    error_type="DatabaseError",
                    message="Database service is temporarily unavailable.",
                    status_code=503,
                )

            if "timeout" in error_message:
                return _error_response(
                    error_type="DatabaseError",
                    message="Database connection timed out. Please try again.",
                    status_code=504,  # Gateway Timeout
                )

            # Default for other OperationalError
            return _error_response(
                error_type="DatabaseError",
                message="Database service is temporarily unavailable.",
                status_code=503,
            )

    # -------------------------------------------------
    # Other DatabaseError types
    # -------------------------------------------------
    database_messages = {
        "ProgrammingError": "A database operation could not be completed.",
        "DataError": "Invalid data was provided for the database.",
        "NotSupportedError": "This database operation is not supported.",
        "InternalError": "An internal database error occurred.",
    }

    message = database_messages.get(
        error_type,
        "A database error occurred."
    )

    return _error_response(
        error_type="DatabaseError",
        message=message,
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

    view = context.get("view")

    logger.exception(
        "Unhandled exception in %s",
        view.__class__.__name__ if view else "unknown view",
        exc_info=exc,
    )

    if settings.DEBUG:

        return _error_response(
            error_type=exc.__class__.__name__,
            message=str(exc),
            status_code=500,
        )

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

    # ---------------------------------------------------------
    # Dictionary
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # List
    # ---------------------------------------------------------

    elif isinstance(errors, list):

        for item in errors:

            if isinstance(item, dict):

                nested_message = flatten_errors(item)

                if nested_message:
                    messages.append(nested_message)

            else:
                messages.append(str(item))

    # ---------------------------------------------------------
    # String / Other
    # ---------------------------------------------------------

    else:

        messages.append(str(errors))

    return "; ".join(messages)
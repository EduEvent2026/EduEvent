from fastapi import status


class AppException(Exception):
    """Bazowy wyjątek aplikacyjny gwarantujący spójny format błędu JSON."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


# Stabilne błędy domenowe dla Modułu 4
def registration_duplicate_error() -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="REGISTRATION_DUPLICATE",
        message="Już jesteś zapisany na to wydarzenie",
    )


def registration_already_cancelled_error() -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="REGISTRATION_ALREADY_CANCELLED",
        message="Ten zapis został już wcześniej anulowany",
    )


def registration_not_found_error() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code="REGISTRATION_NOT_FOUND",
        message="Zapis nie istnieje lub nie masz do niego dostępu",
    )


def event_not_found_error() -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code="EVENT_NOT_FOUND",
        message="Wybrane wydarzenie nie istnieje",
    )


def event_capacity_exceeded_error() -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="EVENT_CAPACITY_EXCEEDED",
        message="Brak wolnych miejsc na liście głównej wydarzenia",
    )


def external_service_error(service_name: str) -> AppException:
    return AppException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="EXTERNAL_SERVICE_UNAVAILABLE",
        message=f"Błąd komunikacji z zewnętrznym modułem: {service_name}",
    )


def unauthorized_error(message: str = "Brak ważnego tokenu uwierzytelniającego") -> AppException:
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="UNAUTHORIZED",
        message=message,
    )


def forbidden_error(message: str = "Brak uprawnień do wykonania tej operacji") -> AppException:
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code="FORBIDDEN",
        message=message,
    )
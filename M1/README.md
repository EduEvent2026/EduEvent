# Moduł 1
Mikroserwis obłusujący rejestacje, logowanie i zarządzanie użytkownikami

## Endpointy

| Metoda | Ścieżka | Dostęp | Opis |
|---|---|---|---|
| GET | `/health` | publiczny | sprawdzenie, czy usługa działa |
| GET | `/me` | zalogowany | profil zalogowanego użytkownika |
| PUT | `/me` | zalogowany | edycja profilu (email, imię, nazwisko) |
| GET | `/admin/users` | rola `admin` | lista użytkowników (`offset`, `limit`) |
| GET | `/admin/users/{id}` | rola `admin` | dane użytkownika wraz z rolami |
| POST | `/admin/users/{id}/block` | rola `admin` | zablokowanie konta i zakończenie jego sesji |
| PUT | `/admin/users/{id}/roles/{rola}` | rola `admin` | przypisanie roli (`admin` lub `user`) |
| DELETE | `/admin/users/{id}/roles/{rola}` | rola `admin` | odebranie roli |
| POST | `/admin/users/{id}/reset-password` | rola `admin` | wysłanie użytkownikowi maila z resetem hasła |

## Uruchomienie
```aiignore
docker compose up -d mysql keycloak
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
| Usługa | Adres |
|---|---|
| Swagger (backend) | http://localhost:8000/docs |
| Panel Keycloaka | http://localhost:8080 (login i hasło z `KEYCLOAK_ADMIN` i `KEYCLOAK_ADMIN_PASSWORD` w `.env`) |
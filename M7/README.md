# Moduł 7: Powiadomienia (In-App)

Mikroserwis obsługujący powiadomienia In-App oraz cykliczne przypomnienia dla systemu EduEvent.

## Endpointy
- `GET /notifications/history` – pobranie historii powiadomień użytkownika 
- `PATCH /notifications/{id}/read` – oznaczenie powiadomienia jako przeczytane 
- `DELETE /notifications/{id}` – usunięcie powiadomienia z historii 
- `POST /notifications` – obsługa zdarzeń z Modułu 4  oraz Modułu 2

## Uruchomienie
```bash
cp .env.example .env
docker compose up --build
# EduEvent — Moduł 5: Kalendarz i harmonogram wydarzeń

Mikroserwis przygotowujący dane wydarzeń do widoku kalendarza i harmonogramu (widok dzienny, tygodniowy oraz miesięczny) oraz filtrujący wydarzenia według zakresu dat.

## Założenia architektoniczne
* **Brak własnej bazy danych:** moduł wyłącznie odczytuje wydarzenia z Modułu 2 (`IEventsAPI`) przez REST API (JSON).
* **Dostęp publiczny:** API kalendarza nie wymaga logowania ani tokenów (dostępne dla Uczestnika, Organizatora i Gościa).
* **Architektura warstwowa:** `CalendarController` (endpointy REST i walidacja dat) -> `CalendarService` (wyliczanie zakresu, grupowanie po dniach w strefie `Europe/Warsaw`, sortowanie) -> `EventsApiClient` (komunikacja HTTP z Modułem 2 z obsługą paginacji).

## Struktura katalogu
```text
M5/
├── app/
│   ├── __init__.py
│   ├── main.py          # Punkt startowy FastAPI (CORS, router, obsługa błędów, pliki statyczne)
│   ├── controller.py    # ICalendarAPI, CalendarController, router /api/calendar oraz obsługa błędów
│   ├── service.py       # CalendarService (zakresy dat, grupowanie po dniach, puste dni, sortowanie)
│   ├── client.py        # EventsApiClient (pobieranie wydarzeń z Modułu 2 + tryb mocka)
│   ├── interfaces.py    # Kontrakt IEventsAPI
│   ├── models.py        # ViewType, Event, CalendarDay, CalendarView (serializacja JSON)
│   └── static/
│       ├── calendar.js  # Komponent frontendowy (mountCalendar)
│       └── test.html    # Przykładowa strona testowa kalendarza
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── readme.md
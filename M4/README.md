# EduEvent – Moduł 4: Zapisy i lista rezerwowa (`IRegistrationsAPI`)

Mikroserwis obsługuje zapisy na wydarzenia, kontrolę limitu miejsc, zapobieganie duplikatom, obsługę kolejki rezerwowej (FIFO po `createdAt`), rezygnacje oraz automatyczne przesuwanie uczestników na listę główną.

## Uruchomienie lokalne

1. Utwórz bazę w MySQL:
   ```sql
   CREATE DATABASE eduevent_registrations CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
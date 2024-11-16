
## Setup

Husk at have docker oppe og køre.

hente repo ned til din lokale computer.

ved første gang du køre projektet køre `docker compose up -d --build` i vs code terminal
efter følgende start container fra docker GUI eller køre `docker compose up -d` i ternimal


Besøg `http://localhost:3000/docs` for at se API i vores database VIA Swagger UI.


## Black Formatter til Python

1. Hent Black Formatter fra vs code extension.
2. Gå til "View" -> "Command Palette" og så efter "Preferences: Open User Settings (JSON)"
3. Copy & Paste `"[python]": {
    "editor.formatOnPaste": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },` ind i settings.json filen som nu skulle være åben. Genstart Vs code
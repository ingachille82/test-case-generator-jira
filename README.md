Il presente progetto è destinato ai functional tester che scrivono scenari in file con estensione .feature
L'applicativo consente il caricamento in Atlassian Jira degli scenari presenti nel feature, linkandoli ad una specifica Storia/Task o generico Item Jira. 
I file devono essere scritti con sintassi Gherkin (Give, When, Then).
Oltre a caricare gli scenari, è possibile aggiungere e/o aggiornare le label presenti nell'item Jira. Al momento dell'upload verranno letti i tag presenti sullo scenario e trasformati in label.

-----------------------------------------------------
1. CONFIGURAZIONE INIZIALE (una volta sola)
-----------------------------------------------------

1a. Crea il file .env nella cartella test-cases-generator-main
    con il seguente contenuto:

    JIRA_BASE_URL=https://ingachille82-testing-gherkin-upload.atlassian.net
    JIRA_TOKEN=Basic <IL_TUO_BASE64>
    JIRA_PROJECT_KEY=SCRUM
    JIRA_TEST_ISSUE_TYPE=Task
    JIRA_LINK_TYPE=Blocks
    PORT=3000

    Nota: sostituisci <IL_TUO_BASE64> con il valore generato
    al punto 1b qui sotto.

1b. Genera il Base64 (nel terminale 2, un comando alla volta):

    $base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("ingachille82@yahoo.it:IL_TUO_API_TOKEN"))
    Write-Host $base64

    Copia l'output e incollalo nel file .env come valore di JIRA_TOKEN
    nel formato: Basic <output>

    Nota: genera un nuovo API Token su
    https://id.atlassian.com/manage-profile/security/api-tokens

1c. Installa le dipendenze (nel terminale 1):

    npm install dotenv

-----------------------------------------------------
2. AVVIO DEL SERVER
-----------------------------------------------------

Nel Terminale 1 di VS Code, dalla cartella test-cases-generator-main:

  npm start

Il server è attivo quando vedi:
  Gherkin→Jira API listening on port 3000

  Nota: non servono più le variabili $env: grazie al file .env

-----------------------------------------------------
3. CHIAMATA API (Terminale 2)
-----------------------------------------------------

Comando 1 - Leggi il feature file:
  $feature = Get-Content -Raw "example\persons.feature"

Comando 2 - Costruisci il body:
  $body = ConvertTo-Json -Depth 5 @{ userStoryKey = "SCRUM-2"; gherkinContent = [string]$feature }

Comando 3 - Lancia la chiamata:
  Invoke-RestMethod -Uri "http://localhost:3000/api/gherkin-to-jira" -Method POST -ContentType "application/json" -Body $body

-----------------------------------------------------
4. VERIFICA
-----------------------------------------------------

Health check del server:
  Invoke-RestMethod -Uri "http://localhost:3000/health"

Verifica autenticazione Jira:
  Invoke-RestMethod -Uri "https://ingachille82-testing-gherkin-upload.atlassian.net/rest/api/3/myself" -Headers @{ Authorization = "Basic $base64"; Accept = "application/json" }



- Il server va riavviato ogni volta che si apre VS Code
- Le variabili $feature e $body vanno ricostruite
  ogni volta che si apre un nuovo terminale
- Per cambiare User Story, modifica il valore "userStoryKey"
  nel Comando 2 della sezione 3
- Per usare un file .feature diverso, modifica il percorso
  nel Comando 1 della sezione 3
- Quando il token Jira scade, aggiorna solo JIRA_TOKEN nel file .env
  e riavvia il server

=====================================================

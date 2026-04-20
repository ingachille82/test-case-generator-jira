This project is intended for functional testers who write scenarios in files with the .feature extension.
The application allows uploading scenarios from a feature file to Atlassian Jira, linking them to a specific Story/Task or generic Jira item.
Files must be written using Gherkin syntax (Given, When, Then).
In addition to uploading scenarios, it is possible to add and/or update labels on the Jira item. During upload, the tags present on the scenario will be read and converted into labels.

-----------------------------------------------------
1. INITIAL SETUP (one time only)
-----------------------------------------------------

1a. Create the .env file in the test-cases-generator-main folder
    with the following content:

    JIRA_BASE_URL=https://ingachille82-testing-gherkin-upload.atlassian.net
    JIRA_TOKEN=Basic <YOUR_BASE64>
    JIRA_PROJECT_KEY=SCRUM
    JIRA_TEST_ISSUE_TYPE=Task
    JIRA_LINK_TYPE=Blocks
    PORT=3000

    Note: replace <YOUR_BASE64> with the value generated
    in step 1b below.

1b. Generate the Base64 (in terminal 2, one command at a time):

    $base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("ingachille82@yahoo.it:YOUR_API_TOKEN"))
    Write-Host $base64

    Copy the output and paste it into the .env file as the value of JIRA_TOKEN
    in the format: Basic <output>

    Note: generate a new API Token at
    https://id.atlassian.com/manage-profile/security/api-tokens

1c. Install dependencies (in terminal 1):

    npm install dotenv

-----------------------------------------------------
2. STARTING THE SERVER
-----------------------------------------------------

In VS Code Terminal 1, from the test-cases-generator-main folder:

  npm start

The server is running when you see:
  Gherkin→Jira API listening on port 3000

  Note: $env: variables are no longer needed thanks to the .env file

-----------------------------------------------------
3. API CALL (Terminal 2)
-----------------------------------------------------

Command 1 - Read the feature file:
  $feature = Get-Content -Raw "example\persons.feature"

Command 2 - Build the request body:
  $body = ConvertTo-Json -Depth 5 @{ userStoryKey = "SCRUM-2"; gherkinContent = [string]$feature }

Command 3 - Send the request:
  Invoke-RestMethod -Uri "http://localhost:3000/api/gherkin-to-jira" -Method POST -ContentType "application/json" -Body $body

-----------------------------------------------------
4. VERIFICATION
-----------------------------------------------------

Server health check:
  Invoke-RestMethod -Uri "http://localhost:3000/health"

Jira authentication check:
  Invoke-RestMethod -Uri "https://ingachille82-testing-gherkin-upload.atlassian.net/rest/api/3/myself" -Headers @{ Authorization = "Basic $base64"; Accept = "application/json" }

-----------------------------------------------------
NOTES
-----------------------------------------------------

- The server must be restarted every time VS Code is opened
- The $feature and $body variables must be rebuilt
  every time a new terminal is opened
- To change the User Story, update the "userStoryKey" value
  in Command 2 of section 3
- To use a different .feature file, update the path
  in Command 1 of section 3
- When the Jira token expires, update only JIRA_TOKEN in the .env file
  and restart the server

=====================================================

=====================================================

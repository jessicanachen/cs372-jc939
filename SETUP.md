# Setup

## Testing the System - Deployment

The easiest way to test the system is to test the deployment on the web app. This web app already has the project running and connected to the external APIs and services for the backend. 

The web app can be accessed here: https://cs372-jc939.vercel.app
You can also directly access and call the backend endpoints directly here: https://pokepedai-backend-api-405120827006.us-east1.run.app/docs (docs gives you a way to call the chat endpoint inside the web without having to curl/call it with some other application).

Just a note about timing, for this project, the default amount of containers allocated to running the backend is 0, thus on first query, 

## Testing the System - Locally

Unfortunately, local deployment will require you to have an open ai api key. The only additional thing you have to do is in the root make a new file called `.env` with the single line `OPENAI_API_KEY=sk-proj-` with the API key. (This has to be done in order to keep the project compliant with basic security. If a api key cannot be provided the deployment still provides a way to test the system in general.)

Once this is done, the only thing to do is to ensure you have Docker opened and installed, cd into this project root file and run `docker compose up --build`. The frontend and backend will be connected automatically in the api calls as long as you are using the ports pre specified in the docker file. (If you change the Docker backend ports at all, you will also in the frontend have to update `/pokepedai-frontend/lib/config.ts` to the appropriate port). If the ports are not changed, the frontend site can be found on http://localhost:3000 and the backend can be queried on http://0.0.0.0:8080/docs.
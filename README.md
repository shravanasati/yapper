# yapper

For running you need a 

- `.env` file: with `GEMINI_API_KEY`.

- `gameplays/` folder with random gameplays

- `cookies.txt` from a browser, ideally firefox on windows. obtain them using this command: 

	```
	yt-dlp --cookies-from-browser firefox --cookies cookies.txt
	```

- `client_secrets.json` from Google Cloud Console, create project > enable youtube data API v3 > OAuth Consent screen > create OAuth Client for desktop > download JSON credentials.

- dependencies
	```
	poetry install
	```

- run the script
	```
	python main.py
	```
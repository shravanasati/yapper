# yapper

For running you need a 

- `.env` file: with `GEMINI_API_KEY`.

- `gameplays/` folder with random gameplays

- `cookies.txt` from a browser, ideally firefox on windows. obtain them using this command: 

	```
	yt-dlp --cookies-from-browser firefox --cookies cookies.txt
	```

- dependencies
	```
	poetry install
	```

- run the script
	```
	python main.py
	````
Site generator for [feeds.code-drill.eu](http://feeds.code-drill.eu/) based on https://getnikola.com/
- pre requirements:
  - manual setup
    - create python venv  `uv sync`

- generate content:
  ```
  cd til.code-drill.eu
  nikola new_post -d --format pandoc
  
  # optionally commit new md file
  gcnow "PUT COMMIT MESSAGE HERE"

  ```
- build site/html:
  ```
  cd feeds.code-drill.eu
  nikola build
  ```

- fetch content and build site/html:
  ```
  cmd-build.cmd
  ```

- deploy content:
  ```
  cmd-push.cmd
  ```
  
- to change theme:
  ```
  nikola theme -l
  nikola theme -i NAME
  ```

- generate content from source:
  - for today
```shell
# activate venv under .venv
uv run python generate_blog_posts.py
```
  - for selected dates
```shell
# activate venv under .venv
uv run python generate_blog_posts.py 2025-08-25 2025-08-26 2025-08-27
```
or when parent os is windows
  - for today
```shell
# activate venv under .venv
uv run python generate_blog_posts.py
```
  - for selected dates
```shell
# activate venv under .venv
uv run python generate_blog_posts.py 2025-08-25 2025-08-26 2025-08-27
```

*** start web server ***
```shell
python -m http.server 9106 --bind 127.0.0.1 --directory feeds.code-drill.eu\output
```
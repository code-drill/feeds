Site generator for [feeds.code-drill.eu](http://feeds.code-drill.eu/) based on https://getnikola.com/
- pre requirements:
  - manual setup
    - create python venv  `uv sync`
  - automatic
    - docker
    - run `run-bash.cmd`

- generate content:
  ```
  cd til.code-drill.eu
  nikola new_post -d --format pandoc
  
  # optionally commit new md file
  gcnow "PUT COMMIT MESSAGE HERE"

  ```
- build site/html:
  ```
  nikola build
  ```

- deploy content:
  ```
  cd output
  open index.html
  gcnow "PUT COMMIT MESSAGE HERE"
  git push -u origin main
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
uv run --active python generate_blog_posts.py
```
  - for selected dates
```shell
# activate venv under .venv
uv run --active python generate_blog_posts.py 2025-08-25 2025-08-26 2025-08-27
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
uv run --active python generate_blog_posts.py 2025-08-25 2025-08-26 2025-08-27
```

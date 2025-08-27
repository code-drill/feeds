Site generator for [til.code-drill.eu](http://til.code-drill.eu/) based on https://getnikola.com/
- pre requirements:
  - manual setup
    - create python venv  `python -m venv .venv`
    - install requirements: `pip install -r requirements-win.txt` 
  - automatic
    - docker
    - run `run-bash.cmd`

- generate content:
  ```
  cd til.code-drill.eu
  nikola new_post -d --format pandoc
  # or
  ./new_post.bsh
  
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
  nkiola theme -i NAME
  ```

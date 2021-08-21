# Development
This is for contributors or developers of the project.

- First, install the package then try to run tests.
  ```bash
  # install dependencies from lock file
  poetry install

  # run checks and tests
  poetry run flake8 .
  poetry run isort .
  poetry run pytest
  ```

- Whether working on a feature or a bug fix, write meaningful test(s) that fail.
- Work on the code change
- Pass the test(s)
- Review your own work
- When you are happy, open a Pull Request and ask for review :)

### Make a Release
For the owner and contributors, when the time comes, we use github Release (and Actions)
to publish the package to PyPI.

- In the Release page, start by "Draft a new release"
- We use semantic versioning and prefix with the letter "v", e.g. "v0.1.7"
- Choose the target branch (usually `main`) and write a meaningful Release title and description
- Click on "Publish release" to trigger the CI to automatically publish the package to PyPI

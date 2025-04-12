Thanks a lot for you interest.

If you have ideas for improvements or want to contribute additional features, such as working on the speech recognition part so that it understands young children, etc. Your contributions are very welcome.

# PRs are welcome!

### Fork [this repository](https://github.com/twaclaw/canismajor.git)

Click the "Fork" button on the top-right corner of the repository page to create a copy of the repository under your GitHub account.

### Clone your forked repository to your local machine:

```bash
git clone https://github.com/your-username/canismajor.git
cd canismajor
```

### Set Upstream Remote

Add the original repository as an upstream remote to keep your fork in sync:

```bash
git remote add upstream https://github.com/twaclaw/canismajor.git
```

### Create a new branch for your changes

For example:

```bash
git checkout -b feature/your-feature-name
```

### Install the application

```bash
uv venv venv --python 3.13 # or 3.11 or 3.12
. venv/bin/activate
uv pip install -e ".[dev]"
```

### Make changes

- Make your changes or additions to the codebase.
- Test your changes locally to ensure they work as expected. This tiny project doesn't have automated tests, so the tests are exploratory.
- Kindly, run `pre-commit`
- Commit your changes
- Push your changes to your forked repository


### Create a Pull Request

- Go to the original repository on GitHub.
- Follow the [instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) to create a pull request.

---

### Keep Your Fork Updated

Periodically sync your fork with the original repository to stay up-to-date:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

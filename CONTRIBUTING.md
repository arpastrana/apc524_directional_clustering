# Contributing

Contributions are welcome and very much appreciated!

## Code contributions

We accept code contributions through pull requests.
In short, this is how that works.

1. Fork [the repository](https://github.com//directional_clustering) and clone
   the fork.

2. Create a virtual environment using your tool of choice (e.g. `virtualenv`,
   `conda`, etc).

3. Install `pyinvoke` to swiftly run the development tasks defined in `./tasks.py`
   and `pytest` which will take care of running the testing suite for us. 

   ```bash
   pip install invoke -U pytest
   ```

4. Install development dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

5. Make sure all tests pass:

   ```bash
   invoke test
   ```

6. Start making your changes to the **master** branch (or branch off of it).

7. Make sure all tests still pass:

   ```bash
   invoke test
   ```

8. Add yourself to the *Contributors* section of `AUTHORS.md`.

9. Write down what changed in the code `CHANGELOG.md`.

10. Commit your changes and push your branch to GitHub.

11. Create a [pull request](https://help.github.com/articles/about-pull-requests/) through the GitHub website.

During development, use [pyinvoke](http://docs.pyinvoke.org/) tasks on the
command line to ease recurring operations:

* `invoke clean`: Clean all generated artifacts.
* `invoke check`: Run various code and documentation style checks.
* `invoke docs`: Generate documentation.
* `invoke test`: Run all tests and checks in one swift command.
* `invoke`: Show available tasks.

## Bug reports

When [reporting a bug](https://github.com//directional_clustering/issues) please include:

* Operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

## Feature requests

When [proposing a new feature](https://github.com//directional_clustering/issues) please include:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.

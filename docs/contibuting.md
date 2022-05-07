# Development

## Contributing

- Fork this repository.
- Clone the forked repository locally.
- Create a virtual environment, activate it and install development dependencies using `pip install '.[dev]'`
- Install pre-commit hooks with `pre-commit install`
- Create a branch, make changes and commit them.
- Push the changes to your forked repository.
- Create a pull request against **this** repository.

## Run tests locally

You can run tests using tox.

```shell
pip install .[test]
tox
```

By default, tests will run against all supported environments. However, if a supported python version is not available
on your machine, you should see an `InterpreterNotFound` error. You can use pyenv to install the needed python versions. 

## Documentation

The documentation is built using Sphinx and is written using markdown thanks to MyST Parser. In many cases, knowing
markdown is enough to update the docs, but if that's not the case, please check the 
[MyST syntax guide](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html) or 
[this cheatsheet](https://jupyterbook.org/reference/cheatsheet.html).

For building the documentation locally, first you'll need to install the documentation dependencies with
```shell
pip install .[doc]
cd docs
make livehtml
```
The last command will start a server that makes the docs available at `http://localhost:9000` and rebuilds it
on any change. That is done thanks to [sphinx-autobuild](https://github.com/executablebooks/sphinx-autobuild).

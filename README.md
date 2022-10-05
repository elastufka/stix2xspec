# stix2xspec

<div align="center">

[![Build status](https://github.com/stix2xspec/stix2xspec/workflows/build/badge.svg?branch=master&event=push)](https://github.com/stix2xspec/stix2xspec/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/stix2xspec.svg)](https://pypi.org/project/stix2xspec/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/stix2xspec/stix2xspec/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/stix2xspec/stix2xspec/blob/master/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/stix2xspec/stix2xspec/releases)
[![License](https://img.shields.io/github/license/stix2xspec/stix2xspec)](https://github.com/stix2xspec/stix2xspec/blob/master/LICENSE)
![Coverage Report](assets/images/coverage.svg)

Convert STIX science data (L1A, L1, or L4 spectrograms or pixel data) to a format compatible with XSPEC

</div>

<!--

## Very first steps

### Initialize your code

1. Initialize `git` inside your repo:

```bash
cd stix2xspec && git init
```

2. If you don't have `Poetry` installed run:

```bash
make poetry-download
```

3. Initialize poetry and install `pre-commit` hooks:

```bash
make install
make pre-commit-install
```

4. Run the codestyle:

```bash
make codestyle
```

5. Upload initial code to GitHub:

```bash
git add .
git commit -m ":tada: Initial commit"
git branch -M main
git remote add origin https://github.com/stix2xspec/stix2xspec.git
git push -u origin main
```

### Set up bots

- Set up [Dependabot](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates) to ensure you have the latest dependencies.
- Set up [Stale bot](https://github.com/apps/stale) for automatic issue closing.

### Poetry

Want to know more about Poetry? Check [its documentation](https://python-poetry.org/docs/).

<details>
<summary>Details about Poetry</summary>
<p>

Poetry's [commands](https://python-poetry.org/docs/cli/#commands) are very intuitive and easy to learn, like:

- `poetry add numpy@latest`
- `poetry run pytest`
- `poetry publish --build`

etc
</p>
</details>

### Building and releasing your package

Building a new version of the application contains steps:

- Bump the version of your package `poetry version <version>`. You can pass the new version explicitly, or a rule such as `major`, `minor`, or `patch`. For more details, refer to the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub`.
- Create a `GitHub release`.
- And... publish 🙂 `poetry publish --build`

## 🎯 What's next

Well, that's up to you 💪🏻. I can only recommend the packages and articles that helped me.

- [`Typer`](https://github.com/tiangolo/typer) is great for creating CLI applications.
- [`Rich`](https://github.com/willmcgugan/rich) makes it easy to add beautiful formatting in the terminal.
- [`Pydantic`](https://github.com/samuelcolvin/pydantic/) – data validation and settings management using Python type hinting.
- [`Loguru`](https://github.com/Delgan/loguru) makes logging (stupidly) simple.
- [`tqdm`](https://github.com/tqdm/tqdm) – fast, extensible progress bar for Python and CLI.
- [`IceCream`](https://github.com/gruns/icecream) is a little library for sweet and creamy debugging.
- [`orjson`](https://github.com/ijl/orjson) – ultra fast JSON parsing library.
- [`Returns`](https://github.com/dry-python/returns) makes you function's output meaningful, typed, and safe!
- [`Hydra`](https://github.com/facebookresearch/hydra) is a framework for elegantly configuring complex applications.
- [`FastAPI`](https://github.com/tiangolo/fastapi) is a type-driven asynchronous web framework.

Articles:

- [Open Source Guides](https://opensource.guide/).
- [A handy guide to financial support for open source](https://github.com/nayafia/lemonade-stand)
- [GitHub Actions Documentation](https://help.github.com/en/actions).
- Maybe you would like to add [gitmoji](https://gitmoji.carloscuesta.me/) to commit names. This is really funny. 😄

## 🚀 Features

### Development features

- Supports for `Python 3.7` and higher.
- [`Poetry`](https://python-poetry.org/) as the dependencies manager. See configuration in [`pyproject.toml`](https://github.com/stix2xspec/stix2xspec/blob/master/pyproject.toml) and [`setup.cfg`](https://github.com/stix2xspec/stix2xspec/blob/master/setup.cfg).
- Automatic codestyle with [`black`](https://github.com/psf/black), [`isort`](https://github.com/timothycrosley/isort) and [`pyupgrade`](https://github.com/asottile/pyupgrade).
- Ready-to-use [`pre-commit`](https://pre-commit.com/) hooks with code-formatting.
- Type checks with [`mypy`](https://mypy.readthedocs.io); docstring checks with [`darglint`](https://github.com/terrencepreilly/darglint); security checks with [`safety`](https://github.com/pyupio/safety) and [`bandit`](https://github.com/PyCQA/bandit)
- Testing with [`pytest`](https://docs.pytest.org/en/latest/).
- Ready-to-use [`.editorconfig`](https://github.com/stix2xspec/stix2xspec/blob/master/.editorconfig), [`.dockerignore`](https://github.com/stix2xspec/stix2xspec/blob/master/.dockerignore), and [`.gitignore`](https://github.com/stix2xspec/stix2xspec/blob/master/.gitignore). You don't have to worry about those things.

### Deployment features

- `GitHub` integration: issue and pr templates.
- `Github Actions` with predefined [build workflow](https://github.com/stix2xspec/stix2xspec/blob/master/.github/workflows/build.yml) as the default CI/CD.
- Everything is already set up for security checks, codestyle checks, code formatting, testing, linting, docker builds, etc with [`Makefile`](https://github.com/stix2xspec/stix2xspec/blob/master/Makefile#L89). More details in [makefile-usage](#makefile-usage).
- [Dockerfile](https://github.com/stix2xspec/stix2xspec/blob/master/docker/Dockerfile) for your package.
- Always up-to-date dependencies with [`@dependabot`](https://dependabot.com/). You will only [enable it](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates).
- Automatic drafts of new releases with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). You may see the list of labels in [`release-drafter.yml`](https://github.com/stix2xspec/stix2xspec/blob/master/.github/release-drafter.yml). Works perfectly with [Semantic Versions](https://semver.org/) specification.

### Open source community features

- Ready-to-use [Pull Requests templates](https://github.com/stix2xspec/stix2xspec/blob/master/.github/PULL_REQUEST_TEMPLATE.md) and several [Issue templates](https://github.com/stix2xspec/stix2xspec/tree/master/.github/ISSUE_TEMPLATE).
- Files such as: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` are generated automatically.
- [`Stale bot`](https://github.com/apps/stale) that closes abandoned issues after a period of inactivity. (You will only [need to setup free plan](https://github.com/marketplace/stale)). Configuration is [here](https://github.com/stix2xspec/stix2xspec/blob/master/.github/.stale.yml).
- [Semantic Versions](https://semver.org/) specification with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter).
-->

## Installation

```bash
pip install -U stix2xspec
```

or install with `Poetry`

```bash
poetry add stix2xspec
```

Then you can run

```bash
stix2xspec --help
```

or with `Poetry`:

```bash
poetry run stix2xspec --help
```

## Dependencies

This software requires the files stored in [STIX-CONF](https://github.com/i4Ds/STIX-CONF). Set up an environment variable that points to this directory.

These files can also be found in the [IDL ground software](https://github.com/i4Ds/STIX-GSW) _dbase_ directory.  

```bash
export STX_CONF=/path/to/STIX-CONF
```

## Example - Background-subtract and convert a STIX FITS file 

### [Try it out in CoLab](https://colab.research.google.com/drive/1bXTpKqWAwyp92lM9alSqrAPZtRw2ocMT?usp=sharing)

Download a FITS file from the [STIX Data Center (SDC)](https://datacenter.stix.i4ds.net/). More details about STIX data products, along with tutorials, can be found on the [STIX wiki](https://datacenter.stix.i4ds.net/wiki/index.php?title=STIX_Data_Products). Official science data products are level 1 (L1). These can be found on the [STIX archive server](http://dataarchive.stix.i4ds.net/data/fits/). 

Pre-release data products (L1A) are supported by this software but not officially recommended for use. There are two types of such data, spectrogram data and pixel data. Spectrogram data have _stix-sci-spectrogram_ in their filename and can be searched for using _product_type='xray-spec'_ in  [stixdcpy FitsQuery](https://github.com/i4Ds/stix0dcpy ). They tend to cover very long time intervals. Pixel data have _stix-sci-xray_ in the filename, and are most often generated for single events (solar flares). Both kinds are returned when searching with _product_type='l1'_. 

Download the corresponding background file. Background files can be found by using the filter _filter='BKG'_ or by looking at the file description on the SDC.

Subtracting the background and converting the file to an OGIP-compatible spectrogram is done via the following:

```python
from stix2xspec.stix2xspec import convert_spectrogram

fitsfile = 'solo_L1A_stix-sci-spectrogram-2207238956_20220723T122007-20220723T182511_079258_V01.fits' # full path
bgfile = 'solo_L1A_stix-sci-xray-l1-2207235029_20220723T113947-20220723T122747_079205_V01.fits'
outfile = convert_spectrogram(fitsfile, bgfile, to_fits = True)
```

![](spectrogram_readme.png)

**Figure 1**: A portion of the converted spectrogram


![](spectrogram_idl_readme.png)

**Figure 2**: The same portion of the same input and background files, converted using the official IDL STIX ground software (_convert_spectrogram.pro_)


Along with the important data processing steps of applying the error lookup table (ELUT) and performing livetime-correction, background subtraction is performed, counts are converted to count rate and an energy-dependent systematic error term is generated, which is useful when using XSPEC. Any necessary FITS header quantities are calculated and added to the existing header as needed.

A .srm file containing the spectral response matrix is also written. This is not yet generated via the appropriate calculations; rather, an existing .srm file is edited to match the energy channels contained in the input file. The STIX spectral response matrix is relatively stable over time, but it can be generated using the official [IDL ground software](https://github.com/i4Ds/STIX-GSW).  

## Example - apply ELUT and livetime correction to spectrogram or pixel data

Data processing can be performed with or without the final step of conversion to count rate.

```python
from stix2xspec.spectrogram import Spectrogram 

spec = Spectrogram(fitsfile)
spec.apply_elut()
spec.correct_counts()
```

Counts can be converted to count rate:

```python
spec.to_rate()
```

The same can be done for background files:

```python
from stix2xspec.spectrogram import Spectrogram 

spec_bg = Spectrogram(bgfile, background = True, use_discriminators = False)
spec_bg.apply_elut()
spec_bg.correct_counts()
```

## Example - fit STIX spectrum with solar-specific models in XSPEC

This requires additional installation of  [sunpy/sunxspex](https://github.com/sunpy/sunxspex) and of course [XSPEC](https://heasarc.gsfc.nasa.gov/xanadu/xspec/), which comes together with [pyxspec](https://heasarc.gsfc.nasa.gov/xanadu/xspec/python/html/index.html). For now, the XSPEC solar models are found in [this fork of sunxspex](https://github.com/elastufka/sunxspex/tree/xspec_functions). 

Be sure to enable XSPEC via command line before starting a Python session.

```bash
. $HEADAS/headas-init.sh
```

Add the thermal bremsstrahlung model _vth_ and the non-thermal thick-target bremsstrahlung model _bremsstrahlung_thick_target_ to XSPEC, then fit them first individually and then together.

```python 
import xspec
from stix2xspec.xspec_utils import *
from sunxspex import xspec_models

mod_th = sunxspex.xspec_models.ThermalModel()
xspec.AllModels.addPyMod(mod_th.model, mod_th.ParInfo, 'add')
mod_th.print_ParInfo() # see the initial configuration of parameters

mod_nt = sunxspex.xspec_models.ThickTargetModel()
xspec.AllModels.addPyMod(mod_nt.model, mod_nt.ParInfo, 'add')
mod_nt.print_ParInfo() # see the initial configuration of parameters

xspec.AllData.clear() # get rid of any data that is still loaded from previous runs
xspec.AllData(f"1:1 {'stx_spectrum_20220723_122031.fits'}{{1140}}") # fit the 1140th data row in the converted spectrogram file. make sure the .srm file is in the same folder as the spectrogram file.

spectime = fits_time_to_datetime('stx_spectrum_20220723_122031.fits', idx=1140)
plot_data(xspec, erange = [4,50],title = f'STIX spectrum at {spectime:%Y-%m-%d %H:%M:%S}').show()
```
![](spectrum_readme.png)

If desired, a time interval rather than a single row (time bin) of the spectrogram can be chosen for fitting. A new FITS file containing only one row must be generated.

```python
spectrum_from_time_interval(stx_spectrum_20220723_122031.fits, '2022-07-23T17:55:00', '2022-07-23T18:05:00', out_fitsname='stx_spectrum_integrated.fits')
```
Then load this data using the usual pyxspec commands.

Fitting with a thermal and/or non-thermal solar model can easily be done with the following. Other commonly used models native to Xspec are:

- [apec]() 
- [powerlaw]()
- [bknpower]()

```python
model, chisq = fit_thermal_nonthermal(xspec, thmodel = 'vth', ntmodel = 'bremsstrahlung_thick_target', lowErange = [3,10])
```

XSPEC will display fitted model parameters either in the terminal or directly in the Python/Jupyter session, depending on how standard output is configured. You can also print and plot using the following commands (requires pandas and plotLy).

```python
show_model(model, df=True)
```
| Model par | Model comp | Component | Parameter | Unit | Value | Sigma |
| :---: | :---: | :---: | --- |--- | --- | --- |
|1 |1 | vth|EM| 1e49| 0.30 | frozen| 
|2 |1 | vth|kT| keV| 1.88 | ± 0.26| 
|3 |1 | vth|abund| | 1.00 | frozen| 
|4 |1 | vth|norm| | 1.86e-03 | ± 7.77e-04| 
|5 |2 | bremsstrahlung_thick_target|p| | 2.65 | ± 346.01| 
|6 |2 | bremsstrahlung_thick_target|eebrk| keV| 16.93 | ± 421.75| 
|7 |2 | bremsstrahlung_thick_target|q| | 6.64 | ± 71.89| 
|8 |2 | bremsstrahlung_thick_target|eelow| keV| 10.43 | ± 176.56| 
|9 |2 | bremsstrahlung_thick_target|eehigh| keV| 1.00e+07 | ± 3.39e+09| 
|10 |2 | bremsstrahlung_thick_target|norm| | 0.57 | ± 11.83|

```
fig = plot_fit(xspec, model, fitrange = [3,30])
fittext = annotate_plot(model, chisq=chisq, exclude_parameters = ['norm','Abundanc','Redshift'], MK=True)
fig.update_layout(width=650, yaxis_range = [-2,3])
fig.add_annotation(x=1.75,y=.5,text=fittext,xref='paper',yref='paper', showarrow = False)
fig.show()
```
![](specfit_readme.png)

<!--
## Example - Convert STIX FITS file and background file independently

no use case for this at the moment
-->

<!--
### Makefile usage

[`Makefile`](https://github.com/stix2xspec/stix2xspec/blob/master/Makefile) contains a lot of functions for faster development.

<details>
<summary>1. Download and remove Poetry</summary>
<p>

To download and install Poetry run:

```bash
make poetry-download
```

To uninstall

```bash
make poetry-remove
```

</p>
</details>

<details>
<summary>2. Install all dependencies and pre-commit hooks</summary>
<p>

Install requirements:

```bash
make install
```

Pre-commit hooks coulb be installed after `git init` via

```bash
make pre-commit-install
```

</p>
</details>

<details>
<summary>3. Codestyle</summary>
<p>

Automatic formatting uses `pyupgrade`, `isort` and `black`.

```bash
make codestyle

# or use synonym
make formatting
```

Codestyle checks only, without rewriting files:

```bash
make check-codestyle
```

> Note: `check-codestyle` uses `isort`, `black` and `darglint` library

Update all dev libraries to the latest version using one comand

```bash
make update-dev-deps
```

<details>
<summary>4. Code security</summary>
<p>

```bash
make check-safety
```

This command launches `Poetry` integrity checks as well as identifies security issues with `Safety` and `Bandit`.

```bash
make check-safety
```

</p>
</details>

</p>
</details>

<details>
<summary>5. Type checks</summary>
<p>

Run `mypy` static type checker

```bash
make mypy
```

</p>
</details>

<details>
<summary>6. Tests with coverage badges</summary>
<p>

Run `pytest`

```bash
make test
```

</p>
</details>

<details>
<summary>7. All linters</summary>
<p>

Of course there is a command to ~~rule~~ run all linters in one:

```bash
make lint
```

the same as:

```bash
make test && make check-codestyle && make mypy && make check-safety
```

</p>
</details>

<details>
<summary>8. Docker</summary>
<p>

```bash
make docker-build
```

which is equivalent to:

```bash
make docker-build VERSION=latest
```

Remove docker image with

```bash
make docker-remove
```

More information [about docker](https://github.com/stix2xspec/stix2xspec/tree/master/docker).

</p>
</details>

<details>
<summary>9. Cleanup</summary>
<p>
Delete pycache files

```bash
make pycache-remove
```

Remove package build

```bash
make build-remove
```

Delete .DS_STORE files

```bash
make dsstore-remove
```

Remove .mypycache

```bash
make mypycache-remove
```

Or to remove all above run:

```bash
make cleanup
```

</p> -->
</details>

## 📈 Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/stix2xspec/stix2xspec/releases) page.

We follow [Semantic Versions](https://semver.org/) specification.

We use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

|               **Label**               |  **Title in Releases**  |
| :-----------------------------------: | :---------------------: |
|       `enhancement`, `feature`        |       🚀 Features       |
| `bug`, `refactoring`, `bugfix`, `fix` | 🔧 Fixes & Refactoring  |
|       `build`, `ci`, `testing`        | 📦 Build System & CI/CD |
|              `breaking`               |   💥 Breaking Changes   |
|            `documentation`            |    📝 Documentation     |
|            `dependencies`             | ⬆️ Dependencies updates |

You can update it in [`release-drafter.yml`](https://github.com/stix2xspec/stix2xspec/blob/master/.github/release-drafter.yml).

GitHub creates the `bug`, `enhancement`, and `documentation` labels for you. Dependabot creates the `dependencies` label. Create the remaining labels on the Issues tab of your GitHub repository, when you need them.

## 🛡 License

[![License](https://img.shields.io/github/license/stix2xspec/stix2xspec)](https://github.com/stix2xspec/stix2xspec/blob/master/LICENSE)

This project is licensed under the terms of the `GNU GPL v3.0` license. See [LICENSE](https://github.com/stix2xspec/stix2xspec/blob/master/LICENSE) for more details.

## 📃 Citation

```bibtex
@misc{stix2xspec,
  author = {stix2xspec},
  title = {Convert STIX science data (L1A, L1, or L4 spectrograms or pixel data) to a format compatible with XSPEC},
  year = {2022},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/stix2xspec/stix2xspec}}
}
```

## Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template)

# TransitCam

Software for the TransitCam set up that is used during public outreach events at the MPS.
It is used to demonstrate the transit method that PLATO will use to discover exoplanets.

## Install

### For development

The packaging is done using [uv](https://docs.astral.sh/uv/). 
To setup the local development environment, [install uv](https://docs.astral.sh/uv/getting-started/installation/)
and then inside the project folder run 

```
$ uv sync
```

This should create a local venv (in folder `.venv`) and install all dependencies listed in `pyproject.toml`. 
Now you should also be able to package the application with `uv build`. This creates a `whl` file (for all platforms)
and a `tar.gz` file (I think for Mac/Linux only) in the `dist` folder. Copy them to where you want to run 
the application during public outreach events / demonstrations.

### For demonstrations

If you only want to run the TransitCam executables, the simplest way is to use one of the files in `dist` 
(see section above, they can be created with the command `uv build`).
E.g. in order to install it on a windows machine, create an virtual environment, then activate it in
a power shell:

```
$ Set-ExecutionPolicy Unrestricted -Scope Process
$ .\.venv\Scripts\activate
```

And then install the `whl` file:

```
$ python -m pip install .\transit_cam-0.1.0-py3-none-any.whl
```

This creates a `star-generator.exe` in your path, that you can simply execute in the power shell:

```
$ star-generator.exe
```

## Development inside a devcontainer

This project includes a devcontainer definition (see folder `.devcontainer`). When you open the project folder in vscode and if you
have docker and the devcontainer extensions installed, vscode will ask you if you want to open the project in a devcontainer.
Developing inside a devcontainer is very convenient. However, the challange here is, that this project also includes GUIs.
To help with this, the devcontainer definition includes the [desktop-lite](https://github.com/devcontainers/features/tree/main/src/desktop-lite) feature. 
This will spawn a Fluxbox based desktop. You can view the desktop in the browser. First you need to forward the container port 6080 
(go to the PORTS panel of vscode, or if you can't find it, open the command palette and type 'forward port', use the 
corresponding command and enter 6080.). Then you can navigate to http://localhost:6080 in your browser.
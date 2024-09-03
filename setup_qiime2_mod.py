import os
import sys
from subprocess import Popen, PIPE

from rich.console import Console  # Import Console from the rich library

con = Console()  # Initialize con as an instance of Console

MINICONDA_PATH = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
MINICONDA_INSTALLER = MINICONDA_PATH.split("/")[-1]
has_conda = "conda version" in os.popen("conda --version").read()
has_qiime = "qiime version" in os.popen("qiime --version").read()

def cleanup():
    """Clean up any temporary files or processes."""
    pass

def run_and_check(
        args, check, message, failure, success, console=None, env_vars=None,
        check_returncode=True
):
    """Run a command and check that it worked."""
    if console:
        console.log(message)
    else:
        print(message)
    env_vars = {**os.environ, **env_vars} if env_vars else os.environ
    r = Popen(args, env=env_vars, stdout=PIPE, stderr=PIPE,
              universal_newlines=True)
    o, e = r.communicate()
    out = o + e

    if (check_returncode and r.returncode == 0 and check in out) or \
            (not check_returncode and check in out):
        if console:
            console.log("[blue]%s[/blue]" % success)
        else:
            print(success)
    else:
        if console:
            console.log("[red]%s[/red]" % failure, out)
        else:
            print(failure, out)
        cleanup()
        sys.exit(1)

def _hack_in_the_plugins():
    """Add the plugins to QIIME."""
    import qiime2.sdk as sdk
    from importlib.metadata import entry_points

    pm = sdk.PluginManager(add_plugins=False)
    for entry in entry_points()["qiime2.plugins"]:
        plugin = entry.load()
        package = entry.value.split(':')[0].split('.')[0]
        pm.add_plugin(plugin, package, entry.name)

if __name__ == "__main__":
    if not has_conda:
        run_and_check(
            ["wget", MINICONDA_PATH],
            "saved",
            ":snake: Downloading miniconda...",
            "failed downloading miniconda :sob:",
            ":snake: Done.",
            console=con  # Explicitly pass the console object
        )

        run_and_check(
            ["bash", MINICONDA_INSTALLER, "-bfp", "/usr/local"],
            "installation finished.",
            ":snake: Installing miniconda...",
            "could not install miniconda :sob:",
            ":snake: Installed miniconda to `/usr/local` :snake:",
            console=con  # Explicitly pass the console object
        )
    else:
        con.log(":snake: Miniconda is already installed. Skipped.")

    # Check if mamba is already installed
    mamba_installed = "mamba version" in os.popen("mamba --version").read()

    if not has_qiime and not mamba_installed:
        run_and_check(
            ["conda", "install", "mamba", "-y", "-n", "base",
             "-c", "conda-forge"],
            "mamba",
            ":mag: Installing mamba...",
            "could not install mamba :sob:",
            ":mag: Done.",
            console=con  # Explicitly pass the console object
        )

        run_and_check(
            ["mamba", "install", "-n", "base", "-y",
             "-c", "conda-forge", "-c", "bioconda", "-c", "qiime2",
             "-c", "https://packages.qiime2.org/qiime2/2023.2/tested/",
             "-c", "defaults",
             "qiime2=2023.2", "q2cli", "q2templates", "q2-alignment",
             "q2-composition", "q2-cutadapt", "q2-dada2", "q2-demux",
             "q2-deblur", "q2-diversity", "q2-diversity-lib", "q2-emperor",
             "q2-feature-classifier", "q2-feature-table",
             "q2-fragment-insertion", "q2-gneiss", "q2-longitudinal",
             "q2-metadata", "q2-mystery-stew", "q2-phylogeny",
             "q2-quality-control", "q2-quality-filter", "q2-sample-classifier",
             "q2-taxa", "q2-vsearch", "pandas<2", "ipykernel"],
            "Extracting Packages: ...working... done",
            ":mag: Installing QIIME 2. This may take a little bit.\n :clock1:",
            "could not install QIIME 2 :sob:",
            ":mag: Done.",
            console=con  # Explicitly pass the console object
        )

        run_and_check(
            ["pip", "install", "redbiom"],
            "Successfully installed",
            ":mag: Installing redbiom. "
            "This may take a little bit.\n :clock1:",
            "could not install redbiom :sob:",
            ":mag: Done.",
            console=con  # Explicitly pass the console object
        )

        # this is a hack to make SRA tools work: this command fails but somehow
        # still manages to configure the toolkit properly
        run_and_check(
            ["pip", "install", "empress"],
            "Successfully installed empress-",
            ":evergreen_tree: Installing Empress...",
            "could not install Empress :sob:",
            ":evergreen_tree: Done.",
            console=con  # Explicitly pass the console object
        )
    else:
        con.log(":mag: QIIME 2 is already installed. Skipped.")

    run_and_check(
        ["qiime", "info"],
        "QIIME 2 release:",
        ":bar_chart: Checking that QIIME 2 command line works...",
        "QIIME 2 command line does not seem to work :sob:",
        ":bar_chart: QIIME 2 command line looks good :tada:",
        console=con  # Explicitly pass the console object
    )

    if sys.version_info[0:2] == (3, 8):
        sys.path.append("/usr/local/lib/python3.8/site-packages")
        con.log(":mag: Fixed import paths to include QIIME 2.")

        con.log(":bar_chart: Checking if QIIME 2 import works...")
        try:
            import qiime2  # noqa
        except Exception:
            con.log("[red]QIIME 2 can not be imported :sob:[/red]")
            sys.exit(1)
        con.log("[blue]:bar_chart: QIIME 2 can be imported :tada:[/blue]")

        con.log(":bar_chart: Setting up QIIME 2 plugins...")
        try:
            _hack_in_the_plugins()
            from qiime2.plugins import feature_table # noqa
        except Exception:
            con.log("[red]Could not add the plugins :sob:[/red]")
            sys.exit(1)
        con.log("[blue]:bar_chart: Plugins are working :tada:[/blue]")

    cleanup()

    con.log("[green]Everything is A-OK. "
            "You can start using QIIME 2 now :thumbs_up:[/green]")

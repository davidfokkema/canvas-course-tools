import rich_click as click
from rich import box, print
from rich.table import Table

from canvas_course_tools import configfile


@click.group()
def servers():
    """Add, remove and list Canvas servers."""
    pass


@servers.command("list")
def show_servers():
    """List the registered servers."""
    config = configfile.read_config()
    try:
        servers = config["servers"]
    except KeyError:
        pass
    else:
        table = Table(box=box.HORIZONTALS)
        table.add_column("Alias")
        table.add_column("URL")
        for alias, settings in servers.items():
            table.add_row(alias, settings["url"])
        print()
        print(table)


@servers.command("add")
@click.argument("alias", type=str)
@click.argument("url", type=str)
@click.argument("token", type=str)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="If alias already exists, force overwrite.",
)
def add_server(alias, url, token, force):
    """Register an alias for a server with corresponding access token.

    Example:

        canvas servers add school http://school.example.com/ 123~secret
    """
    config = configfile.read_config()
    servers = config.setdefault("servers", {})
    if alias in servers and not force:
        print(f"[bold red] Server '{alias}' already exists.[/bold red]")
    else:
        servers[alias] = {"url": url, "token": token}
        configfile.write_config(config)


@servers.command("remove")
@click.argument("alias", type=str)
def remove_server(alias):
    """Remove server from configuration."""
    config = configfile.read_config()
    try:
        del config["servers"][alias]
    except KeyError:
        print(f"[bold red] Unknown server '{alias}'.[/bold red]")
    else:
        configfile.write_config(config)
        print(f"Server '{alias}' removed.")

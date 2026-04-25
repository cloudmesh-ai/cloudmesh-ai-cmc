import click
from typing import Optional, Tuple, Callable
from cloudmesh.common.StopWatch import progress as progress_func

@click.command()
@click.argument('progress_value', type=int)
@click.option('--status', default='running', help='the status')
@click.option('--pid', help='the PID')
@click.option('--now', is_flag=True, help='add a time of now')
@click.option('--sep', default=' ', help='separator when adding key=values')
@click.option('--banner', is_flag=True, help='creates also a banner when specified')
@click.argument('key_values', nargs=-1)
def progress(
    progress_value: int, 
    status: str, 
    pid: Optional[str], 
    now: bool, 
    sep: str, 
    banner: bool, 
    key_values: Tuple[str, ...]
) -> None:
    """
    Prints a progress line of the form

    "# cloudmesh status=ready progress=0 pid=$$ time='2022-08-05 16:29:40.228901' key1=value1 key2=value2"

    Usage:
        progress PROGRESS [--status=STATUS] [--pid=PID] [--now] [KEY=VALUE...] [--sep=SEP] [--banner]

    Arguments:
        PROGRESS   the progress in value from 0 to 100
        KEY=VALUE  the key value pairs to be added

    Options:
        --status=STATUS      the status [default: running]
        --pid=PID            the PID
        --now                add a time of now
        --sep=SEP            separator when adding key=values [default: ' ']
        --banner             creates also a banner
    """
    progress_func(
        progress=str(progress_value), 
        status=status, 
        pid=pid, 
        time=now, 
        sep=sep, 
        banner=banner, 
        key_values=key_values
    )

def register() -> Callable:
    """
    Registers the progress command.
    """
    return progress
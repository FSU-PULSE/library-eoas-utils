"""Common I/O helpers for filesystem paths and lightweight config objects."""

import os
from os import walk, listdir
from os.path import join


def create_folder(output_folder: str) -> None:
    """Create a directory if it does not already exist.

    Args:
        output_folder: Target directory path.

    Side effects:
        Creates ``output_folder`` and any missing parent directories via
        ``os.makedirs``.
    """
    if not (os.path.exists(output_folder)):
        os.makedirs(output_folder)


def all_files_in_folder(
    input_folder: str, file_ext: str | None = None
) -> tuple[list[str], list[str]]:
    """Recursively list file names and full paths under a folder.

    Args:
        input_folder: Root directory to walk.
        file_ext: Optional substring filter applied to each file name. When
            ``None``, all files are returned.

    Returns:
        A tuple ``(file_names, paths)`` where each entry shares the same index.
        ``file_names`` contains basenames only; ``paths`` contains absolute or
        relative paths joined from the walk.
    """
    paths = []
    file_names = []
    for root, d_names, f_names in os.walk(input_folder):
        for f in f_names:
            if file_ext is None or f.find(file_ext) != -1:
                paths.append(os.path.join(root, f))
                file_names.append(f)

    return file_names, paths


def str2bool(cstr: str) -> bool:
    """Parse common truthy string representations into a boolean.

    Args:
        cstr: Input value compared against ``'True'``, ``'true'``, ``'t'``,
            or the boolean ``True``.

    Returns:
        ``True`` when ``cstr`` matches a known truthy token; otherwise
        ``False``.
    """
    return cstr in ['True', 'true', 't', True]


def tuple_to_string(tup: tuple) -> str:
    """Join tuple elements into a comma-separated string.

    Args:
        tup: Tuple of values converted with ``str``.

    Returns:
        Comma-separated string representation of ``tup``.
    """
    return ','.join(str(x) for x in tup)


class dotdict(dict):
    """Dictionary with attribute-style access to keys.

    Example:
        >>> cfg = dotdict({"name": "sst"})
        >>> cfg.name
        'sst'
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


if __name__ == '__main__':
    print(all_files_in_folder("/home/olmozavala/Dropbox/MyProjects/OZ_LIB/eoas-ai-template/test_data/GOMb0.04"))

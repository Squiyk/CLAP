"""File utility functions for CLAP application."""
import os
from typing import Union


def clean_name(path: str) -> str:
    """
    Extract a clean filename from a path by removing NIfTI extensions.
    
    This function removes .nii.gz, .nii, or other common file extensions
    from a file path to get a clean base name suitable for use in 
    generating output filenames.
    
    Args:
        path: Full or relative file path
        
    Returns:
        Clean filename without extension
        
    Examples:
        >>> clean_name("/path/to/image.nii.gz")
        'image'
        >>> clean_name("/path/to/image.nii")
        'image'
        >>> clean_name("/path/to/file.txt")
        'file'
    """
    base = os.path.basename(path)
    if base.endswith(".nii.gz"):
        return base[:-7]
    elif base.endswith(".nii"):
        return base[:-4]
    return os.path.splitext(base)[0]


def get_safe_thread_count(reserve: int = 2, default: int = 4) -> int:
    """
    Calculate a safe number of threads to use for parallel processing.
    
    This function determines the number of CPU cores available and reserves
    a specified number for system operations, returning a safe thread count
    for parallel processing tasks.
    
    Args:
        reserve: Number of cores to reserve for system (default: 2)
        default: Default thread count if CPU count cannot be determined (default: 4)
        
    Returns:
        Safe number of threads to use (minimum of 1)
        
    Examples:
        >>> # On a system with 8 cores
        >>> get_safe_thread_count()
        6
        >>> # On a system with 2 cores
        >>> get_safe_thread_count()
        1
    """
    try:
        total_cores = os.cpu_count()
        if total_cores is None:
            total_cores = default
    except NotImplementedError:
        total_cores = default
    
    return max(1, total_cores - reserve)

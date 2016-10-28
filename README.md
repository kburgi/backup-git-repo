Summary 
==============
Little script that clone --mirror a list of git repo owned by a same user, and
create a tar.xz archive in the folder of your choice. 
* This script NEED IMPROVEMENT *


Plugin purpose
==============
- clone (with option mirror) a list of git repo in a folder (same auth for all)
- create a unique tar.xz archive with all repo inside

Requirement
==============
- Bash
- Python 3 with module sys, os, shutil, pygit2, time, tarfile, contextlib

Usage 
==============
/path/to/git_repo_bk.py


IMPORTANT NOTE
==============
This script is not yet finished, it only support a backup from a
"ssh access with key-auth" for all git repo. Feel free to improve it !





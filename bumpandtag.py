from pathlib import Path
from semver.version import Version as SemVer
from CCSVGit import VersionTags, VersionTag, Versioning
from datetime import datetime
import datetime
from termcolor import cprint, colored
from subprocess import call
import os

def main():
	versioning:Versioning = Versioning(Path(__file__).parent)
	versioning.BumpAndTag()

if __name__ == "__main__":
	main()

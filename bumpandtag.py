from pathlib import Path
from CCSVGit import Versioning

def main():
	versioning:Versioning = Versioning(Path(__file__).parent)
	versioning.BumpAndTag()

if __name__ == "__main__":
	main()


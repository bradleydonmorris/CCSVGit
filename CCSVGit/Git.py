from pathlib import Path
import subprocess
import shutil
import json
import errno
import os
from datetime import datetime
from urllib.parse import urlparse

class GitRepoMeta:
	Name:str|None = None
	Organization:str|None = None
	URL:str|None = None
	ChangeLogPath:Path|None = None
	LicensePath:Path|None = None
	ReadMePath:Path|None = None
	ScopeLinks:dict|None = None
	RepoPath:Path|None = None
	RepoMetaPath:Path|None = None

	def ToDict(self) -> dict:
		return {
			"Name": self.Name,
			"Organization": self.Organization,
			"URL": self.URL,
			"ChangeLogPath": str(self.ChangeLogPath.relative_to(self.RepoPath)),
			"LicensePath": str(self.LicensePath.relative_to(self.RepoPath)),
			"ReadMePath": str(self.ReadMePath.relative_to(self.RepoPath)),
			"ScopeLinks": self.ScopeLinks
		}

	def ToJSON(self) -> str:
		return json.dumps(self.ToDict(), indent=4, default=str)

	def __init__(self,
			repoPath:Path,
			repoMetaPath:Path|None = None,
			name:str|None = None,
			organization:str|None = None,
			url:str|None = None,
			changeLogPath:Path|None = None,
			licensePath:Path|None = None,
			readMePath:Path|None = None) -> None:
		self.RepoPath = repoPath
		self.RepoMetaPath = repoMetaPath
		self.Name = name
		self.Organization = organization
		self.URL = url
		self.ChangeLogPath = changeLogPath
		self.LicensePath = licensePath
		self.ReadMePath = readMePath
		if (self.ChangeLogPath is None):
			self.ChangeLogPath = self.RepoPath.joinpath("CHANGELOG.md")
		if (self.LicensePath is None):
			self.LicensePath = self.RepoPath.joinpath("LICENSE")
		if (self.ReadMePath is None):
			self.ReadMePath = self.RepoPath.joinpath("README.md")
		if (self.RepoMetaPath is None):
			self.RepoMetaPath = self.RepoPath.joinpath(".repometa.json")
		if (self.RepoMetaPath.exists()):
			dictionary:dict = json.loads(self.RepoMetaPath.read_text())
			if ("Name" in dictionary.keys()): self.Name = dictionary["Name"]
			if ("Organization" in dictionary.keys()): self.Organization = dictionary["Organization"]
			if ("URL" in dictionary.keys()): self.URL = dictionary["URL"]
			if ("ChangeLogPath" in dictionary.keys()): self.ChangeLogPath = self.RepoPath.joinpath(dictionary["ChangeLogPath"])
			if ("LicensePath" in dictionary.keys()): self.LicensePath = self.RepoPath.joinpath(dictionary["LicensePath"])
			if ("ReadMePath" in dictionary.keys()): self.ReadMePath = self.RepoPath.joinpath(dictionary["ReadMePath"])
			if ("ScopeLinks" in dictionary.keys()): self.ScopeLinks = dictionary["ScopeLinks"]

	def __str__(self) -> str:
		return self.ToJSON()

class Git:
	CommitAttributes:dict = {
		"Hash": "%H",
		"AbbreviatedHash": "%h",
		"TreeHash": "%T",
		"AbbreviatedTreeHash": "%t",
		"AuthorName": "%an",
		"AuthorName_MailMap": "%aN",
		"AuthorEmail": "%ae",
		"AuthorEmail_MailMap": "%aE",
		"AuthorEmailLocalPart": "%al",
		"AuthorEmailLocalPart_MailMap": "%aL",
		"AuthorDate_date": "%ad",
		"AuthorDate_RFC2822": "%aD",
		"AuthorDate_Relative": "%ar",
		"AuthorDate_UnixTimestamp": "%at",
		"AuthorDate_IS08601Like": "%ai",
		"AuthorDate_IS08601Strict": "%aI",
		"AuthorDate_Short": "%as",
		"AuthorDate_Human": "%ah",
		"AuthorDate_AsObject": "%aI",
		"CommitterName": "%cn",
		"CommitterName_MailMap": "%cN",
		"CommitterEmail": "%ce",
		"CommitterEmail_MailMap": "%cE",
		"CommitterEmailLocalPart": "%cl",
		"CommitterEmailLocalPart_MailMap": "%cL",
		"CommitterDate_date": "%cd",
		"CommitterDate_RFC2822": "%cD",
		"CommitterDate_Relative": "%cr",
		"CommitterDate_UnixTimestamp": "%ct",
		"CommitterDate_IS08601Like": "%ci",
		"CommitterDate_IS08601Strict": "%cI",
		"CommitterDate_Short": "%cs",
		"CommitterDate_Human": "%ch",
		"CommitterDate_AsObject": "%cI",
		"RefName_decorate": "%d",
		"RefName_NoParenth": "%D",
		"RefName_Source": "%S",
		"Encoding": "%e",
		"Subject": "%s",
		"Subject_Sanitized": "%f",
		"Body": "%b",
		"Body_Raw": "%B",
		"CommitNotes": "%N",
		"RawVerificationMessage": "%GG",
		"ValidSignature_G": "%G?",
		"SignerName": "%GS",
		"SignerKey": "%GK",
		"SignerFingurePrint": "%GF",
		"PrimaryKeyOfSignerFingerPrint": "%GP",
		"SignerKeyTrustLevel": "%GT",
		"RefLogSelector": "%gD",
		"RefLogSelector_Shortened": "%gd",
		"RefLogIdentityName": "%gn",
		"RefLogIdentityName_MailMap": "%gN",
		"RefLogIdentityEmail": "%ge",
		"RefLogIdentityEmail_MailMap": "%gE",
		"RefLogSubject": "%gs"
	}

	GitExecPath:Path | None = None
	RepoPath:Path | None = None

	def __init__(self, repoSearchPath:Path, execPath:Path | None = None):
		self.GetRepoPathFromPath(repoSearchPath)
		self.SetGitExecPath(execPath)

	def GetRepoPathFromPath(self, searchPath:Path) -> Path:
		continueLoop:bool = True
		gitRepoDir:Path = None
		if (searchPath.is_file()):
			searchPath = searchPath.parent
		while (continueLoop):
			if (searchPath == searchPath.parent):
				if (searchPath.joinpath(".git").exists()):
					gitRepoDir = searchPath
				else:
					gitRepoDir = None
				continueLoop = False
			if (searchPath != searchPath.parent):
				if (searchPath.joinpath(".git").exists()):
					gitRepoDir = searchPath
					continueLoop = False
				else:
					searchPath = searchPath.parent
		if (gitRepoDir is None):
			raise  Exception("Git Repo Not Found")
		self.RepoPath = gitRepoDir

	def SetGitExecPath(self, execPath:Path = None):
		if (execPath is not None):
			if (not execPath.exists()):
				raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), str(execPath))
			self.GitExecPath = execPath
		else:
			try:
				execPath = Path(shutil.which("git.exe"))
			except:
				execPath = None
			if (execPath is None):
				raise  Exception("Git Not Found")
			if (not execPath.exists()):
				raise  Exception("Git Not Found")
			self.GitExecPath = execPath

	def GetCommit(self, commitHash:str, selectedAttributes:list | None = None) -> dict | None:
		returnValue:dict | None = None
		filteredAttributes:dict = self.CommitAttributes
		if (selectedAttributes is not None
	  		and len(selectedAttributes) > 0):
			filteredAttributes:dict = {key: self.CommitAttributes[key] for key in selectedAttributes}
		format:str = "|:|".join(filteredAttributes.values())
		commitOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" log {commitHash} -1 --format=\"format:{format}\"")
		values:list = commitOutput.decode().split("|:|")
		if (len(values) > 0):
			returnValue:dict = {}
			for index, key in enumerate(filteredAttributes.keys()):
				if (len(values[index]) < 1
					or values[index] == "undefined"):
					returnValue[key] = None
				else:
					if (not str(key).endswith("(AsObject)")):
						returnValue[key] = values[index]
					elif (str(key).startswith("AuthorDate") or str(key).startswith("CommitterDate")):
						returnValue[key] = datetime.fromisoformat(values[index])
		return returnValue

	def GetFirstCommit(self, selectedAttributes:list | None = None) -> dict | None:
		returnValue:dict | None = None
		filteredAttributes:dict = self.CommitAttributes
		if (selectedAttributes is not None
	  		and len(selectedAttributes) > 0):
			filteredAttributes:dict = {key: self.CommitAttributes[key] for key in selectedAttributes}
		format:str = "|:|".join(filteredAttributes.values())
		commitOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" log --max-parents=0 HEAD -1 --format=\"format:{format}\"")
		values:list = commitOutput.decode().split("|:|")
		if (len(values) > 0):
			returnValue:dict = {}
			for index, key in enumerate(filteredAttributes.keys()):
				if (len(values[index]) < 1
					or values[index] == "undefined"):
					returnValue[key] = None
				else:
					if (not str(key).endswith("(AsObject)")):
						returnValue[key] = values[index]
					elif (str(key).startswith("AuthorDate") or str(key).startswith("CommitterDate")):
						returnValue[key] = datetime.fromisoformat(values[index])
		return returnValue

	def GetLastCommit(self, selectedAttributes:list | None = None) -> dict | None:
		returnValue:dict | None = None
		filteredAttributes:dict = self.CommitAttributes
		if (selectedAttributes is not None
	  		and len(selectedAttributes) > 0):
			filteredAttributes:dict = {key: self.CommitAttributes[key] for key in selectedAttributes}
		format:str = "|:|".join(filteredAttributes.values())
		commitOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" log -1 --format=\"format:{format}\"")
		values:list = commitOutput.decode().split("|:|")
		if (len(values) > 0):
			returnValue:dict = {}
			for index, key in enumerate(filteredAttributes.keys()):
				if (len(values[index]) < 1
					or values[index] == "undefined"):
					returnValue[key] = None
				else:
					if (not str(key).endswith("(AsObject)")):
						returnValue[key] = values[index]
					elif (str(key).startswith("AuthorDate") or str(key).startswith("CommitterDate")):
						returnValue[key] = datetime.fromisoformat(values[index])
		return returnValue

	def GetCommitsBetweenHashes(self,
					beginHash:str,
					endHash:str,
					excludeMergeCommits:bool | None = None,
						#Exclude merge commits.
						#--no-merges
					selectedAttributes:list | None = None
				) -> list:
		returnValue:list | None = None
		agrs:str = " log"
		agrs += f" {beginHash}..{endHash}"
		if (excludeMergeCommits is not None):
			agrs += f" --no-merges"
		agrs += f" --format=\"format:%H\""
		commitsOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=agrs)
		commits:list = commitsOutput.decode().split("\n")
		if (commits is not None
	  		and len(commits) > 0):
			returnValue = []
			for hash in commits:
				if (hash != endHash):
					returnValue.append(self.GetCommit(hash, selectedAttributes))
		return returnValue

	def GetCommits(self,
					afterHash:str | None = None,
						#Show only the commits created after commit specifiedc by hash.
						#<after_hash>..HEAD
					lastNCommits:int | None = None,
						#Show only the last n commits.
						#-<n>
					afterDateTime:datetime | None = None,
						#Limit the commits to those made after the specified date.
						#--after
					beforeDateTime:datetime | None = None,
						#Limit the commits to those made before the specified date
						#--before
					excludeMergeCommits:bool | None = None,
						#Exclude merge commits.
						#--no-merges
					selectedAttributes:list | None = None
				) -> list:
		returnValue:list | None = None
		agrs:str = " log"
		if (afterHash is not None):
			agrs += f" {afterHash}..HEAD"
		if (lastNCommits is not None):
			agrs += f" -n {lastNCommits}"
		if (afterDateTime is not None):
			agrs += f" -after \"{afterDateTime.isoformat()}\""
		if (beforeDateTime is not None):
			agrs += f" -before \"{beforeDateTime.isoformat()}\""
		if (excludeMergeCommits is not None):
			agrs += f" --no-merges"
		agrs += f" --format=\"format:%H\""
		commitsOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=agrs)
		commits:list = commitsOutput.decode().split("\n")
		if (commits is not None
	  		and len(commits) > 0):
			returnValue = []
			for hash in commits:
				returnValue.append(self.GetCommit(hash, selectedAttributes))
		return returnValue

	def GetTags(self,
					selectedAttributes:list | None = None) -> list:
		returnValue:list | None = None
		tagsOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=" tag --list")
		tags:list = tagsOutput.decode().split("\n")
		if (tags is not None
			and len(tags) > 0):
			returnValue = []
			for tagName in tags:
				if (len(tagName) > 0):
					tag:dict = {"Name": tagName}
					tag.update(self.GetCommit(tag["Name"], selectedAttributes))
					returnValue.append(tag)
		return returnValue

	def GetRepoMeta(self) -> GitRepoMeta:
		returnValue:GitRepoMeta = None
		name:str = None
		organization:str = None
		url:str = None
		output:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" remote --verbose show")
		remotes:list = output.decode().split("\n")
		if (remotes is not None
	  		and len(remotes) > 0):
			for line in remotes:
				if (line.startswith("origin")
					and line.endswith("(fetch)")):
					originURL:str = line[line.index("origin")+6:line.index("(fetch)")].strip()
					originURL = originURL[:len(originURL)-4]
					if (originURL.startswith("https:")):
						parsedURL = urlparse(originURL)
						pathElements:list = parsedURL.path.split("/")
						if (len(pathElements) == 3):
							name = pathElements[2]
							organization = pathElements[1]
							url = originURL
					else:
						originURL = originURL[originURL.index(":")+1:]
						urlElements:list = originURL.split("/")
						if (len(urlElements) == 2):
							name = urlElements[1]
							organization = urlElements[0]
							url = f"https://github.com/{organization}/{name}"
		returnValue = GitRepoMeta(repoPath=self.RepoPath, name=name, organization=organization, url=url)
		return returnValue

	def MakeCommit(self, message:str, paths:list[Path]) -> str:
		returnValue:str = None
		for path in paths:
			addOutput:bytes = subprocess.check_output(
				executable=self.GitExecPath,
				cwd=self.RepoPath,
				args=f" add {path.relative_to(self.RepoPath.replace("\\", "/"))}")
		commitOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" commit -m\"{message}\"")

		getCommitOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" log --all --grep=\"{message}\" --format=\"format:%H\"")
		returnValue = getCommitOutput.decode().split("\n")[0]
		return returnValue

	def TagCommit(self, tagName:str, commitHash:str):
		tegOutput:bytes = subprocess.check_output(
			executable=self.GitExecPath,
			cwd=self.RepoPath,
			args=f" tag \"{tagName}\" {commitHash}")

__all__ = ["GitRepoMeta", "Git"]

from FancyBoxes import *
import json
from pathlib import Path
from datetime import datetime
from enum import Enum
import tomllib
import tomli_w
from semver.version import Version as SemVer
import datetime
from enum import Enum
from termcolor import cprint, colored
from lxml import etree

from .Git import Git
from .Git import GitRepoMeta

class CommitType(Enum):
	Unknown = 0
	Feat = 2
	Fix = 3
	Docs = 4
	Style = 5
	Refactor = 6
	Perf = 7
	Test = 8
	Build = 9
	CI = 10
	Chore = 11
	Revert = 12

	def __str__(self):
		return self.name

	def GetEmoji(self) -> str:
		returnValue:str = ""
		match self:
			case CommitType.Unknown: returnValue = "🤷"
			case CommitType.Feat: returnValue = "✨"
			case CommitType.Fix: returnValue = "🐛"
			case CommitType.Docs: returnValue = "📚"
			case CommitType.Style: returnValue = "💎"
			case CommitType.Refactor: returnValue = "🔨"
			case CommitType.Perf: returnValue = "🚀"
			case CommitType.Test: returnValue = "🚨"
			case CommitType.Build: returnValue = "📦"
			case CommitType.CI: returnValue = "👷"
			case CommitType.Chore: returnValue = "🔧"
			case CommitType.Revert: returnValue = "🔙"
		return returnValue

class VersionSegment(Enum):
	Major = 1
	Minor = 2
	Patch = 3
	Build = 4
	Prerelease = 5

class ConventionalCommitFooter:
	Tag:str | None = None
	Value:str | None = None

	def __init__(self, tag:str, value:str) -> None:
		self.Tag = tag
		self.Value = value

class ConventionalCommit:
	Hash:str | None = None
	AbbreviatedHash:str | None = None
	CommitterDate:datetime.datetime | None = None
	Subject:str | None = None
	Body:str | None = None
	Type:CommitType = CommitType.Unknown
	Scope:str | None = None
	IsBreakingChange:bool = False
	BreakingChangeDescription:str | None = None
	Description:str | None = None
	Paragraphs:list[str] | None = []
	Footers:list[ConventionalCommitFooter] | None = []
	Files:list[str] | None = []

	def __init__(self,
			hash:str| None = None,
			abbreviatedHash:str | None = None,
			committerDate:datetime.datetime | str | None = None,
			subject:str | None = None,
			body:str | None = None,
			files:list[str] | None = None) -> None:
		self.Hash = hash
		self.AbbreviatedHash = abbreviatedHash
		if isinstance(committerDate, datetime.datetime):
			self.CommitterDate = committerDate
		elif isinstance(committerDate, str):
			self.CommitterDate = datetime.datetime.fromisoformat(committerDate)
		self.Subject = subject
		self.Body = body
		
		if (self.Subject):
			self.ParseSubject()
		if (self.Body):
			self.ParseBody()
		if (files is not None
	  		and len(files) > 0):
			self.Files = files
		else:
			self.Files = None

	def TryParseCommitType(self, value:str) -> CommitType:
		returnValue:CommitType = CommitType.Unknown
		match value.upper():
			case "FEAT": returnValue = CommitType.Feat
			case "FIX": returnValue = CommitType.Fix
			case "DOCS": returnValue = CommitType.Docs
			case "STYLE": returnValue = CommitType.Style
			case "REFACTOR": returnValue = CommitType.Refactor
			case "PERF": returnValue = CommitType.Perf
			case "TEST": returnValue = CommitType.Test
			case "BUILD": returnValue = CommitType.Build
			case "CI": returnValue = CommitType.CI
			case "CHORE": returnValue = CommitType.Chore
			case "REVERT": returnValue = CommitType.Revert
			case _: returnValue = CommitType.Unknown
		return returnValue

	def ParseSubject(self) -> None:
		self.Type = CommitType.Unknown
		self.Scope = None
		self.IsBreakingChange = False
		self.BreakingChangeDescription = None
		self.Description= None
		typeScopeBreak = self.Subject[:self.Subject.index(":")]
		self.IsBreakingChange = typeScopeBreak.endswith("!")
		self.Description = self.Subject[self.Subject.index(":")+1:].strip()
		if ("(" in typeScopeBreak):
			self.Type = self.TryParseCommitType(typeScopeBreak[:typeScopeBreak.index("(")])
		else:
			if (self.IsBreakingChange):
				self.Type = self.TryParseCommitType(typeScopeBreak[:(len(typeScopeBreak) - 1)])
			else:
				self.Type = self.TryParseCommitType(typeScopeBreak)
		if ("(" in typeScopeBreak
			and ")" in typeScopeBreak):
			self.Scope = typeScopeBreak[typeScopeBreak.index("(")+1:typeScopeBreak.index(")")]

	def ParseBody(self) -> None:
		self.Paragraphs = list[str]()
		self.Footers = list[ConventionalCommitFooter]()
		isInParagraph:bool = False
		paragraph:str = ""
		lines:list = self.Body.replace("\r\n", "\n").split("\n")
		for line in lines:
			isBlank:bool = False
			isBreakingChange:bool = False
			isFooter:bool = False
			if (isInParagraph):
				if (len(line) > 0):
					if (paragraph.endswith(" ")):
						paragraph += line
					else:
						paragraph += f" {line}"
				else:
					self.Paragraphs.append(paragraph)
					paragraph = ""
					isInParagraph = False
			if (len(line) == 0):
				isBlank = True
			if (line.startswith("BREAKING CHANGES:")):
				self.IsBreakingChange
				isBreakingChange = True
				self.BreakingChangeDescription = line[line.index(":")+1:].strip()
			if (":" in line):
				tag:str = line[:line.index(":")]
				if (" " not in tag):
					isFooter = True
					value:str = line[line.index(":")+1:].strip()
					self.Footers.append(ConventionalCommitFooter(tag, value))
			if (not isBlank
				and not isBreakingChange
				and not isFooter
				and not isInParagraph):
				isInParagraph = True
				paragraph = line
			if (not isBlank
				and not isBreakingChange
				and not isFooter
				and not isInParagraph):
				pass
		
	def __str__(self) -> str:
		committerDate:str|None = None
		if (isinstance(self.CommitterDate, datetime.datetime)):
			committerDate = self.CommitterDate.isoformat()
		return f"{self.Hash}\t{self.AbbreviatedHash}\t{committerDate}\t{self.Subject}"
	
class ConventionalCommitStats:
	Unknown:int = 0
	Breaking:int = 0
	Feat:int = 0
	Fix:int = 0
	Docs:int = 0
	Style:int = 0
	Refactor:int = 0
	Perf:int = 0
	Test:int = 0
	Build:int = 0
	CI:int = 0
	Chore:int = 0
	Revert:int = 0

	def __init__(self, commits:list[ConventionalCommit] | None) -> None:
		if (commits is not None):
			self.Breaking = sum(c.IsBreakingChange for c in commits)
			self.Feat = sum(c.Type == CommitType.Feat for c in commits)
			self.Fix = sum(c.Type == CommitType.Fix for c in commits)
			self.Docs = sum(c.Type == CommitType.Docs for c in commits)
			self.Style = sum(c.Type == CommitType.Style for c in commits)
			self.Refactor = sum(c.Type == CommitType.Refactor for c in commits)
			self.Perf = sum(c.Type == CommitType.Perf for c in commits)
			self.Test = sum(c.Type == CommitType.Test for c in commits)
			self.Build = sum(c.Type == CommitType.Build for c in commits)
			self.CI = sum(c.Type == CommitType.CI for c in commits)
			self.Chore = sum(c.Type == CommitType.Chore for c in commits)
			self.Revert = sum(c.Type == CommitType.Revert for c in commits)

	def GetBadges(self, excludeZeros:bool = True,
					breakingColor:str = "FF2121", featColor:str="C2EDCE", fixColor:str="CBD5F0",
					docsColor:str="6DAFFE", styleColor:str="F9D326", refactorColor:str="F48882",
					perfColor:str="D1A080", testColor:str="BD9DEA", buildColor:str="8F5B34",
					ciColor:str="8A9EA7", choreColor:str="E3D477", revertColor:str="699E3C"
			   ) -> list[str]:
		returnValue:list[str] = list[str]()
		if (excludeZeros):
			if (self.Breaking > 0): returnValue.append(f"![Breaking-{self.Breaking}](https://img.shields.io/badge/breaking-{self.Breaking}-{breakingColor})")
			if (self.Feat > 0): returnValue.append(f"![Feat-{self.Feat}](https://img.shields.io/badge/features-{self.Feat}-{featColor})")
			if (self.Fix > 0): returnValue.append(f"![Fix-{self.Fix}](https://img.shields.io/badge/fixes-{self.Fix}-{fixColor})")
			if (self.Docs > 0): returnValue.append(f"![Docs-{self.Docs}](https://img.shields.io/badge/docs-{self.Docs}-{docsColor})")
			if (self.Style > 0): returnValue.append(f"![Style-{self.Style}](https://img.shields.io/badge/styles-{self.Style}-{styleColor})")
			if (self.Refactor > 0): returnValue.append(f"![Refactor-{self.Refactor}](https://img.shields.io/badge/refactors-{self.Refactor}-{refactorColor})")
			if (self.Perf > 0): returnValue.append(f"![Perf-{self.Perf}](https://img.shields.io/badge/perfs-{self.Perf}-{perfColor})")
			if (self.Test > 0): returnValue.append(f"![Test-{self.Test}](https://img.shields.io/badge/tests-{self.Test}-{testColor})")
			if (self.Build > 0): returnValue.append(f"![Build-{self.Build}](https://img.shields.io/badge/builds-{self.Build}-{buildColor})")
			if (self.CI > 0): returnValue.append(f"![CI-{self.CI}](https://img.shields.io/badge/ci-{self.CI}-{ciColor})")
			if (self.Chore > 0): returnValue.append(f"![Chore-{self.Chore}](https://img.shields.io/badge/chores-{self.Chore}-{choreColor})")
			if (self.Revert > 0): returnValue.append(f"![Revert-{self.Revert}](https://img.shields.io/badge/reverts-{self.Revert}-{revertColor})")
		else:
			returnValue.append(f"![Breaking-{self.Breaking}](https://img.shields.io/badge/breaking-{self.Breaking}-{breakingColor})")
			returnValue.append(f"![Feat-{self.Feat}](https://img.shields.io/badge/features-{self.Feat}-{featColor})")
			returnValue.append(f"![Fix-{self.Fix}](https://img.shields.io/badge/fixes-{self.Fix}-{fixColor})")
			returnValue.append(f"![Docs-{self.Docs}](https://img.shields.io/badge/docs-{self.Docs}-{docsColor})")
			returnValue.append(f"![Style-{self.Style}](https://img.shields.io/badge/styles-{self.Style}-{styleColor})")
			returnValue.append(f"![Refactor-{self.Refactor}](https://img.shields.io/badge/refactors-{self.Refactor}-{refactorColor})")
			returnValue.append(f"![Perf-{self.Perf}](https://img.shields.io/badge/perfs-{self.Perf}-{perfColor})")
			returnValue.append(f"![Test-{self.Test}](https://img.shields.io/badge/tests-{self.Test}-{testColor})")
			returnValue.append(f"![Build-{self.Build}](https://img.shields.io/badge/builds-{self.Build}-{buildColor})")
			returnValue.append(f"![CI-{self.CI}](https://img.shields.io/badge/ci-{self.CI}-{ciColor})")
			returnValue.append(f"![Chore-{self.Chore}](https://img.shields.io/badge/chores-{self.Chore}-{choreColor})")
			returnValue.append(f"![Revert-{self.Revert}](https://img.shields.io/badge/reverts-{self.Revert}-{revertColor})")
		return returnValue

	def Serializable(self) -> dict:
		return {
			"Breaking": self.Breaking,
			"Feat": self.Feat,
			"Fix": self.Fix,
			"Docs": self.Docs,
			"Style": self.Style,
			"Refactor": self.Refactor,
			"Perf": self.Perf,
			"Test": self.Test,
			"Build": self.Build,
			"CI": self.CI,
			"Chore": self.Chore,
			"Revert": self.Revert
		}

	def __str__(self) -> str:
		return json.dumps(self.Serializable(), indent=4)

class VersionTag:
	Name:str | None = None
	Version:SemVer | None = None
	TagCommit:ConventionalCommit | None = None
	Commits:list[ConventionalCommit] = []
	Stats:ConventionalCommitStats | None = None

	def __init__(self,
			name:str | None = None,
			version:SemVer | str | None = None,
			tagCommit:ConventionalCommit | None = None,
			commits:list[ConventionalCommit] | None = None
			) -> None:
		self.Name = name
		if isinstance(version, SemVer):
			self.Version = version
		elif isinstance(version, str):
			if (version.startswith("v")):
				version = version[1:]
			self.Version = SemVer.parse(version)
		self.TagCommit = tagCommit
		self.Commits = commits
		self.SetStats()

	def SetTagCommit(self, commit:ConventionalCommit | dict) -> None:
		if isinstance(commit, ConventionalCommit):
			self.TagCommit = commit
		elif isinstance(commit, dict):
			files:list[str] | None = None
			if ("Files" in commit.keys()):
				files = commit["Files"]
			self.TagCommit = ConventionalCommit(
				hash=commit["Hash"],
				abbreviatedHash=commit["AbbreviatedHash"],
				committerDate=commit["CommitterDate_IS08601Strict"],
				subject=commit["Subject"],
				body=commit["Body"],
				files=files
			)

	def AppendCommit(self, commit:ConventionalCommit | dict) -> None:
		if (self.Commits is None):
			self.Commits = list[ConventionalCommit]()
		if isinstance(commit, ConventionalCommit):
			self.Commits.append(commit)
		elif isinstance(commit, dict):
			files:list[str] | None = None
			if ("Files" in commit.keys()):
				files = commit["Files"]
			self.Commits.append(ConventionalCommit(
				hash=commit["Hash"],
				abbreviatedHash=commit["AbbreviatedHash"],
				committerDate=commit["CommitterDate_IS08601Strict"],
				subject=commit["Subject"],
				body=commit["Body"],
				files=files
			))

	def AppendCommits(self, commits:list[dict]) -> None:
		for commit in commits:
			self.AppendCommit(commit)

	def SetStats(self) -> None:
		self.Stats = ConventionalCommitStats(self.Commits)

class VersionTags:
	GitRepo:Git | None = None
	RepoPath:Path | None = None
	RepoMeta:GitRepoMeta | None = None
	_list:list[VersionTag] = list[VersionTag]()

	def __iter__(self):
		return self._list.__iter__()

	def __getitem__(self, item):
		return self._list[item]

	def __init__(self, repoSearchPath:Path | None = None) -> None:
		if (repoSearchPath is not None
	  		and repoSearchPath.exists()):
			self.GitRepo = Git(repoSearchPath)
			self.LoadFromRepo()
			self._list = sorted(self._list, key=lambda vt: vt.Version, reverse=True)

	def Add(self, versionTag:VersionTag) -> None:
		self._list.append(versionTag)

	def GetLatest(self) -> VersionTag:
		returnValue:VersionTag = None
		if (len(self._list) > 0):
			sortedList:list[VersionTag] = sorted(self._list, key=lambda vt: vt.Version, reverse=True)
			returnValue = sortedList[0]
		return returnValue

	def SetLatestVersion(self, latestVersion:SemVer) -> None:
		if (len(self._list) > 0):
			sortedList:list[VersionTag] = sorted(self._list, key=lambda vt: vt.Version, reverse=True)
			findVersion:SemVer = sortedList[0].Version
			index:int = next((index for index, vt in enumerate(self._list) if vt.Version == findVersion), -1)
			versionTag:VersionTag = self._list[index]
			versionTag.Version = latestVersion
			versionTag.Name = f"v{versionTag.Version}"
			self._list[index] = versionTag

	def CreatePrerelease(self, commits:list[dict]):
		untaggedSemVer:SemVer = SemVer.parse("0.0.0")
		
		if (len(self._list) > 0):
			untaggedSemVer = self.GetLatest().Version

		prereleaseTag:VersionTag = VersionTag(
				name="v_Untagged",
				tagCommit=None,
				version=untaggedSemVer
			)
		prereleaseTag.AppendCommits(commits)
		prereleaseTag.SetStats()
		if (prereleaseTag.Stats.Breaking > 0):
			prereleaseTag.Version = prereleaseTag.Version.bump_major()
		elif (prereleaseTag.Stats.Feat > 0):
			prereleaseTag.Version = prereleaseTag.Version.bump_minor()
		else:
			prereleaseTag.Version = prereleaseTag.Version.bump_minor()
		prereleaseTag.Version = prereleaseTag.Version.bump_prerelease("prerelease")
		prereleaseTag.Name = f"v{prereleaseTag.Version}"
		self._list.append(prereleaseTag)

	def VersionToDict(self, version:SemVer | None) -> dict:
		returnValue:dict = {}
		if (isinstance(version, SemVer)):
			returnValue:dict = version.to_dict()
		return returnValue

	def StatsToDict(self, stats:ConventionalCommitStats | None) -> dict:
		returnValue:dict = {}
		if (isinstance(stats, ConventionalCommitStats)):
			returnValue:dict = {
				"Breaking": stats.Breaking,
				"Feat": stats.Feat,
				"Fix": stats.Fix,
				"Docs": stats.Docs,
				"Style": stats.Style,
				"Refactor": stats.Refactor,
				"Perf": stats.Perf,
				"Test": stats.Test,
				"Build": stats.Build,
				"CI": stats.CI,
				"Chore": stats.Chore,
				"Revert": stats.Revert
			}
		return returnValue

	def CommitToDict(self, commit:ConventionalCommit | None) -> dict:
		returnValue:dict = {}
		if (isinstance(commit, ConventionalCommit)):
			returnValue:dict = {
				"Hash": commit.Hash,
				"AbbreviatedHash": commit.AbbreviatedHash,
				"Subject": commit.Subject,
				"Body": commit.Body,
				"Type": str(commit.Type),
				"Scope": commit.Scope,
				"IsBreakingChange": commit.IsBreakingChange,
				"BreakingChangeDescription": commit.BreakingChangeDescription,
				"Description": commit.Description,
				"Paragraphs": commit.Paragraphs,
				"Footers": []
			}
			if isinstance(commit.CommitterDate, datetime.datetime):
				returnValue.update({"CommitterDate": commit.CommitterDate.isoformat()})
			else:
				returnValue.update({"CommitterDate": None})
			for footer in commit.Footers:
				returnValue["Footers"].append({
					"Tag": footer.Tag,
					"Value": footer.Value
				})
		return returnValue

	def Serializable(self) -> list[dict]:
		returnValue:list[dict] = list[dict]()
		sortedList:list[VersionTag] = sorted(self._list, key=lambda vt: vt.Version, reverse=True)
		for versionTag in sortedList:
			serializableCommits:list[dict] = list[dict]()
			for commit in sorted(versionTag.Commits, key=lambda c: c.CommitterDate is not None and c.CommitterDate, reverse=True):
				serializableCommits.append(self.CommitToDict(commit))
			versionTagDictionary:dict = {
				"Name": versionTag.Name,
				"Version": self.VersionToDict(versionTag.Version),
				"Stats": self.StatsToDict(versionTag.Stats),
				"TagCommit": self.CommitToDict(versionTag.TagCommit),
				"Commits": serializableCommits
			}
			returnValue.append(versionTagDictionary)
		return returnValue

	def LoadFromRepo(self) -> None:
		self.RepoPath = self.GitRepo.RepoPath
		self.RepoMeta = self.GitRepo.GetRepoMeta()
		selectedAttributes:list = ["Hash", "AbbreviatedHash", "CommitterDate_IS08601Strict", "Subject", "Body"]
		nextBeginCommit:dict = self.GitRepo.GetFirstCommit(selectedAttributes)
		self._list = list[VersionTag]()
		isFirst:bool = True
		for tag in self.GitRepo.GetTags(selectedAttributes):
			commits:list = []
			commits = self.GitRepo.GetCommitsBetweenHashes(nextBeginCommit["Hash"], tag["Hash"], True, selectedAttributes)
			if (isFirst):
				commits.append(nextBeginCommit)
				isFirst = False
			versionTag:VersionTag = VersionTag(
				name=tag["Name"],
				version=tag["Name"]
			)
			versionTag.SetTagCommit(tag)
			versionTag.AppendCommits(commits)
			versionTag.SetStats()
			self.Add(versionTag)
			nextBeginCommit = tag
		self.CreatePrerelease(self.GitRepo.GetCommits(
					afterHash=nextBeginCommit["Hash"],
					selectedAttributes=selectedAttributes))

	def ToJSON(self) -> str:
		return json.dumps(self.Serializable(), indent=4)

	def GetChangeLogMarkdown(self, includeChangedFilesInChangeLog:bool = False) -> str:
		retrunValue:str = ""
		repoURL:str = ""
		if (self.RepoMeta is not None):
			repoURL = self.RepoMeta.URL
			retrunValue = f"# {self.RepoMeta.Organization}/{self.RepoMeta.Name} - CHANGELOG\n---\n\n"
		else:
			retrunValue = f"# CHANGELOG\n---\n\n"
		for versionTag in self._list:
			tagDate:str = ""
			badges:str = "&nbsp;&nbsp;&nbsp;".join(versionTag.Stats.GetBadges())
			if (versionTag.TagCommit is not None
				and versionTag.TagCommit.CommitterDate is not None):
				tagDate = versionTag.TagCommit.CommitterDate.strftime("%Y-%m-%d")
			else:
				tagDate = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
			retrunValue = f"{retrunValue}## [{versionTag.Name}]({repoURL}/releases/tag/{versionTag.Name}) ({tagDate})\n"
			retrunValue = f"{retrunValue}{badges}\n"
			if (versionTag.Commits is not None and len(versionTag.Commits) > 0):
				for commit in versionTag.Commits:
					commitText:str = ""
					commitDate:str = ""
					subject:str = f"{str(commit.Type).lower()}:{commit.Description}"
					commitLink:str = f"[{commit.AbbreviatedHash}]({repoURL}/commit/{commit.Hash})"
					if (commit.CommitterDate is not None):
						commitDate = commit.CommitterDate.strftime("%Y-%m-%d")
					if (commit.Scope is not None):
						if (commit.Scope in self.RepoMeta.ScopeLinks.keys()):
							subject:str = f"{str(commit.Type).lower()}([{commit.Scope}]({self.RepoMeta.ScopeLinks[commit.Scope]})):{commit.Description}"
						else:
							subject:str = f"{str(commit.Type).lower()}({commit.Scope}):{commit.Description}"
					commitText = f"{commit.Type.GetEmoji()} {subject} - {commitLink} {commitDate}"
					if (includeChangedFilesInChangeLog
		 				and commit.Files is not None
		 				and len(commit.Files) > 0):
						for file in commit.Files:
							commitText += f"\n	* {file}"
					retrunValue = f"{retrunValue}* {commitText}\n"
			else:
				retrunValue = f"{retrunValue}* NO COMMITS FOUND\n"
		return retrunValue

	def SaveChangeLog(self, filePath:Path|None = None, includeChangedFilesInChangeLog:bool = False) -> None:
		if (filePath is None):
			filePath = self.RepoPath.joinpath("CHANGELOG.md")
		filePath.write_text(self.GetChangeLogMarkdown(includeChangedFilesInChangeLog=includeChangedFilesInChangeLog), encoding="utf-16")

	def SaveJSON(self, filePath:Path) -> None:
		filePath.write_text(self.ToJSON())

	def CommitVersion(self, tagName:str, message:str, paths:list[Path]):
		commitHash:str = self.GitRepo.MakeCommit(message, paths)
		self.GitRepo.TagCommit(tagName, commitHash)

class Versioning:
	RepoSearchPath:Path | None = None
	RepoVersionTags:VersionTags | None = None
	PyProjectPaths:list[Path] = list[Path]()
	SQLProjectPaths:list[Path] = list[Path]()
	SQLPublishProfilePaths:list[Path] = list[Path]()
	ChangedFiles:list[dict] = list[dict]()

	@staticmethod
	def VersionToBytes(version:str) -> bytes:
		returnValue:bytes = None
		if (version.startswith("v")):
			version = version[1::]
		versionHex:str = ""
		for element in version.split("."):
			versionHex += ''.join(format(x, '02x') for x in int(element).to_bytes(4))
		returnValue = bytes.fromhex(versionHex)
		return returnValue

	@staticmethod
	def VersionCompare(firstVersion:str, secondVersion:str) -> str:
		returnValue:str = "="
		firstVersionBytes:bytes = Versioning.VersionToBytes(firstVersion)
		secondVersionBytes:bytes = Versioning.VersionToBytes(secondVersion)
		if (firstVersionBytes == secondVersionBytes):
			returnValue = "="
		elif (firstVersionBytes < secondVersionBytes):
			returnValue = "<"
		elif (firstVersionBytes > secondVersionBytes):
			returnValue = ">"
		return returnValue

	def __init__(self, repoSearchPath:Path | None = None) -> None:
		self.RepoSearchPath = repoSearchPath
		if (self.RepoSearchPath is not None):
			self.RepoVersionTags = VersionTags(repoSearchPath)
			for path in self.RepoVersionTags.RepoPath.rglob("pyproject.toml"):
				self.PyProjectPaths.append(path)
			for path in self.RepoVersionTags.RepoPath.rglob("*.sqlproj"):
				self.SQLProjectPaths.append(path)
			for path in self.RepoVersionTags.RepoPath.rglob("*.publish.xml"):
				self.SQLPublishProfilePaths.append(path)

	def BumpAndTag(self, includeChangedFilesInChangeLog:bool = False) -> None:
		changedFilePaths:list[Path] = list[Path]()
		if (self.RepoVersionTags is not None):
			self.RepoVersionTags.SaveChangeLog(includeChangedFilesInChangeLog=includeChangedFilesInChangeLog)
			versionTag:VersionTag = self.RepoVersionTags.GetLatest()
			outputMessage:str = BuildBox(
				text="BUMP, COMMIT, AND TAG",
				borderColor="white",
				tabSpaces=4, minimumWidth=100)
			outputMessage += "\n\n"
			outputMessage += colored("Currnet unreleased version is ", color="yellow")
			outputMessage += colored(versionTag.Version, color="red", attrs=["bold", "underline"])
			outputMessage += colored(".", color="yellow")
			print(outputMessage)
			finalVersion = versionTag.Version.finalize_version()
			print()
			outputMessage = colored("Press enter to accept ", color="yellow")
			outputMessage += colored(finalVersion, color="red", attrs=["bold", "underline"])
			outputMessage += colored(" as the final version, or enter a new final version: ", color="yellow")
			newVersion = input(outputMessage)
			if (len(newVersion) > 0):
				if (newVersion.startswith("v")):
					newVersion:str = newVersion[1:]
				finalVersion = SemVer.parse(newVersion)
			print()
			outputMessage = colored(finalVersion, color="red", attrs=["bold", "underline"])
			outputMessage += colored(" will be used as the final version.", color="yellow")
			print(outputMessage)

			self.RepoVersionTags.SetLatestVersion(finalVersion)
			self.RepoVersionTags.SaveChangeLog()
			changedFilePaths.append(self.RepoVersionTags.RepoMeta.ChangeLogPath)
			self.ChangedFiles.append({
				"Type": "ChangeLog",
				"Path": self.RepoVersionTags.RepoMeta.ChangeLogPath,
				"IsChanged": True,
				"PreviousVersion": None,
				"NewVersion": None
			})

			print()
			print(colored("Scanning for pyproject.toml files...", color="green"))
			for tomlPath in self.PyProjectPaths:
				if (self.EvaluatePyProjectVersion(tomlPath, finalVersion)):
					changedFilePaths.append(tomlPath)
				print()

			print()
			print(colored("Scanning for *.sqlproj files...", color="green"))
			for sqlProjectPath in self.SQLProjectPaths:
				if (self.EvaluateSQLProjectVersion(sqlProjectPath, finalVersion)):
					changedFilePaths.append(sqlProjectPath)
				print()

			print()
			print(colored("Scanning for *.publish.xml files...", color="green"))
			for sqlPublishProfilePath in self.SQLPublishProfilePaths:
				if (self.EvaluateSQLPublishProfileVersion(sqlPublishProfilePath, finalVersion)):
					changedFilePaths.append(sqlPublishProfilePath)
				print()

			print(BuildBox(
					text="RESULTS",
					borderColor="white",
					tabSpaces=4, minimumWidth=100))
			print()
			self.PrintOutChangedFiles()

			print()
			outputMessage += colored("Please confirm these files have been changed appropriately before committing.\n", "yellow")
			outputMessage += colored("These files will be committed with the following message.\n", "yellow")
			outputMessage += colored(f"   build: bump version to {finalVersion}\n", "red")
			outputMessage += colored("Do you want to make this commit [Y/n]: ", "yellow")
			makeCommit:str = input(outputMessage)
			if (len(makeCommit) == 0):
				makeCommit = "Y"
			if (makeCommit.upper() == "Y"):
				latestVersionTag:VersionTag = self.RepoVersionTags.GetLatest()
				print(colored(latestVersionTag.Name, "blue"))
				self.RepoVersionTags.CommitVersion(latestVersionTag.Name, f"build: bump version to {finalVersion}", changedFilePaths)
				print(colored("Commit and Tag created.\nDon't forget to push the commit and the tag to origin.", "red"))
				print(colored(f"   git push\n   git push --tags", "red", attrs=["bold"]))
			else:
				print(colored("NO COMMIT WAS MADE", "red"))

	def PrintOutChangedFiles(self) -> None:
		outputMessage = colored("The following file modifications have been made.\n", color="green")
		outputMessage += colored("red = changed", color="red")
		outputMessage += colored("   yellow = unchanged\n", color="yellow")
		outputMessage += "\n"

		maxFileNameLength:int = 78
		for changedFile in self.ChangedFiles:
			relativePath:str = str(changedFile["Path"].relative_to(self.RepoVersionTags.RepoMeta.RepoPath))
			if (len(relativePath) > maxFileNameLength):
				maxFileNameLength = len(relativePath)
		dataRows:list[list[str]] = list[list[str]]()
		for changedFile in self.ChangedFiles:
			relativePath:str = str(changedFile["Path"].relative_to(self.RepoVersionTags.RepoMeta.RepoPath))
			oldVersion:str = "".ljust(11)
			newVersion:str = "".ljust(11)
			if (changedFile["PreviousVersion"] is not None):
				oldVersion = str(changedFile["PreviousVersion"]).ljust(11)
			if (changedFile["NewVersion"] is not None):
				newVersion = str(changedFile["NewVersion"]).ljust(11)
			dataRows.append([
				colored(relativePath.ljust(maxFileNameLength), color="yellow"),
				colored(oldVersion, color="yellow"),
				colored(newVersion, color="yellow")
			])
		headerRows:list[list[str]] = [[
				colored("File Name".ljust(maxFileNameLength), color="green", attrs=["bold"]),
				colored("Old Version".ljust(11), color="green", attrs=["bold"]),
				colored("New Version".ljust(11), color="green", attrs=["bold"])
		]]
		minimumCellWidths:list[int] = [maxFileNameLength, 11, 11]

		outputMessage += BuildTable(
			headerRows=headerRows,
			dataRows=dataRows,
			footerRows=None,
			borderColor="green",
			minimumCellWidths=minimumCellWidths)
		print(outputMessage)

	def EvaluatePyProjectVersion(self, path:Path, finalVersion:SemVer) -> bool:
		returnValue:bool = False
		projectName:str = self.GetPyProjectName(path)
		projectCurrentVersion = self.GetPyProjectVersion(path)
		projectFinalVersion = finalVersion
		outputMessage = colored("Reading ", color="yellow")
		outputMessage += colored(path.relative_to(self.RepoVersionTags.RepoPath), color="red", attrs=["bold", "underline"])
		outputMessage += colored(" ...\n", color="yellow")
		outputMessage += colored("Py Project ", color="yellow")
		outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
		outputMessage += colored(" current version is ", color="yellow")
		outputMessage += colored(projectCurrentVersion, color="red", attrs=["bold", "underline"])
		outputMessage += colored(".\nPress enter to set ", color="yellow")
		outputMessage += colored(projectFinalVersion, color="red", attrs=["bold", "underline"])
		outputMessage += colored(" as the final version for ", color="yellow")
		outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
		outputMessage += colored(", or enter a new final version: ", color="yellow")
		projectNewVersion:str = input(outputMessage)
		if (len(projectNewVersion) > 0):
			if (projectNewVersion.startswith("v")):
				projectNewVersion = projectNewVersion[1:]
			if (projectCurrentVersion != projectNewVersion):
				projectFinalVersion = SemVer.parse(projectNewVersion)
				outputMessage = colored(projectFinalVersion, color="red")
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".", color="yellow")
				print(outputMessage)
				self.SetPyProjectVersion(path, projectFinalVersion)
				self.ChangedFiles.append({
					"Type": "PyProject",
					"Path": path,
					"IsChanged": True,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": projectFinalVersion
				})
				returnValue = True
			else:
				outputMessage = colored(projectCurrentVersion, color="red")
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".\n", color="yellow")
				outputMessage += colored("The file will remain unchanged.", color="red")
				print(outputMessage)
				self.ChangedFiles.append({
					"Type": "PyProject",
					"Path": path,
					"IsChanged": False,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": None
				})
				returnValue = False
		else:
			if (projectCurrentVersion != finalVersion):
				projectFinalVersion = finalVersion
				outputMessage = colored(projectFinalVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".", color="yellow")
				print(outputMessage)
				self.SetPyProjectVersion(path, projectFinalVersion)
				self.ChangedFiles.append({
					"Type": "PyProject",
					"Path": path,
					"IsChanged": True,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": projectFinalVersion
				})
				returnValue = True
			else:
				outputMessage = colored(projectCurrentVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".\n", color="yellow")
				outputMessage += colored("The file will remain unchanged.", color="red")
				print(outputMessage)
				self.ChangedFiles.append({
					"Type": "PyProject",
					"Path": path,
					"IsChanged": False,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": None
				})
				returnValue = False
		return returnValue

	def GetPyProjectName(self, tomlPath:Path) -> str:
		returnValue:str = None
		tomlData:dict = tomllib.loads(tomlPath.read_text())
		returnValue = tomlData["project"]["name"]
		return returnValue

	def GetPyProjectVersion(self, tomlPath:Path) -> SemVer:
		returnValue:SemVer = None
		tomlData:dict = tomllib.loads(tomlPath.read_text())
		returnValue = SemVer.parse(tomlData["project"]["version"])
		return returnValue

	def EvaluateSQLProjectVersion(self, path:Path, finalVersion:SemVer) -> bool:
		returnValue:bool = False
		projectName:str = self.GetSQLProjectName(path)
		projectCurrentVersion = self.GetSQLProjectVersion(path)
		projectFinalVersion = finalVersion
		outputMessage = colored("Reading ", color="yellow")
		outputMessage += colored(path.relative_to(self.RepoVersionTags.RepoPath), color="red", attrs=["bold", "underline"])
		outputMessage += colored(" ...\n", color="yellow")
		outputMessage += colored("SQL Project ", color="yellow")
		outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
		outputMessage += colored(" current version is ", color="yellow")
		outputMessage += colored(projectCurrentVersion, color="red", attrs=["bold", "underline"])
		outputMessage += colored(".\nPress enter to set ", color="yellow")
		outputMessage += colored(projectFinalVersion, color="red", attrs=["bold", "underline"])
		outputMessage += colored(" as the final version for ", color="yellow")
		outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
		outputMessage += colored(", or enter a new final version: ", color="yellow")
		projectNewVersion:str = input(outputMessage)
		if (len(projectNewVersion) > 0):
			if (projectNewVersion.startswith("v")):
				projectNewVersion = projectNewVersion[1:]
			if (projectCurrentVersion != projectNewVersion):
				projectFinalVersion = SemVer.parse(projectNewVersion)
				outputMessage = colored(projectFinalVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".", color="yellow")
				print(outputMessage)
				self.SetSQLProjectVersion(path, projectFinalVersion)
				self.ChangedFiles.append({
					"Type": "SQLProject",
					"Path": path,
					"IsChanged": True,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": projectFinalVersion
				})
				returnValue = True
			else:
				outputMessage = colored(projectCurrentVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".\n", color="yellow")
				outputMessage += colored("The file will remain unchanged.", color="red")
				print(outputMessage)
				self.ChangedFiles.append({
					"Type": "SQLProject",
					"Path": path,
					"IsChanged": False,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": None
				})
				returnValue = False
		else:
			if (projectCurrentVersion != finalVersion):
				projectFinalVersion = finalVersion
				outputMessage = colored(projectFinalVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".", color="yellow")
				print(outputMessage)
				self.SetSQLProjectVersion(path, projectFinalVersion)
				self.ChangedFiles.append({
					"Type": "SQLProject",
					"Path": path,
					"IsChanged": True,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": projectFinalVersion
				})
				returnValue = True
			else:
				outputMessage = colored(projectCurrentVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(projectName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".\n", color="yellow")
				outputMessage += colored("The file will remain unchanged.", color="red")
				print(outputMessage)
				self.ChangedFiles.append({
					"Type": "SQLProject",
					"Path": path,
					"IsChanged": False,
					"PreviousVersion": projectCurrentVersion,
					"NewVersion": None
				})
				returnValue = False
		return returnValue

	def SetPyProjectVersion(self, tomlPath:Path, version:SemVer):
		tomlData:dict = tomllib.loads(tomlPath.read_text())
		tomlData["project"]["version"] = str(version)
		tomlPath.write_text(tomli_w.dumps(tomlData))

	def GetSQLProjectName(self, sqlProjPath:Path) -> str:
		returnValue:str = None
		tree = etree.parse(sqlProjPath)
		projectNameElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'PropertyGroup']/*[local-name() = 'Name']")
		if (projectNameElement is not None and len(projectNameElement) > 0):
			returnValue = projectNameElement[0].text
		return returnValue

	def GetSQLProjectVersion(self, sqlProjPath:Path) -> SemVer:
		returnValue:SemVer = None
		tree = etree.parse(sqlProjPath)
		defaultDatabaseVersionElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'ItemGroup']/*[local-name() = 'SqlCmdVariable' and @Include='DatabaseVersion']/*[local-name() = 'DefaultValue']")
		if (defaultDatabaseVersionElement is not None and len(defaultDatabaseVersionElement) > 0):
			versionText:str = defaultDatabaseVersionElement[0].text
			if (versionText.startswith("v")):
				versionText = versionText[1::]
			returnValue = SemVer.parse(versionText)
		return returnValue

	def SetSQLProjectVersion(self, sqlProjPath:Path, version:SemVer):
		tree = etree.parse(sqlProjPath)
		defaultDatabaseVersionElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'ItemGroup']/*[local-name() = 'SqlCmdVariable' and @Include='DatabaseVersion']/*[local-name() = 'DefaultValue']")
		if (defaultDatabaseVersionElement is not None and len(defaultDatabaseVersionElement) > 0):
			defaultDatabaseVersionElement[0].text = f"v{version}"
		sqlProjPath.write_bytes(etree.tostring(tree, pretty_print=True))

	def EvaluateSQLPublishProfileVersion(self, path:Path, finalVersion:SemVer) -> bool:
		returnValue:bool = False
		profileName:str = self.GetSQLPublishProfileName(path)
		profileCurrentVersion = self.GetSQLPublishProfileVersion(path)
		profileFinalVersion = finalVersion
		outputMessage = colored("Reading ", color="yellow")
		outputMessage += colored(path.relative_to(self.RepoVersionTags.RepoPath), color="red", attrs=["bold", "underline"])
		outputMessage += colored(" ...\n", color="yellow")
		outputMessage += colored("SQL Publish Profile ", color="yellow")
		outputMessage += colored(profileName, color="red", attrs=["bold", "underline"])
		outputMessage += colored(" current version is ", color="yellow")
		outputMessage += colored(profileCurrentVersion, color="red", attrs=["bold", "underline"])
		outputMessage += colored(".\nPress enter to set ", color="yellow")
		outputMessage += colored(profileFinalVersion, color="red", attrs=["bold", "underline"])
		outputMessage += colored(" as the final version for ", color="yellow")
		outputMessage += colored(profileName, color="red", attrs=["bold", "underline"])
		outputMessage += colored(", or enter a new final version: ", color="yellow")
		profileNewVersion:str = input(outputMessage)
		if (len(profileNewVersion) > 0):
			if (profileNewVersion.startswith("v")):
				profileNewVersion = profileNewVersion[1:]
			if (profileCurrentVersion != profileNewVersion):
				profileFinalVersion = SemVer.parse(profileNewVersion)
				outputMessage = colored(profileFinalVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(profileName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".", color="yellow")
				print(outputMessage)
				self.SetSQLPublishProfileVersion(path, profileFinalVersion)
				self.ChangedFiles.append({
					"Type": "SQLPublishProfile",
					"Path": path,
					"IsChanged": True,
					"PreviousVersion": profileCurrentVersion,
					"NewVersion": profileFinalVersion
				})
				returnValue = True
			else:
				outputMessage = colored(profileCurrentVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(profileName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".\n", color="yellow")
				outputMessage += colored("The file will remain unchanged.", color="red")
				print(outputMessage)
				self.ChangedFiles.append({
					"Type": "SQLPublishProfile",
					"Path": path,
					"IsChanged": False,
					"PreviousVersion": profileCurrentVersion,
					"NewVersion": None
				})
				returnValue = False
		else:
			if (profileCurrentVersion != finalVersion):
				profileFinalVersion = finalVersion
				outputMessage = colored(profileFinalVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(profileName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".", color="yellow")
				print(outputMessage)
				self.SetSQLPublishProfileVersion(path, profileFinalVersion)
				self.ChangedFiles.append({
					"Type": "SQLPublishProfile",
					"Path": path,
					"IsChanged": True,
					"PreviousVersion": profileCurrentVersion,
					"NewVersion": profileFinalVersion
				})
				returnValue = True
			else:
				outputMessage = colored(profileCurrentVersion, color="red", attrs=["bold", "underline"])
				outputMessage += colored(" will by used as the final version for ", color="yellow")
				outputMessage += colored(profileName, color="red", attrs=["bold", "underline"])
				outputMessage += colored(".\n", color="yellow")
				outputMessage += colored("The file will remain unchanged.", color="red")
				print(outputMessage)
				self.ChangedFiles.append({
					"Type": "SQLPublishProfile",
					"Path": path,
					"IsChanged": False,
					"PreviousVersion": profileCurrentVersion,
					"NewVersion": None
				})
				returnValue = False
		return returnValue

	def ParseSQLServerConnectionString(self, connectionString:str, removeSensitiveInfo:bool = False) -> dict:
		returnValue:dict = dict()
		for keyValue in connectionString.split(";"):
			keyValue = keyValue.strip()
			if (keyValue):
				keyValuePair:list = keyValue.split("=")
				key:str = ""
				value:str = ""
				if (len(keyValuePair) == 2):
					key = keyValuePair[0].strip()
					value = keyValuePair[1].strip()
					returnValue.update({key: value})
				elif (len(keyValuePair) == 1):
					key = keyValuePair[0].strip()
					value = ""
					returnValue.update({key: value})
		if (removeSensitiveInfo):
			returnValue.pop("Password")
		return returnValue

	def GetSQLPublishProfileName(self, sqlPublishProfilePath:Path) -> str:
		returnValue:str = None
		targetServerName:str = None
		targetDatabaseName:str = None
		targetConnectionString:str = None
		tree = etree.parse(sqlPublishProfilePath)
		targetDatabaseNameElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'PropertyGroup']/*[local-name() = 'TargetDatabaseName']")
		if (targetDatabaseNameElement is not None and len(targetDatabaseNameElement) > 0):
			targetDatabaseName = targetDatabaseNameElement[0].text
		targetConnectionStringElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'PropertyGroup']/*[local-name() = 'TargetConnectionString']")
		if (targetConnectionStringElement is not None and len(targetConnectionStringElement) > 0):
			targetConnectionString = targetConnectionStringElement[0].text
		if (targetConnectionString is not None):
			connString:dict = self.ParseSQLServerConnectionString(targetConnectionString)
			if ("Data Source" in connString.keys()):
				targetServerName = connString["Data Source"]
		returnValue = f"{sqlPublishProfilePath.name} - [{targetServerName}].[{targetDatabaseName}]"
		return returnValue

	def GetSQLPublishProfileVersion(self, sqlPublishProfilePath:Path) -> SemVer:
		returnValue:SemVer = None
		tree = etree.parse(sqlPublishProfilePath)
		databaseVersionElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'ItemGroup']/*[local-name() = 'SqlCmdVariable' and @Include='DatabaseVersion']/*[local-name() = 'Value']")
		if (databaseVersionElement is not None and len(databaseVersionElement) > 0):
			versionText:str = databaseVersionElement[0].text
			if (versionText.startswith("v")):
				versionText = versionText[1::]
			returnValue = SemVer.parse(versionText)
		return returnValue

	def SetSQLPublishProfileVersion(self, sqlPublishProfilePath:Path, version:SemVer):
		tree = etree.parse(sqlPublishProfilePath)
		databaseVersionElement = tree.xpath("//*[local-name() = 'Project']/*[local-name() = 'ItemGroup']/*[local-name() = 'SqlCmdVariable' and @Include='DatabaseVersion']/*[local-name() = 'Value']")
		if (databaseVersionElement is not None and len(databaseVersionElement) > 0):
			databaseVersionElement[0].text = f"v{version}"
		sqlPublishProfilePath.write_bytes(etree.tostring(tree, pretty_print=True))

__all__ = ["CommitType", "VersionSegment",
		   "ConventionalCommitFooter", "ConventionalCommit",
		   "ConventionalCommitStats",
		   "VersionTag", "VersionTags",
		   "Versioning"]

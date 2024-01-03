import os
from typing import List, Optional
from pathlib import Path
from subprocess import Popen
from dataclasses import dataclass
from argparse import ArgumentParser, Namespace

@dataclass
class Package:
    name: str
    version: str
    options: Optional[List[str]]


def run(cmd: str, simulate: bool = False) -> None:
    if simulate:
        print(cmd)
        return
    else:
        ret = Popen(cmd, shell=True).wait()
        if ret != 0:
            raise RuntimeError(f"Failed cmd: {cmd}")


def load(f: str) -> List[Package]:
    raw_packages = open(f, "r").read().splitlines()
    packages: List[Package] = []
    
    for raw_package in raw_packages:
        name, version, options = raw_package.strip().split(",")
        packages.append(Package(name, version, None if options == "" else options.split(";")))
    return packages

def build_packages(packages: List[Package], simulate: bool) -> None:
    profiles = Path(os.getenv("HOME")).joinpath(".conan2").joinpath("profiles")
    for package in packages:
        path = f"recipes/{package.name}/all"
        if package.name == "opencv":
            path = "recipes/opencv/4.x"
        if package.name == "mp-units":
            path = "recipes/mp-units/2.0.0"
        if package.name == "catch2":
            path = "recipes/catch2/3.x.x"
        for profile in [e for e in profiles.iterdir() if e.is_file()]:
            if package.options is not None:
                formatted_options = " ".join([f"-o{option}" for option in package.options])
                run(f"conan create {path} --version={package.version} --profile:all={profile} --build=missing {formatted_options}", simulate)
            else:
                run(f"conan create {path} --version={package.version} --profile:all={profile} --build=missing", simulate)


parser: ArgumentParser = ArgumentParser("Atomicity Conan Manager")
parser.add_argument("PKGS_FILE")
parser.add_argument("-s","--simulate", action='store_true', default=False)
parsed_args: Namespace = parser.parse_args()

simulate: bool = parsed_args.simulate
pkgs_file = parsed_args.PKGS_FILE

# run("conan config install https://github.com/conan-io/hooks.git -sf hooks -tf hooks", simulate)
# run("conan config set hooks.conan-center", simulate)

packages = load(pkgs_file)
build_packages(packages, simulate)
remote = os.getenv('MYREMOTE')
if remote is None:
    raise RuntimeError("Define environment variable MYREMOTE with your remote name")
run(f"conan upload \*/\*:\* -r={remote} -c", simulate)
run("conan remove \*/\*:\* -c", simulate)
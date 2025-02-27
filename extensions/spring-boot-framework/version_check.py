#! /bin/python3

"""Module for checking system and project Java version compatibility."""

import pathlib
import re
import subprocess

# Example output of `java -version`:
# openjdk version "21.0.6" 2025-01-21
# OpenJDK Runtime Environment (build 21.0.6+7-Ubuntu-124.04.1)
# OpenJDK 64-Bit Server VM (build 21.0.6+7-Ubuntu-124.04.1, mixed mode, sharing)
system_java_version_str = subprocess.check_output(
    ["java", "-version"], stderr=subprocess.STDOUT, encoding="utf-8"
)
system_java_version = system_java_version_str.split('"')[1].split(".")[0]

project_java_version = ""
if pathlib.Path("./mvnw").exists():
    # the output is an xml document of project properties
    # i.e. <project.properties>...<java.version>11</java.version></project.properties>
    project_java_version_str = subprocess.check_output(
        [
            "./mvnw",
            "help:evaluate",
            "-Dexpression=project.properties",
            "-q",
            "-DforceStdout",
        ],
        encoding="utf-8",
    )
    pattern = r"<java\.version>(.*?)</java\.version>"
    match = re.search(pattern, project_java_version_str)
    if not match:
        raise RuntimeError("Java version not found in project properties.")
    project_java_version = match.group(1)
elif pathlib.Path("./gradlew"):
    # Example output of `./gradlew javaToolchains`:
    # > Task :javaToolchains
    # ...
    # | Language Version: 11
    project_java_version_str = subprocess.check_output(
        ["./gradlew", "javaToolchains"], encoding="utf-8"
    )
    pattern = r"Language Version: (\d+)"
    match = re.search(pattern, project_java_version_str)
    if not match:
        raise RuntimeError("Java version not found in project toolchain.")
    project_java_version = match.group(1)
else:
    raise RuntimeError("No build tool found.")

try:
    is_compatible_java_version = int(system_java_version) >= int(project_java_version)
except ValueError:
    raise RuntimeError("Failed to detect Java version, please contact the developers.")

if not is_compatible_java_version:
    print("Project Java version higher than build Java version.")
    print(f"System Java version: {system_java_version}")
    print(f"Project Java version: {project_java_version}")
    print(
        "Please override the Java version in the project in the parts > "
        "spring-boot-framework > install-app > override-build section."
    )
    exit(1)

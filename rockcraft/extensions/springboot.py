# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""An extension for the Java Spring Boot application."""

import os
import pathlib
from typing import Any

from overrides import override

from ..errors import ExtensionError
from .extension import Extension, get_extensions_data_dir


class SpringBootFramework(Extension):
    """An extension for constructing Java applications based on the Spring Boot framework."""

    IMAGE_BASE_DIR = "."

    @property
    def name(self) -> str:
        """Return the normalized name of the rockcraft project."""
        return self.yaml_data["name"].replace("-", "_").lower()

    @staticmethod
    @override
    def get_supported_bases() -> tuple[str, ...]:
        """Return supported bases."""
        return "bare", "ubuntu@24.04"

    @staticmethod
    @override
    def is_experimental(base: str | None) -> bool:
        """Check if the extension is in an experimental state."""
        return True

    def get_root_snippet(self) -> dict[str, Any]:
        """Return the root snippet to apply."""
        self._check_project()

        snippet: dict[str, Any] = {
            "run-user": "_daemon_",
            "services": {
                "spring-boot": {
                    "override": "replace",
                    "startup": "enabled",
                    "user": "_daemon_",
                    "working-dir": "/app",
                    "command": 'bash -c "java -jar *.jar"',
                }
            },
        }

        snippet["parts"] = {
            "spring-boot-framework/install-app": self.gen_install_app_part(),
            "spring-boot-framework/runtime": self.gen_runtime_app_part(),
        }

        return snippet

    @override
    def get_part_snippet(self) -> dict[str, Any]:
        """Return the part snippet to apply to existing parts."""
        return {}

    @override
    def get_parts_snippet(self) -> dict[str, Any]:
        """Return the parts to add to parts."""
        return {}

    def _check_project(self) -> None:
        """Check if the project is a Spring Boot project."""
        if not self.mvnw_path.exists() and not self.gradlew_path.exists():
            raise ExtensionError(
                "missing mvnw or gradlew executable file",
                doc_slug="/reference/extensions/spring-boot-framework",
                logpath_report=False,
            )
        if self.mvnw_path.exists() and self.gradlew_path.exists():
            raise ExtensionError(
                "both mvnw and gradlew executable files exist",
                doc_slug="/reference/extensions/spring-boot-framework",
                logpath_report=False,
            )
        if not self.mvnw_path.exists() and not self.gradlew_path.exists():
            raise ExtensionError(
                "missing mvnw or gradlew executable file",
                doc_slug="/reference/extensions/spring-boot-framework",
                logpath_report=False,
            )
        if (self.mvnw_path.exists() and not os.access(self.mvnw_path, os.X_OK)) or (
            self.gradlew_path.exists() and not os.access(self.gradlew_path, os.X_OK)
        ):
            raise ExtensionError(
                "mvnw or gradlew file is not executable",
                doc_slug="/reference/extensions/spring-boot-framework",
                logpath_report=False,
            )

    @property
    def mvnw_path(self) -> pathlib.Path:
        """Return the path to the pom.xml file."""
        return self.project_root / self.IMAGE_BASE_DIR / "mvnw"

    @property
    def gradlew_path(self) -> pathlib.Path:
        """Return the path to the build.gradle file."""
        return self.project_root / self.IMAGE_BASE_DIR / "gradlew"

    @property
    def _rock_base(self) -> str:
        """Return the base of the rockcraft project."""
        return self.yaml_data["base"]

    def gen_install_app_part(self) -> dict[str, Any]:
        """Generate the install-app part."""
        user_build_packages_override = (
            self.yaml_data.get("parts", {})
            .get("spring-boot-framework/install-app", {})
            .get("build-packages", [])
        )
        data_dir = get_extensions_data_dir() / "spring-boot-framework"
        install_app_part = {
            "plugin": "nil",
            "source": f"{self.IMAGE_BASE_DIR}/",
            "build-packages": (
                user_build_packages_override
                if user_build_packages_override
                else [
                    "default-jdk",
                ]
            ),
            "override-build": (
                f"python3 {data_dir}/version_check.py\n"
                "mkdir -p ${CRAFT_PART_INSTALL}/app\n"
                "mkdir -p ${CRAFT_PRIME}/tmp\n"
                "chown 584792 ${CRAFT_PRIME}/tmp\n"
                f"{self._gen_app_build_command()}"
                "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_PART_INSTALL}/app\n"
                "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_STAGE}/\n"
                "craftctl default\n"
            ),
        }
        if self._rock_base == "bare":
            install_app_part["stage-packages"] = ["zlib1g", "libstdc++6"]
        return install_app_part

    def _gen_app_build_command(self) -> str:
        """Generate the override build."""
        if self.mvnw_path.exists():
            return "./mvnw clean install\n"
        return "./gradlew build\n"

    def gen_runtime_app_part(self) -> dict[str, Any]:
        """Return the runtime part."""
        user_build_packages_override = (
            self.yaml_data.get("parts", {})
            .get("spring-boot-framework/runtime", {})
            .get("build-packages")
        )
        runtime_part = {
            "plugin": "jlink",
            "after": ["spring-boot-framework/install-app"],
            "build-packages": (
                user_build_packages_override
                if user_build_packages_override
                else ["default-jdk"]
            ),
        }
        if self._rock_base == "bare":
            runtime_part["stage-packages"] = [
                "bash_bins",
                "ca-certificates_data",
                "coreutils_bins",
            ]

        return runtime_part

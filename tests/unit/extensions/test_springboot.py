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
import sys
from pathlib import Path

import pytest

from rockcraft import extensions
from rockcraft.errors import ExtensionError

_spring_boot_project_name = "test-spring-boot-project"


@pytest.fixture(name="spring_boot_input_yaml")
def spring_boot_input_yaml_fixture():
    return {
        "name": "foo-bar",
        "base": "ubuntu@24.04",
        "build-base": "ubuntu@24.04",
        "platforms": {"amd64": {}},
        "extensions": ["spring-boot-framework"],
    }


@pytest.fixture
def spring_boot_extension(mock_extensions, monkeypatch):
    monkeypatch.setenv("ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS", "1")
    extensions.register("spring-boot-framework", extensions.SpringBootFramework)


@pytest.fixture
def mvnw_file(tmp_path):
    (test_mvnw_file := tmp_path / "mvnw").touch()
    return test_mvnw_file


@pytest.fixture
def mvnw_executable(mvnw_file):
    mvnw_file.chmod(0o755)


@pytest.fixture
def gradlew_file(tmp_path):
    (test_gradlew_file := tmp_path / "gradlew").touch()
    return test_gradlew_file


@pytest.fixture
def gradlew_executable(gradlew_file):
    gradlew_file.chmod(0o755)


@pytest.mark.parametrize(
    "base, expected_yaml_dict",
    [
        pytest.param(
            "bare",
            {
                "base": "bare",
                "build-base": "ubuntu@24.04",
                "name": "foo-bar",
                "platforms": {
                    "amd64": {},
                },
                "run-user": "_daemon_",
                "parts": {
                    "spring-boot-framework/install-app": {
                        "plugin": "nil",
                        "source": "./",
                        "override-build": (
                            f"python3 {Path(sys.prefix) / 'share/rockcraft/extensions'}/"
                            "spring-boot-framework/version_check.py\n"
                            "mkdir -p ${CRAFT_PART_INSTALL}/app\n"
                            "mkdir -p ${CRAFT_PRIME}/tmp\n"
                            "chown 584792 ${CRAFT_PRIME}/tmp\n"
                            "./mvnw clean install\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_PART_INSTALL}/app\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_STAGE}/\n"
                            "craftctl default\n"
                        ),
                        "build-packages": ["default-jdk"],
                        "stage-packages": ["zlib1g", "libstdc++6"],
                    },
                    "spring-boot-framework/runtime": {
                        "plugin": "jlink",
                        "after": ["spring-boot-framework/install-app"],
                        "build-packages": ["default-jdk"],
                        "stage-packages": [
                            "bash_bins",
                            "ca-certificates_data",
                            "coreutils_bins",
                        ],
                    },
                },
                "services": {
                    "spring-boot": {
                        "override": "replace",
                        "startup": "enabled",
                        "user": "_daemon_",
                        "working-dir": "/app",
                        "command": 'bash -c "java -jar *.jar"',
                    }
                },
            },
            id="bare",
        ),
        pytest.param(
            "ubuntu@24.04",
            {
                "base": "ubuntu@24.04",
                "build-base": "ubuntu@24.04",
                "name": "foo-bar",
                "platforms": {
                    "amd64": {},
                },
                "run-user": "_daemon_",
                "parts": {
                    "spring-boot-framework/install-app": {
                        "plugin": "nil",
                        "source": "./",
                        "override-build": (
                            f"python3 {Path(sys.prefix) / 'share/rockcraft/extensions'}/"
                            "spring-boot-framework/version_check.py\n"
                            "mkdir -p ${CRAFT_PART_INSTALL}/app\n"
                            "mkdir -p ${CRAFT_PRIME}/tmp\n"
                            "chown 584792 ${CRAFT_PRIME}/tmp\n"
                            "./mvnw clean install\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_PART_INSTALL}/app\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_STAGE}/\n"
                            "craftctl default\n"
                        ),
                        "build-packages": ["default-jdk"],
                    },
                    "spring-boot-framework/runtime": {
                        "plugin": "jlink",
                        "after": ["spring-boot-framework/install-app"],
                        "build-packages": ["default-jdk"],
                    },
                },
                "services": {
                    "spring-boot": {
                        "override": "replace",
                        "startup": "enabled",
                        "user": "_daemon_",
                        "working-dir": "/app",
                        "command": 'bash -c "java -jar *.jar"',
                    }
                },
            },
            id="ubuntu@24.04",
        ),
    ],
)
@pytest.mark.usefixtures("spring_boot_extension", "mvnw_executable")
def test_spring_boot_extension_default_mvnw(
    tmp_path,
    spring_boot_input_yaml,
    base,
    expected_yaml_dict,
):
    spring_boot_input_yaml["base"] = base
    applied = extensions.apply_extensions(tmp_path, spring_boot_input_yaml)

    assert applied == expected_yaml_dict


@pytest.mark.parametrize(
    "base, expected_yaml_dict",
    [
        pytest.param(
            "bare",
            {
                "base": "bare",
                "build-base": "ubuntu@24.04",
                "name": "foo-bar",
                "platforms": {
                    "amd64": {},
                },
                "run-user": "_daemon_",
                "parts": {
                    "spring-boot-framework/install-app": {
                        "plugin": "nil",
                        "source": "./",
                        "override-build": (
                            f"python3 {Path(sys.prefix) / 'share/rockcraft/extensions'}/"
                            "spring-boot-framework/version_check.py\n"
                            "mkdir -p ${CRAFT_PART_INSTALL}/app\n"
                            "mkdir -p ${CRAFT_PRIME}/tmp\n"
                            "chown 584792 ${CRAFT_PRIME}/tmp\n"
                            "./gradlew build\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_PART_INSTALL}/app\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_STAGE}/\n"
                            "craftctl default\n"
                        ),
                        "build-packages": ["default-jdk"],
                        "stage-packages": ["zlib1g", "libstdc++6"],
                    },
                    "spring-boot-framework/runtime": {
                        "plugin": "jlink",
                        "after": ["spring-boot-framework/install-app"],
                        "build-packages": ["default-jdk"],
                        "stage-packages": [
                            "bash_bins",
                            "ca-certificates_data",
                            "coreutils_bins",
                        ],
                    },
                },
                "services": {
                    "spring-boot": {
                        "override": "replace",
                        "startup": "enabled",
                        "user": "_daemon_",
                        "working-dir": "/app",
                        "command": 'bash -c "java -jar *.jar"',
                    }
                },
            },
            id="bare",
        ),
        pytest.param(
            "ubuntu@24.04",
            {
                "base": "ubuntu@24.04",
                "build-base": "ubuntu@24.04",
                "name": "foo-bar",
                "platforms": {
                    "amd64": {},
                },
                "run-user": "_daemon_",
                "parts": {
                    "spring-boot-framework/install-app": {
                        "plugin": "nil",
                        "source": "./",
                        "override-build": (
                            f"python3 {Path(sys.prefix) / 'share/rockcraft/extensions'}/"
                            "spring-boot-framework/version_check.py\n"
                            "mkdir -p ${CRAFT_PART_INSTALL}/app\n"
                            "mkdir -p ${CRAFT_PRIME}/tmp\n"
                            "chown 584792 ${CRAFT_PRIME}/tmp\n"
                            "./gradlew build\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_PART_INSTALL}/app\n"
                            "cp ${CRAFT_PART_BUILD}/target/*.jar ${CRAFT_STAGE}/\n"
                            "craftctl default\n"
                        ),
                        "build-packages": ["default-jdk"],
                    },
                    "spring-boot-framework/runtime": {
                        "plugin": "jlink",
                        "after": ["spring-boot-framework/install-app"],
                        "build-packages": ["default-jdk"],
                    },
                },
                "services": {
                    "spring-boot": {
                        "override": "replace",
                        "startup": "enabled",
                        "user": "_daemon_",
                        "working-dir": "/app",
                        "command": 'bash -c "java -jar *.jar"',
                    }
                },
            },
            id="ubuntu@24.04",
        ),
    ],
)
@pytest.mark.usefixtures("spring_boot_extension", "gradlew_executable")
def test_spring_boot_extension_default_gradlew(
    tmp_path,
    spring_boot_input_yaml,
    base,
    expected_yaml_dict,
):
    spring_boot_input_yaml["base"] = base
    applied = extensions.apply_extensions(tmp_path, spring_boot_input_yaml)

    assert applied == expected_yaml_dict


@pytest.mark.usefixtures("spring_boot_extension")
def test_spring_boot_extension_no_mvnw_gradlew(tmp_path, spring_boot_input_yaml):
    with pytest.raises(ExtensionError) as exc:
        extensions.apply_extensions(tmp_path, spring_boot_input_yaml)
    assert str(exc.value) == "missing mvnw or gradlew executable file"


@pytest.mark.usefixtures(
    "spring_boot_extension", "mvnw_executable", "gradlew_executable"
)
def test_spring_boot_extension_mvnw_gradlew(tmp_path, spring_boot_input_yaml):
    with pytest.raises(ExtensionError) as exc:
        extensions.apply_extensions(tmp_path, spring_boot_input_yaml)
    assert str(exc.value) == "both mvnw and gradlew executable files exist"


@pytest.mark.usefixtures("spring_boot_extension", "mvnw_file")
def test_spring_boot_extension_mvnw_gradlew(tmp_path, spring_boot_input_yaml):
    with pytest.raises(ExtensionError) as exc:
        extensions.apply_extensions(tmp_path, spring_boot_input_yaml)
    assert str(exc.value) == "mvnw or gradlew file is not executable"

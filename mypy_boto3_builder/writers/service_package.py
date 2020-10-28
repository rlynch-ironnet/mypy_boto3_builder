"""
Service package writer.
"""
import shutil
from pathlib import Path
from typing import List, Tuple

from mypy_boto3_builder.enums.service_module_name import ServiceModuleName
from mypy_boto3_builder.structures.service_package import ServicePackage
from mypy_boto3_builder.writers.utils import blackify, render_jinja2_template, sort_imports


def write_service_package(
    package: ServicePackage, output_path: Path, generate_setup: bool
) -> List[Path]:
    setup_path = output_path / f"{package.service_name.module_name}_package"
    if not generate_setup:
        setup_path = output_path

    modified_paths: List[Path] = []
    package_path = setup_path / package.name

    if setup_path.exists():
        shutil.rmtree(setup_path)

    setup_path.mkdir(exist_ok=True)
    package_path.mkdir(exist_ok=True)

    templates_path = Path("service")
    module_templates_path = templates_path / "service"
    file_paths: List[Tuple[Path, Path]] = []
    if generate_setup:
        file_paths.extend(
            [
                (setup_path / "setup.py", templates_path / "setup.py.jinja2"),
                (setup_path / "README.md", templates_path / "README.md.jinja2"),
            ]
        )
    file_paths.extend(
        [
            (package_path / "version.py", module_templates_path / "version.py.jinja2"),
            (package_path / "__init__.pyi", module_templates_path / "__init__.pyi.jinja2"),
            (package_path / "__init__.py", module_templates_path / "__init__.pyi.jinja2"),
            (package_path / "__main__.py", module_templates_path / "__main__.py.jinja2"),
            (package_path / "py.typed", module_templates_path / "py.typed.jinja2"),
            (
                package_path / ServiceModuleName.client.stub_file_name,
                module_templates_path / ServiceModuleName.client.template_name,
            ),
            (
                package_path / ServiceModuleName.client.file_name,
                module_templates_path / ServiceModuleName.client.template_name,
            ),
        ]
    )
    if package.service_resource:
        file_paths.extend(
            (
                (
                    package_path / ServiceModuleName.service_resource.stub_file_name,
                    module_templates_path / ServiceModuleName.service_resource.template_name,
                ),
                (
                    package_path / ServiceModuleName.service_resource.file_name,
                    module_templates_path / ServiceModuleName.service_resource.template_name,
                ),
            )
        )
    if package.paginators:
        file_paths.extend(
            (
                (
                    package_path / ServiceModuleName.paginator.stub_file_name,
                    module_templates_path / ServiceModuleName.paginator.template_name,
                ),
                (
                    package_path / ServiceModuleName.paginator.file_name,
                    module_templates_path / ServiceModuleName.paginator.template_name,
                ),
            )
        )
    if package.waiters:
        file_paths.extend(
            (
                (
                    package_path / ServiceModuleName.waiter.stub_file_name,
                    module_templates_path / ServiceModuleName.waiter.template_name,
                ),
                (
                    package_path / ServiceModuleName.waiter.file_name,
                    module_templates_path / ServiceModuleName.waiter.template_name,
                ),
            )
        )
    if package.typed_dicts:
        file_paths.extend(
            (
                (
                    package_path / ServiceModuleName.type_defs.stub_file_name,
                    module_templates_path / ServiceModuleName.type_defs.template_name,
                ),
                (
                    package_path / ServiceModuleName.type_defs.file_name,
                    module_templates_path / ServiceModuleName.type_defs.template_name,
                ),
                (
                    package_path / ServiceModuleName.dataclass_defs.file_name,
                    module_templates_path / ServiceModuleName.dataclass_defs.template_name,
                ),
            )
        )

    for file_path, template_path in file_paths:
        content = render_jinja2_template(
            template_path,
            package=package,
            service_name=package.service_name,
        )
        content = blackify(content, file_path)
        content = sort_imports(content, package.service_name.module_name, extension="pyi")

        if not file_path.exists() or file_path.read_text() != content:
            modified_paths.append(file_path)
            file_path.write_text(content)

    return modified_paths

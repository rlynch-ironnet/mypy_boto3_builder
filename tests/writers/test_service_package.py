from pathlib import Path
from unittest.mock import MagicMock, patch

from mypy_boto3_builder.writers.service_package import write_service_package


class TestServicePackage:
    @patch("mypy_boto3_builder.writers.service_package.sort_imports")
    @patch("mypy_boto3_builder.writers.service_package.blackify")
    @patch("mypy_boto3_builder.writers.service_package.render_jinja2_template")
    def test_write_service_package(
        self,
        render_jinja2_template_mock: MagicMock,
        blackify_mock: MagicMock,
        sort_imports_mock: MagicMock,
    ) -> None:
        package_mock = MagicMock()
        output_path_mock = MagicMock()
        output_path_mock.exists.return_value = False
        output_path_mock.__truediv__.return_value = output_path_mock
        assert (
            write_service_package(package_mock, output_path_mock, True) == [output_path_mock] * 18
        )
        render_jinja2_template_mock.assert_called_with(
            Path("service/service/dataclass_defs.pyi.jinja2"),
            package=package_mock,
            service_name=package_mock.service_name,
        )
        blackify_mock.assert_called_with(render_jinja2_template_mock(), output_path_mock)
        sort_imports_mock.assert_called()

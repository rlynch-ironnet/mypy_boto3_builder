from typing import Iterable, List, Optional, Set

from mypy_boto3_builder.enums.service_module_name import ServiceModuleName
from mypy_boto3_builder.import_helpers.import_record import ImportRecord
from mypy_boto3_builder.import_helpers.import_string import ImportString
from mypy_boto3_builder.service_name import ServiceName
from mypy_boto3_builder.structures.client import Client
from mypy_boto3_builder.structures.function import Function
from mypy_boto3_builder.structures.package import Package
from mypy_boto3_builder.structures.paginator import Paginator
from mypy_boto3_builder.structures.service_resource import ServiceResource
from mypy_boto3_builder.structures.waiter import Waiter
from mypy_boto3_builder.type_annotations.fake_annotation import FakeAnnotation
from mypy_boto3_builder.type_annotations.type_typed_dict import TypeTypedDict


class ServicePackage(Package):
    def __init__(
        self,
        name: str,
        pypi_name: str,
        service_name: ServiceName,
        client: Client,
        service_resource: Optional[ServiceResource] = None,
        waiters: Iterable[Waiter] = tuple(),
        paginators: Iterable[Paginator] = tuple(),
        typed_dicts: Iterable[TypeTypedDict] = tuple(),
        helper_functions: Iterable[Function] = tuple(),
    ):
        super().__init__(name=name, pypi_name=pypi_name)
        self.service_name = service_name
        self.client = client
        self.service_resource = service_resource
        self.waiters = list(waiters)
        self.paginators = list(paginators)
        self.typed_dicts = list(typed_dicts)
        self.helper_functions = list(helper_functions)

    def extract_typed_dicts(self) -> List[TypeTypedDict]:
        added_names: List[str] = []
        result: List[TypeTypedDict] = []
        discovered: List[TypeTypedDict] = []
        for type_annotation in sorted(self.get_types()):
            if not isinstance(type_annotation, TypeTypedDict):
                continue

            if type_annotation.name in added_names:
                continue

            result.append(type_annotation)
            added_names.append(type_annotation.name)
            discovered.append(type_annotation)

        while discovered:
            child = discovered.pop()
            child.replace_self_references()
            sub_typed_dicts = child.get_children_typed_dicts()
            for child_typed_dict in sorted(sub_typed_dicts):
                child_typed_dict.stringify = True

                if child_typed_dict.name in added_names:
                    continue

                result.append(child_typed_dict)
                added_names.append(child_typed_dict.name)
                discovered.append(child_typed_dict)

        result.sort()
        return result

    def get_types(self) -> Set[FakeAnnotation]:
        types: Set[FakeAnnotation] = set()
        types.update(self.client.get_types())
        if self.service_resource:
            types.update(self.service_resource.get_types())
        for waiter in self.waiters:
            types.update(waiter.get_types())
        for paginator in self.paginators:
            types.update(paginator.get_types())
        return types

    def get_init_import_records(self) -> List[ImportRecord]:
        import_records: Set[ImportRecord] = set()
        import_records.add(
            ImportRecord(
                ImportString(self.service_name.module_name, ServiceModuleName.client.name),
                self.client.name,
            )
        )
        if self.service_resource:
            import_records.add(
                ImportRecord(
                    ImportString(
                        self.service_name.module_name,
                        ServiceModuleName.service_resource.name,
                    ),
                    self.service_resource.name,
                )
            )
        for waiter in self.waiters:
            import_records.add(
                ImportRecord(
                    ImportString(
                        self.service_name.module_name,
                        ServiceModuleName.waiter.name,
                    ),
                    waiter.name,
                )
            )
        for paginator in self.paginators:
            import_records.add(
                ImportRecord(
                    ImportString(
                        self.service_name.module_name,
                        ServiceModuleName.paginator.name,
                    ),
                    paginator.name,
                )
            )

        return list(sorted(import_records))

    def get_init_all_names(self) -> List[str]:
        names = {self.client.name, self.client.alias_name}
        if self.service_resource:
            names.add(self.service_resource.name)
            names.add(self.service_resource.alias_name)
        for waiter in self.waiters:
            names.add(waiter.name)
        for paginator in self.paginators:
            names.add(paginator.name)

        result = list(names)
        result.sort()
        return result

    def get_client_required_import_records(self) -> List[ImportRecord]:
        import_records: Set[ImportRecord] = set()
        for import_record in self.client.get_required_import_records():
            import_records.add(import_record.get_external(self.service_name.module_name))
            if import_record.fallback:
                import_records.add(ImportRecord(ImportString("sys")))
        for import_record in self.client.exceptions_class.get_required_import_records():
            import_records.add(import_record.get_external(self.service_name.module_name))
            if import_record.fallback:
                import_records.add(ImportRecord(ImportString("sys")))

        return list(sorted(import_records))

    def get_service_resource_required_import_records(self) -> List[ImportRecord]:
        if self.service_resource is None:
            return []

        import_records: Set[ImportRecord] = set()
        class_import_records = self.service_resource.get_required_import_records()
        for import_record in class_import_records:
            import_records.add(import_record.get_external(self.service_name.module_name))
            if import_record.fallback:
                import_records.add(ImportRecord(ImportString("sys")))

        return list(sorted(import_records))

    def get_paginator_required_import_records(self) -> List[ImportRecord]:
        import_records: Set[ImportRecord] = set()
        for paginator in self.paginators:
            for import_record in paginator.get_required_import_records():
                import_records.add(import_record.get_external(self.service_name.module_name))
                if import_record.fallback:
                    import_records.add(ImportRecord(ImportString("sys")))

        return list(sorted(import_records))

    def get_waiter_required_import_records(self) -> List[ImportRecord]:
        import_records: Set[ImportRecord] = set()
        for waiter in self.waiters:
            for import_record in waiter.get_required_import_records():
                import_records.add(import_record.get_external(self.service_name.module_name))
                if import_record.fallback:
                    import_records.add(ImportRecord(ImportString("sys")))

        return list(sorted(import_records))

    def get_type_defs_required_import_records(self) -> List[ImportRecord]:
        if not self.typed_dicts:
            return []

        import_records: Set[ImportRecord] = set()
        import_records.add(ImportRecord(ImportString("sys")))
        import_records.add(
            ImportRecord(
                ImportString("typing"),
                "TypedDict",
                min_version=(3, 8),
                fallback=ImportRecord(ImportString("typing_extensions"), "TypedDict"),
            )
        )
        for types_dict in self.typed_dicts:
            for type_annotation in types_dict.get_children_types():
                import_record = type_annotation.get_import_record()
                if not import_record or import_record.is_builtins():
                    continue
                if import_record.is_type_defs():
                    continue
                import_records.add(import_record.get_external(self.service_name.module_name))

        return list(sorted(import_records))

    def get_dataclass_defs_required_import_records(self) -> List[ImportRecord]:
        if not self.typed_dicts:
            return []

        import_records: Set[ImportRecord] = set()
        import_records.add(ImportRecord(ImportString("sys")))
        import_records.add(ImportRecord(ImportString("typing"), "Optional"))
        import_records.add(ImportRecord(ImportString("dataclasses"), "dataclass"))
        import_records.add(ImportRecord(ImportString("dataclasses"), "field"))
        import_records.add(ImportRecord(ImportString("dataclasses_json"), "DataClassJsonMixin"))
        import_records.add(ImportRecord(ImportString("dataclasses_json"), "config"))
        for types_dict in self.typed_dicts:
            for type_annotation in types_dict.get_children_types():
                import_record = type_annotation.get_import_record()
                if not import_record or import_record.is_builtins():
                    continue
                if import_record.is_type_defs():
                    continue
                import_records.add(import_record.get_external(self.service_name.module_name))

        return list(sorted(import_records))

"""source_test module."""

import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.nodes.croissant_version import CroissantVersion
from mlcroissant._src.structure_graph.nodes.source import Extract
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.structure_graph.nodes.source import get_parent_uid
from mlcroissant._src.structure_graph.nodes.source import is_file_property
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.structure_graph.nodes.source import Transform
from mlcroissant._src.tests.versions import parametrize_conforms_to


def test_source_bool():
    empty_source = Source(transforms=[Transform(replace="\\n/<eos>")])
    assert not empty_source

    whole_source = Source(uid="one/two")
    assert whole_source


@parametrize_conforms_to()
@pytest.mark.parametrize(
    ["json_ld", "expected_source"],
    [
        [
            {
                constants.ML_COMMONS_FIELD: "token-files/content",
            },
            Source(uid="token-files/content", node_type="field"),
        ],
        [
            {
                constants.ML_COMMONS_FIELD: "token-files/content",
                constants.ML_COMMONS_TRANSFORM: [
                    {constants.ML_COMMONS_REPLACE: "\\n/<eos>"},
                    {constants.ML_COMMONS_SEPARATOR: " "},
                ],
            },
            Source(
                uid="token-files/content",
                transforms=[
                    Transform(replace="\\n/<eos>"),
                    Transform(separator=" "),
                ],
                node_type="field",
            ),
        ],
        [
            [
                {
                    constants.ML_COMMONS_FIELD: "token-files/content",
                    constants.ML_COMMONS_TRANSFORM: [
                        {constants.ML_COMMONS_REPLACE: "\\n/<eos>"},
                        {constants.ML_COMMONS_SEPARATOR: " "},
                    ],
                }
            ],
            Source(
                uid="token-files/content",
                transforms=[
                    Transform(replace="\\n/<eos>"),
                    Transform(separator=" "),
                ],
                node_type="field",
            ),
        ],
    ],
)
def test_source_parses_list(conforms_to, json_ld, expected_source):
    issues = Issues()
    assert Source.from_jsonld(issues, conforms_to, json_ld) == expected_source
    assert not issues.errors
    assert not issues.warnings


@pytest.mark.parametrize(
    ["conforms_to", "json_ld", "expected_source"],
    [
        [
            CroissantVersion.V_0_8,
            {
                constants.SCHEMA_ORG_DISTRIBUTION: "my-csv",
                constants.ML_COMMONS_TRANSFORM: [
                    {
                        constants.ML_COMMONS_REPLACE: "\\n/<eos>",
                        constants.ML_COMMONS_SEPARATOR: " ",
                    }
                ],
                constants.ML_COMMONS_EXTRACT: {
                    constants.ML_COMMONS_COLUMN: "my-column"
                },
            },
            Source(
                extract=Extract(column="my-column"),
                uid="my-csv",
                transforms=[Transform(replace="\\n/<eos>", separator=" ")],
                node_type="distribution",
            ),
        ],
        [
            CroissantVersion.V_1_0,
            {
                constants.ML_COMMONS_FILE_OBJECT: "my-csv",
                constants.ML_COMMONS_TRANSFORM: [
                    {
                        constants.ML_COMMONS_REPLACE: "\\n/<eos>",
                        constants.ML_COMMONS_SEPARATOR: " ",
                    }
                ],
                constants.ML_COMMONS_EXTRACT: {
                    constants.ML_COMMONS_COLUMN: "my-column"
                },
            },
            Source(
                extract=Extract(column="my-column"),
                uid="my-csv",
                transforms=[Transform(replace="\\n/<eos>", separator=" ")],
                node_type="fileObject",
            ),
        ],
    ],
)
def test_source_parses_list_with_node_type(conforms_to, json_ld, expected_source):
    issues = Issues()
    assert Source.from_jsonld(issues, conforms_to, json_ld) == expected_source
    assert not issues.errors
    assert not issues.warnings


@pytest.mark.parametrize(
    ["jsonld", "expected_errors"],
    [
        [
            "this is not a list",
            set([
                'Transform "this is not a list" should be a dict with the keys'
                " http://mlcommons.org/schema/format,"
                " http://mlcommons.org/schema/jsonPath,"
                " http://mlcommons.org/schema/regex,"
                " http://mlcommons.org/schema/replace,"
                " http://mlcommons.org/schema/separator"
            ]),
        ],
        [
            [{"not": "the right keys"}],
            set([
                "Transform \"{'not': 'the right keys'}\" should be a dict with at"
                " least one key in http://mlcommons.org/schema/format,"
                " http://mlcommons.org/schema/jsonPath,"
                " http://mlcommons.org/schema/regex,"
                " http://mlcommons.org/schema/replace,"
                " http://mlcommons.org/schema/separator"
            ]),
        ],
    ],
)
def test_transformations_with_errors(jsonld, expected_errors):
    issues = Issues()
    Transform.from_jsonld(issues=issues, jsonld=jsonld)
    assert issues.errors == expected_errors


@pytest.mark.parametrize(
    ["conforms_to", "json_ld"],
    [
        [
            CroissantVersion.V_0_8,
            {
                constants.SCHEMA_ORG_DISTRIBUTION: "my-csv",
                constants.ML_COMMONS_FIELD: "my-record-set/my-field",
            },
        ],
        [
            CroissantVersion.V_1_0,
            {
                constants.ML_COMMONS_FILE_OBJECT: "my-csv",
                constants.ML_COMMONS_FIELD: "my-record-set/my-field",
            },
        ],
        [
            CroissantVersion.V_1_0,
            {
                constants.ML_COMMONS_FILE_SET: "my-csv",
                constants.ML_COMMONS_FIELD: "my-record-set/my-field",
            },
        ],
        [
            CroissantVersion.V_1_0,
            {
                constants.ML_COMMONS_FILE_OBJECT: "my-csv",
                constants.ML_COMMONS_FILE_SET: "my-csv",
            },
        ],
    ],
)
def test_declaring_multiple_sources_in_one(conforms_to, json_ld):
    issues = Issues()
    assert Source.from_jsonld(issues, conforms_to, json_ld) == Source()
    assert len(issues.errors) == 1
    assert (
        "Every http://mlcommons.org/schema/source should declare either"
        in list(issues.errors)[0]
    )


@parametrize_conforms_to()
def test_declaring_multiple_data_extraction_in_one(conforms_to):
    issues = Issues()
    json_ld = {
        constants.ML_COMMONS_EXTRACT: {
            "@id": "jsonld-id",
            constants.ML_COMMONS_COLUMN: "csv_column",
            constants.ML_COMMONS_JSON_PATH: "json_path",
        },
    }
    assert Source.from_jsonld(issues, conforms_to, json_ld) == Source(
        extract=Extract(column="csv_column", json_path="json_path"),
    )
    assert len(issues.errors) == 2
    assert any(
        "http://mlcommons.org/schema/extract should have one of the following"
        " properties"
        in error
        for error in list(issues.errors)
    )


@parametrize_conforms_to()
def test_declaring_wrong_file_property(conforms_to):
    issues = Issues()
    json_ld = {
        constants.ML_COMMONS_EXTRACT: {
            constants.ML_COMMONS_FILE_PROPERTY: "foo",
        },
    }
    Source.from_jsonld(issues, conforms_to, json_ld)
    assert any(
        "Property http://mlcommons.org/schema/fileProperty can only have values in"
        " `fullpath`, `filepath` and `content`. Got: foo"
        in error
        for error in issues.errors
    )


@pytest.mark.parametrize(
    ["source", "expected_column"],
    [
        [
            Source(uid="my-csv", extract=Extract(column="my-csv-column")),
            "my-csv-column",
        ],
        [
            Source(
                uid="my-csv",
                extract=Extract(file_property=FileProperty.content),
            ),
            FileProperty.content,
        ],
        [
            Source(
                uid="my-csv",
                extract=Extract(json_path="/some/json/path"),
            ),
            "/some/json/path",
        ],
        [
            Source(uid="record_set/field_name"),
            "field_name",
        ],
    ],
)
def test_get_field(source: Source, expected_column: str):
    assert source.get_column() == expected_column


def test_is_file_property():
    assert is_file_property("content")
    assert is_file_property("filename")
    assert is_file_property("filepath")
    assert is_file_property("fullpath")
    assert not is_file_property("foo")


def test_check_source_for_valid_json_path():
    issues = Issues()
    Source(uid="uid", extract=Extract(json_path="*.first.second")).check_source(
        issues.add_error
    )
    assert not issues.errors


def test_check_source_for_invalid_json_path():
    issues = Issues()
    Source(uid="uid", extract=Extract(json_path="invalid/json/path")).check_source(
        issues.add_error
    )
    errors = list(issues.errors)
    assert len(errors) == 1
    assert "Wrong JSONPath" in errors[0]


def test_get_parent_uid():
    assert get_parent_uid("foo") == "foo"
    assert get_parent_uid("foo/bar") == "foo"
    assert get_parent_uid("foo/bar/baz") == "foo"

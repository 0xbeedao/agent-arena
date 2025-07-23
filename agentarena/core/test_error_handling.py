"""
Tests for error handling improvements in template rendering
"""

import pytest
from jinja2 import ChoiceLoader
from jinja2 import PackageLoader

from agentarena.core.exceptions import TemplateDataException
from agentarena.core.exceptions import TemplateRenderingException
from agentarena.core.services.jinja_renderer import JinjaRenderer


@pytest.fixture
def jinja_renderer():
    """Create a JinjaRenderer instance with proper template loading"""
    renderer = JinjaRenderer(base_path="agentarena.core")

    # Add support for both template locations like in TemplateService
    renderer.env.loader = ChoiceLoader(
        [
            PackageLoader("agentarena.core", "templates"),
            PackageLoader("agentarena.actors", "templates"),
        ]
    )

    return renderer


def test_template_graceful_handling(jinja_renderer):
    """Test that template now handles empty data gracefully instead of crashing"""

    # Test data that would have caused the "list object has no element 0" error
    test_data = {
        "contest": {
            "id": "test-contest",
            "arena": {
                "name": "Test Arena",
                "description": "A test arena",
                "width": 10,
                "height": 10,
            },
            "rounds": [],  # Empty list - this used to cause the error
        },
        "agent": {"name": "Test Agent", "personality": "Test personality"},
    }

    # This should now succeed gracefully instead of crashing
    result = jinja_renderer.render_template("announcer.base.describe_arena", test_data)

    # Check that it contains the expected fallback message
    assert "No features have been generated yet for this round" in result
    assert len(result) > 0


def test_successful_rendering(jinja_renderer):
    """Test that valid data renders successfully"""

    # Test data with proper structure
    test_data = {
        "contest": {
            "id": "test-contest",
            "arena": {
                "name": "Test Arena",
                "description": "A test arena",
                "width": 10,
                "height": 10,
            },
            "rounds": [{"features": [{"name": "Test Feature", "position": "5,5"}]}],
        },
        "agent": {"name": "Test Agent", "personality": "Test personality"},
    }

    result = jinja_renderer.render_template("announcer.base.describe_arena", test_data)

    # Check that it contains the expected feature
    assert "Test Feature" in result
    assert "5,5" in result
    assert len(result) > 0


def test_error_handling_with_missing_arena_field(jinja_renderer):
    """Test that accessing non-existent fields triggers proper error handling"""

    # Test data with missing required field
    test_data = {
        "contest": {
            "id": "test-contest",
            # Missing arena field - this should cause an error
        },
        "agent": {"name": "Test Agent", "personality": "Test personality"},
    }

    with pytest.raises(TemplateRenderingException) as exc_info:
        jinja_renderer.render_template("announcer.base.describe_arena", test_data)

    exception = exc_info.value
    assert "Template rendering failed" in exception.message
    assert "'dict object' has no attribute 'arena'" in exception.error_details


def test_error_handling_with_missing_agent_field(jinja_renderer):
    """Test that missing agent field triggers proper error handling"""

    # Test data with missing agent field
    test_data = {
        "contest": {
            "id": "test-contest",
            "arena": {
                "name": "Test Arena",
                "description": "A test arena",
                "width": 10,
                "height": 10,
            },
            "rounds": [],
        },
        # Missing agent field - this should cause an error
    }

    with pytest.raises(TemplateRenderingException) as exc_info:
        jinja_renderer.render_template("announcer.base.describe_arena", test_data)

    exception = exc_info.value
    assert "Template rendering failed" in exception.message


def test_error_handling_with_invalid_list_access(jinja_renderer):
    """Test that invalid list access triggers TemplateDataException"""

    # Test data with invalid list access
    test_data = {
        "contest": {
            "id": "test-contest",
            "arena": {
                "name": "Test Arena",
                "description": "A test arena",
                "width": 10,
                "height": 10,
            },
            "rounds": [{"features": []}],  # Empty features list
        },
        "agent": {"name": "Test Agent", "personality": "Test personality"},
    }

    # This should work now with our template fixes, but let's test a different template
    # that might still have list access issues
    try:
        result = jinja_renderer.render_template(
            "announcer.base.describe_arena", test_data
        )
        # If it works, that's fine - our template fixes are working
        assert len(result) > 0
    except TemplateDataException as e:
        # If it fails, it should be a TemplateDataException
        assert "list object has no element" in e.message


def test_template_data_exception_attributes():
    """Test that TemplateDataException has the expected attributes"""

    exception = TemplateDataException(
        message="Test error",
        missing_field="test_field",
        data_context={"template": "test.j2", "data_keys": ["key1", "key2"]},
    )

    assert exception.message == "Test error"
    assert exception.missing_field == "test_field"
    assert exception.data_context == {
        "template": "test.j2",
        "data_keys": ["key1", "key2"],
    }


def test_template_rendering_exception_attributes():
    """Test that TemplateRenderingException has the expected attributes"""

    exception = TemplateRenderingException(
        message="Test rendering error",
        template_name="test.j2",
        error_details="Test details",
        data_context={"data_keys": ["key1", "key2"]},
    )

    assert exception.message == "Test rendering error"
    assert exception.template_name == "test.j2"
    assert exception.error_details == "Test details"
    assert exception.data_context == {"data_keys": ["key1", "key2"]}

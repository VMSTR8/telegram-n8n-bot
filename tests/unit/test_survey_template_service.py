import pytest

from app.models import SurveyTemplate
from app.services import SurveyTemplateService


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyTemplateServiceCreate:
    """
    Unit tests for the creating SurveyTemplateService.
    """

    async def test_create_survey_template_success(self, db: None):
        """
        Test creating a survey template successfully.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        json_content: dict = {
            "info": {
                "title": "shlepa the war crimer",
                "documentTitle": "2025-10-20 04:32"
            }
        }

        template: SurveyTemplate = await service.create_survey_template(
            name='test_template',
            json_content=json_content
        )

        assert template.id is not None
        assert template.name == 'test_template'
        assert template.json_content == json_content

    async def test_create_survey_template_with_empty_json(self, db: None):
        """
        Test creating a survey template with empty JSON content.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        template: SurveyTemplate = await service.create_survey_template(
            name="empty_template",
            json_content={}
        )

        assert template.name == "empty_template"
        assert template.json_content == {}

    async def test_create_survey_template_with_complex_json(self, db: None):
        """
        Test creating a survey template with complex JSON content.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        complex_json: dict = {
            "metadata": {
                "version": "1.0",
                "author": "Test Author"
            },
            "survey": {
                "title": "Complex Survey",
                "sections": [
                    {
                        "name": "Personal Info",
                        "questions": [
                            {"id": 1, "type": "text", "required": True},
                            {"id": 2, "type": "email", "required": False}
                        ]
                    }
                ]
            }
        }

        template: SurveyTemplate = await service.create_survey_template(
            name="complex_template",
            json_content=complex_json
        )

        assert template.name == 'complex_template'
        assert template.json_content == complex_json
        assert template.json_content['metadata']['version'] == '1.0'


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyTemplateServiceGet:
    """
    Unit tests for getting SurveyTemplateService.
    """

    async def test_get_survey_template_by_name_exists(self, db: None):
        """
        Test retrieving an existing survey template by name.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        json_content: dict = {"title": "Existing Template"}
        await service.create_survey_template(
            name='existing_template',
            json_content=json_content
        )

        template: SurveyTemplate | None = await service.get_survey_template_by_name(
            name='existing_template')

        assert template is not None
        assert template.name == 'existing_template'
        assert template.json_content == json_content

    async def test_get_survey_template_by_name_not_exists(self, db: None):
        """
        Test retrieving a non-existing survey template by name.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        template: SurveyTemplate | None = await service.get_survey_template_by_name(
            name='nonexistent_template')

        assert template is None

    async def test_get_survey_template_by_name_case_sensitive(self, db: None):
        """
        Test retrieving a survey template by name with case sensitivity.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        await service.create_survey_template(
            name='test_template',
            json_content={"title": "Test"}
        )

        template: SurveyTemplate | None = await service.get_survey_template_by_name(
            name='TEST_TEMPLATE')
        assert template is None

        template = await service.get_survey_template_by_name(name='test_template')
        assert template is not None

    async def test_get_survey_template_by_name_multiple_templates(self, db: None):
        """
        Test retrieving a survey template when multiple templates exist.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        await service.create_survey_template("template1", {"id": 1})
        await service.create_survey_template("template2", {"id": 2})
        await service.create_survey_template("template3", {"id": 3})

        template: SurveyTemplate | None = await service.get_survey_template_by_name(name='template2')

        assert template is not None
        assert template.name == 'template2'
        assert template.json_content == {'id': 2}


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyTemplateServiceEdgeCases:
    """
    Unit tests for edge cases in SurveyTemplateService.
    """

    async def test_create_survey_template_duplicate_name_raises_error(self, db: None):
        """
        Test that creating a survey template with a duplicate name raises an error.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        await service.create_survey_template("duplicate_name", {"version": 1})

        with pytest.raises(Exception):
            await service.create_survey_template("duplicate_name", {"version": 2})

    async def test_create_survey_template_with_special_characters_in_name(self, db: None):
        """
        Test creating a survey template with special characters in the name.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        special_name: str = 'template_with_underscores_and-dashes_123'
        template: SurveyTemplate = await service.create_survey_template(
            name=special_name,
            json_content={"special": True}
        )

        assert template.name == special_name

        found: SurveyTemplate | None = await service.get_survey_template_by_name(special_name)
        assert found is not None
        assert found.json_content == {"special": True}

    async def test_create_survey_template_with_unicode_name(self, db: None):
        """
        Test creating a survey template with a Unicode name.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        unicode_name: str = 'шаблон_тест_123'
        template: SurveyTemplate = await service.create_survey_template(
            name=unicode_name,
            json_content={"unicode": "тест"}
        )

        assert template.name == unicode_name

        found: SurveyTemplate | None = await service.get_survey_template_by_name(unicode_name)
        assert found is not None
        assert found.json_content == {"unicode": "тест"}

    async def test_get_survey_template_by_name_empty_string(self, db: None):
        """
        Test retrieving a survey template by an empty string name.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        template: SurveyTemplate | None = await service.get_survey_template_by_name(name='')

        assert template is None

    async def test_get_survey_template_by_name_whitespace_name(self, db: None):
        """
        Test retrieving a survey template by a name consisting of whitespace.
        """
        service: SurveyTemplateService = SurveyTemplateService()

        await service.create_survey_template("template with spaces", {"spaced": True})

        template: SurveyTemplate | None = await service.get_survey_template_by_name(name='template with spaces')

        assert template is not None
        assert template.json_content == {"spaced": True}

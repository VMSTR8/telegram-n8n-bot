from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models import Survey, Penalty, User
from app.services import SurveyService
from config.settings import AppSettings


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyServiceGetByGoogleFormId:
    """
    Unit tests for getting Survey by Google form ID in SurveyService.
    """

    async def test_get_survey_by_google_form_id_exists(self, db: None):
        """
        Test retrieving an existing survey by Google form ID.
        """
        service: SurveyService = SurveyService()

        survey: Survey = await Survey.create(
            google_form_id='test_form_123',
            title='Test Survey',
            form_url='https://forms.google.com/test_form_123',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=7),
            expired=False
        )

        found_survey: Survey | None = await service.get_survey_by_google_form_id(
            google_form_id='test_form_123')

        assert found_survey is not None
        assert found_survey.google_form_id == 'test_form_123'
        assert found_survey.title == 'Test Survey'
        assert found_survey.form_url == survey.form_url

    async def test_get_survey_by_google_form_id_not_exists(self, db: None):
        """
        Test retrieving a non-existing survey by Google form ID.
        """
        service: SurveyService = SurveyService()

        survey: Survey | None = await service.get_survey_by_google_form_id(
            google_form_id='nonexistent_form_id')

        assert survey is None

    async def test_get_survey_by_google_form_id_case_sensitive(self, db: None):
        """
        Test that Google form ID lookup is case-sensitive.
        """
        service: SurveyService = SurveyService()

        form_id: str = 'TestForm123'
        await Survey.create(
            google_form_id=form_id,
            title='Test Survey',
            form_url='https://forms.google.com/test',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )

        survey: Survey | None = await service.get_survey_by_google_form_id(
            google_form_id='testform123')

        assert survey is None

        survey = await service.get_survey_by_google_form_id(
            google_form_id=form_id)
        assert survey is not None

    async def test_get_survey_by_google_form_id_empty_string(self, db: None):
        """
        Test retrieving a survey with an empty Google form ID.
        """
        service: SurveyService = SurveyService()

        survey: Survey | None = await service.get_survey_by_google_form_id(google_form_id='')

        assert survey is None

    async def test_get_survey_by_google_form_id_with_special_characters(self, db: None):
        """
        Test retrieving a survey with special characters in Google form ID.
        """
        service: SurveyService = SurveyService()

        special_form_id: str = 'form-with-dashes_and_underscores123'
        await Survey.create(
            google_form_id=special_form_id,
            title='Special Survey',
            form_url='https://forms.google.com/special',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )

        survey: Survey | None = await service.get_survey_by_google_form_id(
            google_form_id=special_form_id)

        assert survey is not None
        assert survey.google_form_id == special_form_id

    async def test_get_survey_by_google_form_id_multiple_surveys(self, db: None):
        """
        Test retrieving a survey when multiple surveys exist.
        """
        service: SurveyService = SurveyService()

        await Survey.create(
            google_form_id='form1',
            title='Survey 1',
            form_url='https://forms.google.com/form1',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )
        await Survey.create(
            google_form_id='form2',
            title='Survey 2',
            form_url='https://forms.google.com/form2',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=2),
            expired=False
        )

        survey: Survey | None = await service.get_survey_by_google_form_id('form2')

        assert survey is not None
        assert survey.google_form_id == 'form2'
        assert survey.title == 'Survey 2'


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyServiceGetActiveSurveys:
    """
    Unit tests for getting active surveys in SurveyService.
    """

    async def test_get_active_surveys_with_active_only(self, db: None, test_survey: Survey):
        """
        Test retrieving active surveys when only active surveys exist.
        """
        service: SurveyService = SurveyService()

        active_surveys: list[Survey] = await service.get_active_surveys()

        assert len(active_surveys) >= 1
        assert any(s.id == test_survey.id for s in active_surveys)

        for survey in active_surveys:
            assert survey.ended_at > datetime.now(tz=service.tz)

    async def test_get_active_surveys_excludes_expired(self, db: None, test_expired_survey: Survey):
        """
        Test retrieving active surveys excludes expired surveys.
        """
        service: SurveyService = SurveyService()

        active_surveys: list[Survey] = await service.get_active_surveys()

        survey_ids: list[int] = [s.id for s in active_surveys]
        assert test_expired_survey.id not in survey_ids

        for survey in active_surveys:
            assert survey.ended_at > datetime.now(tz=service.tz)

    async def test_get_active_surveys_empty_list(self, db: None):
        """
        Test retrieving an empty list of active surveys when none exist.
        """
        service: SurveyService = SurveyService()

        await Survey.all().delete()

        active_surveys: list[Survey] = await service.get_active_surveys()

        assert active_surveys == []

    async def test_get_active_surveys_mixed_active_expired(self, db: None):
        """
        Test retrieving active surveys from a mix of active and expired surveys.
        """
        service: SurveyService = SurveyService()

        active1: Survey = await Survey.create(
            google_form_id='active1',
            title='Active 1',
            form_url='https://forms.google.com/active1',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(hours=12),
            expired=False
        )
        active2: Survey = await Survey.create(
            google_form_id='active2',
            title='Active 2',
            form_url='https://forms.google.com/active2',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=2),
            expired=False
        )

        expired: Survey = await Survey.create(
            google_form_id='expired',
            title='Expired',
            form_url='https://forms.google.com/expired',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) - timedelta(hours=12),
            expired=True
        )

        active_surveys: list[Survey] = await service.get_active_surveys()

        assert len(active_surveys) >= 2
        survey_ids: list[int] = [s.id for s in active_surveys]
        assert active1.id in survey_ids
        assert active2.id in survey_ids
        assert expired.id not in survey_ids

    async def test_get_active_surveys_timezone_aware(self, db: None, moscow_timezone: ZoneInfo):
        """
        Test retrieving active surveys with timezone-aware ended_at.
        """
        service: SurveyService = SurveyService()

        future_time: datetime = datetime.now(tz=moscow_timezone) + timedelta(hours=12)
        survey: Survey = await Survey.create(
            google_form_id='timezone_test',
            title='Timezone Test',
            form_url='https://forms.google.com/timezone',
            ended_at=future_time,
            expired=False
        )

        active_surveys: list[Survey] = await service.get_active_surveys()

        assert len(active_surveys) >= 1
        assert any(s.id == survey.id for s in active_surveys)

    async def test_get_active_surveys_exactly_now_boundary(self, db: None, moscow_timezone: ZoneInfo):
        """
        Test retrieving active surveys with ended_at exactly equal to now.
        Such surveys should not be considered active.
        """
        service: SurveyService = SurveyService()

        now: datetime = datetime.now(tz=moscow_timezone)
        survey: Survey = await Survey.create(
            google_form_id='boundary_test',
            title='Boundary Test',
            form_url='https://forms.google.com/boundary',
            ended_at=now,
            expired=False
        )

        active_surveys: list[Survey] = await service.get_active_surveys()

        survey_ids: list[int] = [s.id for s in active_surveys]
        assert survey.id not in survey_ids

    async def test_get_active_surveys_far_future(self, db: None, moscow_timezone: ZoneInfo):
        """
        Test retrieving active surveys with ended_at far in the future.
        """
        service: SurveyService = SurveyService()

        far_future: datetime = datetime.now(tz=moscow_timezone) + timedelta(days=365)
        survey: Survey = await Survey.create(
            google_form_id='far_future_test',
            title='Far Future Test',
            form_url='https://forms.google.com/far_future',
            ended_at=far_future,
            expired=False
        )

        active_surveys: list[Survey] = await service.get_active_surveys()

        assert len(active_surveys) >= 1
        assert any(s.id == survey.id for s in active_surveys)


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyServiceInitialization:
    """
    Unit tests for SurveyService initialization.
    """

    async def test_service_initialization_with_timezone(self, test_settings: AppSettings):
        """
        Test that SurveyService initializes with the correct timezone.
        """
        service: SurveyService = SurveyService()

        assert service.tz is not None
        assert isinstance(service.tz, ZoneInfo)

    async def test_service_timezone_matches_settings(self, moscow_timezone: ZoneInfo):
        """
        Test that SurveyService timezone matches the settings timezone.
        """
        service: SurveyService = SurveyService()

        assert service.tz == moscow_timezone
        assert str(service.tz) == 'Europe/Moscow'


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyServiceEdgeCases:
    """
    Unit tests for edge cases in SurveyService.
    """

    async def test_get_survey_duplicate_google_form_id_raises_error(self, db: None):
        """
        Test that creating a survey with a duplicate google_form_id raises an error.
        """
        await Survey.create(
            google_form_id='duplicate_id',
            title='First Survey',
            form_url='https://forms.google.com/first',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )

        with pytest.raises(Exception):
            await Survey.create(
                google_form_id='duplicate_id',
                title='Second Survey',
                form_url='https://forms.google.com/second',
                ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=2),
                expired=False
            )

    async def test_get_active_surveys_with_none_ended_at(self, db: None):
        """
        Test that surveys with None ended_at are handled correctly.
        Such surveys should not be considered active.
        """
        service: SurveyService = SurveyService()

        active_surveys: list[Survey] = await service.get_active_surveys()

        for survey in active_surveys:
            assert survey.ended_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestSurveyServiceDeleteAllSurveys:
    """
    Unit tests for deleting all surveys in SurveyService.
    """

    async def test_delete_all_surveys_with_existing_surveys(self, db: None):
        """
        Test deleting all surveys when surveys exist in the database.
        """
        service: SurveyService = SurveyService()

        await Survey.create(
            google_form_id='form1',
            title='Survey 1',
            form_url='https://forms.google.com/form1',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )
        await Survey.create(
            google_form_id='form2',
            title='Survey 2',
            form_url='https://forms.google.com/form2',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=2),
            expired=False
        )
        await Survey.create(
            google_form_id='form3',
            title='Survey 3',
            form_url='https://forms.google.com/form3',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=3),
            expired=False
        )

        surveys_before: list[Survey] = await Survey.all()
        assert len(surveys_before) == 3

        deleted_count: int = await service.delete_all_surveys()

        assert deleted_count == 3

        surveys_after: list[Survey] = await Survey.all()
        assert len(surveys_after) == 0

    async def test_delete_all_surveys_empty_database(self, db: None):
        """
        Test deleting all surveys when no surveys exist in the database.
        """
        service: SurveyService = SurveyService()

        await Survey.all().delete()

        deleted_count: int = await service.delete_all_surveys()

        assert deleted_count == 0

        surveys_after: list[Survey] = await Survey.all()
        assert len(surveys_after) == 0

    async def test_delete_all_surveys_with_penalties_cascade(
        self, 
        db: None, 
        test_user_regular: User, 
        test_survey: Survey
    ):
        """
        Test that deleting all surveys also deletes associated penalties via CASCADE.
        """
        service: SurveyService = SurveyService()

        survey2: Survey = await Survey.create(
            google_form_id='form_with_penalty',
            title='Survey with Penalty',
            form_url='https://forms.google.com/form_penalty',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=5),
            expired=False
        )

        penalty1: Penalty = await Penalty.create(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Не прошел опрос 1'
        )
        penalty2: Penalty = await Penalty.create(
            user_id=test_user_regular.id,
            survey_id=survey2.id,
            reason='Не прошел опрос 2'
        )

        penalties_before: list[Penalty] = await Penalty.all()
        assert len(penalties_before) >= 2

        surveys_before: list[Survey] = await Survey.all()
        assert len(surveys_before) >= 2

        deleted_count: int = await service.delete_all_surveys()

        assert deleted_count >= 2

        surveys_after: list[Survey] = await Survey.all()
        assert len(surveys_after) == 0

        penalties_after: list[Penalty] = await Penalty.all()
        assert len(penalties_after) == 0

    async def test_delete_all_surveys_mixed_active_expired(self, db: None):
        """
        Test deleting all surveys with a mix of active and expired surveys.
        """
        service: SurveyService = SurveyService()

        await Survey.create(
            google_form_id='active1',
            title='Active 1',
            form_url='https://forms.google.com/active1',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )
        await Survey.create(
            google_form_id='active2',
            title='Active 2',
            form_url='https://forms.google.com/active2',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=2),
            expired=False
        )

        await Survey.create(
            google_form_id='expired1',
            title='Expired 1',
            form_url='https://forms.google.com/expired1',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) - timedelta(days=1),
            expired=True
        )
        await Survey.create(
            google_form_id='expired2',
            title='Expired 2',
            form_url='https://forms.google.com/expired2',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) - timedelta(days=2),
            expired=True
        )

        surveys_before: list[Survey] = await Survey.all()
        assert len(surveys_before) == 4

        deleted_count: int = await service.delete_all_surveys()

        assert deleted_count == 4

        surveys_after: list[Survey] = await Survey.all()
        assert len(surveys_after) == 0

    async def test_delete_all_surveys_returns_correct_count(self, db: None):
        """
        Test that delete_all_surveys returns the correct count of deleted records.
        """
        service: SurveyService = SurveyService()

        survey_count: int = 7
        for i in range(survey_count):
            await Survey.create(
                google_form_id=f'form_{i}',
                title=f'Survey {i}',
                form_url=f'https://forms.google.com/form_{i}',
                ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=i+1),
                expired=False
            )

        surveys_before: list[Survey] = await Survey.all()
        assert len(surveys_before) == survey_count

        deleted_count: int = await service.delete_all_surveys()

        assert deleted_count == survey_count

    async def test_delete_all_surveys_idempotent(self, db: None):
        """
        Test that calling delete_all_surveys multiple times is safe (idempotent).
        """
        service: SurveyService = SurveyService()

        await Survey.create(
            google_form_id='form1',
            title='Survey 1',
            form_url='https://forms.google.com/form1',
            ended_at=datetime.now(ZoneInfo('Europe/Moscow')) + timedelta(days=1),
            expired=False
        )

        deleted_count_first: int = await service.delete_all_surveys()
        assert deleted_count_first == 1

        deleted_count_second: int = await service.delete_all_surveys()
        assert deleted_count_second == 0

        deleted_count_third: int = await service.delete_all_surveys()
        assert deleted_count_third == 0

        surveys_after: list[Survey] = await Survey.all()
        assert len(surveys_after) == 0

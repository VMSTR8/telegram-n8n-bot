from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from app.models import Penalty, Survey, User
from app.services.penalty_service import PenaltyService


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceAddPenalty:
    """
    Unit tests for PenaltyService add_penalty method.
    """

    async def test_add_penalty_with_default_date(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test adding a penalty with default date (current date).
        """
        service: PenaltyService = PenaltyService()

        penalty: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Не прошел опрос вовремя'
        )

        assert penalty.id is not None
        assert penalty.user_id == test_user_regular.id
        assert penalty.survey_id == test_survey.id
        assert penalty.reason == 'Не прошел опрос вовремя'
        assert penalty.penalty_date is not None
        assert isinstance(penalty.penalty_date, datetime)

    async def test_add_penalty_creates_db_record(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test that adding a penalty creates a record in the database.
        """
        service: PenaltyService = PenaltyService()

        initial_count: int = await Penalty.all().count()

        penalty: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Тестовый штраф'
        )

        final_count: int = await Penalty.all().count()

        assert final_count == initial_count + 1
        assert penalty.id is not None

    async def test_add_multiple_penalties_to_same_user(
            self, db: None, test_user_regular: User, test_survey: Survey, test_expired_survey: Survey
    ):
        """
        Test adding multiple penalties to the same user for different surveys.
        """
        service: PenaltyService = PenaltyService()

        penalty1: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Первый штраф'
        )

        penalty2: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_expired_survey.id,
            reason='Второй штраф'
        )

        assert penalty1.id != penalty2.id
        assert penalty1.survey_id != penalty2.survey_id
        assert penalty1.user_id == penalty2.user_id

    async def test_add_penalty_to_admin_user(
            self, db: None, test_user_admin: User, test_survey: Survey
    ):
        """
        Test adding a penalty to an admin user.
        """
        service: PenaltyService = PenaltyService()

        penalty: Penalty = await service.add_penalty(
            user_id=test_user_admin.id,
            survey_id=test_survey.id,
            reason='Даже админ может получить штраф'
        )

        assert penalty.id is not None
        assert penalty.user_id == test_user_admin.id


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceGetUserPenalties:
    """
    Unit tests for PenaltyService get_user_penalties method.
    """

    async def test_get_user_penalties_empty_list(self, db: None, test_user_regular: User):
        """
        Test getting penalties for a user with no penalties.
        """
        service: PenaltyService = PenaltyService()

        penalties: list[Penalty] = await service.get_user_penalties(user=test_user_regular)

        assert penalties == []
        assert len(penalties) == 0

    async def test_get_user_penalties_single_penalty(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test getting penalties for a user with a single penalty.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Один штраф'
        )

        penalties: list[Penalty] = await service.get_user_penalties(user=test_user_regular)

        assert len(penalties) == 1
        assert penalties[0].user_id == test_user_regular.id
        assert penalties[0].reason == 'Один штраф'

    async def test_get_user_penalties_multiple_penalties(
            self, db: None, test_user_regular: User, test_survey: Survey, test_expired_survey: Survey
    ):
        """
        Test getting penalties for a user with multiple penalties.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Первый штраф'
        )

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_expired_survey.id,
            reason='Второй штраф'
        )

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Третий штраф'
        )

        penalties: list[Penalty] = await service.get_user_penalties(user=test_user_regular)

        assert len(penalties) == 3
        assert all(p.user_id == test_user_regular.id for p in penalties)

    async def test_get_user_penalties_prefetch_survey(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test that get_user_penalties prefetches survey data.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Тест prefetch'
        )

        penalties: list[Penalty] = await service.get_user_penalties(user=test_user_regular)

        assert len(penalties) == 1
        await penalties[0].fetch_related('survey')
        assert penalties[0].survey.id == test_survey.id

    async def test_get_user_penalties_does_not_return_other_users_penalties(
            self, db: None, test_user_regular: User, test_user_admin: User, test_survey: Survey
    ):
        """
        Test that get_user_penalties returns only penalties for the specified user.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Штраф regular user'
        )

        await service.add_penalty(
            user_id=test_user_admin.id,
            survey_id=test_survey.id,
            reason='Штраф admin user'
        )

        penalties_regular: list[Penalty] = await service.get_user_penalties(user=test_user_regular)
        penalties_admin: list[Penalty] = await service.get_user_penalties(user=test_user_admin)

        assert len(penalties_regular) == 1
        assert len(penalties_admin) == 1
        assert penalties_regular[0].user_id == test_user_regular.id
        assert penalties_admin[0].user_id == test_user_admin.id


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceGetUserPenaltyCount:
    """
    Unit tests for PenaltyService get_user_penalty_count method.
    """

    async def test_get_user_penalty_count_zero(self, db: None, test_user_regular: User):
        """
        Test getting penalty count for a user with no penalties.
        """
        service: PenaltyService = PenaltyService()

        count: int = await service.get_user_penalty_count(user=test_user_regular)

        assert count == 0

    async def test_get_user_penalty_count_single_penalty(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test getting penalty count for a user with a single penalty.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Один штраф'
        )

        count: int = await service.get_user_penalty_count(user=test_user_regular)

        assert count == 1

    async def test_get_user_penalty_count_multiple_penalties(
            self, db: None, test_user_regular: User, test_survey: Survey, test_expired_survey: Survey
    ):
        """
        Test getting penalty count for a user with multiple penalties.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Первый'
        )

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_expired_survey.id,
            reason='Второй'
        )

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Третий'
        )

        count: int = await service.get_user_penalty_count(user=test_user_regular)

        assert count == 3

    async def test_get_user_penalty_count_after_deletion(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test getting penalty count after penalties are deleted.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Будет удален'
        )

        count_before: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_before == 1

        await service.delete_user_penalties(user=test_user_regular)

        count_after: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_after == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceGetAllUsersWithThreePenalties:
    """
    Unit tests for PenaltyService get_all_users_with_three_penalties method.
    """

    async def test_get_all_users_with_three_penalties_empty_list(self, db: None):
        """
        Test getting users with 3+ penalties when no users have penalties.
        """
        service: PenaltyService = PenaltyService()

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert users == []
        assert len(users) == 0

    async def test_get_all_users_with_three_penalties_no_qualified_users(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test getting users with 3+ penalties when users have less than 3 penalties.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Первый'
        )

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Второй'
        )

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert len(users) == 0

    async def test_get_all_users_with_three_penalties_exactly_three(
            self, db: None, test_user_regular: User, test_survey: Survey, test_expired_survey: Survey
    ):
        """
        Test getting users with exactly 3 penalties.
        """
        service: PenaltyService = PenaltyService()

        for i in range(3):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id if i % 2 == 0 else test_expired_survey.id,
                reason=f'Штраф {i + 1}'
            )

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert len(users) == 1
        assert users[0]['telegram_id'] == test_user_regular.telegram_id
        assert users[0]['penalty_count'] == 3
        assert users[0]['callsign'] == test_user_regular.callsign
        assert users[0]['username'] == test_user_regular.username

    async def test_get_all_users_with_three_penalties_more_than_three(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test getting users with more than 3 penalties.
        """
        service: PenaltyService = PenaltyService()

        # Добавляем 5 штрафов
        for i in range(5):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id,
                reason=f'Штраф {i + 1}'
            )

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert len(users) == 1
        assert users[0]['penalty_count'] == 5

    async def test_get_all_users_with_three_penalties_multiple_users(
            self, db: None, test_user_regular: User, test_user_admin: User, test_survey: Survey
    ):
        """
        Test getting multiple users with 3+ penalties.
        """
        service: PenaltyService = PenaltyService()

        for i in range(3):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id,
                reason=f'Regular {i + 1}'
            )

        for i in range(4):
            await service.add_penalty(
                user_id=test_user_admin.id,
                survey_id=test_survey.id,
                reason=f'Admin {i + 1}'
            )

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert len(users) == 2
        telegram_ids: list[int] = [u['telegram_id'] for u in users]
        assert test_user_regular.telegram_id in telegram_ids
        assert test_user_admin.telegram_id in telegram_ids

        regular_user_data = next(u for u in users if u['telegram_id'] == test_user_regular.telegram_id)
        admin_user_data = next(u for u in users if u['telegram_id'] == test_user_admin.telegram_id)

        assert regular_user_data['penalty_count'] == 3
        assert admin_user_data['penalty_count'] == 4

    async def test_get_all_users_with_three_penalties_excludes_users_with_less(
            self, db: None, test_user_regular: User, test_user_admin: User, test_survey: Survey
    ):
        """
        Test that users with less than 3 penalties are excluded.
        """
        service: PenaltyService = PenaltyService()

        for i in range(3):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id,
                reason=f'Regular {i + 1}'
            )

        for i in range(2):
            await service.add_penalty(
                user_id=test_user_admin.id,
                survey_id=test_survey.id,
                reason=f'Admin {i + 1}'
            )

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert len(users) == 1
        assert users[0]['telegram_id'] == test_user_regular.telegram_id


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceDeleteUserPenalties:
    """
    Unit tests for PenaltyService delete_user_penalties method.
    """

    async def test_delete_user_penalties_empty_penalties(self, db: None, test_user_regular: User):
        """
        Test deleting penalties for a user with no penalties.
        """
        service: PenaltyService = PenaltyService()

        await service.delete_user_penalties(user=test_user_regular)

        count: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count == 0

    async def test_delete_user_penalties_single_penalty(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test deleting a single penalty for a user.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Будет удален'
        )

        count_before: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_before == 1

        await service.delete_user_penalties(user=test_user_regular)

        count_after: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_after == 0

    async def test_delete_user_penalties_multiple_penalties(
            self, db: None, test_user_regular: User, test_survey: Survey, test_expired_survey: Survey
    ):
        """
        Test deleting multiple penalties for a user.
        """
        service: PenaltyService = PenaltyService()

        for i in range(5):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id if i % 2 == 0 else test_expired_survey.id,
                reason=f'Штраф {i + 1}'
            )

        count_before: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_before == 5

        await service.delete_user_penalties(user=test_user_regular)

        count_after: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_after == 0

    async def test_delete_user_penalties_preserves_other_users_penalties(
            self, db: None, test_user_regular: User, test_user_admin: User, test_survey: Survey
    ):
        """
        Test that deleting penalties for one user doesn't affect other users.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Regular penalty'
        )

        await service.add_penalty(
            user_id=test_user_admin.id,
            survey_id=test_survey.id,
            reason='Admin penalty'
        )

        await service.delete_user_penalties(user=test_user_regular)

        count_regular: int = await service.get_user_penalty_count(user=test_user_regular)
        count_admin: int = await service.get_user_penalty_count(user=test_user_admin)

        assert count_regular == 0
        assert count_admin == 1

    async def test_delete_user_penalties_can_add_again_after_deletion(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test that penalties can be added again after deletion.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Первый'
        )

        await service.delete_user_penalties(user=test_user_regular)

        count_after_delete: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_after_delete == 0

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='Второй'
        )

        count_after_add: int = await service.get_user_penalty_count(user=test_user_regular)
        assert count_after_add == 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceDeleteAllPenalties:
    """
    Unit tests for PenaltyService delete_all_penalties method.
    """

    async def test_delete_all_penalties_empty_db(self, db: None):
        """
        Test deleting all penalties when database is empty.
        """
        service: PenaltyService = PenaltyService()

        await service.delete_all_penalties()

        total_count: int = await Penalty.all().count()
        assert total_count == 0

    async def test_delete_all_penalties_single_user(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test deleting all penalties with a single user.
        """
        service: PenaltyService = PenaltyService()

        for i in range(3):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id,
                reason=f'Штраф {i + 1}'
            )

        count_before: int = await Penalty.all().count()
        assert count_before == 3

        await service.delete_all_penalties()

        count_after: int = await Penalty.all().count()
        assert count_after == 0

    async def test_delete_all_penalties_multiple_users(
            self, db: None, test_user_regular: User, test_user_admin: User, test_user_creator: User, test_survey: Survey
    ):
        """
        Test deleting all penalties with multiple users.
        """
        service: PenaltyService = PenaltyService()

        users: list[User] = [test_user_regular, test_user_admin, test_user_creator]
        for user in users:
            for i in range(2):
                await service.add_penalty(
                    user_id=user.id,
                    survey_id=test_survey.id,
                    reason=f'Штраф для {user.callsign}'
                )

        count_before: int = await Penalty.all().count()
        assert count_before == 6

        await service.delete_all_penalties()

        count_after: int = await Penalty.all().count()
        assert count_after == 0

        for user in users:
            user_count: int = await service.get_user_penalty_count(user=user)
            assert user_count == 0

    async def test_delete_all_penalties_can_add_again(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test that penalties can be added again after deleting all.
        """
        service: PenaltyService = PenaltyService()

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='До удаления'
        )

        await service.delete_all_penalties()

        count_after_delete: int = await Penalty.all().count()
        assert count_after_delete == 0

        await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='После удаления'
        )

        count_after_add: int = await Penalty.all().count()
        assert count_after_add == 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestPenaltyServiceEdgeCases:
    """
    Unit tests for edge cases in PenaltyService methods.
    """

    async def test_add_penalty_with_empty_reason(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test adding a penalty with an empty reason.
        """
        service: PenaltyService = PenaltyService()

        penalty: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason=''
        )

        assert penalty.id is not None
        assert penalty.reason == ''

    async def test_add_penalty_with_very_long_reason(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test adding a penalty with a very long reason.
        """
        service: PenaltyService = PenaltyService()
        long_reason: str = 'A' * 10000

        penalty: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason=long_reason
        )

        assert penalty.id is not None
        assert penalty.reason == long_reason
        assert len(penalty.reason) == 10000

    async def test_get_all_users_with_three_penalties_boundary_case(
            self, db: None, test_user_regular: User, test_user_admin: User, test_survey: Survey
    ):
        """
        Test boundary case: one user with exactly 3 penalties, another with 2.
        """
        service: PenaltyService = PenaltyService()

        for i in range(3):
            await service.add_penalty(
                user_id=test_user_regular.id,
                survey_id=test_survey.id,
                reason=f'Regular {i + 1}'
            )

        for i in range(2):
            await service.add_penalty(
                user_id=test_user_admin.id,
                survey_id=test_survey.id,
                reason=f'Admin {i + 1}'
            )

        users: list[dict[str, Any]] = await service.get_all_users_with_three_penalties()

        assert len(users) == 1
        assert users[0]['telegram_id'] == test_user_regular.telegram_id
        assert users[0]['penalty_count'] == 3

    async def test_penalty_survives_user_update(
            self, db: None, test_user_regular: User, test_survey: Survey
    ):
        """
        Test that penalties survive when user data is updated.
        """
        service: PenaltyService = PenaltyService()

        penalty: Penalty = await service.add_penalty(
            user_id=test_user_regular.id,
            survey_id=test_survey.id,
            reason='До обновления пользователя'
        )

        test_user_regular.username = 'updated_username'
        await test_user_regular.save()

        penalties: list[Penalty] = await service.get_user_penalties(user=test_user_regular)
        assert len(penalties) == 1
        assert penalties[0].id == penalty.id

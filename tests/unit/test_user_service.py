from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.models import User, UserRole
from app.services.user_service import UserService


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceGetMethods:
    """
    Unit tests for UserService get methods.
    """

    async def test_get_user_by_telegram_id_exists(self, db: None, test_user_regular: User):
        """
        Test retrieving a user by their Telegram ID when the user exists.
        """
        service: UserService = UserService()

        user: User | None = await service.get_user_by_telegram_id(test_user_regular.telegram_id)

        assert user is not None
        assert user.telegram_id == test_user_regular.telegram_id
        assert user.callsign == test_user_regular.callsign
        assert user.role == UserRole.USER

    async def test_get_user_by_telegram_id_not_exists(self, db: None):
        """
        Test retrieving a user by their Telegram ID when the user does not exist.
        """
        service: UserService = UserService()

        user: User | None = await service.get_user_by_telegram_id(999999999)

        assert user is None

    async def test_get_user_by_callsign_exists(self, db: None, test_user_admin: User):
        """
        Test retrieving a user by their callsign when the user exists.
        """
        service: UserService = UserService()

        user: User | None = await service.get_user_by_callsign(test_user_admin.callsign)

        assert user is not None
        assert user.telegram_id == test_user_admin.telegram_id
        assert user.callsign == test_user_admin.callsign
        assert user.role == UserRole.ADMIN

    async def test_get_user_by_callsign_not_exists(self, db: None):
        """
        Test retrieving a user by their callsign when the user does not exist.
        """
        service: UserService = UserService()

        user: User | None = await service.get_user_by_callsign('nonexistent')

        assert user is None

    async def test_get_active_user_by_callsign_exclude_creator(self, db: None, test_user_regular: User):
        """
        Test retrieving an active user by their callsign, excluding the creator.
        """
        service: UserService = UserService()

        user: User | None = await service.get_active_user_by_callsign_exclude_creator(
            test_user_regular.callsign,
        )

        assert user is not None
        assert user.callsign == test_user_regular.callsign
        assert user.active is True
        assert user.role != UserRole.CREATOR

    async def test_get_active_user_by_callsign_exclude_creator_returns_none_for_creator(
            self, db: None, test_user_creator: User
    ):
        """
        Test that retrieving an active user by their callsign returns None when the user is a creator.
        """
        service: UserService = UserService()

        user: User | None = await service.get_active_user_by_callsign_exclude_creator(
            test_user_creator.callsign,
        )

        assert user is None

    async def test_get_active_user_by_callsign_exclude_creator_returns_none_for_inactive(self, db: None):
        """
        Test that retrieving an active user by their callsign returns None when the user is inactive.
        """
        service: UserService = UserService()

        inactive_user: User = User(
            telegram_id=888888888,
            username='inactiveuser',
            callsign='inactiveuser',
            role=UserRole.USER,
            active=False,
        )

        user: User | None = await service.get_active_user_by_callsign_exclude_creator(
            inactive_user.callsign,
        )

        assert user is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceCreateAndUpdate:
    """
    Unit tests for UserService create and update methods.
    """

    async def test_create_user_with_minimal_data(self, db: None):
        """
        Test creating a user with minimal required data.
        """
        service: UserService = UserService()

        new_user: User = await service.create_user(
            telegram_id=777777777,
            callsign='newuser',
        )

        assert new_user.id is not None
        assert new_user.telegram_id == 777777777
        assert new_user.callsign == 'newuser'
        assert new_user.role == UserRole.USER
        assert new_user.active is True
        assert new_user.first_name is None
        assert new_user.last_name is None
        assert new_user.username is None

    async def test_create_user_with_full_data(self, db: None):
        """
        Test creating a user with all possible data fields.
        """
        service: UserService = UserService()

        new_user: User = await service.create_user(
            telegram_id=666666666,
            callsign='fulluser',
            first_name='Full',
            last_name='User',
            username='fulluser123',
            role=UserRole.ADMIN
        )

        assert new_user.id is not None
        assert new_user.telegram_id == 666666666
        assert new_user.callsign == 'fulluser'
        assert new_user.first_name == 'Full'
        assert new_user.last_name == 'User'
        assert new_user.username == 'fulluser123'
        assert new_user.role == UserRole.ADMIN
        assert new_user.active is True

    async def test_create_user_with_creator_role(self, db: None):
        """
        Test creating a user with the CREATOR role.
        """
        service: UserService = UserService()

        new_user: User = await service.create_user(
            telegram_id=555555555,
            callsign='creatoruser',
            role=UserRole.CREATOR
        )

        assert new_user.id is not None
        assert new_user.telegram_id == 555555555
        assert new_user.callsign == 'creatoruser'
        assert new_user.role == UserRole.CREATOR
        assert new_user.active is True

    async def test_update_user_single_field(self, db: None, test_user_regular: User):
        """
        Test updating a single field of an existing user.
        """
        service: UserService = UserService()

        updated_user: User = await service.update_user(
            user_telegram_id=test_user_regular.telegram_id,
            first_name='UpdatedName'
        )

        assert updated_user.first_name == 'UpdatedName'
        assert updated_user.last_name == test_user_regular.last_name
        assert updated_user.username == test_user_regular.username

    async def test_update_user_multiple_fields(self, db: None, test_user_regular: User):
        """
        Test updating multiple fields of an existing user.
        """
        service: UserService = UserService()

        updated_user: User = await service.update_user(
            user_telegram_id=test_user_regular.telegram_id,
            first_name='NewFirstName',
            last_name='NewLastName',
            username='newusername'
        )

        assert updated_user.first_name == 'NewFirstName'
        assert updated_user.last_name == 'NewLastName'
        assert updated_user.username == 'newusername'

    async def test_update_user_callsign(self, db: None, test_user_regular: User):
        """
        Test updating the callsign of an existing user.
        """
        service: UserService = UserService()

        updated_user: User = await service.update_user(
            user_telegram_id=test_user_regular.telegram_id,
            callsign='newcallsign'
        )

        assert updated_user.callsign == 'newcallsign'

        found_user: User | None = await service.get_user_by_callsign('newcallsign')
        assert found_user is not None
        assert found_user.telegram_id == test_user_regular.telegram_id


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceRoleManagement:
    """
    Unit tests for UserService role management methods.
    """

    async def test_set_user_role_success(self, db: None, test_user_regular: User):
        """
        Test setting a user's role successfully.
        """
        service: UserService = UserService()

        result: bool = await service.set_user_role(
            telegram_id=test_user_regular.telegram_id,
            new_role=UserRole.ADMIN
        )

        assert result is True

        updated_user: User | None = await service.get_user_by_telegram_id(telegram_id=test_user_regular.telegram_id)
        assert updated_user is not None
        assert updated_user.role == UserRole.ADMIN
        assert updated_user.is_admin is True

    async def test_set_user_role_user_not_found(self, db: None):
        """
        Test setting a user's role when the user does not exist.
        """
        service: UserService = UserService()

        result: bool = await service.set_user_role(telegram_id=999999999, new_role=UserRole.ADMIN)

        assert result is False

    async def test_set_user_role_from_admin_to_user(self, db: None, test_user_admin: User):
        """
        Test changing a user's role from ADMIN to USER.
        """
        service: UserService = UserService()

        result: bool = await service.set_user_role(
            test_user_admin.telegram_id,
            UserRole.USER
        )

        assert result is True

        updated_user: User | None = await service.get_user_by_telegram_id(telegram_id=test_user_admin.telegram_id)
        assert updated_user is not None
        assert updated_user.role == UserRole.USER
        assert updated_user.is_admin is False

    async def test_set_user_role_updates_timestamp(self, db: None, test_user_regular: User, moscow_timezone: ZoneInfo):
        """
        Test that setting a user's role updates the updated_at timestamp.
        """
        service: UserService = UserService()

        old_updated_at: datetime = test_user_regular.updated_at

        await service.set_user_role(telegram_id=test_user_regular.telegram_id, new_role=UserRole.ADMIN)

        updated_user: User | None = await service.get_user_by_telegram_id(telegram_id=test_user_regular.telegram_id)
        assert updated_user is not None
        assert updated_user.updated_at > old_updated_at


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceActivationDeactivation:
    """
    Unit tests for UserService activation and deactivation methods.
    """

    async def test_activate_user_success(self, db: None):
        """
        Test activating a user successfully.
        """
        service: UserService = UserService()

        inactive_user: User = await User.create(
            telegram_id=444444444,
            callsign='inactive',
            role=UserRole.USER,
            active=False
        )

        result: bool = await service.activate_user(telegram_id=inactive_user.telegram_id)

        assert result is True

        activated_user: User | None = await service.get_user_by_telegram_id(
            telegram_id=inactive_user.telegram_id)
        assert activated_user is not None
        assert activated_user.active is True

    async def test_activate_user_already_active(self, db: None, test_user_regular: User):
        """
        Test activating a user who is already active.
        """
        service: UserService = UserService()

        result: bool = await service.activate_user(telegram_id=test_user_regular.telegram_id)

        assert result is False

    async def test_activate_user_not_found(self, db: None):
        """
        Test activating a user who does not exist.
        """
        service: UserService = UserService()

        result: bool = await service.activate_user(telegram_id=999999999)

        assert result is False

    async def test_deactivate_user_success(self, db: None, test_user_regular: User):
        """
        Test deactivating a user successfully.
        """
        service: UserService = UserService()

        result: bool = await service.deactivate_user(telegram_id=test_user_regular.telegram_id)

        assert result is True

        deactivated_user: User | None = await service.get_user_by_telegram_id(
            telegram_id=test_user_regular.telegram_id)
        assert deactivated_user is not None
        assert deactivated_user.active is False

    async def test_deactivate_user_already_inactive(self, db: None):
        """
        Test deactivating a user who is already inactive.
        """
        service: UserService = UserService()

        # Создаем неактивного пользователя
        inactive_user: User = await User.create(
            telegram_id=333333333,
            callsign="alreadyinactive",
            role=UserRole.USER,
            active=False
        )

        result: bool = await service.deactivate_user(telegram_id=inactive_user.telegram_id)

        assert result is False

    async def test_deactivate_user_not_found(self, db: None):
        """
        Test deactivating a user who does not exist.
        """
        service: UserService = UserService()

        result: bool = await service.deactivate_user(telegram_id=999999999)

        assert result is False

    async def test_activate_deactivate_cycle(self, db: None, test_user_regular: User):
        """
        Test a full cycle of deactivating and then activating a user.
        """
        service: UserService = UserService()

        result1: bool = await service.deactivate_user(telegram_id=test_user_regular.telegram_id)
        assert result1 is True

        user: User | None = await service.get_user_by_telegram_id(telegram_id=test_user_regular.telegram_id)
        assert user is not None
        assert user.active is False

        result2: bool = await service.activate_user(telegram_id=test_user_regular.telegram_id)
        assert result2 is True

        user = await service.get_user_by_telegram_id(telegram_id=test_user_regular.telegram_id)
        assert user is not None
        assert user.active is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceFiltering:
    """
    Unit tests for UserService filtering methods.
    """

    async def test_get_users_by_role_user(self, db: None, test_users_bulk: list[User]):
        """
        Test retrieving users by role USER.
        """
        service: UserService = UserService()

        users: list[User] = await service.get_users_by_role(role=UserRole.USER)

        # in the test_users_bulk fixture, we create 1 creator, 1 admin, and at least 3 regular users
        assert len(users) >= 3
        for user in users:
            assert user.role == UserRole.USER
            assert user.active is True

    async def test_get_users_by_role_admin(self, db: None, test_users_bulk: list[User]):
        """
        Test retrieving users by role ADMIN.
        """
        service: UserService = UserService()

        users: list[User] = await service.get_users_by_role(role=UserRole.ADMIN)

        assert len(users) >= 1
        for user in users:
            assert user.role == UserRole.ADMIN
            assert user.active is True

    async def test_get_users_by_role_creator(self, db: None, test_users_bulk: list[User]):
        """
        Test retrieving users by role CREATOR.
        """
        service: UserService = UserService()

        users: list[User] = await service.get_users_by_role(role=UserRole.CREATOR)

        assert len(users) >= 1
        for user in users:
            assert user.role == UserRole.CREATOR
            assert user.active is True

    async def test_get_users_by_role_excludes_inactive(self, db: None):
        """
        Test that get_users_by_role excludes inactive users.
        """
        service: UserService = UserService()

        await User.create(
            telegram_id=222222222,
            callsign='activeuser',
            role=UserRole.USER,
            active=True
        )
        await User.create(
            telegram_id=111111111,
            callsign='inactiveuser',
            role=UserRole.USER,
            active=False
        )

        users: list[User] = await service.get_users_by_role(role=UserRole.USER)

        callsigns: list[str] = [user.callsign for user in users]
        assert 'activeuser' in callsigns
        assert 'inactiveuser' not in callsigns

    async def test_get_users_without_reservation_exclude_creators(self, db: None, test_users_bulk: list[User]):
        """
        Test retrieving users without reservations, excluding creators.
        """
        service: UserService = UserService()

        users: list[User] = await service.get_users_without_reservation_exclude_creators()

        # All users in test_users_bulk have reserved=False, except for the CREATOR
        assert len(users) >= 4  # 1 ADMIN + 3 USER (w/out CREATOR)
        for user in users:
            assert user.reserved is False
            assert user.active is True
            assert user.role != UserRole.CREATOR

    async def test_get_users_without_reservation_excludes_reserved(self, db: None):
        """
        Test that get_users_without_reservation_exclude_creators excludes users with reservations.
        """
        service: UserService = UserService()

        await User.create(
            telegram_id=101010101,
            callsign='reserveduser',
            role=UserRole.USER,
            active=True,
            reserved=True
        )
        await User.create(
            telegram_id=202020202,
            callsign='unreserveduser',
            role=UserRole.USER,
            active=True,
            reserved=False
        )

        users: list[User] = await service.get_users_without_reservation_exclude_creators()

        callsigns: list[str] = [user.callsign for user in users]
        assert 'unreserveduser' in callsigns
        assert 'reserveduser' not in callsigns

    async def test_get_users_without_reservation_excludes_inactive(self, db: None):
        """
        Test that get_users_without_reservation_exclude_creators excludes inactive users.
        """
        service: UserService = UserService()

        await User.create(
            telegram_id=303030303,
            callsign='activeuser2',
            role=UserRole.USER,
            active=True,
            reserved=False
        )
        await User.create(
            telegram_id=404040404,
            callsign='inactiveuser2',
            role=UserRole.USER,
            active=False,
            reserved=False
        )

        users: list[User] = await service.get_users_without_reservation_exclude_creators()

        callsigns: list[str] = [user.callsign for user in users]
        assert 'activeuser2' in callsigns
        assert 'inactiveuser2' not in callsigns


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceDeletion:
    """
    Unit tests for UserService deletion methods.
    """

    async def test_delete_all_users_exclude_creators(self, db: None, test_users_bulk: list[User]):
        """
        Test deleting all users except those with the CREATOR role.
        """
        service: UserService = UserService()

        deleted_count: int = await service.delete_all_users_exclude_creators()

        assert deleted_count >= 4

        remaining_users: list[User] = await User.all()
        assert len(remaining_users) >= 1
        for user in remaining_users:
            assert user.role == UserRole.CREATOR

    async def test_delete_all_users_exclude_creators_preserves_creators(
            self, db: None, test_user_creator: User, test_user_admin: User, test_user_regular: User
    ):
        """
        Test that delete_all_users_exclude_creators preserves users with the CREATOR role.
        """
        service: UserService = UserService()

        deleted_count: int = await service.delete_all_users_exclude_creators()

        assert deleted_count >= 2

        creator: User | None = await service.get_user_by_telegram_id(
            telegram_id=test_user_creator.telegram_id)
        assert creator is not None
        assert creator.role == UserRole.CREATOR

        admin: User | None = await service.get_user_by_telegram_id(
            telegram_id=test_user_admin.telegram_id)
        regular: User | None = await service.get_user_by_telegram_id(
            telegram_id=test_user_regular.telegram_id)
        assert admin is None
        assert regular is None

    async def test_delete_all_users_exclude_creators_empty_db(self, db: None, test_user_creator: User):
        """
        Test deleting all users except creators in an empty database (only creator exists).
        """
        service: UserService = UserService()

        deleted_count: int = await service.delete_all_users_exclude_creators()

        assert deleted_count == 0

        creator: User | None = await service.get_user_by_telegram_id(
            telegram_id=test_user_creator.telegram_id)
        assert creator is not None

    async def test_delete_all_users_exclude_creators_multiple_creators(self, db: None):
        """
        Test deleting all users except creators when multiple creators exist.
        """
        service: UserService = UserService()

        creator1: User = await User.create(
            telegram_id=111000111,
            callsign='creator1',
            role=UserRole.CREATOR
        )
        creator2: User = await User.create(
            telegram_id=222000222,
            callsign='creator2',
            role=UserRole.CREATOR
        )
        await User.create(
            telegram_id=333000333,
            callsign='regularuser',
            role=UserRole.USER
        )

        deleted_count: int = await service.delete_all_users_exclude_creators()

        assert deleted_count >= 1

        remaining_creator1: User | None = await service.get_user_by_telegram_id(creator1.telegram_id)
        remaining_creator2: User | None = await service.get_user_by_telegram_id(creator2.telegram_id)
        assert remaining_creator1 is not None
        assert remaining_creator2 is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserServiceEdgeCases:
    """
    Unit tests for edge cases in UserService methods.
    """

    async def test_create_user_with_same_telegram_id_raises_error(self, db: None, test_user_regular: User):
        """
        Test that creating a user with an existing Telegram ID raises an error.
        """
        service: UserService = UserService()

        with pytest.raises(Exception):
            await service.create_user(
                telegram_id=test_user_regular.telegram_id,
                callsign="differentcallsign"
            )

    async def test_create_user_with_same_callsign_raises_error(self, db: None, test_user_regular: User):
        """
        Test that creating a user with an existing callsign raises an error.
        """
        service: UserService = UserService()

        with pytest.raises(Exception):
            await service.create_user(
                telegram_id=999888777,
                callsign=test_user_regular.callsign
            )

    async def test_update_nonexistent_user_raises_error(self, db: None):
        """
        Test that updating a non-existent user raises an error.
        """
        service: UserService = UserService()

        with pytest.raises(Exception):
            await service.update_user(user_telegram_id=999999999, first_name="Test")

    async def test_get_users_by_role_empty_result(self, db: None):
        """
        Test that get_users_by_role returns an empty list when no users match the role.
        """
        service: UserService = UserService()

        users: list[User] = await service.get_users_by_role(role=UserRole.ADMIN)

        assert users == []

    async def test_user_properties_after_role_change(self, db: None, test_user_regular: User):
        """
        Test that user properties are consistent after a role change.
        """
        service: UserService = UserService()

        # USER at start
        assert test_user_regular.is_admin is False
        assert test_user_regular.is_creator is False

        # Change to ADMIN
        await service.set_user_role(
            telegram_id=test_user_regular.telegram_id, new_role=UserRole.ADMIN)
        updated_user: User | None = await service.get_user_by_telegram_id(
            telegram_id=test_user_regular.telegram_id)
        assert updated_user is not None
        assert updated_user.is_admin is True
        assert updated_user.is_creator is False

        # Change to CREATOR
        await service.set_user_role(
            telegram_id=test_user_regular.telegram_id, new_role=UserRole.CREATOR)
        updated_user = await service.get_user_by_telegram_id(
            telegram_id=test_user_regular.telegram_id)
        assert updated_user is not None
        assert updated_user.is_admin is True
        assert updated_user.is_creator is True

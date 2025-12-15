from typing import Optional, List, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.database_models import Address, User
from app.schemas.address import AddressCreate, AddressUpdate

class AddressRepository:
    async def get_by_id(self, session: AsyncSession, address_id: UUID) -> Optional[Address]:
        """Получить адрес по UUID с предзагрузкой связанных данных"""
        result = await session.execute(
            select(Address)
            .options(selectinload(Address.user))
            .where(Address.id == address_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filter(
        self,
        session: AsyncSession,
        count: int = 10,
        page: int = 1,
        **kwargs: Any
    ) -> List[Address]:
        """Получить список адресов с фильтрацией, пагинацией и предзагрузкой связей"""
        query = select(Address).options(selectinload(Address.user))
        
        # Применяем фильтры
        for key, value in kwargs.items():
            if hasattr(Address, key) and value is not None:
                query = query.where(getattr(Address, key) == value)
        
        # Применяем пагинацию
        offset = (page - 1) * count if page > 0 else 0
        query = query.offset(offset).limit(count)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_user_addresses(
        self,
        session: AsyncSession,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[Address]:
        """Получить все адреса пользователя, опционально включая неактивные"""
        query = select(Address).where(Address.user_id == user_id)
        
        if not include_inactive:
            query = query.where(Address.is_primary == True)
        
        result = await session.execute(query.order_by(Address.is_primary.desc()))
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        address_data: AddressCreate
    ) -> Address:
        """Создать новый адрес"""
        # Если у пользователя уже есть основной адрес, сделаем его неосновным
        if address_data.is_primary:
            await session.execute(
                Address.__table__.update()
                .where(Address.user_id == address_data.user_id)
                .where(Address.is_primary == True)
                .values(is_primary=False)
            )
        
        address_dict = address_data.model_dump(exclude_unset=True, exclude={"id"})
        new_address = Address(**address_dict)
        
        session.add(new_address)
        await session.commit()
        await session.refresh(new_address)
        
        return new_address

    async def update(
        self,
        session: AsyncSession,
        address_id: UUID,
        address_data: AddressUpdate
    ) -> Address:
        """Обновить данные адреса с бизнес-логикой"""
        address = await self.get_by_id(session, address_id)
        if not address:
            raise ValueError(f"Address with id {address_id} not found")
        
        update_data = address_data.model_dump(exclude_unset=True)
        
        # Если обновляем основной адрес, сняем флаг с других адресов пользователя
        if 'is_primary' in update_data and update_data['is_primary']:
            await session.execute(
                Address.__table__.update()
                .where(Address.user_id == address.user_id)
                .where(Address.is_primary == True)
                .where(Address.id != address_id)
                .values(is_primary=False)
            )
        
        for field, value in update_data.items():
            if hasattr(address, field) and value is not None:
                setattr(address, field, value)
        
        session.add(address)
        await session.commit()
        await session.refresh(address)
        
        return address

    async def delete(
        self,
        session: AsyncSession,
        address_id: UUID
    ) -> None:
        """Удалить адрес с проверкой бизнес-правил"""
        address = await self.get_by_id(session, address_id)
        if not address:
            raise ValueError(f"Address with id {address_id} not found")
        
        # Проверяем, не используется ли адрес в заказах
        from models.database_models import Order  # Импорт внутри функции для избежания циклических зависимостей
        order_count = await session.scalar(
            select(func.count()).where(Order.address_id == address_id)
        )
        
        if order_count > 0:
            raise ValueError("Cannot delete address that is used in existing orders")
        
        await session.delete(address)
        await session.commit()
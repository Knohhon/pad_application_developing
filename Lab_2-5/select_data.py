from database import User
from sqlalchemy import create_engine, select
from sqlalchemy.orm import selectinload, sessionmaker

connect_url = "postgresql://postgres:postgres@localhost/database"

engine = create_engine(connect_url, echo=True)
session_factory = sessionmaker(engine)

with session_factory() as session:
    query = select(User).options(selectinload(User.addresses))
    result = session.execute(query)
    for user in result.scalars().all():
        print(user.username, user.email)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import User, Address, Product, Order

connect_url = 'postgresql://postgres:postgres@localhost/database'

engine = create_engine(
    connect_url,
    echo=True
)

session_factory = sessionmaker(engine)


products = {}

with session_factory() as session:
    user = User(username='John Doe2', email='jdoe2@example.com')

    address = Address(
        user_id=user.id,
        street="Lenina St, 42",
        city="Moscow",
        country="Russia",
        state="Moscow Oblast",
        zip_code="123456",
        is_primary=True
    )
    user.addresses.append(address)
    session.add(user)
    session.flush()

    products = []
    for i in range(5):
        product = Product(
            label=f"Product {i}",
            count_in_package=1
        )
        session.add(product)
        session.flush()
        products.append(product)

    for product in products:
        order = Order(
            user_id=user.id,
            address_id=address.id,
            product_id=product.id
        )
        session.add(order)
    session.commit()
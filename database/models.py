from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    age_verified = Column(Boolean, default=False)
    balance = Column(Float, default=0.0)  # stored in USD
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)  # stored in USD
    stock = Column(Integer, default=0)
    category = Column(String)

    city = Column(
        String,
        nullable=False,
        default="Trójmiasto"
    )

    image = Column(String)


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

    user = relationship("User")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float)  # stored in USD
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    items = relationship(
        "OrderItem",
        back_populates="order"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price_at_purchase = Column(Float)  # stored in USD

    order = relationship(
        "Order",
        back_populates="items"
    )

    product = relationship("Product")


class TopUpRequest(Base):
    """
    A manual balance top-up request created by a user and
    approved / rejected by the admin via inline buttons.
    """

    __tablename__ = "topup_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)  # requested amount in USD
    status = Column(String, default="pending")  # pending / approved / rejected
    proof_file_id = Column(String, nullable=True)  # telegram photo file_id, if a screenshot was sent
    proof_text = Column(String, nullable=True)  # raw text confirmation, if no photo was sent
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User")
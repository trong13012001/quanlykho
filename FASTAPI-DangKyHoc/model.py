from typing import Text
from sqlalchemy import Column,Date,BLOB,ForeignKey
from sqlalchemy.types import String, Integer, Text, Float,Double

from database import Base
from sqlalchemy.orm import  relationship


#Sản phẩm
class ProductSchema(Base):
    __tablename__="Products"
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(100))
    category = Column(String(45))
    brand = Column(String(10))
    serial = Column(String(10), unique=True)
    descripton = Column(String(10000))
    quantity_in_stock = Column(Integer)
    unit_price = Column(Integer)

#Nhà cung cấp
class SuppliersSchema(Base):
    __tablename__="Suppliers"
    supplier_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(45))
    contact_phone = Column(Integer)
    contact_email = Column(String(100),unique=True)

#Đơn hàng
class OrdersSchema(Base):
    __tablename__="Orders"
    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer)
    order_date = Column(Date)
    status = Column(String(20))

#Chi tiết đơn hàng
class OrderDetailsSchema(Base):
    __tablename__="OrderDetails"
    order_detail_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer)
    product_id = Column(Integer)
    quantity = Column(Integer)
    unit_price = Column(Integer)

#Người dùng
class UserSchema(Base):
    __tablename__="User"
    user_id = Column(Integer, primary_key=True, index=True)
    userName = Column(String(45), unique=True)
    userPassword = Column(String(45), unique=True)
    userRole = Column(Integer)

#Lịch sử thay đổi của kho
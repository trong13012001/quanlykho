from typing import Text
from sqlalchemy import Column,Date,BLOB,ForeignKey
from sqlalchemy.types import String, Integer, Text, Float,Double

from database import Base
from sqlalchemy.orm import  relationship


#Sản phẩm
class ProductSchema(Base):
    __tablename__="Products"
    Id = Column(Integer, primary_key=True, index=True)
    productId= Column(String)
    hasBeenDeleted=Column(String)
    supplierId = Column(String)
    productName = Column(String(100))
    categoryId = Column(String(45))
    brand = Column(String(10))
    serial = Column(String(10), unique=True)
    description = Column(String)
    quantity = Column(Integer)
    unitPrice = Column(Integer)

#Nhà cung cấp
class SuppliersSchema(Base):
    __tablename__="Suppliers"
    _supplierId = Column(Integer, primary_key=True, index=True)
    supplierName = Column(String(45))
    contactPhone = Column(Integer)
    contactEmail = Column(String(100),unique=True)
    hasBeenDeleted=Column(String)


#Đơn hàng
class OrdersSchema(Base):
    __tablename__="Orders"
    orderId = Column(Integer, primary_key=True, index=True)
    customerId = Column(Integer)
    orderDate = Column(Date)
    status = Column(String(20))

#Chi tiết đơn hàng
class OrderDetailsSchema(Base):
    __tablename__="OrderDetails"
    orderDetailId = Column(Integer, primary_key=True, index=True)
    orderId = Column(Integer)
    productId = Column(Integer)
    amount = Column(Integer)
    unitPrice = Column(Integer)

#Người dùng
class UserSchema(Base):
    __tablename__="User"
    userId = Column(Integer, primary_key=True, index=True)
    userName = Column(String(45), unique=True)
    userPassword = Column(String(45), unique=True)
    userRole = Column(Integer)

#Phân loại hàng
class CategorySchema(Base):
    __tablename__="Category"
    Id = Column(Integer,primary_key=True, index=True)
    categoryName = Column(String)
    hasBeenDeleted=Column(String)

"""Holds all classes related to defining both nurse and patient devices."""
from dispatcher.models.base import Base
import enum
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum
import uuid


class DeviceStatus(enum.Enum):
    INACTIVE = 0
    ACTIVE = 1
    DEACTIVATED = 2
    RETIRED = 3


class Device(Base):
    """Represents any device that needs to have credentials managed for
    authentication to the WPA2 network."""
    __tablename__ = 'devices'

    id = Column(String(32), primary_key=True)
    serial_number = Column(String(60), primary_key=True)
    devicetype = Column(String(32), ForeignKey('devicetypes.id'))
    status = Column(Enum(DeviceStatus), nullable=False)
    used_by = Column(String(10))
    __mapper_args__ = {'polymorphic_on': used_by}

    def serialize(self, **kwargs):
        id = str(self.id)[2:-1]
        devicetype = str(self.devicetype)[2:-1]
        return {
            'id': id,
            'serial_number': self.serial_number,
            'devicetype': devicetype,
            'status': self.status.name,
            'used_by': self.used_by,
            **kwargs
        }


class PatientDevice(Device):
    """Represents an individual patient device. This is associated with one or
    many patients but is identified to nurses via its location."""
    location = Column(String(50))
    issues = relationship('Issue',
                          primaryjoin='Device.id == \
                          Issue.patientdevice')
    __mapper_args__ = {'polymorphic_identity': 'patient'}

    def __init__(self, devicetype: String,
                 location: String,
                 serial_number: String):
        self.id = str(uuid.uuid4().hex).encode('ascii')
        self.serial_number = serial_number
        self.devicetype = devicetype
        self.status = DeviceStatus.INACTIVE
        self.location = location

    def serialize(self):
        return super(PatientDevice, self)\
            .serialize(location=self.location)


class NurseDevice(Device):
    floor = Column(String(50))
    responses = relationship('Response',
                             order_by='Response.first_issued',
                             primaryjoin='NurseDevice.id == \
                             Response.nursedevice')
    __mapper_args__ = {'polymorphic_identity': 'nurse'}

    def __init__(self, devicetype: String,
                 floor: String,
                 serial_number: String):
        self.id = str(uuid.uuid4().hex).encode('ascii')
        self.serial_number = serial_number
        self.devicetype = devicetype
        self.status = DeviceStatus.INACTIVE
        self.floor = floor

    def serialize(self):
        return super(NurseDevice, self)\
            .serialize(floor=self.floor)


class DeviceType(Base):
    __tablename__ = 'devicetypes'

    id = Column(String(32), primary_key=True)
    product_name = Column(String, nullable=False)
    product_description = Column(String, nullable=False)
    discriminator = Column('used_by', String(50))
    devices = relationship('Device',
                           primaryjoin='DeviceType.id == Device.devicetype',
                           foreign_keys='Device.devicetype')
    __mapper_args__ = {'polymorphic_on': discriminator}

    def serialize(self, **kwargs):
        id = str(self.id)[2:-1]
        return {
            'id': id,
            'product_name': self.product_name,
            'product_description': self.product_description,
            'used_by': self.discriminator,
            **kwargs
        }


class NurseDeviceType(DeviceType):
    __mapper_args__ = {'polymorphic_identity': 'nurse'}
    devices = relationship('Device')

    def __init__(self, product_name: String, product_description: String):
        self.id = str(uuid.uuid4().hex).encode('ascii')
        self.product_name = product_name
        self.product_description = product_description


class PatientDeviceType(DeviceType):
    requesttypes = relationship('RequestType')
    devices = relationship('Device')
    __mapper_args__ = {'polymorphic_identity': 'patient'}

    def __init__(self, product_name: String, product_description: String):
        self.id = str(uuid.uuid4().hex).encode('ascii')
        self.product_name = product_name
        self.product_description = product_description

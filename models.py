from dataclasses import dataclass
from datetime import date, datetime

from extensions import db

"""#####################################################################################################################
########################################## DB TABLE DATACLASSES ########################################################
#####################################################################################################################"""


class AccessLevel(db.Model):
    __tablename__ = 'TBL_ACCESSLEVEL'

    ACCESS_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ACCESSCODE = db.Column(db.Integer, nullable=False)
    DESCRIPTION = db.Column(db.String(100), unique=False, nullable=False)

    def __repr__(self):
        return '<TBL_ACCESSLEVEL (Type: %r) %r>' % (self.ACCESSCODE, self.DESCRIPTION)


@dataclass
class SJFLStatus(db.Model):
    __tablename__ = 'TBL_SJFL_STATUS'

    STATUS_ID: int
    STATUS: str

    STATUS_ID = db.Column(db.Integer, primary_key=True)
    STATUS = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<TBL_SJFL_STATUS (Type: %r) %r>' % (self.STATUS_ID, self.STATUS)


@dataclass
class StatusUpdate(db.Model):
    __tablename__ = 'TBL_STATUS_UPDATE'

    STATUS_ID: int
    REMARKS: str
    SID: int
    STATUS_UPDATE_ID: int

    STATUS_ID = db.Column(db.Integer, db.ForeignKey('TBL_SJFL_STATUS.STATUS_ID'))
    REMARKS = db.Column(db.String(20), nullable=False)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))
    STATUS_UPDATE_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)

    def __repr__(self):
        return '<TBL_STATUS_UPDATE (Type: %r) %r>' % (self.SID, self.STATUS_ID)


@dataclass
class PersonalInformation(db.Model):
    __tablename__ = 'TBL_PERSONAL_INFORMATION'

    SID: int
    FIRST_NAME: str
    LAST_NAME: str
    GENDER: str
    NATIONALITY: str
    BLOOD_GROUP: str
    PHOTO_URL: str
    DATE_OF_BIRTH: date
    STATUS_ID: int
    WELCOME_KIT_DISPATCH_DATE: date
    ADMISSION_DATE: date
    LOCATION: str
    CENTRE: str

    SID = db.Column(db.Integer, primary_key=True, autoincrement=False)
    FIRST_NAME = db.Column(db.String(20), nullable=False)
    LAST_NAME = db.Column(db.String(20))
    GENDER = db.Column(db.String(2), nullable=False)
    NATIONALITY = db.Column(db.String(20))
    BLOOD_GROUP = db.Column(db.String(20))
    PHOTO_URL = db.Column(db.String(200), unique=False, nullable=False)
    DATE_OF_BIRTH = db.Column(db.Date())
    STATUS_ID = db.Column(db.Integer, db.ForeignKey(SJFLStatus.STATUS_ID), nullable=False)
    WELCOME_KIT_DISPATCH_DATE = db.Column(db.Date())
    ADMISSION_DATE = db.Column(db.Date())
    CENTRE = db.Column(db.String(20))
    LOCATION = db.Column(db.String(20))

    def __repr__(self):
        return '<TBL_PERSONAL_INFORMATION (Type: %r)>' % (self.SID)


@dataclass
class Contacts(db.Model):
    __tablename__ = 'TBL_CONTACTS'

    CONTACT_ID: int
    SID: int
    PHONE_NUMBER: str
    LAST_UPDATED: datetime
    CONTACT_RELATION: str

    CONTACT_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))
    PHONE_NUMBER = db.Column(db.String(20), nullable=False)
    LAST_UPDATED = db.Column(db.DateTime())
    CONTACT_RELATION = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<TBL_CONTACTS (Type: %r) %r>' % (self.SID, self.PHONE_NUMBER)


@dataclass
class CommunicationDetails(db.Model):
    __tablename__ = 'TBL_COMMUNICATION_DETAILS'

    COMMUNICATION_ID: int
    ADDRESS: str
    DISTRICT: str
    STATE: str
    COUNTRY: str
    PINCODE: str
    EMAIL: str
    SID: int

    COMMUNICATION_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ADDRESS = db.Column(db.String(200), unique=False, nullable=False)
    DISTRICT = db.Column(db.String(20))
    STATE = db.Column(db.String(20))
    COUNTRY = db.Column(db.String(20))
    PINCODE = db.Column(db.String(20))
    EMAIL = db.Column(db.String(20))
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))

    def __repr__(self):
        return '<TBL_COMMUNICATION_DETAILS (Type: %r)>' % (self.SID)


@dataclass
class FamilyDetails(db.Model):
    __tablename__ = 'TBL_FAMILY_DETAILS'

    DETAIL_ID: int
    FATHER_NAME: str
    FATHER_DOB: date
    FATHER_QUALIFICATION: str
    FATHER_OCCUPATION: str
    FATHER_INCOME_MONTHLY: int
    MOTHER_NAME: str
    MOTHER_DOB: date
    MOTHER_QUALIFICATION: str
    MOTHER_OCCUPATION: str
    MOTHER_INCOME_MONTHLY: int
    SIBLING_DETAILS: str
    REMARKS: str
    SID: int

    DETAIL_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FATHER_NAME = db.Column(db.String(20))
    FATHER_DOB = db.Column(db.Date())
    FATHER_QUALIFICATION = db.Column(db.String(50))
    FATHER_OCCUPATION = db.Column(db.String(50))
    FATHER_INCOME_MONTHLY = db.Column(db.Integer)
    MOTHER_NAME = db.Column(db.String(20))
    MOTHER_DOB = db.Column(db.Date())
    MOTHER_QUALIFICATION = db.Column(db.String(50))
    MOTHER_OCCUPATION = db.Column(db.String(50))
    MOTHER_INCOME_MONTHLY = db.Column(db.Integer)
    SIBLING_DETAILS = db.Column(db.String(50), unique=False, nullable=False)
    REMARKS = db.Column(db.Text())
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))

    def __repr__(self):
        return '<TBL_FAMILY_DETAILS (Type: %r)>' % (self.SID)


class NgoUserRoles(db.Model):
    __tablename__ = 'TBL_NGOUSERROLES'

    ROLE_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RNAME = db.Column(db.String(20))
    ACTIVE = db.Column(db.Integer)
    LEVEL = db.Column(db.Integer, db.ForeignKey('TBL_ACCESSLEVEL.ACCESS_ID'))

    def __repr__(self):
        return '<TBL_NGOUSERROLES (Type: %r) %r>' % (self.ROLE_ID, self.RNAME)


@dataclass
class NgoUsers(db.Model):
    __tablename__ = 'TBL_NGOUSERS'

    UID: int
    UNAME: str
    UEMAIL: str
    ACTIVE: int
    ROLE_ID: int

    UID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UNAME = db.Column(db.String(40))
    UEMAIL = db.Column(db.String(40))
    ACTIVE = db.Column(db.Integer)
    ROLE_ID = db.Column(db.Integer, db.ForeignKey('TBL_NGOUSERROLES.ROLE_ID'))

    def __repr__(self):
        return '<TBL_NGOUSERS (Type: %r) %r>' % (self.UID, self.UNAME)


@dataclass
class FollowUpTypes(db.Model):
    __tablename__ = 'TBL_FOLLOWUPTYPES'

    FOLLOWUPTYPEID: int
    FOLLOWUPTYPE: str

    FOLLOWUPTYPEID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FOLLOWUPTYPE = db.Column(db.String(20))

    def __repr__(self):
        return '<TBL_FOLLOWUPTYPES (Type: %r) %r>' % (self.FOLLOWUPTYPEID, self.FOLLOWUPTYPE)


@dataclass
class FollowupMaster(db.Model):
    __tablename__ = 'TBL_FOLLOWUPMASTER'

    FOLLOWUPID: int
    FOLLOWUPTYPEID: int
    SID: int
    FOLLOWEDUPBY: int
    FOLLOWUPDATE: str

    FOLLOWUPID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FOLLOWUPTYPEID = db.Column(db.Integer, db.ForeignKey('TBL_FOLLOWUPTYPES.FOLLOWUPTYPEID'), nullable=False)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'), nullable=False)
    FOLLOWEDUPBY = db.Column(db.Integer, db.ForeignKey('TBL_NGOUSERS.UID'), unique=False, nullable=False)
    FOLLOWUPDATE = db.Column(db.DateTime(), unique=False, nullable=False)

    def __repr__(self):
        return '<TBL_FOLLOWUPMASTER (Type: %r) %r>' % (self.FOLLOWUPTYPEID, self.FOLLOWUPID)


@dataclass
class FollowupQuestions(db.Model):
    __tablename__ = 'TBL_FOLLOWUPQUESTIONS'

    QUESTIONID: int
    FOLLOWUPTYPEID: int
    QUESTION_TEXT: str
    QUESTION_TYPE: str
    OPTIONS: str
    ACTIVE: int
    ORDERNUMBER: int

    QUESTIONID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FOLLOWUPTYPEID = db.Column(db.Integer, db.ForeignKey('TBL_FOLLOWUPTYPES.FOLLOWUPTYPEID'), nullable=False)
    QUESTION_TEXT = db.Column(db.String(300), unique=False, nullable=False)
    QUESTION_TYPE = db.Column(db.String(50), unique=False, nullable=False)
    OPTIONS = db.Column(db.Text(), unique=False, nullable=True)
    ACTIVE = db.Column(db.Integer, default=0)
    ORDERNUMBER = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<TBL_FOLLOWUPQUESTIONS (Type: %r) %r>' % (self.QUESTION_TYPE, self.QUESTION_TEXT)


@dataclass
class AspirationQuestionWeights(db.Model):
    __tablename__ = 'TBL_ASPIRATION_WEIGHTS'

    QUESTIONID: int
    ATTRIBUTE_W: int
    CATEGORY: str
    CATEGORY_W: int
    PARAMETER: str
    PARAMETER_W: int

    QUESTIONID = db.Column(db.Integer, primary_key=True)
    ATTRIBUTE_W = db.Column(db.Integer, default=0)
    CATEGORY = db.Column(db.String(50), unique=False, nullable=False)
    CATEGORY_W = db.Column(db.Integer, default=0)
    PARAMETER = db.Column(db.String(50), unique=False, nullable=False)
    PARAMETER_W = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<TBL_ASPIRATION_WEIGHTS (QID: %r)>' % self.QUESTIONID


@dataclass
class FollowUpAnswers(db.Model):
    __tablename__ = 'TBL_FOLLOWUPANSWERS'

    ANSWER: str
    FOLLOWUPID: int
    QUESTIONID: int

    ANSWER = db.Column(db.Text(), unique=False, nullable=True)
    FOLLOWUPID = db.Column(db.Integer, db.ForeignKey('TBL_FOLLOWUPMASTER.FOLLOWUPID'), primary_key=True)
    QUESTIONID = db.Column(db.Integer, db.ForeignKey('TBL_FOLLOWUPQUESTIONS.QUESTIONID'), primary_key=True)

    def __repr__(self):
        return '<TBL_FOLLOWUPANSWERS (Type: %r) %r>' % (self.FOLLOWUPID, self.QUESTIONID)


@dataclass
class HospitalInfo(db.Model):
    __tablename__ = 'TBL_HOSPITAL_INFO'

    HOSPITALID: int
    HOSPITAL_NAME: str
    HOSPITAL_REGNO: str
    HOSPITAL_REGDATE: date
    CANCER_TYPE: str
    CANCER_STAGE: str
    DOCTOR_NAME: str
    SID: int

    HOSPITALID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    HOSPITAL_NAME = db.Column(db.String(100), unique=False, nullable=False)
    HOSPITAL_REGNO = db.Column(db.String(100), unique=False, nullable=False)
    HOSPITAL_REGDATE = db.Column(db.Date())
    CANCER_TYPE = db.Column(db.String(50), unique=False, nullable=False)
    CANCER_STAGE = db.Column(db.String(50), unique=False, nullable=False)
    DOCTOR_NAME = db.Column(db.String(50))
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))

    def __repr__(self):
        return '<TBL_HOSPITAL_INFO (Type: %r) %r>' % (self.SID, self.HOSPITAL_NAME)


class InsuranceCards(db.Model):
    __tablename__ = 'TBL_INSURANCECARDS'

    CARDID: int
    SID: int
    CARDLINK: str
    RENEWALDATE: datetime

    CARDID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))
    CARDLINK = db.Column(db.String(512))
    RENEWALDATE = db.DateTime()

    def __repr__(self):
        return '<TBL_INSURANCECARDS (Type: %r) %r>' % (self.SID, self.CARDID)


@dataclass
class NextFollowUp(db.Model):
    __tablename__ = 'TBL_NEXTFOLLOWUP'

    NEXT_FOLLOW_UP_ID: int
    FOLLOWUPTYPEID: int
    NEXTFOLLOWUPDATE: datetime
    LASTMODIFIEDBY: int
    LASTMODIFIEDDATE: datetime
    SID: int

    NEXT_FOLLOW_UP_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FOLLOWUPTYPEID = db.Column(db.Integer, db.ForeignKey('TBL_FOLLOWUPTYPES.FOLLOWUPTYPEID'))
    NEXTFOLLOWUPDATE = db.Column(db.DateTime())
    LASTMODIFIEDBY = db.Column(db.Integer, db.ForeignKey('TBL_NGOUSERS.UID'))
    LASTMODIFIEDDATE = db.Column(db.DateTime())
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))

    def __repr__(self):
        return '<TBL_NEXTFOLLOWUP (Type: %r) %r>' % (self.SID, self.FOLLOWUPTYPEID)

@dataclass
class Plan(db.Model):
    __tablename__ = 'TBL_PLAN'

    PLAN_TBL_ID: int
    SID: int

    PLAN_TBL_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))

    def __repr__(self):
        return '<TBL_PLAN (Type: %r) %r>' % (self.SID, self.PLAN_TBL_ID)

@dataclass
class PlanColX(db.Model):
    __tablename__ = 'TBL_PLAN_COL_X'

    PLAN_COL_X_ID: int
    PLAN_TBL_ID: int
    COL_HEADER: str

    PLAN_COL_X_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PLAN_TBL_ID = db.Column(db.Integer, db.ForeignKey('TBL_PLAN.PLAN_TBL_ID'))
    COL_HEADER = db.Column(db.String(50))

    def __repr__(self):
        return '<TBL_PLAN_COL_X (Type: %r) %r>' % (self.PLAN_TBL_ID, self.COL_HEADER)

@dataclass
class PlanColY(db.Model):
    __tablename__ = 'TBL_PLAN_COL_Y'

    PLAN_COL_Y_ID: int
    PLAN_TBL_ID: int
    COL_HEADER: str

    PLAN_COL_Y_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PLAN_TBL_ID = db.Column(db.Integer, db.ForeignKey('TBL_PLAN.PLAN_TBL_ID'))
    COL_HEADER = db.Column(db.String(50))

    def __repr__(self):
        return '<TBL_PLAN_COL_Y (Type: %r) %r>' % (self.PLAN_TBL_ID, self.COL_HEADER)


@dataclass
class PlanData(db.Model):
    __tablename__ = 'TBL_PLAN_DATA'

    PLAN_DATA: str

    PLAN_DATA_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PLAN_COL_X_ID = db.Column(db.Integer, db.ForeignKey('TBL_PLAN_COL_X.PLAN_COL_X_ID'))
    PLAN_COL_Y_ID = db.Column(db.Integer, db.ForeignKey('TBL_PLAN_COL_Y.PLAN_COL_Y_ID'))
    PLAN_DATA = db.Column(db.String(512))

    def __repr__(self):
        return '<TBL_PLAN_COL_Y (Type: %r) %r>' % (self.PLAN_TBL_ID, self.COL_HEADER)

@dataclass
class Budget(db.Model):
    __tablename__ = 'TBL_BUDGET'

    BUDGET_TBL_ID: int
    SID: int
    BUDGET_NAME: str	

    BUDGET_TBL_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))
    BUDGET_NAME = db.Column(db.String(50))

    def __repr__(self):
        return '<TBL_BUDGET (Type: %r) %r>' % (self.SID, self.BUDGET_TBL_ID)


@dataclass
class BudgetActualSpent(db.Model):
    __tablename__ = 'TBL_BUDGET_ACTUAL_SPENT'

    ACTUAL_ID: int
    BUDGET_TBL_ID: int	
    ITEM: str	
    UNIT: int	
    PERIOD: int	
    UNIT_COST: float	

    ACTUAL_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    BUDGET_TBL_ID = db.Column(db.Integer, db.ForeignKey('TBL_BUDGET.BUDGET_TBL_ID'))
    ITEM = db.Column(db.String(50))
    UNIT = db.Column(db.Integer)
    PERIOD = db.Column(db.Integer)
    UNIT_COST = db.Column(db.Float)

    def __repr__(self):
        return '<TBL_BUDGET_ACTUAL_SPENT (Type: %r) %r>' % (self.BUDGET_TBL_ID, self.ACTUAL_ID)


@dataclass
class BudgetProjected(db.Model):
    __tablename__ = 'TBL_BUDGET_PROJECTED'

    PROJECTED_ID: int
    BUDGET_TBL_ID: int	
    ITEM: str	
    UNIT: int	
    PERIOD: int	
    UNIT_COST: float	

    PROJECTED_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    BUDGET_TBL_ID = db.Column(db.Integer, db.ForeignKey('TBL_BUDGET.BUDGET_TBL_ID'))
    ITEM = db.Column(db.String(50))
    UNIT = db.Column(db.Integer)
    PERIOD = db.Column(db.Integer)
    UNIT_COST = db.Column(db.Float)

    def __repr__(self):
        return '<TBL_BUDGET_PROJECTED (Type: %r) %r>' % (self.BUDGET_TBL_ID, self.PROJECTED_ID)


@dataclass
class SJFLSupport(db.Model):
    __tablename__ = 'TBL_SJFLSUPPORT'

    SJFLSUPPORT_ID: int
    SID: int
    THEMATIC_AREA: str
    FINANCIAL_SUPPORT: str
    NATURE_OF_SUPPORT: str
    SOURCE_OF_SUPPORT: str
    AID_DATE: date
    PROCESSED_BY: str
    PROCESSED_DATE: date
    AMOUNT: int
    FILE_NAME: str
    CREATED_ON: datetime

    SJFLSUPPORT_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('TBL_PERSONAL_INFORMATION.SID'))
    THEMATIC_AREA = db.Column(db.String(50))
    FINANCIAL_SUPPORT = db.Column(db.String(10))
    NATURE_OF_SUPPORT = db.Column(db.String(150))
    SOURCE_OF_SUPPORT = db.Column(db.String(100))
    AID_DATE = db.Column(db.Date())
    PROCESSED_BY = db.Column(db.String(100))
    PROCESSED_DATE = db.Column(db.Date())
    AMOUNT = db.Column(db.Integer)
    FILE_NAME = db.Column(db.String(150))
    CREATED_ON = db.Column(db.DateTime())

    def __repr__(self):
        return '<TBL_SJFLSUPPORT (Type: %r) %r>' % (self.SJFLSUPPORT_ID, self.SID)


"""#####################################################################################################################
########################################### CUSTOM DATACLASSES #########################################################
#####################################################################################################################"""

@dataclass
class NgoUsersWithRole(object):
    UID: int
    UNAME: str
    UEMAIL: str
    ACTIVE: int
    ROLE_ID: int
    ROLE: str


@dataclass
class JoinOp(object):
    SID: int
    LASTFOLLOWEDUPBY: int
    LASTFOLLOWUPDATE: str
    FOLLOWUPTYPEID: int
    FOLLOWUPTYPE: str
    QUESTIONID: int
    QUESTION_TEXT: str
    QUESTION_TYPE: str
    OPTIONS: str
    ANSWER: str
    ORDERNUMBER: int
    CATEGORY: str
    CATEGORY_W: int
    PARAMETER: str
    PARAMETER_W: int
    ATTRIBUTE_W: int


@dataclass
class FollowupQuestionsWithAspirationWeights(object):
    QUESTIONID: int
    FOLLOWUPTYPEID: int
    QUESTION_TEXT: str
    QUESTION_TYPE: str
    OPTIONS: str
    ACTIVE: int
    ORDERNUMBER: int
    CATEGORY: str
    CATEGORY_W: int
    PARAMETER: str
    PARAMETER_W: int
    ATTRIBUTE_W: int


@dataclass
class NextFollowUps(object):
    NEXT_FOLLOW_UP_ID: int
    FOLLOWUPTYPEID: int
    NEXTFOLLOWUPDATE: str
    LASTMODIFIEDBY: int
    LASTMODIFIEDDATE: str
    SID: int
    FOLLOWUPTYPE: str
    S_FIRST_NAME: str
    S_LAST_NAME: str
    S_PHOTO_URL: str


@dataclass
class SearchResult(object):
    SID: int
    FIRST_NAME: str
    LAST_NAME: str
    LINK: str


@dataclass
class InsuranceResult(object):
    SID: int
    CARDLINK: str
    CARDID: int


@dataclass
class PastFollowUpData(object):
    FOLLOWUPID: int
    QUESTIONID: int
    QUESTION_TEXT: str
    ANSWER: str
    SID: int
    FOLLOWUPTYPE: str
    FOLLOWEDUPBY: int
    FOLLOWUPDATE: str

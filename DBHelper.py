# File having all the functions for database calls
from datetime import datetime
import hashlib
import os
import random

from sqlalchemy import text, select, or_, func, and_

import constants
from aspiration_index_calculator import calculate_aspiration_index
from models import *
from configurations import *


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_filename(sid, ext):
    return 'survivor_' + str(sid) + '.' + str(ext)


class DBHelper(object):

    def __init__(self):
        pass

    def test_connection(self):
        sql = text("select 'connection successful' ")
        result = db.session.execute(sql)
        return True if result else False

    def get_followup_questions(self, futype='GENERAL'):
        '''
        The function accepts a followup type and returns the active questions associated with it.
        :param futype: the followup type whose questions need to be retrieved
        :return: list of dicts consisting one question each
        '''
        try:
            # query for followup questions based on followup type
            results = db.session.query(FollowupQuestions.QUESTIONID,
                                       FollowupQuestions.FOLLOWUPTYPEID,
                                       FollowupQuestions.QUESTION_TEXT,
                                       FollowupQuestions.QUESTION_TYPE,
                                       FollowupQuestions.OPTIONS,
                                       FollowupQuestions.ACTIVE,
                                       FollowupQuestions.ORDERNUMBER,
                                       AspirationQuestionWeights.CATEGORY,
                                       AspirationQuestionWeights.CATEGORY_W,
                                       AspirationQuestionWeights.PARAMETER,
                                       AspirationQuestionWeights.PARAMETER_W,
                                       AspirationQuestionWeights.ATTRIBUTE_W) \
                .select_from(FollowUpTypes) \
                .join(FollowupQuestions, FollowupQuestions.FOLLOWUPTYPEID == FollowUpTypes.FOLLOWUPTYPEID) \
                .join(AspirationQuestionWeights, AspirationQuestionWeights.QUESTIONID == FollowupQuestions.QUESTIONID, isouter=True)\
                .filter(and_(FollowUpTypes.FOLLOWUPTYPE == futype.upper())) \
                .order_by(FollowupQuestions.ORDERNUMBER, AspirationQuestionWeights.CATEGORY, AspirationQuestionWeights.PARAMETER)

            # convert the base query to a list of Question object to make it jsonify-able
            converted_results = [
                FollowupQuestionsWithAspirationWeights(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in results.all()]

            return "SUCCESS", converted_results
        except Exception as e:
            return "ERROR", str(e)

    def update_followup_questions(self, futype, data):
        for question_details in data:
            updates = {}
            qid = question_details.get('QUESTIONID')
            qtext = question_details.get('QUESTION_TEXT')
            qtype = question_details.get('QUESTION_TYPE')
            qactive = question_details.get('ACTIVE')
            qopts = question_details.get('OPTIONS')
            qorder = question_details.get('ORDERNUMBER')

            if qtext: updates[FollowupQuestions.QUESTION_TEXT] = qtext
            if qtype: updates[FollowupQuestions.QUESTION_TYPE] = qtype
            if qactive is not None: updates[FollowupQuestions.ACTIVE] = qactive
            if qopts: updates[FollowupQuestions.OPTIONS] = qopts
            if qorder: updates[FollowupQuestions.ORDERNUMBER] = qorder

            try:
                db.session.query(FollowupQuestions).filter(FollowupQuestions.QUESTIONID == qid).update(updates)
            except Exception as e:
                db.session.rollback()
                db.session.flush()
                return str(e)
        db.session.commit()
        return "Successfully updated followup question"

    def update_aspiration_waightage(self, data):
        for weightage_details in data:
            updates = {}
            qid = weightage_details.get('QUESTIONID')
            qtext = weightage_details.get('QUESTION_TEXT')
            qattw = weightage_details.get('ATTRIBUTE_W')
            qcat = weightage_details.get('CATEGORY')
            qcatw = weightage_details.get('CATEGORY_W')
            qpara = weightage_details.get('PARAMETER')
            qparaw = weightage_details.get('PARAMETER_W')

            if qattw: updates[AspirationQuestionWeights.ATTRIBUTE_W] = qattw
            if qcat: updates[AspirationQuestionWeights.CATEGORY] = qcat
            if qcatw: updates[AspirationQuestionWeights.CATEGORY_W] = qcatw
            if qpara: updates[AspirationQuestionWeights.PARAMETER] = qpara
            if qparaw: updates[AspirationQuestionWeights.PARAMETER_W] = qparaw

            try:
                # update question text if modified
                if qtext:
                    db.session.query(FollowupQuestions).filter(FollowupQuestions.QUESTIONID == qid).update(
                        {FollowupQuestions.QUESTION_TEXT: qtext})
                # update all asked weightages
                db.session.query(AspirationQuestionWeights).filter(AspirationQuestionWeights.QUESTIONID == qid).update(updates)
            except Exception as e:
                db.session.rollback()
                db.session.flush()
                return str(e)
        # commit changes
        db.session.commit()
        return "Successfully updated aspiration question weightages"

    def add_followup_questions(self, data):
        # loop into question details received, and form a list of FollowupQuestions objects to add
        questions_to_add = []
        for question_details in data:
            # get followup type id
            result = db.session.query(FollowUpTypes).filter(
                FollowUpTypes.FOLLOWUPTYPE == question_details.get('FOLLOWUPTYPE').upper()
            ).all()
            questions_to_add.append(
                FollowupQuestions(
                    FOLLOWUPTYPEID=result[0].FOLLOWUPTYPEID,
                    QUESTION_TEXT=question_details.get('QUESTION_TEXT'),
                    QUESTION_TYPE=question_details.get('QUESTION_TYPE'),
                    OPTIONS=question_details.get('OPTIONS'),
                    ACTIVE=1,  # default value while additions must be active
                    ORDERNUMBER=random.randint(500, 1000))
            )

        # make entries in the database
        try:
            db.session.add_all(questions_to_add)
            db.session.commit()
            return "Successfully added followup questions"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def add_aspiration_question(self, data):

        # get followup type id
        result = db.session.query(FollowUpTypes).filter(
            FollowUpTypes.FOLLOWUPTYPE == data.get('FOLLOWUPTYPE').upper()
        ).all()

        aspiration_question = FollowupQuestions(
            FOLLOWUPTYPEID=result[0].FOLLOWUPTYPEID,
            QUESTION_TEXT=data.get('QUESTION_TEXT'),
            QUESTION_TYPE=data.get('QUESTION_TYPE'),
            OPTIONS=data.get('OPTIONS'),
            ACTIVE=1,  # default value while additions must be active
            ORDERNUMBER=1001)  # default value while addition of aspitation question as it will be sorted by cat/param
        try:
            db.session.add(aspiration_question)

            # required to get the newly added ID, as we are not committing we wont get that unless flushed and refreshed
            db.session.flush()
            db.session.refresh(aspiration_question)

            aspiration_weight_details = AspirationQuestionWeights(
                QUESTIONID=aspiration_question.QUESTIONID,
                ATTRIBUTE_W=data.get('ATTRIBUTE_W'),
                CATEGORY=data.get('CATEGORY'),
                CATEGORY_W=data.get('CATEGORY_W'),
                PARAMETER=data.get('PARAMETER'),
                PARAMETER_W=data.get('PARAMETER_W')
            )

            # make entries in the database
            db.session.add(aspiration_weight_details)
            db.session.commit()
            return "Successfully added aspiration index question"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def get_followup_questions_with_answers_for_survivor(self, sid, futype):
        '''
        Returns latest record of a particular followup type for a survivor
        :param sid: survivors id
        :param futype: followup type
        :return:
        '''
        try:
            # create a subquery to get max date for a sid-followuptype
            subquery_sid_latest_followups = db.session.query(FollowupMaster.SID,
                                                             FollowupMaster.FOLLOWUPTYPEID,
                                                             func.max(FollowupMaster.FOLLOWUPDATE).label("MAXDATE")) \
                .filter(FollowupMaster.SID == sid) \
                .group_by(FollowupMaster.SID, FollowupMaster.FOLLOWUPTYPEID).subquery()

            # join followup tables to get the latest followup data of a particular type
            results = db.session.query(FollowupMaster.SID,
                                       FollowupMaster.FOLLOWEDUPBY,
                                       FollowupMaster.FOLLOWUPDATE,
                                       FollowupMaster.FOLLOWUPTYPEID,
                                       FollowUpTypes.FOLLOWUPTYPE,
                                       FollowupQuestions.QUESTIONID,
                                       FollowupQuestions.QUESTION_TEXT,
                                       FollowupQuestions.QUESTION_TYPE,
                                       FollowupQuestions.OPTIONS,
                                       FollowUpAnswers.ANSWER,
                                       FollowupQuestions.ORDERNUMBER,
                                       AspirationQuestionWeights.CATEGORY,
                                       AspirationQuestionWeights.CATEGORY_W,
                                       AspirationQuestionWeights.PARAMETER,
                                       AspirationQuestionWeights.PARAMETER_W,
                                       AspirationQuestionWeights.ATTRIBUTE_W
                                       ) \
                .select_from(FollowupMaster) \
                .join(FollowUpTypes, FollowUpTypes.FOLLOWUPTYPEID == FollowupMaster.FOLLOWUPTYPEID) \
                .join(subquery_sid_latest_followups,
                      subquery_sid_latest_followups.c.MAXDATE == FollowupMaster.FOLLOWUPDATE) \
                .join(FollowupQuestions, FollowupQuestions.FOLLOWUPTYPEID == FollowupMaster.FOLLOWUPTYPEID) \
                .join(FollowUpAnswers, and_(FollowUpAnswers.QUESTIONID == FollowupQuestions.QUESTIONID,
                                            FollowUpAnswers.FOLLOWUPID == FollowupMaster.FOLLOWUPID), isouter=True) \
                .join(AspirationQuestionWeights, AspirationQuestionWeights.QUESTIONID == FollowupQuestions.QUESTIONID,
                      isouter=True) \
                .filter(and_(
                    FollowUpTypes.FOLLOWUPTYPE == futype,
                    FollowupMaster.SID == sid,
                    FollowupQuestions.ACTIVE == 1)) \
                .order_by(FollowupQuestions.ORDERNUMBER) \
                .all()

            converted_results = [JoinOp(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12], x[13], x[14], x[15]) for x in results]

            # return the received data or a set of active questions without answers
            return self.get_followup_questions(futype) if len(converted_results) == 0 else ("SUCCESS", converted_results)
        except Exception as e:
            return "ERROR", str(e)

    def save_survivor_data(self, survivors):
        personalInformationData = []
        familyInfoData = []
        communicationInfoData = []
        contactInfoData = []
        hospitalInfoData = []
        sjfl_status_updates = []
        try:
            for i, d in enumerate(survivors[:-1]):
                if len(d) == 0:
                    continue
                data = {}
                req_data = {}
                contact_details = []
                for k, v in d.items():
                    mapKey = EXCEL_TO_COLUMN_MAP.get(k)
                    if "Contact No" not in k and "Relation" not in k:
                        req_data[mapKey] = v
                    elif "Contact No" in k:
                        contact_info = {}
                        contact_number = k[-1]
                        relationKey = "Relation to Patient-" + contact_number
                        contact_info[v] = d.get(relationKey)
                        contact_details.append(contact_info)
                req_data['STATUS'] = constants.TO_BE_ENROLLED_ID
                data['details'] = req_data
                data['contact_info'] = contact_details
                survivor_data = data.get('details')
                sid = survivor_data.get('SID')
                if sid is None:
                    continue

                personalInformation = PersonalInformation(
                    SID=sid,
                    FIRST_NAME=survivor_data.get('FIRST_NAME'),
                    LAST_NAME=survivor_data.get('LAST_NAME'),
                    DATE_OF_BIRTH=survivor_data.get('DATE_OF_BIRTH'),
                    GENDER=survivor_data.get('GENDER'),
                    NATIONALITY=survivor_data.get('NATIONALITY'),
                    BLOOD_GROUP=survivor_data.get('BLOOD_GROUP'),
                    PHOTO_URL=survivor_data['PHOTO_URL'],
                    STATUS_ID=survivor_data['STATUS'],
                    LOCATION=survivor_data['LOCATION'],
                    CENTRE=survivor_data['CENTRE'],
                    ADMISSION_DATE=survivor_data['ADMISSION_DATE']
                )
                personalInformationData.append(personalInformation)

                hospitalInformation = HospitalInfo(
                    HOSPITAL_NAME=survivor_data.get('HOSPITAL_NAME'),
                    HOSPITAL_REGNO=survivor_data.get('HOSPITAL_REGNO'),
                    HOSPITAL_REGDATE=survivor_data.get('HOSPITAL_REGDATE'),
                    CANCER_TYPE=survivor_data['CANCER_TYPE'],
                    DOCTOR_NAME=survivor_data['DOCTOR_NAME'],
                    SID=sid
                )
                hospitalInfoData.append(hospitalInformation)

                # db.session.add(hospitalInformation)
                familyInfo = FamilyDetails(
                    FATHER_NAME=survivor_data['FATHER_NAME'],
                    FATHER_DOB=survivor_data['FATHER_DOB'],
                    FATHER_QUALIFICATION=survivor_data['FATHER_QUALIFICATION'],
                    FATHER_OCCUPATION=survivor_data['FATHER_OCCUPATION'],
                    FATHER_INCOME_MONTHLY=survivor_data['FATHER_INCOME_MONTHLY'],
                    MOTHER_NAME=survivor_data['MOTHER_NAME'],
                    MOTHER_DOB=survivor_data['MOTHER_DOB'],
                    MOTHER_QUALIFICATION=survivor_data['MOTHER_QUALIFICATION'],
                    MOTHER_OCCUPATION=survivor_data['MOTHER_OCCUPATION'],
                    MOTHER_INCOME_MONTHLY=survivor_data['MOTHER_INCOME_MONTHLY'],
                    SIBLING_DETAILS=str(survivor_data.get('SIBLING_DETAILS')),
                    REMARKS=survivor_data['REMARKS'],
                    SID=sid
                )
                familyInfoData.append(familyInfo)

                # db.session.add(familyInfo)
                communicationInfo = CommunicationDetails(
                    ADDRESS=survivor_data['ADDRESS'],
                    DISTRICT=survivor_data['DISTRICT'],
                    STATE=survivor_data['STATE'],
                    COUNTRY=survivor_data['COUNTRY'],
                    PINCODE=survivor_data['PINCODE'],
                    EMAIL=survivor_data['EMAIL'],
                    SID=sid
                )
                communicationInfoData.append(communicationInfo)
                # db.session.add(communicationInfo)
                contact_details = data['contact_info']
                contact_full_data = []
                for item in contact_details:
                    for k, v in item.items():
                        contactInfo = Contacts(
                            SID=sid,
                            PHONE_NUMBER=k,
                            CONTACT_RELATION=v,
                            LAST_UPDATED=datetime.today()
                        )
                        contact_full_data.append(contactInfo)
                        # db.session.add(contactInfo)
                contactInfoData.append(contact_full_data)
                sjfl_status_update = StatusUpdate(SID=sid, REMARKS='To be Onboarded',STATUS_ID=constants.TO_BE_ENROLLED_ID)
                sjfl_status_updates.append(sjfl_status_update)

            db.session.bulk_save_objects(personalInformationData)
            db.session.bulk_save_objects(hospitalInfoData, )
            db.session.bulk_save_objects(familyInfoData, )
            db.session.bulk_save_objects(communicationInfoData, )
            for contact_d in contactInfoData:
                db.session.bulk_save_objects(contact_d, )
            db.session.bulk_save_objects(sjfl_status_updates, )
            db.session.commit()
            return "Successfully added survivor details"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def get_all_survivors(filter=None):
        # TODO: where is this being used??
        stmt = select(PersonalInformation)
        result = db.session.execute(stmt)
        return result

    def add_user(self, ngo_user):
        try:
            db.session.add(ngo_user)
            db.session.commit()
            return "User Successfully Added"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def check_user(self, email):
        exists = db.session.query(NgoUsers.UID).filter_by(UEMAIL=email).scalar() is not None
        return exists

    def get_user_data(self, email):
        try:
            user = db.session.query(NgoUsers, NgoUserRoles).filter(NgoUsers.ROLE_ID == NgoUserRoles.ROLE_ID, NgoUsers.UEMAIL == email).all()
        
            result = NgoUsersWithRole(
                UID=user[0][0].UID,
                UNAME=user[0][0].UNAME,
                UEMAIL=user[0][0].UEMAIL,
                ACTIVE=user[0][0].ACTIVE,
                ROLE_ID=user[0][0].ROLE_ID,
                ROLE=user[0][1].RNAME
                )
            return "SUCCESS", result
        except Exception as e:
            return "ERROR", str(e)

    def add_new_followup_with_answers(self, futypeid, sid, fubyid, answers):
        try:
            # create entry in followup master
            master_entry = FollowupMaster(FOLLOWUPTYPEID=futypeid,
                                          SID=sid,
                                          FOLLOWEDUPBY=fubyid,
                                          FOLLOWUPDATE=datetime.now())
            db.session.add(master_entry)

            # required to get the newly added ID, as we are not committing we wont get that unless flushed and refreshed
            db.session.flush()
            db.session.refresh(master_entry)

            # create entry for each answer
            answers_to_be_added = []
            for qid, ans in answers.items():
                answers_to_be_added.append(
                    FollowUpAnswers(ANSWER=ans, FOLLOWUPID=master_entry.FOLLOWUPID, QUESTIONID=qid)
                )
            db.session.add_all(answers_to_be_added)

            # commit only after both operations have completed
            db.session.commit()
            return "Successfully added new FollowUp"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def get_all_next_followups(self):
        # TODO : fix number of reminders to be displayed
        try:
            results = db.session.query(NextFollowUp, FollowUpTypes, PersonalInformation) \
                .join(FollowUpTypes, FollowUpTypes.FOLLOWUPTYPEID == NextFollowUp.FOLLOWUPTYPEID) \
                .join(PersonalInformation, PersonalInformation.SID == NextFollowUp.SID) \
                .order_by(NextFollowUp.NEXTFOLLOWUPDATE).all()
            nextFollowUps = []
            for result in results:
                converted_result = NextFollowUps(
                    result[0].NEXT_FOLLOW_UP_ID,
                    result[0].FOLLOWUPTYPEID,
                    result[0].NEXTFOLLOWUPDATE,
                    result[0].LASTMODIFIEDBY,
                    result[0].LASTMODIFIEDDATE,
                    result[0].SID,
                    result[1].FOLLOWUPTYPE,
                    result[2].FIRST_NAME,
                    result[2].LAST_NAME,
                    result[2].PHOTO_URL,
                )
                nextFollowUps.append(converted_result)
            return "SUCCESS", nextFollowUps
        except Exception as e:
            return "ERROR", str(e)

    def get_survivor_info(self, sid):
        # index: 0 => personal info
        # index: 1 => hospital info
        # index: 2 => family info
        # index: 3 => residence/communication info
        # index: 4 => contact info
        # index: 5 => SJFL status info
        # index: 6 => aspiration index info

        results = []
        try:
            # get survivor details from personal information table
            result_personalInfo = db.session.query(PersonalInformation).filter(PersonalInformation.SID == sid).all()
            converted_result_personalInfo = PersonalInformation(
                SID=result_personalInfo[0].SID,
                FIRST_NAME=result_personalInfo[0].FIRST_NAME,
                LAST_NAME=result_personalInfo[0].LAST_NAME,
                GENDER=result_personalInfo[0].GENDER,
                NATIONALITY=result_personalInfo[0].NATIONALITY,
                BLOOD_GROUP=result_personalInfo[0].BLOOD_GROUP,
                PHOTO_URL=result_personalInfo[0].PHOTO_URL,
                DATE_OF_BIRTH=result_personalInfo[0].DATE_OF_BIRTH,
                STATUS_ID=result_personalInfo[0].STATUS_ID,
                WELCOME_KIT_DISPATCH_DATE=result_personalInfo[0].WELCOME_KIT_DISPATCH_DATE,
                ADMISSION_DATE=result_personalInfo[0].ADMISSION_DATE,
                LOCATION=result_personalInfo[0].LOCATION,
                CENTRE=result_personalInfo[0].CENTRE
            )
            results.append(converted_result_personalInfo)

            result_hospitalInfo = db.session.query(HospitalInfo).filter(HospitalInfo.SID == sid).all()
            converted_result_hospitalInfo = HospitalInfo(
                HOSPITALID=result_hospitalInfo[0].HOSPITALID,
                HOSPITAL_NAME=result_hospitalInfo[0].HOSPITAL_NAME,
                HOSPITAL_REGNO=result_hospitalInfo[0].HOSPITAL_REGNO,
                HOSPITAL_REGDATE=result_hospitalInfo[0].HOSPITAL_REGDATE,
                CANCER_TYPE=result_hospitalInfo[0].CANCER_TYPE,
                DOCTOR_NAME=result_hospitalInfo[0].DOCTOR_NAME,
                CANCER_STAGE=result_hospitalInfo[0].CANCER_STAGE,
                SID=result_hospitalInfo[0].SID
            )
            results.append(converted_result_hospitalInfo)

            result_familyInfo = db.session.query(FamilyDetails).filter(FamilyDetails.SID == sid).all()
            converted_result_familyInfo = FamilyDetails(
                DETAIL_ID=result_familyInfo[0].DETAIL_ID,
                FATHER_NAME=result_familyInfo[0].FATHER_NAME,
                FATHER_DOB=result_familyInfo[0].FATHER_DOB,
                FATHER_QUALIFICATION=result_familyInfo[0].FATHER_QUALIFICATION,
                FATHER_OCCUPATION=result_familyInfo[0].FATHER_OCCUPATION,
                FATHER_INCOME_MONTHLY=result_familyInfo[0].FATHER_INCOME_MONTHLY,
                MOTHER_NAME=result_familyInfo[0].MOTHER_NAME,
                MOTHER_DOB=result_familyInfo[0].MOTHER_DOB,
                MOTHER_QUALIFICATION=result_familyInfo[0].MOTHER_QUALIFICATION,
                MOTHER_OCCUPATION=result_familyInfo[0].MOTHER_OCCUPATION,
                MOTHER_INCOME_MONTHLY=result_familyInfo[0].MOTHER_INCOME_MONTHLY,
                SIBLING_DETAILS=result_familyInfo[0].SIBLING_DETAILS,
                REMARKS=result_familyInfo[0].REMARKS,
                SID=result_familyInfo[0].SID
            )
            results.append(converted_result_familyInfo)

            result_communicationInfo = db.session.query(CommunicationDetails).filter(CommunicationDetails.SID == sid).all()
            converted_result_communicationInfo = CommunicationDetails(
                COMMUNICATION_ID=result_communicationInfo[0].COMMUNICATION_ID,
                ADDRESS=result_communicationInfo[0].ADDRESS,
                DISTRICT=result_communicationInfo[0].DISTRICT,
                STATE=result_communicationInfo[0].STATE,
                COUNTRY=result_communicationInfo[0].COUNTRY,
                PINCODE=result_communicationInfo[0].PINCODE,
                EMAIL=result_communicationInfo[0].EMAIL,
                SID=result_communicationInfo[0].SID
            )
            results.append(converted_result_communicationInfo)

            contact_list = []
            result_contactInfo = db.session.query(Contacts).filter(Contacts.SID == sid).limit(5).all()
            for result in result_contactInfo:
                converted_result_contactInfo = Contacts(
                    CONTACT_ID=result.CONTACT_ID,
                    SID=result.SID,
                    PHONE_NUMBER=result.PHONE_NUMBER,
                    LAST_UPDATED=result.LAST_UPDATED,
                    CONTACT_RELATION=result.CONTACT_RELATION
                )
                contact_list.append(converted_result_contactInfo)

            results.append(contact_list)

            result_statusInfo = db.session.query(SJFLStatus).filter(
                SJFLStatus.STATUS_ID == result_personalInfo[0].STATUS_ID).all()
            converted_result_statusInfo = SJFLStatus(
                STATUS_ID=result_statusInfo[0].STATUS_ID,
                STATUS=result_statusInfo[0].STATUS
            )
            results.append(converted_result_statusInfo)

            result_nextFollowUpInfo = db.session.query(NextFollowUp).filter(NextFollowUp.FOLLOWUPTYPEID == 2,
                                                                            NextFollowUp.SID == sid).all()
            if len(result_nextFollowUpInfo) > 0:
                converted_result_nextFollowUpInfo = NextFollowUp(
                    NEXT_FOLLOW_UP_ID=result_nextFollowUpInfo[0].NEXT_FOLLOW_UP_ID,
                    FOLLOWUPTYPEID=result_nextFollowUpInfo[0].FOLLOWUPTYPEID,
                    NEXTFOLLOWUPDATE=result_nextFollowUpInfo[0].NEXTFOLLOWUPDATE,
                    LASTMODIFIEDBY=result_nextFollowUpInfo[0].LASTMODIFIEDBY,
                    LASTMODIFIEDDATE=result_nextFollowUpInfo[0].LASTMODIFIEDDATE,
                    SID=result_nextFollowUpInfo[0].SID
                )
                results.append(converted_result_nextFollowUpInfo)
            else:
                results.append({})

            result_statusUpdateInfo = db.session.query(StatusUpdate).filter(
                StatusUpdate.STATUS_ID == result_personalInfo[0].STATUS_ID,
                StatusUpdate.SID == result_personalInfo[0].SID).all()
            converted_result_statusUpdateInfo = StatusUpdate(
                SID=result_statusUpdateInfo[0].SID,
                STATUS_ID=result_statusUpdateInfo[0].STATUS_ID,
                REMARKS=result_statusUpdateInfo[0].REMARKS
            )
            results.append(converted_result_statusUpdateInfo)

            # index: calculate and get the aspiration index value
            aspiration_index = calculate_aspiration_index(sid)
            results.append(aspiration_index)

            return "SUCCESS", results
        except Exception as e:
            return "ERROR", str(e)

    def get_budget(self, sid):
        results = {}
        budgets = {}
        items = {}
        
        result_budget = db.session.query(Budget).filter(Budget.SID == sid).all()
        if result_budget==[]:
            return None
        for result in result_budget:
            id = result.BUDGET_TBL_ID
            tempBudget = Budget(
                BUDGET_TBL_ID = result.BUDGET_TBL_ID,
                SID = result.SID,
                BUDGET_NAME = result.BUDGET_NAME
            ) 
            budgets[result.BUDGET_TBL_ID] = tempBudget

            actual = db.session.query(BudgetActualSpent).filter(BudgetActualSpent.BUDGET_TBL_ID == id).order_by(BudgetActualSpent.ITEM).all()
            projected = db.session.query(BudgetProjected).filter(BudgetProjected.BUDGET_TBL_ID == id).order_by(BudgetProjected.ITEM).all()
            table = {}
            for i in range(0,len(actual)):
                tempActual = BudgetActualSpent(
                    ACTUAL_ID = actual[i].ACTUAL_ID,
                    BUDGET_TBL_ID = actual[i].BUDGET_TBL_ID,	
                    ITEM = actual[i].ITEM,
                    UNIT = actual[i].UNIT,
                    PERIOD = actual[i].PERIOD,
                    UNIT_COST = actual[i].UNIT_COST
                )
                tempProjected = BudgetProjected(
                    PROJECTED_ID = projected[i].PROJECTED_ID,
                    BUDGET_TBL_ID = projected[i].BUDGET_TBL_ID,	
                    ITEM = projected[i].ITEM,
                    UNIT = projected[i].UNIT,
                    PERIOD = projected[i].PERIOD,
                    UNIT_COST = projected[i].UNIT_COST
                )
                table[projected[i].ITEM] = {"actual":tempActual, "projected":tempProjected}
            items[result.BUDGET_TBL_ID] = table

        results["budget"] = budgets
        results["items"] = items

        return results

    def get_plan(self, sid):
        results = {}
        resultCol = {}
        resultRow = {}
        resultData = {}

        result_plan = db.session.query(Plan).filter(Plan.SID == sid).all()
        if result_plan==[]:
            return None

        planID = result_plan[0].PLAN_TBL_ID
        result_X = db.session.query(PlanColX).filter(PlanColX.PLAN_TBL_ID == planID).all()
        result_Y = db.session.query(PlanColY).filter(PlanColY.PLAN_TBL_ID == planID).all()

        for row in result_Y:
            resultRow[row.PLAN_COL_Y_ID] = row.COL_HEADER

        for col in result_X:
            resultCol[col.PLAN_COL_X_ID] = col.COL_HEADER

        for row in result_Y:
            for col in result_X:
                data = db.session.query(PlanData).filter(PlanData.PLAN_COL_Y_ID == row.PLAN_COL_Y_ID, PlanData.PLAN_COL_X_ID == col.PLAN_COL_X_ID).all()
                key = str(row.PLAN_COL_Y_ID) +"-"+ str(col.PLAN_COL_X_ID)
                value = data[0].PLAN_DATA
                resultData[key] = value

        results["Rows"] = resultRow
        results["Cols"] = resultCol
        results["Data"] = resultData
        return results

    def update_budget(self, items):
        failed = False
        try:
            for k_items, v_items in items.items():
                result_budget = db.session.query(Budget).filter(Budget.BUDGET_TBL_ID == k_items).all()[0]
                for k, v in v_items.items():
                    a = v["actual"]
                    db.session.query(BudgetActualSpent).filter(BudgetActualSpent.ACTUAL_ID == a["ACTUAL_ID"]).update(
                    {BudgetActualSpent.UNIT: a["UNIT"],
                    BudgetActualSpent.PERIOD: a["PERIOD"],
                    BudgetActualSpent.UNIT_COST: a["UNIT_COST"]})

                    p = v["projected"]
                    db.session.query(BudgetProjected).filter(BudgetProjected.PROJECTED_ID ==p["PROJECTED_ID"]).update(
                    {BudgetProjected.UNIT: p["UNIT"],
                    BudgetProjected.PERIOD: p["PERIOD"],
                    BudgetProjected.UNIT_COST: p["UNIT_COST"]})
            
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def add_plan(self, sid):
        failed = False
        try:
            plan = Plan(SID = sid)
            db.session.add(plan)            
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def add_budget(self, sid, name, items):
        failed = False
        try:
            budget = Budget(SID = sid, BUDGET_NAME=name)
            db.session.add(budget)            
            db.session.flush()
            db.session.refresh(budget)
            budgetId = budget.BUDGET_TBL_ID
            for item in items:
                projected = BudgetProjected(
                    BUDGET_TBL_ID = budgetId,
                    ITEM = item,	
                    UNIT = 0,	
                    PERIOD = 0,	
                    UNIT_COST = 0.0
                )
                db.session.add(projected)
                actual = BudgetActualSpent(
                    BUDGET_TBL_ID = budgetId,
                    ITEM = item,	
                    UNIT = 0,	
                    PERIOD = 0,	
                    UNIT_COST = 0.0
                )
                db.session.add(actual)            

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def update_plan(self, sid, rows, cols, data):
        failed = False
        try:
            result_plan = db.session.query(Plan).filter(Plan.SID == sid).all()
            planID = result_plan[0].PLAN_TBL_ID

            for row in rows:
                y_id = int(row)
                db.session.query(PlanColY).filter(PlanColY.PLAN_TBL_ID == planID, PlanColY.PLAN_COL_Y_ID == y_id).update(
                {PlanColY.COL_HEADER: rows[row]})
            
            for col in cols:
                x_id = int(col)
                db.session.query(PlanColX).filter(PlanColX.PLAN_TBL_ID == planID, PlanColX.PLAN_COL_X_ID == x_id).update(
                {PlanColX.COL_HEADER: cols[col]})

            for d in data:
                y,x = d.split("-")
                y_id = int(y)
                x_id = int(x)
                db.session.query(PlanData).filter(PlanData.PLAN_COL_Y_ID == y_id, PlanData.PLAN_COL_X_ID == x_id).update(
                {PlanData.PLAN_DATA: data[d]})

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def add_plan_row(self, sid, newRow, rowData):
        failed = False
        try:
            result_plan = db.session.query(Plan).filter(Plan.SID == sid).all()
            planID = result_plan[0].PLAN_TBL_ID
            row = PlanColY(PLAN_TBL_ID = planID, COL_HEADER = newRow)
            db.session.add(row)
            db.session.flush()
            db.session.refresh(row)
            for data in rowData:
                tempData = PlanData(PLAN_COL_X_ID=data, PLAN_COL_Y_ID=row.PLAN_COL_Y_ID, PLAN_DATA=rowData[data])
                db.session.add(tempData)            
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed
        
    def add_plan_col(self, sid, newCol, colData):
        failed = False
        try:
            result_plan = db.session.query(Plan).filter(Plan.SID == sid).all()
            planID = result_plan[0].PLAN_TBL_ID
            col = PlanColX(PLAN_TBL_ID = planID, COL_HEADER = newCol)
            db.session.add(col)
            db.session.flush()
            db.session.refresh(col)
            for data in colData:
                tempData = PlanData(PLAN_COL_X_ID=col.PLAN_COL_X_ID, PLAN_COL_Y_ID=data, PLAN_DATA=colData[data])
                db.session.add(tempData)            
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def deletePlanRow(self, sid, id):
        failed = False
        try:
            PlanData.query.filter(PlanData.PLAN_COL_Y_ID==id).delete()
            PlanColY.query.filter(PlanColY.PLAN_COL_Y_ID==id).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def deletePlanCol(self, sid, id):
        failed = False
        try:
            PlanData.query.filter(PlanData.PLAN_COL_X_ID==id).delete()
            PlanColX.query.filter(PlanColX.PLAN_COL_X_ID==id).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def  deleteBudgetTable(self, id):
        failed = False
        try:
            Budget.query.filter(Budget.BUDGET_TBL_ID == id).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def  deleteBudgetRow(self, a_id,p_id):
        failed = False
        try:
            BudgetActualSpent.query.filter(BudgetActualSpent.ACTUAL_ID == a_id).delete()
            BudgetProjected.query.filter(BudgetProjected.PROJECTED_ID == p_id).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def addBudgetRow(self, name, id):
        failed = False
        try:
            act = BudgetActualSpent(BUDGET_TBL_ID = id, ITEM = name, UNIT=0, PERIOD=0, UNIT_COST=0)
            db.session.add(act)

            pro = BudgetProjected(BUDGET_TBL_ID = id, ITEM = name, UNIT=0, PERIOD=0, UNIT_COST=0)
            db.session.add(pro)
            
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
            db.session.flush()
            failed = True
        return failed

    def update_status(self, sid, updated_status, updated_remarks):
        try:
            result = db.session.query(SJFLStatus).filter(SJFLStatus.STATUS == updated_status).all()
            if len(result) <= 0:
                return "Status not configured in database"
            db.session.query(PersonalInformation).filter(PersonalInformation.SID == sid).update(
                {PersonalInformation.STATUS_ID: result[0].STATUS_ID})
            status_result = db.session.query(StatusUpdate).filter(StatusUpdate.SID == sid, StatusUpdate.STATUS_ID == result[0].STATUS_ID).all()

            if len(status_result) > 0:
                db.session.query(StatusUpdate).filter(StatusUpdate.SID == sid, StatusUpdate.STATUS_ID == result[0].STATUS_ID).update(
                    {StatusUpdate.REMARKS: updated_remarks})
            else:
                statusUpdate = StatusUpdate(SID=sid, STATUS_ID=result[0].STATUS_ID, REMARKS=updated_remarks)
                db.session.add(statusUpdate)
            db.session.commit()
            return "Successfully updated status"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def update_family_details(self, sid, fatherName, fatherDOB, fatherOccupation, fatherQualification, fatherIncome, motherName, 
                                motherDOB, motherOccupation, motherQualification, motherIncome, siblingDetails, remarks):
        try:
            db.session.query(FamilyDetails).filter(FamilyDetails.SID == sid).update(
                {FamilyDetails.FATHER_NAME: fatherName,
                 FamilyDetails.FATHER_DOB: fatherDOB,
                 FamilyDetails.FATHER_OCCUPATION: fatherOccupation,
                 FamilyDetails.FATHER_QUALIFICATION: fatherQualification,
                 FamilyDetails.FATHER_INCOME_MONTHLY: fatherIncome, FamilyDetails.MOTHER_OCCUPATION: motherOccupation,
                 FamilyDetails.MOTHER_NAME: motherName,
                 FamilyDetails.MOTHER_DOB: motherDOB,
                 FamilyDetails.MOTHER_QUALIFICATION: motherQualification,
                 FamilyDetails.MOTHER_INCOME_MONTHLY: motherIncome, FamilyDetails.SIBLING_DETAILS: siblingDetails,
                 FamilyDetails.REMARKS: remarks})
            db.session.commit()
            return "Successfullly updated family details"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def update_personal_info(self, sid, firstName, lastName, dateOfBirth, gender, nationality, bloodGroup,
                             admissionDate, location, centre):
        try:
            db.session.query(PersonalInformation).filter(PersonalInformation.SID == sid).update(
                {
                    PersonalInformation.FIRST_NAME: firstName,
                    PersonalInformation.LAST_NAME: lastName,
                    PersonalInformation.DATE_OF_BIRTH: dateOfBirth,
                    PersonalInformation.GENDER: gender,
                    PersonalInformation.NATIONALITY: nationality,
                    PersonalInformation.BLOOD_GROUP: bloodGroup,
                    PersonalInformation.ADMISSION_DATE: admissionDate,
                    PersonalInformation.LOCATION: location,
                    PersonalInformation.CENTRE: centre
                })
            db.session.commit()
            return "Successfully updated personal information"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def update_hospital_details(self, sid, hospitalName, hospitalRegNo, hospitalRegDate, doctorName, cancerStage, cancerType):
        try:
            db.session.query(HospitalInfo).filter(HospitalInfo.SID == sid).update(
                {HospitalInfo.HOSPITAL_NAME: hospitalName, HospitalInfo.HOSPITAL_REGNO: hospitalRegNo,
                 HospitalInfo.HOSPITAL_REGDATE: hospitalRegDate, HospitalInfo.DOCTOR_NAME: doctorName,
                 HospitalInfo.CANCER_STAGE: cancerStage, HospitalInfo.CANCER_TYPE: cancerType})
            db.session.commit()
            return "Successfully updated hospital details"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def update_communication_details(self, sid, address, district, state, country, pincode, email, contact1, relation1,
                                     contact2, relation2, contact3, relation3, contact4, relation4, contact5,
                                     relation5):
        try:
            db.session.query(CommunicationDetails).filter(CommunicationDetails.SID == sid).update(
                {CommunicationDetails.ADDRESS: address, CommunicationDetails.DISTRICT: district,
                 CommunicationDetails.STATE: state, CommunicationDetails.COUNTRY: country,
                 CommunicationDetails.PINCODE: pincode, CommunicationDetails.EMAIL: email})
            db.session.commit()
            results = db.session.query(Contacts).filter(Contacts.SID == sid).limit(5).all()
            contact_list = [contact1, contact2, contact3, contact4, contact5]
            relation_list = [relation1, relation2, relation3, relation4, relation5]
            i = 0
            for result in results:
                db.session.query(Contacts).filter(Contacts.CONTACT_ID == result.CONTACT_ID).update(
                    {Contacts.PHONE_NUMBER: contact_list[i], Contacts.CONTACT_RELATION: relation_list[i],
                     Contacts.LAST_UPDATED: datetime.now()})
                i = i + 1
                db.session.commit()
            return "Successfully updated communication details"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def get_survivors_search(self, searchText):
        hasOnlyFirstName = True
        try:
            search = "%{}%".format(int(searchText))
            searchIsID = True
        except:
            search = "%{}%".format(str(searchText))
            searchIsID = False

        if not searchIsID:
            if " " in search and search.count(" ") == 1:
                hasOnlyFirstName = False
                fname = "%{}%".format(str(searchText).split(" ")[0])
                lname = "%{}%".format(str(searchText).split(" ")[1])
            else:
                search = "%{}%".format(str(searchText))
                hasOnlyFirstName = True

        if searchIsID:
            results = db.session.query(PersonalInformation) \
                .filter(PersonalInformation.SID.like(search)).limit(5).all()
        elif not hasOnlyFirstName:
            results = db.session.query(PersonalInformation) \
                .filter(
                (PersonalInformation.FIRST_NAME.like(fname) & PersonalInformation.LAST_NAME.like(lname))).limit(5).all()
        else:
            results = db.session.query(PersonalInformation) \
                .filter(
                or_(PersonalInformation.FIRST_NAME.like(search), PersonalInformation.LAST_NAME.like(search))).limit(5).all()

        try:
            searchResult = []
            for result in results:
                converted_result = SearchResult(
                    SID=result.SID,
                    FIRST_NAME=result.FIRST_NAME,
                    LAST_NAME=result.LAST_NAME,
                    LINK=constants.react_URL + "/survivor/" + str(result.SID) + "/basicprofile"
                )
                searchResult.append(converted_result)
            return "SUCCESS", searchResult
        except Exception as e:
            return "ERROR", str(e)

    def update_dispatch_date(self, sid, date):
        try:
            db.session.query(PersonalInformation).filter(PersonalInformation.SID == sid).update(
                {PersonalInformation.WELCOME_KIT_DISPATCH_DATE: date})
            db.session.commit()
            return "Successfully updated dispatch date"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def update_photo(self, sid, file):
        try:
            results = db.session.query(PersonalInformation).filter(PersonalInformation.SID == sid).all()
            old_filename = results[0].PHOTO_URL
            if old_filename is not None:
                os.remove(os.path.join(UPLOAD_FOLDER, old_filename))

            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = get_filename(sid, ext)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                db.session.query(PersonalInformation).filter(PersonalInformation.SID == sid).update(
                    {PersonalInformation.PHOTO_URL: filename})
                db.session.commit()
            return "Successfully updated profile photo"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def nextnonexistent(self, f):
        ''' if file exists, create file_1 ,file_2 and so on '''
        fnew = f
        root, ext = os.path.splitext(f)
        i = 0
        while os.path.exists(fnew):
            i += 1
            fnew = '%s_%i%s' % (root, i, ext)
        return fnew

    def saveInsuranceCardInfo(self, sid, files):
        '''
            Save insurance data for a given sid and also upload insurance cards.
        '''
        try:
            if files:
                insurancecards = []
                for file in files:
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = get_filename(sid, ext)
                    fileWithPath = os.path.join(INSURANCE_CARD_FOLDER, filename)
                    nextFile = self.nextnonexistent(fileWithPath)
                    file.save(nextFile)
                    card = InsuranceCards(
                        SID = sid,
                        CARDLINK = nextFile
                    )
                    insurancecards.append(card)
                db.session.add_all(insurancecards)
                db.session.commit()
                return "Successfully added insurance card info"
            else:
                return "No file"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def fetchCardsForSID(self, sid):
        try:
            results = db.session.query(InsuranceCards).filter(InsuranceCards.SID == sid).all()
            searchResult = []
            for result in results:
                converted_result = InsuranceResult(
                    SID=result.SID,
                    CARDID=result.CARDID,
                    CARDLINK=result.CARDLINK,
                )
                searchResult.append(converted_result)
            return "SUCCESS", searchResult
        except Exception as e:
            return "ERROR", str(e)

    def deleteCardsForSID(self, sid, filelink):
        try:
            os.remove(filelink)
            InsuranceCards.query.filter_by(SID=int(sid), CARDLINK=filelink).delete()
            db.session.commit()
            return "Successfully deleted insurance card"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def get_support_data(self, sid, thematicArea):
        result = []
        try:
            supportData = db.session.query(SJFLSupport).filter(SJFLSupport.SID == sid,
                                                               SJFLSupport.THEMATIC_AREA == thematicArea).order_by(
                SJFLSupport.CREATED_ON.desc()).all()
            for data in supportData:
                converted_data = SJFLSupport(
                    SJFLSUPPORT_ID=data.SJFLSUPPORT_ID,
                    SID=data.SID,
                    THEMATIC_AREA=data.THEMATIC_AREA,
                    FINANCIAL_SUPPORT=data.FINANCIAL_SUPPORT,
                    NATURE_OF_SUPPORT=data.NATURE_OF_SUPPORT,
                    SOURCE_OF_SUPPORT=data.SOURCE_OF_SUPPORT,
                    AID_DATE=data.AID_DATE,
                    PROCESSED_BY=data.PROCESSED_BY,
                    PROCESSED_DATE=data.PROCESSED_DATE,
                    AMOUNT=data.AMOUNT,
                    FILE_NAME=data.FILE_NAME,
                    CREATED_ON=data.CREATED_ON
                )
                result.append(converted_data)
            return "SUCCESS", result
        except Exception as e:
            return "ERROR", str(e)

    def update_support_data(self, sid, files, thematicArea, financialSupport, natureOfSupport, sourceOfSupport, aidDate,
                            processedBy, processedDate, amount):
        try:
            if len(files) > 0:
                for file in files:
                    created_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    str2hash = sid + file.filename + created_on
                    str_hash = hashlib.md5(str2hash.encode())
                    filename = str_hash.hexdigest() + file.filename
                    file.save(os.path.join(SUPPORT_FOLDER, filename))
                    support_details = SJFLSupport(SID=sid,
                                                  FILE_NAME=filename,
                                                  THEMATIC_AREA=thematicArea,
                                                  FINANCIAL_SUPPORT=financialSupport,
                                                  AMOUNT=amount,
                                                  NATURE_OF_SUPPORT=natureOfSupport,
                                                  SOURCE_OF_SUPPORT=sourceOfSupport,
                                                  AID_DATE=aidDate,
                                                  PROCESSED_BY=processedBy,
                                                  PROCESSED_DATE=processedDate,
                                                  CREATED_ON=created_on)
                    db.session.add(support_details)

                db.session.commit()
                return "Successfully added SJFL support information"
            else:
                return "No file"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def delete_support_data(self, sid, filename, createdOn):
        try:
            str2hash = sid + filename + createdOn
            str_hash = hashlib.md5(str2hash.encode())
            db_filename = str_hash.hexdigest() + filename
            os.remove(SUPPORT_FOLDER + db_filename)
            SJFLSupport.query.filter_by(SID=sid,FILE_NAME=db_filename).delete()
            db.session.commit()
            return "Successfully deleted SJFL support data"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

    def get_followup_data_for_sid(self, sid, futype):

        results = db.session.query(FollowUpAnswers.FOLLOWUPID,
                                   FollowupQuestions.QUESTIONID,
                                   FollowupQuestions.QUESTION_TEXT,
                                   FollowUpAnswers.ANSWER,
                                   FollowupMaster.SID,
                                   FollowUpTypes.FOLLOWUPTYPE,
                                   FollowupMaster.FOLLOWEDUPBY,
                                   FollowupMaster.FOLLOWUPDATE) \
            .select_from(FollowupMaster) \
            .join(FollowUpAnswers, FollowupMaster.FOLLOWUPID == FollowUpAnswers.FOLLOWUPID ) \
            .join(FollowupQuestions, FollowUpAnswers.QUESTIONID == FollowupQuestions.QUESTIONID) \
            .join(FollowUpTypes, and_(FollowUpTypes.FOLLOWUPTYPEID == FollowupMaster.FOLLOWUPTYPEID)) \
            .filter(and_(FollowupMaster.SID == sid, FollowUpTypes.FOLLOWUPTYPE == futype)) \
            .order_by(FollowupMaster.FOLLOWUPID) # sorting by followupID as it will be higher for a latest date

        searchResult = []
        for result in results:
            converted_results = PastFollowUpData(
                FOLLOWUPID=result.FOLLOWUPID,
                QUESTIONID=result.QUESTIONID,
                QUESTION_TEXT=result.QUESTION_TEXT,
                ANSWER=result.ANSWER,
                SID=result.SID,
                FOLLOWUPTYPE=result.FOLLOWUPTYPE,
                FOLLOWEDUPBY=result.FOLLOWEDUPBY,
                FOLLOWUPDATE=result.FOLLOWUPDATE
            )

            searchResult.append(converted_results)

        followupmap = self.covertfollowuplisttomap(searchResult)
        keyList = list(followupmap)
        fuData = self.getmapvalues(keyList, followupmap)
        return "SUCCESS", fuData

    def getmapvalues(self, keyList, followupMap):
        mapList = []
        for key in keyList:
            val = followupMap.get(key)
            mapList.append(val)

        return mapList

    def covertfollowuplisttomap(self, converted_results):
        followupMap={}
        for result in converted_results:
            id = result.FOLLOWUPID
            if followupMap.get(id) != None:
                result1= followupMap.get(id)
                result1.append(result)
                followupMap[id] = result1
            else:
                searchResult = list()
                searchResult.append(result)
                followupMap[id] = searchResult

        return followupMap

    def get_all_users(self):
        try:
            users = db.session.query(NgoUsers, NgoUserRoles).join(NgoUserRoles).all()
            all_users = []
            for user in users:
                converted_result = NgoUsersWithRole(
                    UID=user[0].UID,
                    UNAME=user[0].UNAME,
                    UEMAIL=user[0].UEMAIL,
                    ACTIVE=user[0].ACTIVE,
                    ROLE_ID=user[0].ROLE_ID,
                    ROLE=user[1].RNAME
                )
                all_users.append(converted_result)
            return "SUCCESS", all_users
        except Exception as e:
            return "ERROR", str(e)

    def update_user(self, id, data):
        try:
            for user_detail in data:
                updates = {}
                uactive = user_detail.get('ACTIVE')
                urole = user_detail.get('ROLE')

                if uactive is not None: updates[NgoUsers.ACTIVE] = uactive
                if urole:
                    # get roleid from role
                    roleid = db.session.query(NgoUserRoles).filter(NgoUserRoles.RNAME == urole).all()[0].ROLE_ID
                    updates[NgoUsers.ROLE_ID] = roleid
                if bool(updates):
                    db.session.query(NgoUsers).filter(NgoUsers.UID == id).update(updates)
                else:
                    return "Nothing to update"
            db.session.commit()
            return "Successfully updated user role"
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return str(e)

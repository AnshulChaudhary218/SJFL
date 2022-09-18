import pandas as pd
from sqlalchemy import func, and_
from models import *


def calculate_aspiration_index(sid):
    '''
        Returns latest record of a particular followup type for a survivor
        :param sid: survivors id
        :param futype: followup type
        :return:
        '''
    # create a subquery to get max date for a sid-followuptype
    subquery_sid_latest_followups = db.session.query(FollowupMaster.SID,
                                                     FollowupMaster.FOLLOWUPTYPEID,
                                                     func.max(FollowupMaster.FOLLOWUPDATE).label("MAXDATE")) \
        .filter(FollowupMaster.SID == sid) \
        .group_by(FollowupMaster.SID, FollowupMaster.FOLLOWUPTYPEID).subquery()

    # join followup tables to get the latest followup data of a particular type
    query = db.session.query(FollowUpAnswers.ANSWER,
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
        FollowUpTypes.FOLLOWUPTYPE == 'ASPIRATION',
        FollowupMaster.SID == sid,
        FollowupQuestions.ACTIVE == 1)
    )

    # create dataframe from ORM query
    df = pd.read_sql(query.statement, query.session.bind)
    if df.empty:
        return 0

    # convert answer to int, as ANSWER has been stored as str but for aspiration index it will always be an int
    df['ANSWER'] = df['ANSWER'].fillna(0).astype(int)

    # get an attribute's total contribution
    df['ATTRIBUTE_WxANSWER'] = df['ATTRIBUTE_W'] * df['ANSWER']

    # get parameter level weighted average
    # FYI: aspiration index questions are categorized as CATEGORY >> PARAMETER >> ATTRIBUTES/QUESTIONS
    level0 = df.groupby(['CATEGORY', 'CATEGORY_W', 'PARAMETER', 'PARAMETER_W'])
    level0 = level0.ATTRIBUTE_WxANSWER.sum()/level0.ATTRIBUTE_W.sum()
    level0 = level0.reset_index([0, 1, 2, 3], name='ATTRIBUTE_WA')
    level0['PARAMETER_WxATTRIBUTE_WA'] = level0['PARAMETER_W'] * level0['ATTRIBUTE_WA']

    level1 = level0.groupby(['CATEGORY', 'CATEGORY_W'])
    level1 = level1.PARAMETER_WxATTRIBUTE_WA.sum()/level1.CATEGORY_W.sum()
    level1 = level1.reset_index([0, 1], name='PARAMETER_WA')
    level1['CATEGORY_WxPARAMETER_WA'] = level1['CATEGORY_W'] * level1['PARAMETER_WA']

    aspiration_index = level1.CATEGORY_WxPARAMETER_WA.sum()/level1.CATEGORY_W.sum()
    return round(aspiration_index, 2)

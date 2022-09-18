from http import HTTPStatus
from time import time
from flasgger import Swagger
from flask_cors import CORS

from flasgger import swag_from
from flask import Flask, Response, request, jsonify

from DBHelper import DBHelper
from models import *

from extensions import db as db_main

from base64 import b64decode
import jwt
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import requests
import constants
import json
# Initialize flask app
app = Flask(__name__)

# Initialize Config for swagger
app.config['SWAGGER'] = {
    'title': 'SJFL Flask API Swagger UI',
}

# Initialize config for sqlalchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://' \
                                                + constants.db_username + ':' \
                                                + constants.db_password + '@' \
                                                + constants.db_hostname + ':' \
                                                + str(constants.db_port) + '/' \
                                                + constants.db_name + '?driver=' \
                                                + constants.db_driver.replace(' ', '+')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
Swagger(app)

db_main.init_app(app)

db = DBHelper()



def token_validator(func):
    def decoder(*args, **kwargs):
        try:
            token_header = request.headers.get('Authorization')
            token = token_header.split(' ')[1]
            client_id = constants.client_id
            jwks_uri = 'https://login.microsoftonline.com/common/discovery/v2.0/keys'

            jwkeys = requests.get(jwks_uri).json()['keys']
            token_key_id = jwt.get_unverified_header(token)['kid']
            jwk = [key for key in jwkeys if key['kid'] == token_key_id][0]
            der_cert = b64decode(jwk['x5c'][0])
            cert = x509.load_der_x509_certificate(der_cert, default_backend())
            public_key = cert.public_key()
            pem_key = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
            token_claims = jwt.decode(token, pem_key, audience=client_id, algorithms=["RS256"])
            now = time()
            if token_claims == None:
                return "Invalid Token, Please retry", 404

            if token_claims['aud'] != client_id:
                return "UnValid Audience, Not Authorized", 404

            if now > token_claims['exp']:
                return "Session Expired, Please open page in new tab", 404

            return func(*args, **kwargs)

        except Exception as e:
            return "Failed : " + str(e), 404

    decoder.__name__ = func.__name__
    return decoder


@app.route('/healthcheck', methods=['GET', 'POST'])
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'SUCCESS'
        }
    }
})
def healthcheck():
    response_string = 'Hello India - FFG - 2021 - St. Jude India ChildCare <Br><Br>Server is up and running!<Br>'
    try:
        db.test_connection()
        response_string += 'DB connection working!'
    except Exception as ex:
        response_string += 'DB connection not working with error: {}\n'.format(ex)

    return Response(response_string)


@app.route('/', methods=['GET', 'POST'])
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'SUCCESS'
        }
    }
})
def index():
    return Response("Hello India - FFG - 2021 - St. Jude India ChildCare")


@app.route('/users', methods=['GET'])
@token_validator
def get_all_users():
    status, data = db.get_all_users()
    return (jsonify(data), 200) if status == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/user/<uid>', methods=['PATCH'])
def updates_user(uid):
    data = request.get_json()
    status = db.update_user(uid, data)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/users/<uid>', methods=['GET'])
@token_validator
def fetch_user(uid):
    pass


@app.route('/users', methods=['PATCH'])
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'SUCCESS'
        }
    }
})
@token_validator
def store_user():
    data = request.get_json()
    user_name = data.get('name')
    user_email = data.get('email')

    if user_name is None:
        user_name = user_email.rpartition('@')[0]

    if db.check_user(user_email):
        return "Success: User already exists! Nothing was changed.", 200
    else:
        ngo_user = NgoUsers(
            UNAME=user_name,
            UEMAIL=user_email,
            ACTIVE=1,
            ROLE_ID=4
        )
        status = db.add_user(ngo_user)
        return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/users/<uid>', methods=['DELETE'])
@token_validator
def delete_user(uid):
    pass


@app.route('/user/<email>', methods=['GET'])
@token_validator
def get_user(email):
    """
    Accepts email ID and returns all user details for that user
    :param email: str
    :return: complete user details
    """
    status, data = db.get_user_data(email)
    return (jsonify(data), 200) if status == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/followups', methods=['GET'])
@token_validator
def get_all_upcoming_followups():
    status, data = db.get_all_next_followups()
    return (jsonify(data), 200) if status == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/followups/<fid>', methods=['GET'])
@token_validator
def get_followup_details(fid):
    pass


@app.route('/followup/questions/<futype>', methods=['GET'])
@token_validator
def get_follow_up_questions(futype):
    status, data = db.get_followup_questions(futype)
    return (jsonify(data), 200) if status == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/followup/questions/', methods=['POST'])
@token_validator
def add_follow_up_question():
    """
    Expects FOLLOWUPTYPE in the request body
    :return:
    """
    data = request.get_json()
    status = db.add_followup_questions(data)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/aspiration/questions/', methods=['POST'])
@token_validator
def add_aspiration_question():
    """
    Expects FOLLOWUPTYPE in the request body
    :return:
    """

    data = request.get_json()
    status = db.add_aspiration_question(data)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/followup/questions/<futype>', methods=['PATCH'])
@token_validator
def update_follow_up_questions(futype):
    data = request.get_json()
    status = db.update_followup_questions(futype, data)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/aspiration/weightages', methods=['PATCH'])
@token_validator
def update_aspiration_weightages():
    data = request.get_json()
    status = db.update_aspiration_waightage(data)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/followups', methods=['POST'])
@token_validator
def insert_empty_followup():
    pass


@app.route('/followups/<fid>', methods=['PATCH'])
@token_validator
def update_followup_details(fid):
    pass


@app.route('/survivors/<searchtext>', methods=['GET'])
@token_validator
def search_survivor(searchtext):
    status, data = db.get_survivors_search(searchtext)
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors', methods=['GET'])
@token_validator
def get_all_survivors():
    pass


@app.route('/survivors', methods=['POST'])
@token_validator
def add_survivor():
    data = request.get_json()
    status = db.save_survivor_data(data)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/sjflsupport', methods=['GET'])
@token_validator
def get_support_data(sid):
    thematicArea = request.args.get('thematic_area')
    status, data = db.get_support_data(sid, thematicArea)
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/<sid>/sjflsupport', methods=['POST'])
@token_validator
def store_support_data(sid):
    files = request.files.getlist('File')
    thematicArea = request.form['ThematicArea']
    financialSupport = request.form['FinancialSupport']
    amount = request.form['Amount']
    natureOfSupport = request.form['NatureOfSupport']
    sourceOfSupport = request.form['SourceOfSupport']
    aidDate = request.form['AidDate']
    processedBy = request.form['ProcessedBy']
    processedDate = request.form['ProcessedDate']
    status = db.update_support_data(sid, files, thematicArea, financialSupport, natureOfSupport, sourceOfSupport, aidDate, processedBy, processedDate, amount)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/sjflsupport', methods=['DELETE'])
@token_validator
def delete_support_data(sid):
    data = request.get_json()
    filename = data.get('filename')
    createdOn = data.get('createdOn')
    status = db.delete_support_data(sid, filename, createdOn)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/followups', methods=['GET'])
@token_validator
def get_all_followups(sid):
    status, data = db.get_followup_data_for_sid(sid, futype='COUNSELING') # TODO: change this to GENERAL
    return (jsonify(data), 200) if status == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/<sid>/insurancecards', methods=['GET'])
@token_validator
def get_all_insurance_cards(sid):
    status, data = db.fetchCardsForSID(sid)
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/<sid>/insurancecards', methods=['POST'])
@token_validator
def store_insurance_card(sid):
    files = request.files.getlist('File')
    status = db.saveInsuranceCardInfo(sid=sid,files=files)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/insurancecards', methods=['DELETE'])
@token_validator
def delete_insurance_card(sid):
    data = request.get_json()
    link = data.get('filelink', None)
    status = db.deleteCardsForSID(sid, link)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/basicdetails', methods=['GET'])
@token_validator
def get_basic_details(sid):
    status, data = db.get_survivor_info(sid)
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)

@app.route('/survivors/<sid>/budget', methods=['GET'])
@token_validator
def get_survivor_budget(sid):
    survivorBudget = db.get_budget(sid)
    return jsonify(survivorBudget)

@app.route('/survivors/<sid>/budget', methods=['POST'])
@token_validator
def add_survivor_budget(sid):
    req = request.get_json()
    name = req.get('name')
    items = req.get('items')
    failed = db.add_budget(sid, name, items)
    if not failed:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/UpdateBudget', methods=['PATCH'])
@token_validator
def update_survivor_budget(sid):
    req = request.get_json()
    items = req.get('items')
    failed = db.update_budget(items)
    if not failed:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/plan', methods=['GET'])
@token_validator
def get_survivor_plan(sid):
    survivorPlan = db.get_plan(sid)
    return jsonify(survivorPlan)

@app.route('/survivors/<sid>/plan', methods=['POST'])
@token_validator
def add_survivor_plan(sid):
    failed = db.add_plan(sid)
    if not failed:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/planUpdate', methods=['PATCH'])
@token_validator
def update_survivor_plan(sid):
    req = request.get_json()
    row = req.get('row')
    col = req.get('col')
    data = req.get('data')
    failed = db.update_plan(sid, row, col, data)
    if not failed:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/addPlanCol', methods=['PATCH'])
@token_validator
def add_survivor_plan_col(sid):
    req = request.get_json()
    newCol = req.get('newCol')
    colData = req.get('colData')
    failed = db.add_plan_col(sid, newCol, colData)
    if not failed:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/addPlanRow', methods=['PATCH'])
@token_validator
def add_survivor_plan_row(sid):
    req = request.get_json()
    newRow = req.get('newRow')
    rowData = req.get('rowData')
    failed = db.add_plan_row(sid, newRow, rowData)
    if not failed:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/deletePlanRow', methods=['DELETE'])
@token_validator
def delete_plan_row(sid):
    data = request.get_json()
    id = data.get("id")
    result = db.deletePlanRow(sid, id) 
    if not result:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/deletePlanCol', methods=['DELETE'])
@token_validator
def delete_plan_col(sid):
    data = request.get_json()
    id = data.get("id")
    result = db.deletePlanCol(sid, id) 
    if not result:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/deleteTableEntry', methods=['DELETE'])
@token_validator
def delete_budget_table(sid):
    data = request.get_json()
    id = data.get("id")
    result = db.deleteBudgetTable(id) 
    if not result:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/deleteRowEntry', methods=['DELETE'])
@token_validator
def delete_budget_row(sid):
    data = request.get_json()
    a_id = data.get("a_id")
    p_id = data.get("p_id")
    result = db.deleteBudgetRow(a_id, p_id) 
    if not result:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/addRowEntry', methods=['POST'])
@token_validator
def add_budget_row(sid):
    data = request.get_json()
    name = data.get("name")
    id = data.get("id")
    result = db.addBudgetRow(name, id) 
    if not result:
        return "Success", 200
    return "Failed", 400

@app.route('/survivors/<sid>/status', methods=['PATCH'])
@token_validator
def update_status(sid):
    data = request.get_json()
    updated_status = data.get('status')
    updated_remarks = data.get('remarks')
    status = db.update_status(sid, updated_status, updated_remarks)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/personalinfo', methods=['PATCH'])
@token_validator
def update_personal_info(sid):
    data = request.get_json()
    firstName = data.get('first_name')
    lastName = data.get('last_name')
    dateOfBirth = data.get('date_of_birth')
    gender = data.get('gender')
    nationality = data.get('nationality')
    bloodGroup = data.get('blood_group')
    admissionDate = data.get('admission_date')
    location = data.get('location')
    centre = data.get('centre')
    status = db.update_personal_info(sid, firstName, lastName, dateOfBirth, gender, nationality, bloodGroup, admissionDate, location, centre)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/family', methods=['PATCH'])
@token_validator
def update_family_details(sid):
    data = request.get_json()
    fatherName = data.get('father_name')
    fatherDOB = data.get('father_dob')
    fatherOccupation = data.get('father_occupation')
    fatherQualification = data.get('father_qualification')
    fatherIncome = data.get('father_income')
    motherName = data.get('mother_name')
    motherDOB = data.get('mother_dob')
    motherOccupation = data.get('mother_occupation')
    motherQualification = data.get('mother_qualification')
    motherIncome = data.get('mother_income')
    siblingDetails = data.get('sibling_details')
    remarks = data.get('remarks')
    status = db.update_family_details(sid, fatherName, fatherDOB, fatherOccupation, fatherQualification, fatherIncome, motherName,
                                        motherDOB, motherOccupation, motherQualification, motherIncome, siblingDetails, remarks)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/hospital', methods=['PATCH'])
@token_validator
def update_hospital_details(sid):
    data = request.get_json()
    hospitalName = data.get('hospital_name')
    hospitalRegNo = data.get('hospital_reg_no')
    hospitalRegDate = data.get('hospital_reg_date')
    doctorName = data.get('doctor_name')
    cancerStage = data.get('cancer_stage')
    cancerType = data.get('cancer_type')
    status = db.update_hospital_details(sid, hospitalName, hospitalRegNo, hospitalRegDate, doctorName, cancerStage, cancerType)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/communication', methods=['PATCH'])
@token_validator
def update_communication_details(sid):
    data = request.get_json()
    address = data.get('address')
    district = data.get('district')
    state = data.get('state')
    country = data.get('country')
    pincode = data.get('pincode')
    email = data.get('email')
    contact1 = data.get('contact1')
    relation1 = data.get('relation1')
    contact2 = data.get('contact2')
    relation2 = data.get('relation2')
    contact3 = data.get('contact3')
    relation3 = data.get('relation3')
    contact4 = data.get('contact4')
    relation4 = data.get('relation4')
    contact5 = data.get('contact5')
    relation5 = data.get('relation5')
    status = db.update_communication_details(sid, address, district, state, country, pincode, email, contact1,
                                             relation1, contact2, relation2, contact3, relation3, contact4, relation4,
                                             contact5, relation5)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/dispatchdate', methods=['POST'])
@token_validator
def update_kit_dispatch_date(sid):
    data = request.get_json()
    dispatch_date = data.get('date')
    status = db.update_dispatch_date(sid, dispatch_date)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/photo', methods=['PATCH'])
@token_validator
def update_photo(sid):
    file = request.files['File']
    status = db.update_photo(sid, file)
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/counseling', methods=['GET'])
@token_validator
def get_survivor_counselling_details(sid):
    status, data = db.get_followup_questions_with_answers_for_survivor(sid, futype='COUNSELING')
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/followup', methods=['POST'])
@token_validator
def add_survivor_counselling_details():
    data = request.get_json()
    status = db.add_new_followup_with_answers(futypeid=data.get('FOLLOWUPTYPEID'),
                                     sid=data.get('SID'),
                                     fubyid=data.get('FOLLOWEDUPBY'),
                                     answers=data.get('ANSWERS'))
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/followup/aspiration', methods=['POST'])
@token_validator
def add_survivor_aspiration_details():
    data = request.get_json()
    status = db.add_new_followup_with_answers(futypeid=data.get('FOLLOWUPTYPEID'),
                                     sid=data.get('SID'),
                                     fubyid=data.get('FOLLOWEDUPBY'),
                                     answers=data.get('ANSWERS'))
    return (status, 200) if 'SUCCESS' in status.upper() else ("Failed with error: " + status, 500)


@app.route('/survivors/<sid>/baseline', methods=['GET'])
@token_validator
def get_survivor_baseline_details(sid):
    status, data = db.get_followup_questions_with_answers_for_survivor(sid, futype='BASELINE')
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/<sid>/baseline', methods=['PATCH'])
@token_validator
def update_survivor_baseline_details(sid):
    pass


@app.route('/survivors/<sid>/aspiration', methods=['GET'])
@token_validator
def get_survivor_aspiration_details(sid):
    status, data = db.get_followup_questions_with_answers_for_survivor(sid, futype='ASPIRATION')
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/<sid>/aspiration', methods=['PATCH'])
@token_validator
def update_survivor_aspiration_details(sid):
    pass


@app.route('/survivors/<sid>/generalfollowup', methods=['GET'])
@token_validator
def get_survivor_general_details(sid):
    status, data = db.get_followup_questions(futype='GENERAL')
    return (jsonify(data), 200) if status  == 'SUCCESS' else ("Failed with error: " + data, 500)


@app.route('/survivors/<sid>/generalfollowup', methods=['POST'])
@token_validator
def add_survivor_general_followup():
    pass


# By default runs at localhost:5000
if __name__ == '__main__':
    app.run(debug=True)

from services.validation import validate_question, validate_upload, validate_records, ValidationError

def test_question_validation():
    assert validate_question('  sales? ')=='sales?'
    try: validate_question(' ')
    except ValidationError: pass
    else: assert False

def test_upload_rejects_non_csv_and_oversize():
    ok,errs=validate_upload('data.txt',4,b'test',1)
    assert not ok and any('csv' in e.lower() for e in errs)
    ok,errs=validate_upload('data.csv',2*1024*1024,b'x'*(2*1024*1024),1)
    assert not ok

def test_records_validation():
    assert validate_records([{'product_id':'P1'}])['ok']
    assert not validate_records([{}])['ok']

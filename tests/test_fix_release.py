"""Regression gates for the 1.0.3 audit fixes. No paid provider requests."""
import secrets,time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import accounts,db,spend

def reg(role='candidate'):
 c=TestClient(app);r=c.post('/api/auth/register',json={'email':secrets.token_hex(6)+'@example.invalid','password':'QA-password-123','agree':True,'age18':True,'role':role});assert r.status_code==200;return c

def test_phone_is_not_resume_authority_and_completion_gate():
 r=reg('recruiter');cid=r.post('/api/hub/campaigns',json={'name':'QA','modules':['voice','quiz'],'n_questions':3}).json()['id']
 a=TestClient(app);payload={'name':'QA','phone':'9876543210','consent':True};s=a.post('/api/s/o-'+cid+'/start',json=payload).json();token=s['token']
 assert TestClient(app).post('/api/s/o-'+cid+'/start',json=payload).status_code==409
 assert a.post('/api/s/o-'+cid+'/start',json={**payload,'resume_token':token}).json()['token']==token
 assert a.post('/api/s/'+token+'/finish',json={}).status_code==409
 assert a.post('/api/s/'+token+'/module',json={'module':'quiz','answers':[0]*10}).status_code==200
 assert a.post('/api/s/'+token+'/finish',json={}).status_code==409

def test_expired_session_not_readable():
 sid=db.create({'resume':'QA'})
 with accounts.Conn() as c:c.run('UPDATE sessions SET created=? WHERE id=?',(time.time()-db.TTL_SECONDS-1,sid))
 assert db.load(sid) is None

def test_affirmative_consent_and_origin_required():
 c=TestClient(app);p={'email':secrets.token_hex(6)+'@example.invalid','password':'QA-password-123'}
 assert c.post('/api/auth/register',json=p).status_code==400
 assert c.post('/api/auth/register',json={**p,'agree':True,'age18':True},headers={'Origin':'https://evil.invalid'}).status_code==403
 assert c.post('/api/auth/register',json={**p,'agree':True,'age18':True}).status_code==200
 assert c.post('/api/history',json={'kind':'star','data':{}},headers={'Origin':'https://evil.invalid'}).status_code==403

def test_spend_store_failure_stops_calls(monkeypatch):
 monkeypatch.setattr(spend,'_refresh',lambda:(_ for _ in ()).throw(RuntimeError()))
 with pytest.raises(spend.BudgetExceeded):spend.check()

def test_spend_admission_reserves_and_rejects(monkeypatch):
 monkeypatch.setattr(spend,'TOTAL_CAP',0.1);monkeypatch.setattr(spend,'DAILY_CAP',0.1)
 with accounts.Conn() as c:
  c.run('CREATE TABLE IF NOT EXISTS spend(day TEXT PRIMARY KEY,micro BIGINT NOT NULL)');c.run('DELETE FROM spend')
 h=spend.reserve(.06)
 with pytest.raises(spend.BudgetExceeded):spend.reserve(.06)
 spend.settle(h,.01)
 assert spend.reserve(.06)

def test_recovery_code_one_use_and_session_revocation():
 c=reg();email=c.get('/api/auth/me').json()['user']['email'];code=c.post('/api/auth/recovery-code',json={}).json()['code']
 d=TestClient(app);payload={'email':email,'code':code,'password':'NEW-QA-password-123'}
 assert d.post('/api/auth/recover',json={**payload,'code':'wrong'}).status_code==401
 assert d.post('/api/auth/recover',json=payload).status_code==200
 assert c.get('/api/auth/me').json()['user'] is None
 assert d.post('/api/auth/recover',json=payload).status_code==401
 assert d.post('/api/auth/login',json={'email':email,'password':'NEW-QA-password-123'}).status_code==200

def test_api_revocation():
 c=reg('recruiter');k=c.post('/api/hub/org/apikey',json={}).json()['api_key'];p=TestClient(app)
 assert p.get('/api/v1/results',headers={'X-API-Key':k}).status_code==200
 assert c.delete('/api/hub/org/apikey').status_code==200
 assert p.get('/api/v1/results',headers={'X-API-Key':k}).status_code==401

def test_shared_limiter_survives_instances():
 from app.guard import shared_limit
 key=secrets.token_hex(12)
 assert shared_limit('qa',key,2,60)
 assert shared_limit('qa',key,2,60)
 assert not shared_limit('qa',key,2,60)

def test_session_restore_does_not_leak_reference_answers():
 c=TestClient(app);s=c.post('/api/session',json={'resume':'QA engineer with five years of automation and API testing experience.','role':'QA','country':'India','followups':True}).json()
 r=c.get('/api/session/'+s['session_id']+'/state');assert r.status_code==200
 assert 'refs' not in r.json() and 'resume' not in r.json()
 c.post('/api/session/'+s['session_id']+'/answer',json={'answer':'I built tests and checked their results with developers.'})
 r=c.get('/api/session/'+s['session_id']+'/state');assert r.status_code==200
 if r.json()['pending']:assert r.json()['question']['type']=='follow-up'

def test_empty_module_and_voice_not_accepted():
 r=reg('recruiter');cid=r.post('/api/hub/campaigns',json={'name':'QA','modules':['voice','quiz','reading','typing']}).json()['id']
 c=TestClient(app);t=c.post('/api/s/o-'+cid+'/start',json={'name':'QA','phone':'9876543210','consent':True}).json()['token']
 assert c.post('/api/s/'+t+'/voice',json={'idx':0,'text':''}).status_code==400
 for module in ['quiz','reading','typing']:
  assert c.post('/api/s/'+t+'/module',json={'module':module}).status_code==400

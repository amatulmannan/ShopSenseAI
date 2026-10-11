from types import SimpleNamespace
import sys, types
import llm_provider as lp

class FakeProviderException(Exception):
    def __init__(self, *args, **kwargs): super().__init__(*args)

def fake_sdk(monkeypatch, retrieve=None, create=None):
    if not lp.LLM_MODEL: monkeypatch.setattr(lp,'LLM_MODEL','fake-model')
    class FakeClient:
        def __init__(self, **kwargs):
            def do_retrieve(model):
                if retrieve: return retrieve(model)
                return {'id':model}
            def do_create(**kwargs):
                if create: return create(**kwargs)
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Evidence-based explanation.'))])
            self.models=SimpleNamespace(retrieve=do_retrieve)
            self.chat=SimpleNamespace(completions=SimpleNamespace(create=do_create))
    sdk=types.ModuleType('openai'); sdk.OpenAI=FakeClient
    for name in ['AuthenticationError','RateLimitError','APITimeoutError','APIConnectionError','NotFoundError','BadRequestError']:
        setattr(sdk,name,type(name,(FakeProviderException,),{}))
    monkeypatch.setitem(sys.modules,'openai',sdk)
    return sdk

def test_missing_key_status(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','')
    assert lp.provider_status().state == 'missing'
    status=lp.test_connection()
    assert status.state == 'missing' and 'API key' in status.message

def test_connection_success_mocked(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key'); monkeypatch.setattr(lp,'LLM_MODEL','fake-model')
    fake_sdk(monkeypatch)
    status=lp.test_connection()
    assert status.state=='connected' and 'verified' in status.message

def test_invalid_key_maps_to_actionable_error(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key')
    sdk=fake_sdk(monkeypatch, retrieve=lambda model: (_ for _ in ()).throw(sys.modules['openai'].AuthenticationError('invalid')))
    status=lp.test_connection()
    assert status.state=='error' and 'Authentication failed' in status.message

def test_timeout_error_maps_to_actionable_error(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key')
    fake_sdk(monkeypatch, retrieve=lambda model: (_ for _ in ()).throw(sys.modules['openai'].APITimeoutError('timeout')))
    status=lp.test_connection()
    assert status.state=='error' and 'timed out' in status.message

def test_ai_payload_contains_only_question_and_compact_evidence(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key'); monkeypatch.setattr(lp,'LLM_MODEL','fake-model')
    captured={}
    fake_sdk(monkeypatch, create=lambda **kwargs: (captured.update(kwargs) or SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Evidence-based explanation.'))])))
    result=lp.explain_with_llm('total sales?',{'answer':'10.00','evidence':['2 rows']})
    assert result=='Evidence-based explanation.'
    joined=str(captured['messages'])
    assert 'total sales?' in joined and '10.00' in joined
    assert 'customer_name' not in joined and 'full_dataset' not in joined

def test_quota_billing_error_is_actionable(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key')
    fake_sdk(monkeypatch, retrieve=lambda model: (_ for _ in ()).throw(sys.modules['openai'].RateLimitError('insufficient_quota billing quota')))
    status=lp.test_connection()
    assert status.state=='error' and 'quota or billing' in status.message

def test_network_error_is_actionable(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key')
    fake_sdk(monkeypatch, retrieve=lambda model: (_ for _ in ()).throw(sys.modules['openai'].APIConnectionError('network unavailable')))
    status=lp.test_connection()
    assert status.state=='error' and 'network' in status.message.lower()

def test_unsupported_model_is_actionable(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key')
    fake_sdk(monkeypatch, retrieve=lambda model: (_ for _ in ()).throw(sys.modules['openai'].NotFoundError('model missing')))
    status=lp.test_connection()
    assert status.state=='error' and 'could not find this model' in status.message

def test_missing_model_configuration_is_reported(monkeypatch):
    monkeypatch.setattr(lp,'LLM_API_KEY','format-only-test-key')
    monkeypatch.setattr(lp,'LLM_MODEL','')
    status=lp.test_connection()
    assert status.state=='missing' and 'model name' in status.message.lower()

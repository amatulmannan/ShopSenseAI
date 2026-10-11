from i18n import t, LANGUAGES

def test_languages_registered():
    assert set(LANGUAGES)=={'English','اردو','Roman Urdu'}

def test_translation_fallback_is_safe():
    assert t('English','dashboard')=='Dashboard'
    assert t('اردو','dashboard')=='ڈیش بورڈ'
    assert t('Roman Urdu','dashboard')=='Dashboard'

def test_parameterized_translation():
    assert t('English','valid_sales_rows',n=4)=='Across 4 sales rows'

def test_required_settings_and_privacy_labels_exist_for_all_languages():
    for language in LANGUAGES:
        assert t(language,'test_connection')
        assert t(language,'privacy_heading')
        assert t(language,'ask_ai_optin')
        assert t(language,'quality_heading')

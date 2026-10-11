from pathlib import Path

def test_app_avoids_arrow_backed_dataframe_renderers():
    source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf-8')
    assert 'st.dataframe(' not in source
    assert 'st.table(' not in source
    assert 'st.line_chart(' not in source
    assert 'st.plotly_chart(' in source

def test_app_has_per_question_consent_and_real_provider_call():
    source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf-8')
    assert 'st.checkbox(t(lang,"ask_ai_optin")' in source
    assert 'explain_with_llm(question,evidence)' in source
    assert 'test_connection()' in source

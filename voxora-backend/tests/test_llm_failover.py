import asyncio
import os
import json
import logging
from unittest.mock import patch, AsyncMock
from uuid import uuid4

# Setup basic logging to see warnings
logging.basicConfig(level=logging.WARNING)

async def test_all():
    # Import inside async to ensure event loop is set up for any clients
    from app.services.text_to_sql import text_to_sql_engine
    from app.services.llm_service import llm_service, get_settings
    from app.integrations.bigquery.client import bigquery_client
    import groq

    settings = get_settings()

    async def run_sql_query(question: str, provider_force: str = None) -> tuple[str, str, float]:
        original_provider = settings.llm_provider
        if provider_force:
            settings.llm_provider = provider_force
            
        try:
            sql, provider = await text_to_sql_engine.generate_sql(question)
            print(f"Generated SQL via {provider}:\n{sql}\n")
            
            # Execute query
            res = await bigquery_client.execute_query(sql)
            row = res["rows"][0]
            val = list(row.values())[0] if row else 0.0
            
            if provider_force:
                settings.llm_provider = original_provider
                
            return sql, provider, float(val) if val else 0.0
        except Exception as e:
            if provider_force:
                settings.llm_provider = original_provider
            print(f"Query generation failed: {e}")
            return "", "error", 0.0


    print("\n--- Test 1: Groq only, 5x ---")
    val_groq = None
    for i in range(5):
        sql, prov, val = await run_sql_query("what's today's revenue (September 12, 2026)", "groq")
        if val_groq is None:
            val_groq = val
        assert val == val_groq, f"Mismatch in Groq runs: {val} != {val_groq}"
    print(f"Groq consistent result: {val_groq}")


    print("\n--- Test 2: Gemini only ---")
    sql, prov, val_gemini = await run_sql_query("what's today's revenue (September 12, 2026)", "gemini")
    assert val_gemini == val_groq, f"Gemini ({val_gemini}) != Groq ({val_groq})"
    print(f"Gemini consistent result: {val_gemini}")


    print("\n--- Test 3: Differently phrased (Groq) ---")
    q1 = "revenue today for September 12, 2026"
    q2 = "how much did we make today September 12, 2026"
    q3 = "today's total sales September 12, 2026"
    
    _, _, v1 = await run_sql_query(q1, "groq")
    _, _, v2 = await run_sql_query(q2, "groq")
    _, _, v3 = await run_sql_query(q3, "groq")
    
    assert v1 == v2 == v3, f"Phrasing mismatch: {v1}, {v2}, {v3}"
    print(f"Phrasing matched: {v1}")


    print("\n--- Test 4: Simulate genuine Groq failure (Auth Error) ---")
    with patch.object(llm_service, '_call_groq', new_callable=AsyncMock) as mock_groq:
        import httpx
        dummy_request = httpx.Request("POST", "https://api.groq.com")
        dummy_response = httpx.Response(401, request=dummy_request)
        mock_groq.side_effect = groq.AuthenticationError("Invalid API Key", response=dummy_response, body={})
        
        sql, prov, val = await run_sql_query("what's today's revenue (September 12, 2026)", "groq")
        assert prov == "gemini", f"Expected gemini, got {prov}"
        print(f"Failover successful to Gemini. Val: {val}")


    print("\n--- Test 5: Simulate UNCLASSIFIED exception type ---")
    with patch.object(llm_service, '_call_groq', new_callable=AsyncMock) as mock_groq:
        mock_groq.side_effect = ValueError("Some weird internal error")
        
        sql, prov, val = await run_sql_query("what's today's revenue (September 12, 2026)", "groq")
        assert prov == "gemini", f"Expected gemini, got {prov}"
        print(f"Unclassified failover successful to Gemini. Val: {val}")


    print("\n--- Test 6: 3-part consistency check ---")
    _, _, val_a = await run_sql_query("last month's revenue (August 2026)", "groq")
    _, _, val_b = await run_sql_query("the month before (July 2026)", "groq")
    _, _, val_c = await run_sql_query("total for both months August 2026 and July 2026", "groq")
    
    print(f"August: {val_a}")
    print(f"July: {val_b}")
    print(f"Total: {val_c}")
    assert abs((val_a + val_b) - val_c) < 1.0, f"Math mismatch: {val_a} + {val_b} != {val_c}"
    print("Consistency check passed!")
    
    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test_all())

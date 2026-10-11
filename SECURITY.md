# Security and privacy notes

- API credentials are read from the server-side `.env` file and are never rendered in the UI. Do not commit `.env`, paste keys into screenshots, or share key-bearing logs.
- Uploaded CSVs are processed in the Streamlit session and are not intentionally written to disk by this application. Hosting platforms may have their own session, proxy, or diagnostic logging policies; review those before deployment.
- By default, business questions use deterministic local calculations only. The optional AI explanation checkbox must be enabled for each question before the app sends the question plus a compact calculated evidence object to the configured provider. The full uploaded CSVs, customer-level rows, and full product lists are not sent by this workflow.
- The Settings connection test sends a model-access request but no business data.
- Do not upload customer names, phone numbers, addresses, payment details, credentials, or other personal/sensitive information unless your business has an approved legal and privacy basis.
- CSV uploads are treated as data, never executed. HTML table output escapes cell contents. If exporting business-derived CSV is added later, spreadsheet formula injection must be neutralized before export.
- This is a local-first small-business application, not an authenticated multi-tenant production service. Before public deployment, add authentication, authorization, HTTPS termination, rate limiting, operational monitoring, and a documented retention policy.
- If Windows Application Control blocks PyArrow DLL loading, do not disable or bypass the policy. This UI avoids Streamlit's Arrow-backed dataframe/table rendering paths by using escaped HTML tables and Plotly charts. If the runtime itself is blocked, ask the administrator to approve the signed/known Python distribution and package files through the organization's normal policy process.

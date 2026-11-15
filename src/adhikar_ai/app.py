"""Browse the curated dataset using local keyword search and filters."""

import json
from pathlib import Path

import streamlit as st

from adhikar_ai import document_matching, eligibility, rag, semantic_search, voice


DATA_PATH = Path(__file__).resolve().parents[2] / "data/processed/schemes.json"
FACT_FIELDS = {
    "benefits": "Benefits",
    "eligibility_conditions": "Published eligibility conditions",
    "exclusions": "Exclusions",
    "required_documents": "Required documents",
    "application_process": "Application process",
}


def label(value: str) -> str:
    """Present stored taxonomy values without changing their meaning."""
    return "All India" if value == "all_india" else value.replace("_", " ").title()


def render_scheme(scheme: dict) -> None:
    """Keep each fact's evidence links and qualifications beside its text."""
    sources = {source["source_id"]: source for source in scheme["sources"]}
    with st.expander(scheme["scheme_name"]):
        st.caption(
            f"{scheme['scheme_id']} · {label(scheme['government_level'])} · "
            f"{label(scheme['state'])} · {label(scheme['category'])}"
        )
        st.caption(
            f"Verification date: {scheme['verification_date']} · "
            f"Effective date: {scheme['effective_date']}"
        )
        for field, heading in FACT_FIELDS.items():
            fact = scheme[field]
            st.markdown(f"**{heading} — {fact['status']}**")
            for item in fact["items"]:
                st.markdown(f"- {item}")
            st.write(fact["note"])
            if fact["source_ids"]:
                st.markdown("Sources: " + "; ".join(
                    f"[{sources[sid]['title']}]({sources[sid]['url']})"
                    for sid in fact["source_ids"]
                ))
        st.markdown("**Verification notes**")
        for note in scheme["verification_notes"]:
            st.write(note)
        st.markdown(f"[Official source]({scheme['official_source_url']})")
        st.text(scheme["source_passage"])
        st.markdown("**Source details**")
        for source in scheme["sources"]:
            st.markdown(f"[{source['title']}]({source['url']})")
            st.caption(f"Accessed: {source['accessed_on']}")
            st.write(source["sections"])


def main() -> None:
    """Search descriptive records without making eligibility decisions."""
    st.set_page_config(page_title="AdhikarAI", page_icon="🇮🇳")
    st.title("AdhikarAI — Government Scheme Discovery")
    st.info(
        "Browse published scheme information. Eligibility mode checks documented criteria only, not entitlement. "
        "Records may be partial or historical; check the cited official sources for current terms."
    )
    try:
        schemes = json.loads(DATA_PATH.read_text(encoding="utf-8"))["schemes"]
    except (OSError, ValueError, KeyError):
        st.error("The scheme dataset could not be loaded. Please restore the curated dataset and retry.")
        return

    mode = st.radio("Search mode", ["Keyword", "Semantic", "Q&A", "My documents", "Profiles", "Eligibility"], horizontal=True, key="search_mode")
    if mode == "Eligibility":
        render_eligibility(schemes)
        return
    if mode == "Profiles":
        render_profiles()
        return
    if mode == "My documents":
        render_document_matching()
        return
    render_voice_input("search_voice", "query")
    query = st.text_input(
        "Search government schemes", key="query",
        placeholder="Scheme name, ID, benefit, or keyword",
        help="Keyword mode matches all words. Semantic mode finds related meanings locally.",
    )
    filters = {}
    for column, field, heading in zip(
        st.columns(3),
        ("government_level", "state", "category"),
        ("Government level", "Coverage", "Category"),
    ):
        with column:
            filters[field] = st.selectbox(
                heading, ["all"] + sorted({scheme[field] for scheme in schemes}),
                format_func=label, key=field,
            )
    st.caption("Coverage filters the recorded scope: All India schemes also cover West Bengal.")
    if mode in ("Semantic", "Q&A"):
        render_semantic_search(query, filters, qa=mode == "Q&A")
        return
    terms = query.casefold().split()
    results = []
    for scheme in schemes:
        searchable = " ".join(
            [scheme["scheme_name"], scheme["scheme_id"], label(scheme["category"]),
             label(scheme["state"]), label(scheme["government_level"])]
            + [text for field in FACT_FIELDS
               for text in scheme[field]["items"] + [scheme[field]["note"]]]
        ).casefold()
        if (all(value == "all" or scheme[field] == value for field, value in filters.items())
                and all(term in searchable for term in terms)):
            results.append(scheme)
    st.caption(f"Showing {len(results)} of {len(schemes)} schemes")
    if not results:
        st.info("No schemes match your search and filters. Try fewer keywords or choose All in the filters.")
    for scheme in results:
        render_scheme(scheme)


def render_eligibility(schemes):
    st.subheader("Check documented eligibility criteria")
    st.caption(
        "Deterministic checks of the recorded sources, not an official approval or a guarantee of current entitlement. "
        "No LLM is used. Answers stay in this session; no identity or bank account numbers are needed."
    )
    if st.button("Clear eligibility answers", key="clear_eligibility"):
        for key in list(st.session_state):
            if key.startswith("elig_"):
                del st.session_state[key]
        st.rerun()
    by_id = {s["scheme_id"]: s for s in schemes}
    sid = st.selectbox("Scheme to check", list(by_id),
                       format_func=lambda key: by_id[key]["scheme_name"], key="elig_scheme")
    scheme = by_id[sid]
    st.caption(f"Source verification date: {scheme['verification_date']}. Checks use recorded evidence, not live verification.")
    if sid in eligibility.SUSPENDED:
        st.info(eligibility.SUSPENDED[sid])
    with st.form("eligibility_form"):
        purpose = st.selectbox("Application type", ["New application", "Renewal / continuation / claim"], key="elig_purpose")
        profile = {}
        for key in eligibility.SCHEME_FIELDS.get(sid, []):
            kind, heading = eligibility.FIELDS[key]
            widget_key = f"elig_{sid}_{key}"
            if kind == "bool":
                answer = st.selectbox(heading, ["Unknown", "Yes", "No"], key=widget_key)
                profile[key] = {"Unknown": None, "Yes": True, "No": False}[answer]
            else:
                value = st.text_input(heading, key=widget_key, help="Leave blank if unknown. Use digits; do not enter identifying numbers.")
                try:
                    profile[key] = float(value) if value.strip() else None
                except ValueError:
                    profile[key] = None
        submitted = st.form_submit_button("Check criteria")
    if submitted:
        result = eligibility.evaluate(scheme, profile, new_application=purpose == "New application")
        st.subheader(result["outcome"])
        st.caption("Meets criteria refers only to the documented checks below. A known failed requirement takes precedence over missing answers; otherwise missing or unresolved information prevents a positive result.")
        for check in result["checks"]:
            st.write(f"{check['outcome']}: {check['criterion']}")
            for source in check["sources"]:
                st.markdown(f"[{source['title']}]({source['url']})")
            with st.expander("Recorded evidence: " + check["criterion"]):
                for text in check["evidence"]:
                    st.write(text)
                st.write(check["note"])
        for note in scheme["verification_notes"]:
            st.caption(note)
    render_scheme(scheme)


def render_document_matching():
    st.subheader("Find schemes from your documents")
    st.write("Upload a text-based PDF or TXT file, or describe your circumstances below.")
    st.caption(
        "Processed locally in memory. Personal uploads are not saved, added to Chroma, "
        "or sent to Groq. Remove identity numbers and other details you do not need for matching."
    )
    generation = st.session_state.get("upload_generation", 0)
    if st.button("Clear documents and details", key="clear_documents"):
        st.session_state["upload_generation"] = generation + 1
        st.session_state.pop(f"profile_{generation}", None)
        st.session_state.pop(f"profile_source_{generation}", None)
        st.rerun()
    uploaded = st.file_uploader(
        "Your document (PDF or TXT, up to 5 MB / 20 PDF pages)",
        type=["pdf", "txt"], key=f"personal_upload_{generation}",
    )
    profile_key = f"profile_{generation}"
    source_key = f"profile_source_{generation}"
    # Track only the upload's digest to detect replacement, not a duplicate of its text.
    import hashlib
    upload_digest = hashlib.sha256(uploaded.getvalue()).hexdigest() if uploaded else None
    if st.session_state.get(source_key) != upload_digest:
        st.session_state[source_key] = upload_digest
        st.session_state[profile_key] = ""
        if uploaded:
            try:
                st.session_state[profile_key] = document_matching.extract_upload(
                    uploaded.name, uploaded.getvalue(),
                )
            except ValueError as exc:
                st.warning(str(exc))
    render_voice_input(f"document_voice_{generation}", profile_key)
    profile = st.text_area(
        "Review extracted text or enter your details",
        key=profile_key, height=200, max_chars=document_matching.MAX_CHARS,
        help="Include relevant details such as occupation, state, age, and the support you need. Correct extraction errors before matching.",
    )
    state = st.selectbox("Where do you live?", ["Not specified", "West Bengal", "Another state"],
                         key="profile_state")
    st.caption("West Bengal includes national schemes. Another state shows national schemes only.")
    if not st.button("Find potential schemes", key="match_documents"):
        return
    if not profile.strip():
        st.info("Upload a readable document or enter your details first.")
        return
    render_potential_matches(profile, state)


def render_potential_matches(profile, state, member_label=""):
    try:
        documents = semantic_search.load_documents()
        filters = {"kind": "scheme"}
        if state == "Another state":
            filters["state"] = "all_india"
        with st.spinner("Matching locally..."):
            matches = semantic_search.search(documents, profile, 5, filters)
    except semantic_search.IndexNotReady:
        st.info("Build the local index in Semantic mode, then return here to find schemes.")
        return
    except Exception:
        st.error("Local matching is unavailable. Check the local model and index, then try again.")
        return
    st.warning(
        "Potential matches only. Similarity to your documents does not establish eligibility. "
        "Check every published condition, exclusion, and current application requirement."
    )
    if not matches:
        st.info("No sufficiently relevant schemes found")
    for rank, match in enumerate(matches, 1):
        scheme = json.loads(match["metadata"]["evidence_json"])
        st.subheader(f"{rank}. {scheme['scheme_name']}")
        st.caption("Matched by document meaning. Eligibility remains unverified.")
        for item in scheme["application_process"]["items"]:
            st.write(item)
        st.write(scheme["application_process"]["note"])
        links = document_matching.application_links(scheme)
        if links:
            for link in links:
                st.link_button("Apply / official instructions — " + link["title"] + member_label, link["url"])
        else:
            st.info("Application instructions are not documented for this scheme.")
            st.link_button("Official scheme information" + member_label, scheme["official_source_url"])
        render_scheme(scheme)


def render_voice_input(key, target):
    with st.popover("Voice input"):
        st.caption("Record up to two minutes. Clicking Transcribe sends only this recording to Groq. Review the text before using it. App recordings are not saved to disk.")
        enabled = rag.configured()
        if not enabled:
            st.info("Configure GROQ_API_KEY for voice transcription, or type instead.")
        audio = st.audio_input("Record your details", key=key, disabled=not enabled)
        if st.button("Transcribe into text", key=key + "_submit",
                     disabled=not enabled or audio is None):
            with st.spinner("Transcribing recording..."):
                result = voice.transcribe(audio.getvalue())
            if result["error"]:
                st.warning(result["error"])
            else:
                st.session_state[target] = result["text"]
                st.success("Transcribed. Review and correct the text below before continuing.")


def render_profiles():
    st.subheader("Individual and family profiles")
    st.caption("Profiles are saved only in this browser session, not to disk or an account. Avoid identity numbers. A family profile keeps each member's circumstances separate.")
    if st.button("Delete all saved profiles", key="delete_profiles"):
        for key in list(st.session_state):
            if key.startswith("person_") or key.startswith("household_") or key == "saved_profiles":
                del st.session_state[key]
        st.rerun()
    kind = st.radio("Profile type", ["Individual", "Family"], key="profile_kind")
    saved = st.session_state.get("saved_profiles", {}).get(kind, {})
    prefix = "person_" if kind == "Individual" else "household_"
    states = ["Not specified", "West Bengal", "Another state"]
    state = st.selectbox("Home state", states, index=states.index(saved.get("state", "Not specified")),
                         key=prefix + "state")
    count = 1 if kind == "Individual" else int(st.number_input(
        "Family members", min_value=1, max_value=10, value=len(saved.get("members", [])) or 2,
        step=1, key=prefix + "count",
    ))
    members = []
    for index in range(count):
        previous = saved.get("members", [])
        member = previous[index] if index < len(previous) else {}
        key = prefix + str(index)
        st.markdown(f"**{'Your details' if kind == 'Individual' else 'Member ' + str(index + 1)}**")
        name = st.text_input("Name or nickname (optional)", value=member.get("name", ""), key=key + "_name",
                             max_chars=80)
        age = st.number_input("Age (0 means not provided)", min_value=0, max_value=120,
                              value=member.get("age", 0), key=key + "_age")
        occupation = st.text_input("Occupation or student status", value=member.get("occupation", ""),
                                   key=key + "_occupation", max_chars=200)
        detail_key = key + "_details"
        render_voice_input(key + "_voice", detail_key)
        details = st.text_area("Support needed and relevant circumstances", value=member.get("details", ""),
                               key=detail_key, max_chars=10000)
        members.append({"name": name, "age": age, "occupation": occupation, "details": details})
    if st.button("Save profile for this session", key="save_profile"):
        profiles = dict(st.session_state.get("saved_profiles", {}))
        profiles[kind] = {"state": state, "members": members}
        st.session_state["saved_profiles"] = profiles
        st.success(f"{kind} profile saved for this session.")
    if st.button("Find schemes for this profile", key="match_profile"):
        st.caption("Using the details currently shown. Matching is performed separately for each person.")
        for index, member in enumerate(members):
            st.subheader(member["name"] or f"Member {index + 1}")
            if not member["occupation"].strip() and not member["details"].strip():
                st.info("Add an occupation or describe the support needed for this member.")
                continue
            # Names are display labels, not matching signals.
            profile = f"State: {state}. " + member["occupation"] + ". " + member["details"]
            if member["age"]:
                profile += f" Age: {member['age']}."
            render_potential_matches(profile, state, member_label=f" (member {index + 1})")


def render_semantic_search(query, filters, qa=False):
    """Present retrieved source content without generating an answer."""
    st.caption(
        "Semantic ranking is not an eligibility decision or a confidence score. "
        "The first index build downloads a free embedding model; inference runs locally."
    )
    st.caption("PDF chunks have no scheme taxonomy: selecting a scheme filter excludes PDF results.")
    top_k = st.slider("Top matches", 1, 20, 5)
    if qa:
        st.caption("Ask a question in the search box. Answering sends your question and retrieved evidence to Groq.")
        if not rag.configured():
            st.info("Set GROQ_API_KEY in the project .env or server environment to enable Q&A. Semantic search remains available.")
    try:
        documents = semantic_search.load_documents()
        pdf_count = sum(doc["metadata"]["kind"] == "pdf" for doc in documents)
        st.caption(f"Available sources: {len(documents) - pdf_count} schemes, {pdf_count} PDF chunks")
        if st.button("Build / update local index"):
            with st.spinner("Building local semantic index..."):
                count = semantic_search.build_index(documents)
            st.success(f"Local index ready: {count} documents.")
        if not query.strip():
            st.info("Enter a question or description to find semantic matches.")
            return
        with st.spinner(
            "Loading the local search model and searching. The first search after "
            "starting the dashboard can take a few minutes; later searches reuse the model.",
            show_time=True,
        ):
            matches = semantic_search.search(documents, query, top_k, filters)
    except semantic_search.IndexNotReady as exc:
        st.info(str(exc))
        return
    except Exception:
        st.error("Semantic search is unavailable.")
        st.info("Check dependencies and model download access, then build the index again. Keyword search remains available.")
        return
    if not matches:
        st.info("No sufficiently relevant schemes found")
        return
    if qa and st.button("Answer from sources", disabled=not rag.configured(), key="answer"):
        with st.spinner("Selecting supported evidence..."):
            result = rag.answer(query, matches)
        if result["status"] == "answered":
            st.write(result["message"])
        else:
            st.info(result["message"])
        for passage in result["passages"]:
            st.markdown(f"**{passage['title']}**")
            st.text(passage["text"])
            st.text(passage["qualification"])
            st.caption(f"Source date: {passage['date']}" + (
                f" · page {passage['page']}" if "page" in passage else ""
            ))
            for source in passage["sources"]:
                st.markdown(f"[{source['title']}]({source['url']})")
    for rank, match in enumerate(matches, 1):
        meta = match["metadata"]
        st.caption(f"Match {rank} · cosine distance {match['distance']:.3f} (lower is closer)")
        evidence = json.loads(meta["evidence_json"])
        if meta["kind"] == "scheme":
            render_scheme(evidence)
        else:
            with st.expander(f"{meta['title']} — page {meta['page_number']}"):
                st.write(match["text"])
                st.markdown(f"[Official PDF]({meta['url']}) · page {meta['page_number']}")
                if meta["resolved_url"] != meta["url"]:
                    st.markdown(f"[Downloaded PDF]({meta['resolved_url']})")
                st.caption(f"Retrieved: {meta['retrieved_at']} · Publisher: {evidence['source']['publisher']}")
                st.caption(f"Extraction status: {meta['page_status']}")
                if meta["page_status"] != "extracted":
                    st.warning("This extracted text requires review against the original PDF.")
                st.caption(
                    f"Chunk: {evidence['chunk_id']} · "
                    f"Cleaned-page offsets: {evidence['start_char']}–{evidence['end_char']} · "
                    f"Document SHA-256: {meta['document_sha256']}"
                )


if __name__ == "__main__":
    main()
